$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Path '.evidence' -Force | Out-Null
docker compose -p erp-demo exec -T servicio python -m tools.ensayar_alertas
$taskResultado=$LASTEXITCODE
docker compose -p erp-demo cp servicio:/datos/ensayos_alertas.json .evidence/ensayos_alertas.json
if($taskResultado -ne 0){throw 'No se cumplió el objetivo de recepción de notificaciones.'}
Write-Output 'Tres ciclos técnicos verificados. Estos ciclos no sustituyen los ensayos manuales completos.'
