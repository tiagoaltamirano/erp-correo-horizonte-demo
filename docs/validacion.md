# Verificación técnica de la prueba de concepto

Fecha: 21 de octubre de 2026. Servicio y operaciones ficticias. Los resultados siguientes provienen de ejecuciones reales del entorno local.

## Resultado de las comprobaciones

| Comprobación | Resultado |
|---|---|
| Pruebas automatizadas de registros y configuración | 19 aprobadas. Incluyen duplicados, líneas incompletas, tipos inválidos, bytes corruptos y volumen exacto. |
| Expresiones de disponibilidad en Prometheus | 6 comprobaciones aprobadas: tres fallos, recuperación con dos éxitos consecutivos, secuencias interrumpidas y sondeador no disponible. |
| Accesos locales | Control, Grafana, Prometheus, Mailpit y GLPI respondieron HTTP 200. |
| Configuración de GLPI | Credencial local, categoría ERP Correo Horizonte y técnico asignado comprobados después de reinicios. |
| Colector detenido | Indicadores de latencia y errores sin datos; no se sustituyen por resultados saludables. |
| Sondeador detenido | Disponibilidad desconocida; no se presenta como caída confirmada ni como disponibilidad comprobada. |
| Volumen insuficiente | Con cero operaciones válidas en la ventana no se publican p95 ni tasa de errores como valores válidos. |
| Reinicio y conservación | Estado de la simulación previa, registros, métricas, correos y configuración de GLPI conservados en volúmenes. Arranque sin construcción ni descargas verificado. |
| Ensayos manuales mediante Edge | Dos recorridos operativos completos, de 119,1 s y 170,6 s. Tickets #1 y #2 cerrados manualmente, con primera atención y solución persistidas. |

## Simulación previa y contraste de registros

Intervalo: **21/10/2026, 20:38:46–20:42:31 UTC** (17:38:46–17:42:31 en Buenos Aires). Se ejecutaron fases normales, demora y errores; se conservaron sus marcas temporales.

- Registros válidos dentro del intervalo: **1.347**.
- Comparaciones entre indicadores guardados en Prometheus y registros de sus ventanas: **405**.
- Diferencias: **0**.

| Operación | Mayor p95 con volumen suficiente | Mayor tasa de errores con volumen suficiente |
|---|---:|---:|
| Admisión | 3,052 s | 10 % |
| Seguimiento | 3,052 s | 10 % |
| Facturación | 3,052 s | 10 % |

El colector calcula ventanas móviles de 30 s. El p95 utiliza el rango más próximo y cada operación requiere al menos 20 registros válidos. Los paneles históricos muestran un intervalo fechado; estos ejemplos no se atribuyen a la caída del recorrido en vivo.

## Recepción de correos con distintos desfases

Última serie verificada: 21/10/2026, 20:47–20:50 UTC. Se mide desde el cambio solicitado al simulador hasta la recepción observada en Mailpit. El sondeo de comprobación añade como máximo unas décimas de segundo a la medición.

| Desfase del ensayo | Caída → correo | Restablecimiento → correo |
|---|---:|---:|
| 0 s | 22,331 s | 14,998 s |
| 3 s | 16,901 s | 20,049 s |
| 7 s | 17,999 s | 14,996 s |

Las seis notificaciones cumplieron el objetivo de 30 s en esta serie. Las mediciones previas detectaron demoras en ciclos repetidos; la configuración final reduce a 10 s la retención de estados resueltos y fue verificada nuevamente.

## Funcionamiento sin salida a Internet

Se retiró temporalmente la ruta externa de los ocho contenedores de la demo, conservando la red entre componentes y el acceso local. Se comprobó que la conexión externa del simulador fallaba con `ENETUNREACH`. La conectividad del equipo y de otros proyectos no se modificó.

Durante ese aislamiento pasaron las 19 pruebas, las expresiones de Prometheus, la comprobación de GLPI, los cinco accesos HTTP y las 405 comparaciones históricas. Un ciclo adicional recibió el correo de caída en **18,504 s** y el de recuperación en **14,974 s**. Las rutas originales se restauraron al terminar.

## Evidencia conservada y alcance de la validación

Los archivos detallados se conservan localmente en `.evidence/`: `auditoria_historico.json`, `ensayos_alertas.json`, `ensayo_sin_internet.json` y las comprobaciones `calidad_*.json`. Los volúmenes mantienen los registros y las métricas originales. Las credenciales y estos archivos de ejecución quedan fuera de Git.

## Ensayos manuales y revisión de pantallas

Se ejecutaron dos recorridos consecutivos mediante la interfaz de **Microsoft Edge**, con las sesiones preparadas y sin locución. El registro detallado y los pasos de GLPI están en [recorrido.md](recorrido.md).

| Ensayo | Duración total | Ticket cerrado | Caída → correo | Restablecimiento → correo |
|---|---:|---|---:|---:|
| 1 | 119,1 s | #1, 18:10:55 UTC−3 | 14,127 s | 16,314 s |
| 2 | 170,6 s | #2, 18:14:38 UTC−3 | 15,833 s | 21,856 s |

Las cuatro notificaciones cumplieron 30 s. Cada ticket conserva tipo incidente, categoría ERP Correo Horizonte, urgencia, impacto y prioridad en nivel 5, el técnico local asignado, la primera atención y la solución. Una consulta de solo lectura confirmó el estado cerrado y las fechas guardadas; los tickets se crearon y cerraron por la interfaz, sin inserciones automáticas.

Se revisaron el control, el histórico fechado, la disponibilidad y alerta en vivo, los mensajes de Mailpit y los formularios de GLPI. El control mostró inicialmente la fecha según la zona del navegador: se fijó Buenos Aires en el control y en ambos tableros. Grafana se reinició para aplicar la configuración. GLPI conserva sus campos de fecha en UTC, aclarado en el recorrido.

Las capturas inicial y final del histórico permitieron observar p95 alrededor de 3,05 s y errores del 10 %, con las curvas y el intervalo fechado visibles. Algunas capturas de pestañas en segundo plano omitieron el contenido de los gráficos; se repitió la comprobación con la ventana visible y se conservó `revision-historico-final.png`. La revisión visual y los dos recorridos operativos quedaron completados. Los tiempos registrados corresponden a recorridos sin locución, no a una exposición hablada.

La evidencia local adicional está en `.evidence/ensayos-manuales.json`, `ensayos-correo.json`, `tickets-verificados.json`, los archivos `ensayo*-ticket.txt` y las capturas disponibles. Estos archivos siguen excluidos de Git.

Los resultados no acreditan cumplimiento de un SLO o SLA mensual, cobertura humana continua ni una implementación sobre un ERP productivo.
