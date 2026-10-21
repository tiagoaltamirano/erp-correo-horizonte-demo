$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/api/preparar' -ContentType 'application/json' -Body '{}' | Out-Null
Write-Output 'Simulación previa iniciada. Dura aproximadamente cuatro minutos.'
Write-Output 'Consultar su progreso en http://localhost:8000. Esperar la finalización y un minuto en estado normal.'
