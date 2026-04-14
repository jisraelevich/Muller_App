@echo off
REM Script para sincronizar production con cambios

echo ==================================
echo SINCRONIZANDO CON PRODUCCION
echo ==================================
echo.

cd /d "%~dp0"

REM Activar entorno virtual
call venv\Scripts\activate.bat

echo ========================================
echo Limpiando archivos cache...
echo ========================================

REM Limpiar pycache
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul

REM Limpiar archivos .pyc
for /r . %%f in (*.pyc) do @if exist "%%f" del "%%f" 2>nul

echo.
echo ========================================
echo Mostrando cambios en templates...
echo ========================================
echo.

REM Mostrar cambios en tab_7_reportes_pagos.html
echo Verificando tab_7_reportes_pagos.html...
findstr /C:"btn-exportar-pdf" templates\tab_7_reportes_pagos.html >nul
if %errorlevel%==0 (
    echo [OK] Botón PDF encontrado
) else (
    echo [ERROR] Botón PDF NO encontrado
)

findstr /C:"chk-solo-regulares" templates\tab_7_reportes_pagos.html >nul
if %errorlevel%==0 (
    echo [OK] Checkbox regulares encontrado
) else (
    echo [ERROR] Checkbox regulares NO encontrado
)

findstr /C:"matricula_monto" templates\tab_7_reportes_pagos.html >nul
if %errorlevel%==0 (
    echo [OK] Monto matricula encontrado
) else (
    echo [ERROR] Monto matricula NO encontrado
)

echo.
echo ========================================
echo PRODUCTION SYNC COMPLETADO
echo ========================================
echo.
echo PROXIMO PASO:
echo 1. Reinicia el servidor en produccion
echo 2. Limpia cache del navegador (Ctrl+F5)
echo 3. Verifica que aparezca el boton PDF y columna Matricula
echo.
pause
