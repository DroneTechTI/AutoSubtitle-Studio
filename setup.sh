#!/bin/bash
# Setup script for Subtitle Generator - Linux/macOS

echo "========================================"
echo "Subtitle Generator - Setup"
echo "========================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERRORE: Python 3 non trovato!"
    echo ""
    echo "Installazione:"
    echo "- macOS: brew install python3"
    echo "- Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "- Fedora: sudo dnf install python3 python3-pip"
    echo ""
    exit 1
fi

echo "[1/4] Python trovato"
python3 --version
echo ""

# Create virtual environment
echo "[2/4] Creazione ambiente virtuale..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Ambiente virtuale creato."
else
    echo "Ambiente virtuale gia esistente."
fi
echo ""

# Activate virtual environment and install packages
echo "[3/4] Installazione dipendenze Python..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo ""

# Check/Install FFmpeg
echo "[4/4] Verifica FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo ""
    echo "ATTENZIONE: FFmpeg non trovato!"
    echo ""
    echo "FFmpeg e necessario per estrarre l'audio dai video."
    echo ""
    echo "Installazione:"
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "- macOS: brew install ffmpeg"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            echo "- Ubuntu/Debian: sudo apt install ffmpeg"
        elif command -v dnf &> /dev/null; then
            echo "- Fedora: sudo dnf install ffmpeg"
        elif command -v pacman &> /dev/null; then
            echo "- Arch: sudo pacman -S ffmpeg"
        else
            echo "- Usa il package manager della tua distribuzione"
        fi
    fi
    
    echo ""
    echo "Dopo l'installazione di FFmpeg, riesegui questo script."
    echo ""
    exit 1
else
    echo "FFmpeg trovato!"
    ffmpeg -version | head -n 1
    echo ""
fi

echo "========================================"
echo "Setup completato!"
echo "========================================"
echo ""
echo "Per avviare l'applicazione, esegui: ./start.sh"
echo ""
