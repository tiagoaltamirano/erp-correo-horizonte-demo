"""Comprueba estados desconocidos e insuficientes sin registrarlos como saludables."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx
from tools.generar_config import DISPONIBILIDAD, latencia, errores, volumen


def consulta(expr):
    r=httpx.get("http://prometheus:9090/api/v1/query",params={"query":expr},timeout=10)
    r.raise_for_status();d=r.json()
    if d["status"]!="success":raise RuntimeError(d)
    return d["data"]["result"]


def main():
    p=argparse.ArgumentParser();p.add_argument("modo",choices=["normal","colector_detenido","sondeador_detenido","volumen_insuficiente"]);a=p.parse_args()
    disponibilidad=consulta(DISPONIBILIDAD)
    lat=consulta(latencia("en_vivo"));err=consulta(errores("en_vivo"));vol=consulta(volumen("en_vivo"))
    if a.modo=="normal":
        assert len(disponibilidad)==1 and float(disponibilidad[0]["value"][1])==1
        assert len(lat)==3 and len(err)==3
    elif a.modo=="colector_detenido":
        assert not lat and not err
        assert float(consulta('up{job="colector"}')[0]["value"][1])==0
    elif a.modo=="sondeador_detenido":
        assert not disponibilidad
        assert float(consulta('up{job="erp_disponibilidad"}')[0]["value"][1])==0
    else:
        assert vol and all(float(f["value"][1])<20 for f in vol)
        assert not lat and not err
    resultado={"modo":a.modo,"fecha_utc":datetime.now(timezone.utc).isoformat(),"correcto":True,"disponibilidad":disponibilidad,"latencia":lat,"errores":err,"volumen":vol}
    Path("/datos/calidad_"+a.modo+".json").write_text(json.dumps(resultado,indent=2),encoding="utf8")
    print(json.dumps(resultado),flush=True)


if __name__=="__main__":main()
