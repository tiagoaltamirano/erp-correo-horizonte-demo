$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
docker compose -p erp-demo exec -T servicio python -m pytest -q
if($LASTEXITCODE -ne 0){throw 'Fallaron las pruebas automáticas.'}
docker compose -p erp-demo cp tests/probes.yml prometheus:/tmp/probes.yml
docker compose -p erp-demo exec -T prometheus promtool test rules /tmp/probes.yml
if($LASTEXITCODE -ne 0){throw 'Falló la verificación de los sondeos consecutivos.'}
docker compose -p erp-demo cp tools/glpi_verificar.php glpi:/tmp/glpi_verificar.php
docker compose -p erp-demo exec -T glpi php /tmp/glpi_verificar.php
if($LASTEXITCODE -ne 0){throw 'Falló la verificación de la configuración de GLPI.'}
foreach($taskUrl in @('http://localhost:8000/api/status','http://localhost:3000/api/health','http://localhost:9090/-/ready','http://localhost:8025','http://localhost:8081')) {
  $taskResponse=Invoke-WebRequest -Uri $taskUrl -TimeoutSec 20
  Write-Output ($taskUrl+' '+$taskResponse.StatusCode)
}
