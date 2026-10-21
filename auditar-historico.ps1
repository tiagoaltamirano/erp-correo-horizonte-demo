$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Path '.evidence' -Force | Out-Null
docker compose -p erp-demo exec -T servicio python -m tools.auditar_historico
if($LASTEXITCODE -ne 0){throw 'La auditoría histórica no pasó. Consultar el resultado antes de exponer.'}
docker compose -p erp-demo cp servicio:/datos/auditoria_historico.json .evidence/auditoria_historico.json
Write-Output 'Indicadores contrastados con sus registros originales.'
