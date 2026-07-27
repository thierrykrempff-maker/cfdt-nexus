@echo off
setlocal
cd /d "%~dp0..\.."

set "NEXUS_LOCAL_URL=http://127.0.0.1:8765/"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$client = New-Object Net.Sockets.TcpClient; try { $client.Connect('127.0.0.1', 8765) } catch { exit 1 } finally { $client.Dispose() }; try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 2; if ($health.service -eq 'nexus-local-interface') { exit 0 } } catch {}; exit 2" >nul 2>&1
set "NEXUS_PORT_STATE=%ERRORLEVEL%"

if "%NEXUS_PORT_STATE%"=="0" (
  echo.
  echo Une instance Nexus est deja active.
  echo Ouvrez : %NEXUS_LOCAL_URL%
  exit /b 0
)

if "%NEXUS_PORT_STATE%"=="2" (
  echo.
  echo Le port 8765 est deja utilise par une autre application.
  echo Fermez cette application ou liberez le port avant de lancer Nexus.
  exit /b 1
)

set "NEXUS_LOCAL_CONFIG=%CD%\local-index\nexus-local-secrets.cmd"

if not exist "%NEXUS_LOCAL_CONFIG%" (
  echo.
  echo Configuration locale Nexus absente.
  echo Fichier attendu :
  echo %NEXUS_LOCAL_CONFIG%
  echo.
  echo Legifrance et JUDILIBRE ne pourront pas etre utilises.
  pause
  exit /b 1
)

call "%NEXUS_LOCAL_CONFIG%"

if not defined CFDT_NEXUS_LEGIFRANCE_CLIENT_ID (
  echo Identifiant Legifrance absent.
  pause
  exit /b 1
)

if not defined CFDT_NEXUS_LEGIFRANCE_CLIENT_SECRET (
  echo Secret Legifrance absent.
  pause
  exit /b 1
)

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONDONTWRITEBYTECODE=1

if defined CFDT_NEXUS_PYTHON (
  "%CFDT_NEXUS_PYTHON%" apps\nexus-local-interface\server.py --open
) else (
  python apps\nexus-local-interface\server.py --open
)

if errorlevel 1 (
  echo.
  echo Python est introuvable ou l'interface Nexus n'a pas pu demarrer.
  echo Lancer depuis le depot avec: python apps\nexus-local-interface\server.py --open
  pause
  exit /b 1
)
