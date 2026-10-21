"""Comprueba un ciclo real de correo sin ruta externa en los contenedores."""
import errno
import json
import socket
import time
from pathlib import Path
from tools.ensayar_alertas import cambio, medir


def main():
    with socket.socket() as s:
        s.settimeout(2)
        codigo=s.connect_ex(("1.1.1.1",443))
        if codigo != errno.ENETUNREACH:raise RuntimeError("La salida externa no está aislada")
    try:
        caida=medir("caida","firing")
        time.sleep(5)
        recuperacion=medir("normal","resolved")
    finally:
        cambio("normal")
    resultado={"salida_externa_errno":codigo,"caida":caida,"recuperacion":recuperacion,"objetivo_30s":caida["demora_s"]<=30 and recuperacion["demora_s"]<=30}
    Path("/datos/ensayo_sin_internet.json").write_text(json.dumps(resultado,indent=2),encoding="utf8")
    print(json.dumps(resultado),flush=True)
    if not resultado["objetivo_30s"]:raise SystemExit(1)


if __name__=="__main__":main()
