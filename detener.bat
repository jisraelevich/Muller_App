@echo off
REM Detener servidor Flask y limpiar cache

echo Matando proceso de Flask...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq*Muller*"

echo.
echo Limpiando archivos de cache...
REM Limpiar pycache
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s/q "%%d"

REM Limpiar archivos .pyc
for /r . %%f in (*.pyc) do @if exist "%%f" del "%%f"

echo.
echo Limpiando cache de sesiones si existe...
if exist "__pycache__" rmdir /s/q "__pycache__"

echo.
echo ✓ Proceso terminado y cache limpiado
echo.
pause
