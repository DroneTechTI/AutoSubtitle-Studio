@echo off
REM Automatic FFmpeg installer for Windows
echo ========================================
echo FFmpeg Installer per Windows
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Esecuzione come Amministratore: OK
    echo.
) else (
    echo ATTENZIONE: Non stai eseguendo come Amministratore!
    echo.
    echo Per installare FFmpeg automaticamente serve:
    echo 1. Click destro su questo file
    echo 2. Seleziona "Esegui come amministratore"
    echo.
    pause
    exit /b 1
)

echo Scaricamento FFmpeg in corso...
echo.

REM Create temp directory
if not exist "%TEMP%\ffmpeg_install" mkdir "%TEMP%\ffmpeg_install"
cd /d "%TEMP%\ffmpeg_install"

REM Download FFmpeg using PowerShell
echo Download da GitHub (BtbN build - ultima versione)...
echo URL: https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip
echo.
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host 'Download in corso... attendere...'; Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip' -OutFile 'ffmpeg.zip' -UserAgent 'Mozilla/5.0'; Write-Host 'Download completato!'}"

if not exist "ffmpeg.zip" (
    echo.
    echo ERRORE: Download fallito!
    echo.
    echo Prova l'installazione manuale:
    echo 1. Vai su https://github.com/BtbN/FFmpeg-Builds/releases
    echo 2. Scarica ffmpeg-master-latest-win64-gpl-shared.zip
    echo 3. Estrai nella cartella C:\ffmpeg
    echo 4. Aggiungi C:\ffmpeg\bin al PATH di sistema
    echo.
    pause
    exit /b 1
)

echo.
echo Estrazione in corso...
powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath '.' -Force"

REM Find extracted folder
for /d %%i in (ffmpeg-*) do set FFMPEG_FOLDER=%%i

if not defined FFMPEG_FOLDER (
    echo ERRORE: Cartella FFmpeg non trovata!
    pause
    exit /b 1
)

echo.
echo Installazione in C:\ffmpeg...

REM Remove old installation if exists
if exist "C:\ffmpeg" (
    echo Rimozione installazione precedente...
    rmdir /s /q "C:\ffmpeg"
)

REM Move to C:\ffmpeg
move "%FFMPEG_FOLDER%" "C:\ffmpeg" >nul

echo.
echo Aggiunta al PATH di sistema...

REM Add to system PATH using PowerShell
powershell -Command "& {$oldPath = [Environment]::GetEnvironmentVariable('Path', 'Machine'); if ($oldPath -notlike '*C:\ffmpeg\bin*') {[Environment]::SetEnvironmentVariable('Path', $oldPath + ';C:\ffmpeg\bin', 'Machine'); Write-Host 'PATH aggiornato!'}}"

echo.
echo Pulizia file temporanei...
cd /d "%TEMP%"
rmdir /s /q "%TEMP%\ffmpeg_install"

echo.
echo ========================================
echo Installazione completata!
echo ========================================
echo.
echo FFmpeg installato in: C:\ffmpeg
echo.
echo IMPORTANTE: Chiudi e riapri il Prompt dei Comandi
echo per applicare le modifiche al PATH.
echo.
echo Dopo aver riaperto il terminale, verifica con:
echo   ffmpeg -version
echo.
pause
