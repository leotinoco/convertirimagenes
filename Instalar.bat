@echo off
setlocal
cd /d "%~dp0"
title Instalador de ConvertirImagenes

:: Instalador de un solo clic. Toda la logica esta en Instalar.ps1; este .bat
:: solo lo lanza (con la politica de ejecucion saltada UNICAMENTE para este
:: proceso: no cambia ninguna configuracion de Windows) y mantiene la ventana
:: abierta para que se pueda leer el resultado.

where powershell >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se encontro Windows PowerShell, necesario para instalar.
    echo Se incluye en Windows 7 y posteriores; verifica que tu Windows no este danado.
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0Instalar.ps1" (
    echo [ERROR] Falta Instalar.ps1 junto a este archivo.
    echo Si descargaste un .zip, extrae TODA la carpeta antes de ejecutar el instalador.
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Instalar.ps1" %*
set "RC=%errorlevel%"

echo.
if not "%RC%"=="0" (
    echo La instalacion termino con errores. Lee el mensaje de arriba.
) else (
    echo Todo listo.
)
echo.
pause
exit /b %RC%
