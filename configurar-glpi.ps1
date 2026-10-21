$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
docker compose -p erp-demo exec -T glpi php /opt/demo/configurar.php
if($LASTEXITCODE -ne 0){throw 'GLPI todavía no terminó de instalarse. Consultar docker compose logs glpi.'}
