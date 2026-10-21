$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
docker compose -p erp-demo stop
if($LASTEXITCODE -ne 0){throw 'No se pudo detener el entorno.'}
