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

REM Verificar si Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python no esta instalado
    echo.
    echo Por favor instale Python 3.8 o superior desde:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Durante la instalacion marque
    echo "Add Python to PATH"
    echo.
    pause
    exit /b
)

echo Python detectado
echo.

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo Error creando entorno virtual
        pause
        exit /b
    )
    echo Entorno virtual creado
    echo.
)

REM Activar entorno virtual
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo.
    echo Error activando entorno virtual
    pause
    exit /b
)

echo Entorno virtual activado
echo.

REM Instalar dependencias
if not exist "venv\Lib\site-packages\flask" (
    echo Instalando dependencias (solo la primera vez)...
    echo Esto puede tomar 1-2 minutos...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Error instalando dependencias
        pause
        exit /b
    )
    echo Dependencias instaladas
    echo.
)

REM Iniciar la aplicacion
echo.
echo ========================================
echo   SERVIDOR INICIADO CORRECTAMENTE
echo ========================================
echo.
echo Abriendo navegador en:
echo    http://localhost:5000
echo.
echo Para CERRAR la aplicacion:
echo    Cierre esta ventana o presione Ctrl+C
echo.
echo ========================================
echo.

REM Esperar 2 segundos antes de abrir el navegador
timeout /t 2 /nobreak >nul

REM Abrir navegador
start http://\


REM Ejecutar servidor
python app.py

REM Si el servidor se cierra, pausar para ver errores
echo.
echo.
echo El servidor se ha detenido.
pause