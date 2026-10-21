"""Contrasta los indicadores guardados en Prometheus con sus registros originales."""
import json
import math
from datetime import datetime
from pathlib import Path
import httpx
from src.colector import validar


def matriz(expr,fin):
    r=httpx.get("http://prometheus:9090/api/v1/query",params={"query":expr,"time":fin},timeout=15)
    r.raise_for_status()
    datos=r.json()
    if datos["status"] != "success":raise RuntimeError(datos)
    return datos["data"]["result"]


def main():
    estado=json.loads(Path("/datos/estado.json").read_text())
    s=estado["simulacion_previa"]
    if s["estado"] != "completa":raise RuntimeError("La simulación no está completa")
    inicio=datetime.fromisoformat(s["inicio"]).timestamp()
    fin=datetime.fromisoformat(s["fin"]).timestamp()
    segundos=math.ceil(fin-inicio)+5
    ciclos=matriz(f"colector_ultimo_ciclo_timestamp_segundos[{segundos}s]",fin)
    relojes={float(t):float(v) for serie in ciclos for t,v in serie["values"]}
    filas={}
    for linea in Path("/datos/operaciones.jsonl").read_text().splitlines():
        try:
            f=validar(json.loads(linea));f["ts"]=datetime.fromisoformat(f["timestamp"]).timestamp()
            if f["fase"]=="simulacion_previa" and inicio-30<=f["ts"]<=fin:filas[f["id"]]=f
        except (ValueError,TypeError):pass
    verificaciones=0;diferencias=[];maximos={}
    for nombre in ["erp_operaciones_ventana","erp_latencia_p95_ventana_segundos","erp_errores_ventana_porcentaje"]:
        for serie in matriz(f'{nombre}{{fase="simulacion_previa"}}[{segundos}s]',fin):
            tipo=serie["metric"]["operacion"]
            for t,v in serie["values"]:
                t=float(t);corte=relojes.get(t)
                if corte is None or not inicio+1<=corte<=fin:continue
                ventana=[f for f in filas.values() if f["operacion"]==tipo and corte-30<=f["ts"]<=corte]
                n=len(ventana)
                esperado=n if nombre=="erp_operaciones_ventana" else (100*sum(f["resultado"]=="fallo" for f in ventana)/n if nombre=="erp_errores_ventana_porcentaje" and n else (sorted(f["segundos"] for f in ventana)[math.ceil(.95*n)-1] if n else float("nan")))
                real=float(v)
                verificaciones+=1
                if not ((math.isnan(real) and math.isnan(esperado)) or abs(real-esperado)<.000001):
                    diferencias.append({"metrica":nombre,"tipo":tipo,"corte_utc":datetime.fromtimestamp(corte).isoformat(),"real":real,"esperado":esperado})
                if n>=20 and math.isfinite(real):maximos[nombre+":"+tipo]=max(real,maximos.get(nombre+":"+tipo,0))
    resultado={"simulacion":s,"registros_validos":len(filas),"comparaciones":verificaciones,"diferencias":diferencias,"maximos_con_volumen_suficiente":maximos}
    Path("/datos/auditoria_historico.json").write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps(resultado,ensure_ascii=False),flush=True)
    if diferencias or verificaciones==0:raise SystemExit(1)
    for tipo in ["admision","seguimiento","facturacion"]:
        if maximos.get("erp_latencia_p95_ventana_segundos:"+tipo,0)<=2 or maximos.get("erp_errores_ventana_porcentaje:"+tipo,0)<=1:raise SystemExit(1)


if __name__=="__main__":main()
