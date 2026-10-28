@echo off
setlocal
cd /d "%~dp0"
title Facu Drums - Audio a MIDI
where py >nul 2>nul
if errorlevel 1 goto sinpython
py -3.11 --version >nul 2>nul
if errorlevel 1 goto sinpython
if exist ".venv\Scripts\python.exe" goto dependencias
echo Creando entorno de Python...
py -3.11 -m venv .venv
if errorlevel 1 goto error
:dependencias
if exist ".venv\instalado.ok" goto ejecutar
echo Instalando dependencias. La primera vez puede tardar varios minutos...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
echo OK>".venv\instalado.ok"
:ejecutar
echo Abriendo http://localhost:8000
echo Deja esta ventana abierta mientras usas el programa.
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 4; Start-Process 'http://localhost:8000'"
".venv\Scripts\python.exe" server.py
if errorlevel 1 goto error
pause
exit /b 0
:sinpython
echo Se necesita Python 3.11 de 64 bits con el lanzador py.
echo Instala Python y luego volve a abrir INICIAR.bat.
start "" "https://www.python.org/downloads/release/python-3119/"
pause
exit /b 1
:error
echo No se pudo iniciar. Revisa el mensaje de error de arriba.
pause
exit /b 1
