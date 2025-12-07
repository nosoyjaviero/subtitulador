@echo off
chcp 65001 >nul
echo ============================================
echo   Subtitulador con Interfaz Grafica
echo ============================================
echo.

cd /d "%~dp0"

REM Verificar si Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado.
    echo Por favor, instala Python 3.10+ desde https://python.org
    pause
    exit /b 1
)

echo Verificando dependencias e iniciando...
echo.
python subtitulador_gui.py

if errorlevel 1 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar la aplicacion.
    pause
)

pause
