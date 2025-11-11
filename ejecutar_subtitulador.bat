@echo off
setlocal

REM Ir al directorio donde está este .bat
cd /d "%~dp0"

set "VENV_DIR=venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

REM 1) Crear venv si no existe
if not exist "%VENV_PY%" (
  echo No se encontró el entorno virtual. Creándolo en "%CD%\%VENV_DIR%"...
  where py >nul 2>&1
  if %ERRORLEVEL%==0 (
    py -m venv "%VENV_DIR%"
  ) else (
    python -m venv "%VENV_DIR%"
  )

  if not exist "%VENV_PY%" (
    echo ERROR: No se pudo crear el entorno virtual.
    echo Asegúrate de tener Python instalado y en el PATH.
    goto :end
  )
  echo Entorno virtual creado correctamente.
)

REM 2) Instalar/actualizar dependencias
echo Instalando/actualizando dependencias en el entorno virtual...
"%VENV_PY%" -m pip install --upgrade pip
if exist "requirements.txt" (
  "%VENV_PY%" -m pip install -r requirements.txt
) else (
  echo ADVERTENCIA: No se encontro requirements.txt. Continuando sin instalar dependencias.
)

REM 3) Ejecutar la aplicación
echo Ejecutando subtitulador...
"%VENV_PY%" "%CD%\subtitulador.py"

:end
echo.
pause
