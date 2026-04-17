@echo off
REM Mata todos los procesos Python

echo Matando todos los procesos Python...
taskkill /IM python.exe /F

echo Procesos Python terminados.
pause
