$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$taskEstado=Invoke-RestMethod http://localhost:8000/api/status
if($taskEstado.preparando -or $taskEstado.escenario -ne 'normal'){throw 'Finalizar la preparación y dejar el servicio normal antes de verificar.'}
$taskRedIpv6=docker network inspect erp-demo_default --format '{{.EnableIPv6}}'
if($taskRedIpv6 -ne 'false'){throw 'Esta comprobación requiere la red IPv4 predeterminada de la demo.'}
$taskNombres=@(docker compose -p erp-demo ps --format '{{.Name}}')
if($taskNombres.Count -ne 8){throw 'Iniciar los ocho contenedores de la demo antes de verificar.'}
$taskRutas=@()
foreach($taskNombre in $taskNombres) {
  $taskOwner=docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' $taskNombre
  if($taskOwner -ne 'erp-demo'){throw 'Contenedor ajeno a la demo.'}
  $taskRuta=docker run --rm --pull never --network ('container:'+$taskNombre) --user 0 --entrypoint /bin/ip prom/prometheus:v3.15.1 -4 route show default
  if($taskRuta -notmatch 'default via (\S+) dev (\S+)'){throw ('No se pudo guardar la ruta de '+$taskNombre)}
  $taskRutas+=@{Nombre=$taskNombre;Gateway=$Matches[1];Interfaz=$Matches[2]}
}
$taskAislados=@()
try {
  foreach($taskRuta in $taskRutas) {
    docker run --rm --pull never --network ('container:'+$taskRuta.Nombre) --user 0 --cap-add NET_ADMIN --entrypoint /bin/ip prom/prometheus:v3.15.1 route del default
    if($LASTEXITCODE -ne 0){throw ('No se pudo aislar '+$taskRuta.Nombre)}
    $taskAislados+=$taskRuta
  }
  ./verificar.ps1
  docker compose -p erp-demo cp tools/ensayar_sin_internet.py servicio:/app/tools/ensayar_sin_internet.py
  docker compose -p erp-demo exec -T servicio python -m tools.ensayar_sin_internet
  if($LASTEXITCODE -ne 0){throw 'Falló el ciclo sin salida externa.'}
  ./auditar-historico.ps1
  New-Item -ItemType Directory -Path '.evidence' -Force | Out-Null
  docker compose -p erp-demo cp servicio:/datos/ensayo_sin_internet.json .evidence/ensayo_sin_internet.json
} finally {
  foreach($taskRuta in $taskAislados) {
    docker run --rm --pull never --network ('container:'+$taskRuta.Nombre) --user 0 --cap-add NET_ADMIN --entrypoint /bin/ip prom/prometheus:v3.15.1 route replace default via $taskRuta.Gateway dev $taskRuta.Interfaz
    if($LASTEXITCODE -ne 0){Write-Warning ('Reiniciar el contenedor para restablecer su red: '+$taskRuta.Nombre)}
  }
}
Write-Output 'Verificación terminada; rutas externas de la demo restablecidas. La conectividad del equipo no se modificó.'
