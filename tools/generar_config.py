"""Genera los paneles y reglas versionados de Grafana."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DS = {"type": "prometheus", "uid": "prometheus"}
FUENTE = ' and on() (up{job="colector"} == 1) and on() (colector_fuente_disponible == 1) and on() ((time() - colector_ultimo_ciclo_timestamp_segundos) < 10)'
SONDEOS = 'probe_success{job="erp_disponibilidad"}'
CAIDA = f'((max_over_time({SONDEOS}[15s]) == bool 0) * (count_over_time({SONDEOS}[15s]) >= bool 3))'
RECUPERACION = f'((min_over_time({SONDEOS}[10s]) == bool 1) * (count_over_time({SONDEOS}[10s]) >= bool 2))'
DISPONIBILIDAD = f'((1 - {CAIDA}) * (0.5 + 0.5 * {RECUPERACION})) and on(instance) (up{{job="erp_disponibilidad"}} == 1)'


def volumen(fase):
    return f'sum by (operacion) (erp_operaciones_ventana{{fase="{fase}"}})'


def latencia(fase):
    return f'erp_latencia_p95_ventana_segundos{{fase="{fase}"}} and on(operacion) ({volumen(fase)} >= 20)' + FUENTE


def errores(fase):
    return f'erp_errores_ventana_porcentaje{{fase="{fase}"}} and on(operacion) ({volumen(fase)} >= 20)' + FUENTE


def panel(i, titulo, expr, tipo, x, y, w=12, h=8, unidad="short", umbral=None):
    pasos=[{"color":"green","value":None}]
    if umbral is not None:pasos.append({"color":"red","value":umbral})
    return {"id":i,"title":titulo,"type":tipo,"datasource":DS,"gridPos":{"x":x,"y":y,"w":w,"h":h},
            "targets":[{"refId":"A","expr":expr,"legendFormat":"{{operacion}}","range":True}],
            "fieldConfig":{"defaults":{"unit":unidad,"noValue":"Dato insuficiente o desconocido","thresholds":{"mode":"absolute","steps":pasos}},"overrides":[]},
            "options":{"legend":{"displayMode":"list","placement":"bottom"},"tooltip":{"mode":"multi"},"reduceOptions":{"calcs":["lastNotNull"],"fields":"","values":False},"colorMode":"value"}}


def dashboard(historico=False):
    fase="simulacion_previa" if historico else "en_vivo"
    titulo="Simulación previa" if historico else "Monitoreo en vivo"
    aviso=("SIMULACIÓN PREVIA · Las gráficas corresponden al intervalo fechado de una ejecución anterior. " if historico else "EN VIVO · Servicio simulado y datos ficticios. ")
    aviso+="p95 > 2 s · Errores > 1 % · Mínimo 20 operaciones por tipo · Ventana acelerada 30 s. No acredita SLO/SLA mensual."
    panels=[{"id":1,"title":titulo,"type":"text","gridPos":{"x":0,"y":0,"w":24,"h":3},"options":{"mode":"markdown","content":aviso}}]
    if not historico:
        p=panel(2,"Disponibilidad actual del ERP",'probe_success{job="erp_disponibilidad"} and on(instance) (up{job="erp_disponibilidad"} == 1)',"stat",0,3,8,4)
        p["targets"][0].update({"instant":True,"range":False})
        p["fieldConfig"]["defaults"]["mappings"]=[{"type":"value","options":{"0":{"text":"NO DISPONIBLE","color":"red"},"1":{"text":"DISPONIBLE","color":"green"}}}]
        panels.append(p)
        p=panel(3,"Fuente de métricas",'(up{job="colector"} * colector_fuente_disponible) * on() ((time() - colector_ultimo_ciclo_timestamp_segundos) < bool 10)',"stat",8,3,8,4)
        p["targets"][0].update({"instant":True,"range":False})
        p["fieldConfig"]["defaults"]["mappings"]=[{"type":"value","options":{"0":{"text":"SIN DATOS FIABLES","color":"orange"},"1":{"text":"DISPONIBLE","color":"green"}}}]
        panels.append(p)
        panels.append({"id":4,"title":"Alerta de disponibilidad","type":"alertlist","gridPos":{"x":16,"y":3,"w":8,"h":4},"options":{"viewMode":"list","groupMode":"default","maxItems":5,"sortOrder":1,"stateFilter":{"firing":True,"pending":True,"noData":True,"normal":True,"error":True},"alertName":"Indisponibilidad"}})
    y=3 if historico else 7
    panels.extend([panel(5,"Latencia p95 por operación · mínimo 20",latencia(fase),"timeseries",0,y,unidad="s",umbral=2),
                   panel(6,"Tasa de errores por operación · mínimo 20",errores(fase),"timeseries",12,y,unidad="percent",umbral=1),
                   panel(7,"Operaciones válidas en ventana de 30 s",volumen(fase)+FUENTE,"timeseries",0,y+8),
                   panel(8,"Sondeos HTTP · 1 éxito / 0 fallo",'probe_success{job="erp_disponibilidad"}',"timeseries",12,y+8)])
    return {"uid":"erp-historico" if historico else "erp-vivo","title":titulo+" · ERP Correo Horizonte","schemaVersion":39,"version":1,"editable":False,"tags":["demo","ERP"],"timezone":"America/Argentina/Buenos_Aires","refresh":"5s" if not historico else "", "time":{"from":"now-5m","to":"now"},"panels":panels,"annotations":{"list":[{"builtIn":1,"datasource":{"type":"grafana","uid":"-- Grafana --"},"enable":True,"hide":True,"iconColor":"rgba(80,80,80,1)","name":"Annotations & Alerts","type":"dashboard"}]}}


def regla(uid,titulo,expr,limite,pendiente="0s",recuperacion=None):
    condicion={"evaluator":{"params":[limite],"type":"lt" if recuperacion is not None else "gt"},"operator":{"type":"and"},"query":{"params":["B"]},"reducer":{"type":"last","params":[]},"type":"query"}
    if recuperacion is not None:condicion["unloadEvaluator"]={"params":[recuperacion],"type":"gt"}
    return {"uid":uid,"title":titulo,"condition":"B","for":pendiente,"keepFiringFor":"0s","noDataState":"NoData","execErrState":"Error","isPaused":False,
            "annotations":{"summary":titulo,"description":"Servicio simulado. Verificar el aviso y registrar manualmente el incidente en GLPI."},
            "labels":{"servicio":"erp","entorno":"demostracion"},
            "data":[{"refId":"A","relativeTimeRange":{"from":60,"to":0},"datasourceUid":"prometheus","model":{"refId":"A","expr":expr,"instant":True,"range":False,"intervalMs":5000,"maxDataPoints":43200,"datasource":DS}},
                    {"refId":"B","relativeTimeRange":{"from":0,"to":0},"datasourceUid":"__expr__","model":{"refId":"B","type":"threshold","expression":"A","datasource":{"type":"__expr__","uid":"__expr__"},"conditions":[condicion]}}]}


def generar():
    (ROOT/"dashboards").mkdir(exist_ok=True)
    for historico in [False,True]:
        (ROOT/"dashboards"/("historico.json" if historico else "vivo.json")).write_text(json.dumps(dashboard(historico),ensure_ascii=False,indent=2),encoding="utf8")
    reglas=[regla("erp-caida","ERP · Indisponibilidad",DISPONIBILIDAD,.01,recuperacion=.75),
            regla("erp-latencia","ERP · Simulación previa · Latencia superior a 2 s",latencia("simulacion_previa"),2,"20s"),
            regla("erp-errores","ERP · Simulación previa · Errores superiores al 1 %",errores("simulacion_previa"),1,"20s")]
    config={"apiVersion":1,"groups":[{"orgId":1,"name":"ERP demostracion","folder":"Correo Horizonte","interval":"10s","rules":reglas}],
            "contactPoints":[{"orgId":1,"name":"Buzon local","receivers":[{"uid":"correo-local","type":"email","disableResolveMessage":False,"settings":{"addresses":"ti@correo-horizonte.test","singleEmail":True,"subject":"[DEMO ERP] {{ .Status }} · {{ .CommonLabels.alertname }}","message":"Alerta de un servicio simulado. El incidente se registra y se cierra manualmente en GLPI."}}]}],
            "policies":[{"orgId":1,"receiver":"Buzon local","group_by":["alertname","grafana_folder"],"group_wait":"0s","group_interval":"5s","repeat_interval":"1h"}]}
    ruta=ROOT/"config/grafana/alerting"
    ruta.mkdir(parents=True,exist_ok=True)
    (ruta/"erp.yml").write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding="utf8")
    muestras=[{"series":'probe_success{job="erp_disponibilidad",instance="erp_correo_horizonte"}',"values":"1 0 0 0 1 0 1 1"},
              {"series":'up{job="erp_disponibilidad",instance="erp_correo_horizonte"}',"values":"1 1 1 1 1 1 1 1"}]
    esperado='{instance="erp_correo_horizonte",job="erp_disponibilidad"}'
    pruebas={"rule_files":[],"evaluation_interval":"5s","tests":[{"interval":"5s","input_series":muestras,"promql_expr_test":[{"expr":DISPONIBILIDAD,"eval_time":t,"exp_samples":[{"labels":esperado,"value":v}]} for t,v in [("15s",0),("20s",.5),("25s",.5),("30s",.5),("35s",1)]]},
              {"interval":"5s","input_series":[muestras[0],{"series":muestras[1]["series"],"values":"1 1 1 0"}],"promql_expr_test":[{"expr":DISPONIBILIDAD,"eval_time":"15s","exp_samples":[]}]}]}
    (ROOT/"tests/probes.yml").write_text(json.dumps(pruebas,indent=2),encoding="utf8")


if __name__=="__main__":generar()
