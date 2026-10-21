$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Path '.evidence' -Force | Out-Null
function Test-Datos([string]$taskModo) {
  docker compose -p erp-demo exec -T servicio python -m tools.verificar_calidad $taskModo
  if($LASTEXITCODE -ne 0){throw ('Falló la comprobación: '+$taskModo)}
  docker compose -p erp-demo cp ('servicio:/datos/calidad_'+$taskModo+'.json') ('.evidence/calidad_'+$taskModo+'.json')
}
try {
  $taskEstado=Invoke-RestMethod http://localhost:8000/api/status
  if($taskEstado.preparando){throw 'Esperar a que termine la preparación histórica.'}
  Test-Datos 'normal'
  docker compose -p erp-demo stop colector
  Start-Sleep -Seconds 10
  Test-Datos 'colector_detenido'
  docker compose -p erp-demo start colector
  Start-Sleep -Seconds 15
  docker compose -p erp-demo stop blackbox
  Start-Sleep -Seconds 10
  Test-Datos 'sondeador_detenido'
  docker compose -p erp-demo start blackbox
  Start-Sleep -Seconds 20
  Invoke-RestMethod http://localhost:8000/api/escenario -Method Post -ContentType 'application/json' -Body '{"escenario":"caida"}' | Out-Null
  Start-Sleep -Seconds 35
  Test-Datos 'volumen_insuficiente'
} finally {
  docker compose -p erp-demo start colector blackbox
  Invoke-RestMethod http://localhost:8000/api/escenario -Method Post -ContentType 'application/json' -Body '{"escenario":"normal"}' | Out-Null
}
Start-Sleep -Seconds 20
Test-Datos 'normal'
Write-Output 'Fallas de fuentes y datos insuficientes identificados sin resultados saludables falsos.'
