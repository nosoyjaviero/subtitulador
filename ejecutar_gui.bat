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
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

REM El script se encarga de crear el venv y las dependencias automaticamente
echo Iniciando Subtitulador...
echo (La primera vez puede tardar en instalar dependencias)
echo.

python "%~dp0subtitulador_gui.py"

if errorlevel 1 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar la aplicacion.
    echo Revisa que tengas Python 3.10+ instalado correctamente.
    echo.
)

pause
