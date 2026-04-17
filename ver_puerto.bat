@echo off
REM Muestra qué está usando el puerto 5000 y los procesos Python

echo.
echo ===== PROCESOS EN PUERTO 5000 =====
netstat -aon | find ":5000"

echo.
echo ===== PROCESOS PYTHON ACTIVOS =====
tasklist /FI "IMAGENAME eq python.exe"

echo.
pause
