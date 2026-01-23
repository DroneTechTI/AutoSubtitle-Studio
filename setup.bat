@echo off
REM Setup script for Subtitle Generator - Windows
echo ========================================
echo Subtitle Generator - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato!
    echo.
    echo Installa Python da:
    echo https://www.python.org/downloads/
    echo oppure dal Microsoft Store
    echo.
    pause
    exit /b 1
)

echo [1/4] Python trovato
python --version
echo.

REM Create virtual environment
echo [2/4] Creazione ambiente virtuale...
if not exist venv (
    python -m venv venv
    echo Ambiente virtuale creato.
) else (
    echo Ambiente virtuale gia esistente.
)
echo.

REM Activate virtual environment and install packages
echo [3/4] Installazione dipendenze Python...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.

REM Check/Install FFmpeg
echo [4/4] Verifica FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ATTENZIONE: FFmpeg non trovato!
    echo.
    echo FFmpeg e necessario per estrarre l'audio dai video.
    echo.
    echo Installazione automatica con Chocolatey:
    echo 1. Apri PowerShell come Amministratore
    echo 2. Installa Chocolatey:
    echo    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'^)^)
    echo 3. Chiudi e riapri PowerShell come Amministratore
    echo 4. Esegui: choco install ffmpeg
    echo.
    echo Installazione manuale:
    echo 1. Scarica FFmpeg da: https://ffmpeg.org/download.html
    echo 2. Estrai i file
    echo 3. Aggiungi la cartella bin al PATH di sistema
    echo.
    echo Dopo l'installazione di FFmpeg, riesegui questo script.
    echo.
    pause
) else (
    echo FFmpeg trovato!
    ffmpeg -version | findstr ffmpeg
    echo.
)

echo ========================================
echo Setup completato!
echo ========================================
echo.
echo Per avviare l'applicazione, esegui: start.bat
echo.
pause
