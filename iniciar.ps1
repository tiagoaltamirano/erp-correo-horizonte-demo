param([switch]$SinDescargas)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
if (!(Get-Command docker -ErrorAction SilentlyContinue)){throw 'Instalar Docker Desktop y volver a ejecutar.'}
docker info --format '{{.ServerVersion}}' | Out-Null
if ($LASTEXITCODE -ne 0){throw 'Iniciar Docker Desktop y esperar a que su motor esté disponible.'}
if (!(Test-Path -LiteralPath '.env')) {
  $taskLines=@()
  foreach($taskKey in @('GRAFANA_PASSWORD','GLPI_DB_PASSWORD','MYSQL_ROOT_PASSWORD','DEMO_PASSWORD')) {
    $taskSecret=[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(18))
    $taskLines+=($taskKey+'='+$taskSecret)
  }
  [IO.File]::WriteAllLines((Join-Path $PSScriptRoot '.env'),$taskLines)
}
if ($SinDescargas) {
  docker compose -p erp-demo up -d --no-build --pull never
} else {
  docker compose -p erp-demo up -d --build
}
if($LASTEXITCODE -ne 0){throw 'No se pudo iniciar el entorno.'}
Write-Output 'Entorno iniciado. Esperar la instalación inicial de GLPI y ejecutar configurar-glpi.ps1.'
Write-Output 'Control: http://localhost:8000 | Grafana: http://localhost:3000 | GLPI: http://localhost:8081 | Correo: http://localhost:8025'
