@echo off
setlocal
cd /d "%~dp0..\.."

set "NEXUS_LOCAL_URL=http://127.0.0.1:8765/"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$client = New-Object Net.Sockets.TcpClient; try { $client.Connect('127.0.0.1', 8765) } catch { exit 1 } finally { $client.Dispose() }; try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 2; if ($health.service -eq 'nexus-local-interface') { exit 0 } } catch {}; exit 2" >nul 2>&1
set "NEXUS_PORT_STATE=%ERRORLEVEL%"

if "%NEXUS_PORT_STATE%"=="0" (
  echo.
  echo Une instance Nexus est deja active.
  echo Ouverture de : %NEXUS_LOCAL_URL%
  start "" "%NEXUS_LOCAL_URL%"
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
  echo Configuration locale des connecteurs externes absente.
  echo Nexus demarrera en mode degrade, sans Legifrance ni JUDILIBRE.
) else (
  call "%NEXUS_LOCAL_CONFIG%"
)

if not defined CFDT_NEXUS_LEGIFRANCE_CLIENT_ID (
  echo Connecteur Legifrance indisponible : identifiant absent.
)

if not defined CFDT_NEXUS_LEGIFRANCE_CLIENT_SECRET (
  echo Connecteur Legifrance indisponible : secret absent.
)

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONDONTWRITEBYTECODE=1

if defined CFDT_NEXUS_PYTHON (
  "%CFDT_NEXUS_PYTHON%" --version >nul 2>&1
  if errorlevel 1 goto PYTHON_MISSING
  start "" /b "%CFDT_NEXUS_PYTHON%" apps\nexus-local-interface\server.py
) else (
  python --version >nul 2>&1
  if errorlevel 1 goto PYTHON_MISSING
  start "" /b python apps\nexus-local-interface\server.py
)

set "NEXUS_WAIT_ATTEMPTS=20"

:WAIT_FOR_NEXUS
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 1; if ($health.service -eq 'nexus-local-interface') { exit 0 } } catch {}; exit 1" >nul 2>&1
if not errorlevel 1 goto OPEN_NEXUS

set /a NEXUS_WAIT_ATTEMPTS-=1
if %NEXUS_WAIT_ATTEMPTS% LEQ 0 goto NEXUS_START_FAILED
timeout /t 1 /nobreak >nul
goto WAIT_FOR_NEXUS

:OPEN_NEXUS
echo.
echo Nexus est pret. Ouverture de : %NEXUS_LOCAL_URL%
start "" "%NEXUS_LOCAL_URL%"
exit /b 0

:NEXUS_START_FAILED
echo.
echo L'interface Nexus n'a pas repondu sur le port 8765.
echo Verifiez Python puis relancez le raccourci.
pause
exit /b 1

:PYTHON_MISSING
echo.
echo Python est indisponible. Installez Python 3.10 ou superieur,
echo ou definissez CFDT_NEXUS_PYTHON dans la configuration locale.
pause
exit /b 1
