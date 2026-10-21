"""Mide la entrega SMTP local con tres desfases; no crea ni cierra incidentes."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import httpx

BASE=os.getenv("SERVICIO_URL","http://servicio:8000")
MAIL=os.getenv("MAILPIT_URL","http://mailpit:8025")


def mensajes():
    r=httpx.get(MAIL+"/api/v1/messages",timeout=5);r.raise_for_status()
    return r.json()["messages"]


def cambio(nombre):
    r=httpx.post(BASE+"/api/escenario",json={"escenario":nombre},timeout=5)
    r.raise_for_status()
    return r.json()


def medir(escenario,estado):
    anteriores={m["ID"] for m in mensajes()}
    inicio=time.monotonic();evento=cambio(escenario)
    while time.monotonic()-inicio < 45:
        for m in mensajes():
            if m["ID"] not in anteriores and "Indisponibilidad" in m["Subject"] and f"] {estado} " in m["Subject"]:
                resultado={"escenario":escenario,"evento_utc":evento["timestamp"],"correo_utc":m["Created"],"demora_s":round(time.monotonic()-inicio,3),"correo_id":m["ID"]}
                print(json.dumps(resultado,ensure_ascii=False),flush=True)
                return resultado
        time.sleep(.25)
    raise RuntimeError("No se recibió el correo esperado en 45 segundos")


def main():
    resultados=[]
    cambio("normal");time.sleep(20)
    try:
        for desfase in [0,3,7]:
            time.sleep(desfase)
            caida=medir("caida","firing")
            # La alerta permanece durante el registro manual en el recorrido de exposición.
            time.sleep(5)
            recuperacion=medir("normal","resolved")
            resultados.append({"desfase_s":desfase,"caida":caida,"recuperacion":recuperacion})
            time.sleep(20)
    finally:
        cambio("normal")
    salida={"fecha_utc":datetime.now(timezone.utc).isoformat(),"resultados":resultados,"objetivo_30s":all(r[k]["demora_s"]<=30 for r in resultados for k in ["caida","recuperacion"])}
    Path("/datos/ensayos_alertas.json").write_text(json.dumps(salida,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps(salida,ensure_ascii=False),flush=True)
    if not salida["objetivo_30s"]:raise SystemExit(1)


if __name__=="__main__":main()
