@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$health = $null; try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 2 } catch {}; " ^
  "if (-not $health -or $health.service -ne 'nexus-local-interface') { Write-Host 'Aucune instance CFDT Nexus reconnue sur le port 8765.'; exit 0 }; " ^
  "$connection = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; " ^
  "if (-not $connection) { Write-Host 'Instance Nexus deja arretee.'; exit 0 }; " ^
  "Stop-Process -Id $connection.OwningProcess -ErrorAction Stop; Write-Host 'CFDT Nexus est arrete proprement.'"

exit /b %ERRORLEVEL%
