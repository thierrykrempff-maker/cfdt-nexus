@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONDONTWRITEBYTECODE=1
python server.py --open
if errorlevel 1 (
  echo.
  echo Python est introuvable ou l'interface Nexus n'a pas pu demarrer.
  echo Lancer depuis le depot avec: python apps\nexus-local-interface\server.py --open
  pause
)
