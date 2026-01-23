@echo off
REM Start script for Subtitle Generator - Windows
echo Avvio Subtitle Generator...
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ERRORE: Ambiente virtuale non trovato!
    echo.
    echo Esegui prima setup.bat per installare le dipendenze.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment and run application
call venv\Scripts\activate.bat
python main.py

REM Pause only if there was an error
if errorlevel 1 pause
