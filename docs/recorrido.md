# Recorrido de uso

## Preparación

Iniciar el entorno, configurar GLPI una sola vez y generar la simulación previa. Comprobar `./verificar.ps1`. Mantener abiertas las sesiones de Grafana y GLPI, el control y Mailpit.

1. Mostrar disponibilidad normal y abrir **Simulación previa**, indicando su fecha. Observar los ejemplos de latencia p95 > 2 s y errores > 1 %, con volumen suficiente por operación.
2. En el control, seleccionar **Provocar caída**. Comprobar la alerta de indisponibilidad en Grafana y el correo en Mailpit.
3. Guardar manualmente el incidente P1 en GLPI, con categoría, responsable y primera atención.
4. Seleccionar **Restablecer servicio**. Comprobar la disponibilidad y el correo de recuperación.
5. Registrar la solución, verificar el funcionamiento y cerrar manualmente el incidente.

## Contenido del incidente

- Título: **[P1] ERP Correo Horizonte — indisponibilidad**.
- Tipo: incidente.
- Categoría: **ERP Correo Horizonte**.
- Urgencia: **Muy urgente**. Impacto: **Muy alto**. GLPI calcula prioridad **Muy urgente** (nivel 5), equivalente a P1 en el proceso del proyecto.
- Responsable: **Equipo TI Correo Horizonte** (cuenta local `glpi`).
- Descripción: «El sondeo de disponibilidad confirmó tres fallos consecutivos del servicio simulado. Se recibió la alerta de indisponibilidad. Admisión, seguimiento y facturación se consideran afectadas en este escenario de demostración».
- Primera atención: «Se verifica la alerta, se reconoce el incidente y se inicia el diagnóstico de disponibilidad».
- Solución, una vez recuperado: «Se restableció el servicio simulado. Se confirmaron dos sondeos exitosos consecutivos, la recepción del correo de recuperación y la ejecución de operaciones normales».
- Cierre: registrar la verificación y cerrar manualmente el ticket. No atribuir esa acción a la alerta automática.

En GLPI, guardar el incidente con **Agregar**. Registrar la primera atención con **Responder → Agregar**. Después de comprobar la recuperación, usar **Ver otras acciones → Agrega una solución → Agregar**; el ticket queda **Resuelto**. Seleccionar **Estado → Cerrado → Guardar** y comprobar el encabezado **Cerrado**. Guardar una solución por sí solo no cierra el ticket.

El control y los tableros usan la zona horaria de Buenos Aires (UTC−3). Los campos de fecha de esta instancia de GLPI se muestran en UTC: por ejemplo, 21:10 UTC equivale a 18:10 en Buenos Aires.

Los horarios del ticket deben corresponder al recorrido ejecutado. Los ejemplos previos de demora y errores permanecen identificados como simulación anterior. No se afirma cumplimiento de un SLA mensual.

## Registro de los ensayos completos

Registrar dos ejecuciones consecutivas con la misma configuración. Cada una debe incluir la navegación, el ticket guardado y su cierre manual, además de las notificaciones. Las pruebas automáticas de alertas no sustituyen estos ensayos.

| Ensayo | Inicio y fin | Ticket | Duración | Observaciones |
|---|---|---|---|---|
| 1 | 21/10/2026, 18:09:02–18:11:01 (UTC−3) | #1, cerrado | 119,1 s (1:59,1) | P1, primera atención y solución guardadas; correos de caída y recuperación comprobados. |
| 2 | 21/10/2026, 18:11:50–18:14:41 (UTC−3) | #2, cerrado | 170,6 s (2:50,6) | Misma configuración; P1, primera atención, solución y cierre manual comprobados. |

Los recorridos se operaron por la interfaz de Edge, con las sesiones abiertas antes de comenzar.

La revisión visual final confirmó las curvas históricas de latencia y errores en la ventana visible de Edge. Algunas capturas de pestañas en segundo plano omitieron el contenido de los gráficos; para verificar o capturar las curvas, mantener visible la pestaña del tablero.
