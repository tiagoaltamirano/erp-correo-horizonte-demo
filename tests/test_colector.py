import json
import time
from datetime import datetime, timezone
import pytest
from prometheus_client import CollectorRegistry
from src.colector import Lector, validar


def registro(**cambios):
    return {"id":"operacion-1","timestamp":datetime.now(timezone.utc).isoformat(),"operacion":"admision","resultado":"exito","fase":"en_vivo","duration_ms":120,**cambios}


def test_validacion_elimina_campos_ajenos():
    validado=validar(registro(correo="persona@ejemplo.test",password="valor-ficticio"))
    assert "correo" not in validado and "password" not in validado
    assert validado["segundos"]==.12


@pytest.mark.parametrize("cambios",[{"duration_ms":float("nan")},{"duration_ms":-1},{"duration_ms":float("inf")},{"duration_ms":True},{"timestamp":"sin-fecha"},{"timestamp":"2026-01-01T00:00:00"},{"operacion":"etiqueta-no-autorizada"},{"operacion":[]},{"fase":{}},{"resultado":[]},{"resultado":"desconocido"}])
def test_rechaza_datos_invalidos(cambios):
    with pytest.raises(ValueError):validar(registro(**cambios))


def test_no_duplica_y_no_consume_lineas_incompletas(tmp_path):
    f=tmp_path/"datos.jsonl"
    correcto=json.dumps(registro())
    f.write_text(correcto+'\n'+correcto+'\n'+'{invalido}\n'+json.dumps(registro(id="operacion-2")),encoding="utf8")
    registry=CollectorRegistry()
    lector=Lector(f,registry)
    lector.leer()
    labels={"operacion":"admision","resultado":"exito","fase":"en_vivo"}
    assert registry.get_sample_value("erp_operaciones_total",labels)==1
    assert registry.get_sample_value("colector_registros_duplicados_total")==1
    assert registry.get_sample_value("colector_registros_descartados_total",{"motivo":"json"})==1
    lector.leer()
    assert registry.get_sample_value("erp_operaciones_total",labels)==1
    with f.open("a",encoding="utf8") as salida:salida.write('\n')
    lector.leer()
    assert registry.get_sample_value("erp_operaciones_total",labels)==2


def test_archivo_ausente_no_es_fuente_saludable(tmp_path):
    registry=CollectorRegistry();lector=Lector(tmp_path/"ausente",registry);lector.leer()
    assert registry.get_sample_value("colector_fuente_disponible")==0
    assert registry.get_sample_value("colector_ultimo_ciclo_timestamp_segundos")<=time.time()


def test_ventana_cuenta_registros_reales_y_calcula_indicadores(tmp_path):
    f=tmp_path/"ventana.jsonl"
    anteriores=datetime.fromtimestamp(time.time()-40,timezone.utc).isoformat()
    filas=[registro(id=str(i),duration_ms=3100 if i==19 else 120,resultado="fallo" if i==19 else "exito") for i in range(20)]
    filas.append(registro(id="anterior",timestamp=anteriores,duration_ms=9000,resultado="fallo"))
    f.write_text("".join(json.dumps(x)+"\n" for x in filas),encoding="utf8")
    registry=CollectorRegistry();lector=Lector(f,registry);lector.leer()
    labels={"operacion":"admision","fase":"en_vivo"}
    assert registry.get_sample_value("erp_operaciones_ventana",labels)==20
    assert registry.get_sample_value("erp_latencia_p95_ventana_segundos",labels)==.12
    assert registry.get_sample_value("erp_errores_ventana_porcentaje",labels)==5
    lector.leer()
    assert registry.get_sample_value("erp_operaciones_ventana",labels)==20


def test_diecinueve_operaciones_no_se_extrapolan_a_veinte(tmp_path):
    f=tmp_path/"insuficiente.jsonl"
    f.write_text("".join(json.dumps(registro(id=str(i)))+"\n" for i in range(19)),encoding="utf8")
    registry=CollectorRegistry();lector=Lector(f,registry);lector.leer()
    assert registry.get_sample_value("erp_operaciones_ventana",{"operacion":"admision","fase":"en_vivo"})==19


def test_linea_con_bytes_invalidos_no_interrumpe_la_lectura(tmp_path):
    f=tmp_path/"bytes.jsonl"
    f.write_bytes(b'\xff\xfe\n'+(json.dumps(registro())+'\n').encode())
    registry=CollectorRegistry();lector=Lector(f,registry);lector.leer()
    assert registry.get_sample_value("colector_registros_descartados_total",{"motivo":"json"})==1
    assert registry.get_sample_value("erp_operaciones_ventana",{"operacion":"admision","fase":"en_vivo"})==1
