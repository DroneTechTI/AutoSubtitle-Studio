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
    
    REM Ask if user wants automatic installation
    set /p INSTALL_FFMPEG="Vuoi installare FFmpeg automaticamente? (S/N): "
    
    if /i "%INSTALL_FFMPEG%"=="S" (
        echo.
        echo Avvio installazione automatica FFmpeg...
        echo NOTA: Richiede privilegi di amministratore!
        echo.
        
        REM Run installer as admin
        powershell -Command "Start-Process '%~dp0install_ffmpeg_windows.bat' -Verb RunAs"
        
        echo.
        echo L'installer FFmpeg e stato avviato in una nuova finestra.
        echo.
        echo IMPORTANTE:
        echo 1. Completa l'installazione nella finestra dell'installer
        echo 2. Dopo l'installazione, CHIUDI questo terminale
        echo 3. Riapri un NUOVO terminale
        echo 4. Riesegui setup.bat
        echo.
        pause
        exit /b 0
    ) else (
        echo.
        echo Installazione manuale FFmpeg:
        echo.
        echo METODO 1 - Automatico ^(Consigliato^):
        echo   1. Click destro su "install_ffmpeg_windows.bat"
        echo   2. Seleziona "Esegui come amministratore"
        echo   3. Segui le istruzioni
        echo.
        echo METODO 2 - Chocolatey:
        echo   1. Apri PowerShell come Amministratore
        echo   2. Installa Chocolatey: https://chocolatey.org/install
        echo   3. Esegui: choco install ffmpeg
        echo.
        echo METODO 3 - Manuale:
        echo   1. Vai su: https://github.com/BtbN/FFmpeg-Builds/releases
        echo   2. Scarica: ffmpeg-master-latest-win64-gpl-shared.zip
        echo   3. Estrai in C:\ffmpeg
        echo   4. Aggiungi C:\ffmpeg\bin al PATH di sistema
        echo.
        echo Dopo l'installazione di FFmpeg:
        echo   - Chiudi questo terminale
        echo   - Apri un NUOVO terminale
        echo   - Riesegui setup.bat
        echo.
        pause
        exit /b 0
    )
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
