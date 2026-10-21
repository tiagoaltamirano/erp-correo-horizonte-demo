import importlib.util
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]


def test_notificaciones_y_evaluacion():
    cfg=yaml.safe_load((ROOT/"config/grafana/alerting/erp.yml").read_text(encoding="utf8"))
    assert cfg["groups"][0]["interval"]=="10s"
    reglas=cfg["groups"][0]["rules"]
    assert reglas[0]["for"]=="0s"
    assert reglas[0]["data"][1]["model"]["conditions"][0]["unloadEvaluator"]["params"]==[.75]
    assert [r["for"] for r in reglas[1:]]==["20s","20s"]
    for r in reglas[1:]:
        assert 'erp_operaciones_ventana' in r["data"][0]["model"]["expr"]
        assert '>= 20' in r["data"][0]["model"]["expr"]
        assert 'up{job="colector"} == 1' in r["data"][0]["model"]["expr"]
    p=cfg["policies"][0]
    assert (p["group_wait"],p["group_interval"],p["repeat_interval"])==("0s","5s","1h")
    assert cfg["contactPoints"][0]["receivers"][0]["disableResolveMessage"] is False


def test_puertos_locales_y_registros_solo_lectura():
    cfg=yaml.safe_load((ROOT/"compose.yaml").read_text())
    assert cfg["services"]["colector"]["volumes"]==["registros:/datos:ro"]
    for service in cfg["services"].values():
        for puerto in service.get("ports",[]):assert puerto.startswith("127.0.0.1:")
