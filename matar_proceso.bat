@echo off
REM Mata el servidor Flask en puerto 5000

echo Matando procesos en puerto 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000"') do (
    taskkill /PID %%a /F
)

echo Proceso terminado.
pause
