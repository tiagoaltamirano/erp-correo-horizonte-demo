"""Exportador externo: solo lee registros, valida campos y evita duplicados."""
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from prometheus_client import Counter, Gauge, Histogram, start_http_server

TIPOS = {"admision", "seguimiento", "facturacion"}
FASES = {"en_vivo", "simulacion_previa"}


def validar(fila, ahora=None):
    if not isinstance(fila, dict):
        raise ValueError("formato")
    if not isinstance(fila.get("operacion"),str) or not isinstance(fila.get("fase"),str) or fila["operacion"] not in TIPOS or fila["fase"] not in FASES:
        raise ValueError("etiquetas")
    if not isinstance(fila.get("resultado"),str) or fila["resultado"] not in {"exito", "fallo"}:
        raise ValueError("resultado")
    if not isinstance(fila.get("id"), str) or not 1 <= len(fila["id"]) <= 100:
        raise ValueError("identificador")
    try:
        if isinstance(fila["duration_ms"],bool):raise ValueError()
        duracion = float(fila["duration_ms"])
        fecha = datetime.fromisoformat(fila["timestamp"])
        if fecha.tzinfo is None or fecha.timestamp() > (ahora or time.time()) + 30:
            raise ValueError()
        if not math.isfinite(duracion) or not 0 <= duracion <= 60000:
            raise ValueError()
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ValueError("fecha_o_duracion") from None
    return {k: fila[k] for k in ["id", "timestamp", "operacion", "resultado", "fase"]} | {"segundos": duracion / 1000}


class Lector:
    def __init__(self, ruta, registry=None):
        from prometheus_client import REGISTRY
        registry = registry or REGISTRY
        self.ruta = Path(ruta)
        self.offset = 0
        self.ids = set()
        self.recientes = []
        self.operaciones = Counter("erp_operaciones_total", "Operaciones observadas en registros válidos", ["operacion", "resultado", "fase"], registry=registry)
        self.duracion = Histogram("erp_operacion_duracion_segundos", "Duración de operaciones del ERP simulado", ["operacion", "fase"], buckets=(.1,.25,.5,1,1.5,2,2.5,3,4,5,10), registry=registry)
        self.descartados = Counter("colector_registros_descartados_total", "Registros inválidos", ["motivo"], registry=registry)
        self.duplicados = Counter("colector_registros_duplicados_total", "Identificadores repetidos", registry=registry)
        self.fuente = Gauge("colector_fuente_disponible", "El archivo puede leerse", registry=registry)
        self.ciclo = Gauge("colector_ultimo_ciclo_timestamp_segundos", "Última lectura del colector", registry=registry)
        self.ventana = Gauge("erp_operaciones_ventana", "Operaciones válidas terminadas en los últimos 30 segundos", ["operacion", "fase"], registry=registry)
        self.p95 = Gauge("erp_latencia_p95_ventana_segundos", "Percentil 95 por rango más próximo en ventana de 30 segundos", ["operacion", "fase"], registry=registry)
        self.errores = Gauge("erp_errores_ventana_porcentaje", "Porcentaje de fallos en ventana de 30 segundos", ["operacion", "fase"], registry=registry)
        for tipo in sorted(TIPOS):
            for fase in sorted(FASES):
                for resultado in ("exito", "fallo"):
                    self.operaciones.labels(tipo, resultado, fase).inc(0)
                self.duracion.labels(tipo, fase)

    def leer(self):
        ahora = time.time()
        try:
            if self.ruta.stat().st_size < self.offset:
                self.offset = 0
            with self.ruta.open("rb") as f:
                f.seek(self.offset)
                while True:
                    pos = f.tell()
                    linea = f.readline()
                    if not linea or not linea.endswith(b"\n"):
                        self.offset = pos
                        break
                    self.offset = f.tell()
                    try:
                        fila = validar(json.loads(linea))
                    except (json.JSONDecodeError, ValueError) as e:
                        motivo = str(e) if str(e) in {"formato","etiquetas","resultado","identificador","fecha_o_duracion"} else "json"
                        self.descartados.labels(motivo).inc()
                        continue
                    if fila["id"] in self.ids:
                        self.duplicados.inc()
                        continue
                    self.ids.add(fila["id"])
                    self.operaciones.labels(fila["operacion"],fila["resultado"],fila["fase"]).inc()
                    self.duracion.labels(fila["operacion"],fila["fase"]).observe(fila["segundos"])
                    if datetime.fromisoformat(fila["timestamp"]).timestamp() >= ahora-30:
                        self.recientes.append(fila)
            self.fuente.set(1)
        except OSError:
            self.fuente.set(0)
        self.recientes = [f for f in self.recientes if datetime.fromisoformat(f["timestamp"]).timestamp() >= ahora-30]
        for tipo in sorted(TIPOS):
            for fase in sorted(FASES):
                filas = [f for f in self.recientes if f["operacion"] == tipo and f["fase"] == fase and datetime.fromisoformat(f["timestamp"]).timestamp() <= ahora]
                n = len(filas)
                self.ventana.labels(tipo,fase).set(n)
                duraciones = sorted(f["segundos"] for f in filas)
                self.p95.labels(tipo,fase).set(duraciones[math.ceil(.95*n)-1] if n else float("nan"))
                self.errores.labels(tipo,fase).set(100*sum(f["resultado"] == "fallo" for f in filas)/n if n else float("nan"))
        self.ciclo.set(ahora)


if __name__ == "__main__":
    lector = Lector(Path(os.getenv("DATA_DIR", "/datos")) / "operaciones.jsonl")
    lector.leer()
    start_http_server(9101)
    while True:
        lector.leer()
        time.sleep(1)
