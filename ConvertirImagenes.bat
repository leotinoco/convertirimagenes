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

:: Check the dependencies are installed *for this interpreter*. With several
:: Python versions installed, a new one can take over the PATH and leave the
:: app pointing at an interpreter that has none of the packages.
python -c "import customtkinter, PIL" >nul 2>&1
if errorlevel 1 (
    echo ============================================
    echo   Faltan dependencias para este Python.
    echo ============================================
    echo.
    echo Python en uso:
    python -c "import sys; print('  ' + sys.executable); print('  version ' + sys.version.split()[0])"
    echo.
    echo Instalalas con:
    echo   python -m pip install -r requirements.txt
    echo.
    echo Si tienes varias versiones de Python y prefieres usar otra,
    echo lanza la aplicacion con ella, por ejemplo:
    echo   py -3.13 app.py
    echo.
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
