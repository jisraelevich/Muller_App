@echo off
REM Mata el servidor Flask y todos los procesos Python

echo.
echo ===== MATANDO PROCESOS =====
echo.

REM Mata por puerto 5000
echo [1/2] Buscando procesos en puerto 5000...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":5000"') do (
    echo   - Matando PID: %%a
    taskkill /PID %%a /F 2>nul
)

REM Mata todos los python
echo [2/2] Matando procesos python.exe...
taskkill /IM python.exe /F 2>nul

echo.
echo ===== PROCESO COMPLETADO =====
echo.
pause
