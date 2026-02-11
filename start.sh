#!/bin/bash
# Start script for Subtitle Generator - Linux/macOS

echo "Avvio Subtitle Generator..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERRORE: Ambiente virtuale non trovato!"
    echo ""
    echo "Esegui prima ./setup.sh per installare le dipendenze."
    echo ""
    exit 1
fi

# Activate virtual environment and run application
source venv/bin/activate
python main.py
