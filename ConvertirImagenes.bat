@echo off
cd /d "%~dp0"

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no fue encontrado en el PATH del sistema.
    echo Instala Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Run the application
python app.py

:: If it crashes, keep the window open so the user can read the error
if errorlevel 1 (
    echo.
    echo ============================================
    echo   La aplicacion cerro con un error.
    echo   Revisa el mensaje de arriba para detalles.
    echo ============================================
    pause
)
