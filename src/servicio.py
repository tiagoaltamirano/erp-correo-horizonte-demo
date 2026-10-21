"""Servicio ficticio y control de escenarios de la demostración local."""
import asyncio
import json
import os
import time
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

DATA = Path(os.getenv("DATA_DIR", "/datos"))
OPERACIONES = ("admision", "seguimiento", "facturacion")
ESCENARIOS = ("normal", "caida", "demora", "errores")
estado = {"escenario": "normal", "fase": "en_vivo", "preparando": False, "historial": []}
secuencias = Counter()
activas = set()


def ahora():
    return datetime.now(timezone.utc).isoformat()


def guardar():
    DATA.mkdir(parents=True, exist_ok=True)
    temp = DATA / "estado.tmp"
    temp.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf8")
    temp.replace(DATA / "estado.json")


def cambiar(escenario):
    estado["escenario"] = escenario
    secuencias.clear()
    evento = {"timestamp": ahora(), "escenario": escenario, "fase": estado["fase"]}
    estado["historial"] = (estado["historial"] + [evento])[-100:]
    guardar()
    return evento


async def trafico():
    async with httpx.AsyncClient(timeout=8) as cliente:
        async def pedir(tipo):
            try:
                await cliente.post(f"http://127.0.0.1:8000/erp/operaciones/{tipo}")
            except httpx.HTTPError:
                pass
        while True:
            for tipo in OPERACIONES:
                t = asyncio.create_task(pedir(tipo))
                activas.add(t)
                t.add_done_callback(activas.discard)
            await asyncio.sleep(0.5)


@asynccontextmanager
async def vida(app):
    DATA.mkdir(parents=True, exist_ok=True)
    anterior = DATA / "estado.json"
    if anterior.exists():
        try:
            previo = json.loads(anterior.read_text(encoding="utf8"))
            estado["historial"] = previo.get("historial", [])
            estado["simulacion_previa"] = previo.get("simulacion_previa")
            if estado["simulacion_previa"] and estado["simulacion_previa"].get("estado") == "en_curso":
                estado["simulacion_previa"]["estado"] = "interrumpida"
        except (ValueError, OSError):
            pass
    cambiar("normal")
    tarea = asyncio.create_task(trafico())
    yield
    tarea.cancel()
    for t in list(activas):
        t.cancel()


app = FastAPI(title="Simulación del ERP de Correo Horizonte", lifespan=vida)


class Escenario(BaseModel):
    escenario: str


@app.get("/erp/health")
async def health():
    caido = estado["escenario"] == "caida"
    return JSONResponse({"servicio": "ERP simulado", "disponible": not caido}, status_code=503 if caido else 200)


@app.post("/erp/operaciones/{tipo}")
async def operar(tipo: str):
    if tipo not in OPERACIONES:
        raise HTTPException(404, "Operación inexistente")
    escenario = estado["escenario"]
    fase = estado["fase"]
    if escenario == "caida":
        # El servicio rechaza la solicitud antes de ejecutar una operación de negocio.
        return JSONResponse({"detalle": "Servicio no disponible"}, status_code=503)
    secuencias[tipo] += 1
    numero = secuencias[tipo]
    inicio = time.monotonic()
    await asyncio.sleep(3.05 if escenario == "demora" else 0.12)
    fallo = escenario == "errores" and numero % 10 == 0
    registro = {"id": str(uuid.uuid4()), "timestamp": ahora(), "operacion": tipo,
                "duration_ms": round((time.monotonic() - inicio) * 1000, 3),
                "resultado": "fallo" if fallo else "exito", "fase": fase}
    with (DATA / "operaciones.jsonl").open("a", encoding="utf8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return JSONResponse({"id": registro["id"], "resultado": registro["resultado"]}, status_code=500 if fallo else 200)


@app.get("/api/status")
def status():
    return {**estado, "hora_utc": ahora(), "operaciones_por_segundo": 6}


@app.post("/api/escenario")
def escenario(datos: Escenario):
    if estado["preparando"]:
        raise HTTPException(409, "La simulación previa está en curso")
    if datos.escenario not in ESCENARIOS:
        raise HTTPException(422, "Escenario inválido")
    return cambiar(datos.escenario)


async def preparar():
    estado["preparando"] = True
    estado["fase"] = "simulacion_previa"
    simulacion = {"id": str(uuid.uuid4()), "inicio": ahora(), "estado": "en_curso", "etapas": []}
    estado["simulacion_previa"] = simulacion
    try:
        for nombre, segundos in [("normal", 35), ("demora", 55), ("normal", 40), ("errores", 55), ("normal", 40)]:
            evento = cambiar(nombre)
            etapa = {**evento, "duracion_prevista_s": segundos}
            simulacion["etapas"].append(etapa)
            guardar()
            await asyncio.sleep(segundos)
            etapa["fin"] = ahora()
        simulacion.update({"fin": ahora(), "estado": "completa"})
    finally:
        estado["fase"] = "en_vivo"
        estado["preparando"] = False
        cambiar("normal")


@app.post("/api/preparar")
async def iniciar_preparacion():
    if estado["preparando"]:
        raise HTTPException(409, "La preparación ya está en curso")
    # Marcar antes de devolver la respuesta impide dos preparaciones simultáneas.
    estado["preparando"] = True
    tarea = asyncio.create_task(preparar())
    activas.add(tarea)
    tarea.add_done_callback(activas.discard)
    return {"estado": "iniciada", "duracion_prevista_s": 225}


@app.get("/api/registros")
def registros():
    archivo = DATA / "operaciones.jsonl"
    return [json.loads(l) for l in archivo.read_text(encoding="utf8").splitlines()[-12:]] if archivo.exists() else []


@app.get("/api/historico")
def historico():
    s = estado.get("simulacion_previa")
    if not s or s.get("estado") != "completa":
        raise HTTPException(409, "Todavía no existe una simulación previa completa")
    inicio = int(datetime.fromisoformat(s["inicio"]).timestamp() * 1000)
    fin = int(datetime.fromisoformat(s["fin"]).timestamp() * 1000)
    return {"simulacion": s, "url": f"http://localhost:3000/d/erp-historico/simulacion-previa?from={inicio}&to={fin}"}


@app.get("/", response_class=HTMLResponse)
def portada():
    return (Path(__file__).parent / "control.html").read_text(encoding="utf8")
