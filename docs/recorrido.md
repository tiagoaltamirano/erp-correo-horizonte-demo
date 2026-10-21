# Recorrido de exposición

## Preparación

Iniciar el entorno, configurar GLPI una sola vez y generar la simulación previa. Comprobar `./verificar.ps1`. Mantener abiertas las sesiones de Grafana y GLPI, el control y Mailpit. El reloj comienza antes de mostrar los ejemplos anteriores.

| Tiempo acumulado | Acción y resultado que se observa |
|---|---|
| 0:00–0:35 | Iniciar el cronómetro. Mostrar disponibilidad normal y la vista **Simulación previa**, indicando su fecha. Señalar latencia p95 > 2 s y errores > 1 %, con volumen suficiente por operación. |
| 0:35–1:15 | En el control, seleccionar **Provocar caída**. Mostrar la alerta de indisponibilidad en Grafana y su correo en Mailpit. |
| 1:15–2:45 | Guardar manualmente el incidente P1 en GLPI, con categoría, responsable y primera atención. |
| 2:45–3:30 | Seleccionar **Restablecer servicio**. Mostrar disponibilidad y correo de recuperación. |
| 3:30–4:15 | Registrar solución, comprobar funcionamiento y cerrar manualmente el incidente. Finalizar el cronómetro. |
| 4:15–5:00 | Margen de navegación. |

## Contenido del incidente

- Título: **[P1] ERP Correo Horizonte — indisponibilidad**.
- Tipo: incidente.
- Categoría: **ERP Correo Horizonte**.
- Urgencia e impacto: muy altos. Prioridad muy alta en GLPI, equivalente a P1 en el proceso del proyecto.
- Responsable: **Equipo TI Correo Horizonte** (cuenta local `glpi`).
- Descripción: «El sondeo de disponibilidad confirmó tres fallos consecutivos del servicio simulado. Se recibió la alerta de indisponibilidad. Admisión, seguimiento y facturación se consideran afectadas en este escenario de demostración».
- Primera atención: «Se verifica la alerta, se reconoce el incidente y se inicia el diagnóstico de disponibilidad».
- Solución, una vez recuperado: «Se restableció el servicio simulado. Se confirmaron dos sondeos exitosos consecutivos, la recepción del correo de recuperación y la ejecución de operaciones normales».
- Cierre: registrar la verificación y cerrar manualmente el ticket. No atribuir esa acción a la alerta automática.

Los horarios del ticket deben corresponder al recorrido ejecutado. Los ejemplos previos de demora y errores permanecen identificados como simulación anterior. No se afirma cumplimiento de un SLA mensual.

## Registro de los ensayos completos

Registrar dos ejecuciones consecutivas con la misma configuración. Cada una debe incluir la navegación, el ticket guardado y su cierre manual, además de las notificaciones. Las pruebas automáticas de alertas no sustituyen estos ensayos.

| Ensayo | Inicio y fin | Ticket | Duración | Observaciones |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
