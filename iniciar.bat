@echo off
title Instituto Jorge Muller - Sistema de Gestion
color 0A

echo ========================================
echo   INSTITUTO JORGE MULLER
echo   Sistema de Gestion - Salta
echo ========================================
echo.
echo Iniciando servidor...
echo.

cd /d "%~dp0"

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    echo Entorno virtual creado
    echo.
)

REM Activar entorno virtual
call venv\Scripts\activate.bat

echo Entorno virtual activado
echo.

REM Instalar/actualizar dependencias
echo Instalando dependencias...
pip install -r requirements.txt --quiet
echo Dependencias actualizadas
echo.

REM Limpiar cache
echo Limpiando cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul

echo.
echo ========================================
echo   SERVIDOR INICIADO CORRECTAMENTE
echo ========================================
echo.
echo URL: http://localhost:5000
echo.
echo Para cerrar: Presione Ctrl+C
echo.
echo ========================================
echo.

REM Ejecutar servidor
python app.py

REM Si el servidor se cierra, pausar para ver errores
echo.
echo El servidor se ha detenido.
pause
echo.
echo.
echo El servidor se ha detenido.
pause