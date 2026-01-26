# AutoSubtitle Studio 🎬

> 🌍 **[English version](README_EN.md)** | **[Versione Italiana](README.md)**

**Studio professionale per la generazione automatica di sottotitoli** con intelligenza artificiale, download da OpenSubtitles, sincronizzazione avanzata e molto altro.

Applicazione completa e professionale per generare automaticamente sottotitoli dai tuoi video usando l'intelligenza artificiale, oppure scaricare sottotitoli già esistenti da OpenSubtitles.

## ✨ Funzionalità Principali

### 🤖 Generazione Automatica
- **AI Speech-to-Text** con Whisper (OpenAI) - uno dei migliori modelli open-source
- **90+ lingue supportate** (Italiano, Inglese, Spagnolo, Francese, Tedesco, Cinese, Giapponese, ecc.)
- **5 livelli di qualità**: tiny (veloce) → large (massima qualità)
- **Elaborazione batch**: processa più video contemporaneamente
- **Auto-sync**: regolazione automatica del timing

### 🌐 Download Sottotitoli
- **Integrazione OpenSubtitles.com** per scaricare sottotitoli esistenti
- **Ricerca intelligente** tramite hash del video per match precisi
- **Multi-lingua**: cerca sottotitoli in qualsiasi lingua disponibile

### 🎨 Interfaccia Utente
- **GUI intuitiva** con drag & drop
- **Preview sottotitoli** in tempo reale
- **Editor integrato** per modifiche rapide
- **Progress bar e log** per monitorare l'elaborazione
- **Salvataggio preferenze** per un utilizzo veloce

### 📁 Formati e Compatibilità
- **Video**: MP4, MKV, AVI, MOV, WMV, FLV, WEBM, M4V, MPG, MPEG
- **Sottotitoli**: SRT, VTT (compatibili con VLC, YouTube, Plex, Kodi, ecc.)
- **Traduzione**: traduci sottotitoli tra lingue diverse

## 📋 Requisiti di Sistema

| Componente | Minimo | Consigliato |
|------------|--------|-------------|
| **OS** | Windows 10, macOS 10.15, Linux | Windows 11, macOS 13+, Linux recente |
| **RAM** | 4 GB | 8 GB+ |
| **Spazio Disco** | 3 GB | 5 GB+ |
| **CPU** | Dual-core | Quad-core+ |
| **Internet** | Per setup e download modelli | - |

## 🚀 Installazione e Avvio

### ⚡ Quick Start (5 minuti)

#### Prima Installazione

**Windows:**
```bash
# Doppio click su:
setup.bat
```

**macOS/Linux:**
```bash
chmod +x setup.sh start.sh
./setup.sh
```

⏳ L'installazione richiede 5-10 minuti e installa automaticamente tutte le dipendenze.

#### Avvio Normale

**Windows:**
```bash
# Doppio click su:
start.bat
```

**macOS/Linux:**
```bash
./start.sh
```

### 🔧 Installazione FFmpeg (se richiesto)

**Windows - METODO AUTOMATICO (Consigliato):**

Se durante il setup FFmpeg non è installato, ti verrà chiesto se vuoi installarlo automaticamente.

Oppure puoi lanciarlo manualmente:
1. **Click destro** su `install_ffmpeg_windows.bat`
2. Seleziona **"Esegui come amministratore"**
3. Segui le istruzioni
4. Chiudi e riapri il terminale
5. Riesegui `setup.bat`

**Windows - METODO CHOCOLATEY (Alternativo):**
```powershell
# Installa Chocolatey (se non ce l'hai)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Installa FFmpeg
choco install ffmpeg
```

**Windows - METODO MANUALE:**
1. Vai su https://github.com/BtbN/FFmpeg-Builds/releases
2. Scarica `ffmpeg-master-latest-win64-gpl-shared.zip` (ultima versione)
3. Estrai in `C:\ffmpeg`
4. Aggiungi `C:\ffmpeg\bin` al PATH di sistema:
   - Cerca "Variabili d'ambiente" nel menu Start
   - Clicca "Modifica variabili d'ambiente di sistema"
   - Click su "Variabili d'ambiente"
   - Seleziona "Path" e click "Modifica"
   - Click "Nuovo" e aggiungi `C:\ffmpeg\bin`
   - OK su tutto
5. Chiudi e riapri il terminale

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg
```

## 📖 Guida Utilizzo

### 1️⃣ Generazione Automatica

1. **Avvia l'applicazione**
2. **Aggiungi video:**
   - Click su "Sfoglia" o drag & drop
   - Per batch: click su "Aggiungi più video"
3. **Scegli modalità:** 🤖 Auto-Genera
4. **Configura opzioni:**
   - **Lingua**: Seleziona la lingua parlata nel video
   - **Modello**: Scegli tra tiny/base/small/medium/large
   - **Formato**: SRT (universale) o VTT (web)
5. **Click "Avvia"** e attendi
6. **Trova i risultati** in `output_subtitles/`

### 2️⃣ Download da OpenSubtitles

1. **Avvia l'applicazione**
2. **Seleziona video**
3. **Scegli modalità:** 🌐 Scarica da OpenSubtitles
4. **Seleziona lingua**
5. **Click "Avvia"**
6. L'app cercherà e scaricherà i sottotitoli disponibili

### 3️⃣ Elaborazione Batch (Novità!)

Per processare più video contemporaneamente:

1. Click su **"Modalità Batch"**
2. Aggiungi tutti i video desiderati
3. Configura le impostazioni comuni
4. Click **"Elabora Tutti"**
5. Monitora il progresso di ciascun video

### 4️⃣ Preview e Modifica

1. Dopo la generazione, click **"Anteprima"**
2. Visualizza i sottotitoli con timing
3. Click su un segmento per modificarlo
4. Salva le modifiche

### 5️⃣ Traduzione Sottotitoli

1. Apri un file sottotitoli esistente
2. Click su **"Traduci"**
3. Seleziona lingua di destinazione
4. Scegli il servizio di traduzione
5. Click **"Avvia Traduzione"**

## 📊 Tempi di Elaborazione

| Video | Modello | Tempo Stimato |
|-------|---------|---------------|
| 5 min | tiny | 30 sec - 1 min |
| 5 min | base | 1-2 min |
| 5 min | small | 2-3 min |
| 30 min | base | 10-15 min |
| 1 ora | base | 20-30 min |
| 1 ora | large | 60-90 min |
| 2 ore | medium | 60-90 min |

*I tempi variano in base alla CPU. La prima volta che usi un modello sarà più lento (download necessario).*

## 🎯 Guida Scelta Modello

| Modello | RAM | Velocità | Qualità | Quando Usarlo |
|---------|-----|----------|---------|---------------|
| **tiny** | 1 GB | ⚡⚡⚡⚡⚡ | ⭐⭐ | Test rapidi, preview |
| **base** | 1 GB | ⚡⚡⚡⚡ | ⭐⭐⭐ | **Uso quotidiano (consigliato)** |
| **small** | 2 GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Qualità migliore, buona velocità |
| **medium** | 5 GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Alta qualità, lingue complesse |
| **large** | 10 GB | ⚡ | ⭐⭐⭐⭐⭐ | Massima precisione, lingue rare |

## 🔧 Risoluzione Problemi

### ❌ L'applicazione non si avvia

**Problema:** Doppio click su `start.bat` non fa nulla

**Soluzioni:**
1. Hai eseguito `setup.bat` prima? Se no, fallo subito
2. Verifica che Python sia installato: `python --version`
3. Apri il Prompt dei comandi nella cartella e digita: `start.bat`
4. Controlla il file `subtitle_generator.log` per errori dettagliati

### ❌ "FFmpeg non trovato"

**Soluzione:** Installa FFmpeg seguendo le istruzioni nella sezione "Installazione FFmpeg" sopra

### ❌ "Errore nell'estrazione dell'audio"

**Possibili cause e soluzioni:**
- **File corrotto**: Prova ad aprire il video con VLC per verificare
- **Formato non supportato**: Converti il video in MP4 con HandBrake o VLC
- **Permessi insufficienti**: Sposta il video in una cartella dove hai permessi completi

### ❌ Generazione lentissima

**Soluzioni:**
1. Usa un modello più piccolo (`tiny` o `base`)
2. Chiudi applicazioni pesanti per liberare RAM
3. Verifica che il PC non sia in modalità risparmio energetico
4. Per video lunghi (>1 ora), sii paziente o usa `small` invece di `large`

### ❌ Sottotitoli sfasati

**Soluzione:** Usa l'editor integrato per regolare il timing:
1. Apri i sottotitoli con il pulsante "Anteprima"
2. Click su "Regola Timing"
3. Aggiungi/sottrai secondi secondo necessità
4. Salva

### ❌ OpenSubtitles non trova sottotitoli

**Soluzioni:**
1. Rinomina il video con il titolo esatto (es: `Avatar.2009.mp4`)
2. Verifica su opensubtitles.com che esistano sottotitoli in quella lingua
3. Configura la tua API key di OpenSubtitles (vedi sezione configurazione)
4. Usa la generazione automatica come alternativa

### ❌ "Out of memory" / Memoria insufficiente

**Soluzioni:**
1. Usa un modello più piccolo (`tiny` o `base`)
2. Chiudi browser e altre applicazioni
3. Riavvia il PC per liberare RAM
4. Elabora video più corti separatamente invece del batch

### ❌ Batch processing bloccato

**Soluzioni:**
1. Riduci il numero di video elaborati contemporaneamente
2. Verifica che tutti i video siano accessibili
3. Controlla il log per vedere quale video causa problemi
4. Rimuovi quel video e riprova

## 💡 Suggerimenti e Best Practices

### 🎯 Per Risultati Ottimali

- ✅ **Audio pulito**: Meno rumore di fondo = migliore precisione
- ✅ **Modello adeguato**: `base` per uso normale, `large` per massima qualità
- ✅ **Lingua corretta**: Seleziona la lingua effettivamente parlata nel video
- ✅ **File originali**: Evita video ricompressi più volte

### ⚡ Per Velocizzare

- ✅ **Modello tiny/base** per elaborazioni rapide
- ✅ **Batch processing** per più video (gestisce automaticamente le risorse)
- ✅ **Chiudi altre app** per liberare CPU e RAM
- ✅ **SSD invece di HDD** accelera lettura/scrittura

### 📝 Per Sottotitoli Professionali

- ✅ **Revisiona sempre**: L'AI è ottima ma non perfetta
- ✅ **Usa l'editor integrato** per correzioni rapide
- ✅ **Controlla il timing** con la preview
- ✅ **Formato SRT** è il più compatibile universalmente

## 🎨 Configurazione Avanzata

### Impostazioni Preferenze

L'app salva automaticamente le tue preferenze:
- Lingua predefinita
- Modello preferito
- Formato sottotitoli
- Cartella output personalizzata

Per modificare manualmente, edita `config.py`:

```python
# Lingua predefinita
DEFAULT_LANGUAGE = "it"  # Cambia in "en", "es", "fr", ecc.

# Modello Whisper predefinito
DEFAULT_WHISPER_MODEL = "base"  # Cambia in "small", "medium", ecc.

# Cartella output personalizzata
OUTPUT_DIR = Path("C:/I_miei_sottotitoli")  # Windows
OUTPUT_DIR = Path("/home/user/subtitles")   # Linux/Mac
```

### API Key OpenSubtitles

Per il download automatico da OpenSubtitles:

1. Registrati gratis su [opensubtitles.com](https://www.opensubtitles.com)
2. Vai nel tuo profilo → **API**
3. Genera una API key
4. Nel file `config.py`, aggiungi:

```python
OPENSUBTITLES_API_KEY = "la_tua_api_key_qui"
```

### Servizi di Traduzione

Per la traduzione sottotitoli, configura uno di questi servizi:

**Google Translate (Gratuito):**
```python
TRANSLATION_SERVICE = "google"
# Nessuna configurazione necessaria
```

**DeepL (Migliore qualità):**
```python
TRANSLATION_SERVICE = "deepl"
DEEPL_API_KEY = "la_tua_api_key_deepl"
```

## 🏗️ Architettura Tecnica

### Struttura Progetto

```
subtitle_generator/
├── main.py                  # Entry point applicazione
├── app_controller.py        # Controller principale
├── config.py               # Configurazione
├── requirements.txt        # Dipendenze Python
│
├── engines/                # Motori generazione sottotitoli
│   ├── base_engine.py     # Classe astratta
│   └── whisper_engine.py  # Implementazione Whisper
│
├── services/              # Servizi esterni
│   ├── opensubtitles_service.py
│   └── translation_service.py
│
├── utils/                 # Utilità
│   ├── audio_extractor.py
│   ├── subtitle_formatter.py
│   └── subtitle_editor.py
│
└── gui/                   # Interfaccia utente
    ├── main_window.py
    ├── batch_processor.py
    ├── preview_window.py
    └── editor_window.py
```

### Pattern Utilizzati

- **MVC**: Separazione interfaccia/logica/dati
- **Strategy**: Motori intercambiabili (Whisper, futuro: Google, Azure)
- **Facade**: Controller semplifica accesso ai subsystems
- **Observer**: Notifiche progresso in tempo reale

### Estensibilità

Facile aggiungere nuovi motori:

```python
from engines.base_engine import SubtitleEngine

class GoogleSpeechEngine(SubtitleEngine):
    def generate_subtitles(self, audio_path, language, **kwargs):
        # Tua implementazione
        pass
```

## 📚 Esempi d'Uso

### Esempio 1: Film in Italiano

```
Video: Il_Mio_Film.mp4
Modalità: Auto-Genera
Lingua: Italiano
Modello: base
Formato: SRT

Risultato: Il_Mio_Film.srt in output_subtitles/
Tempo: ~15 minuti per un film di 90 minuti
```

### Esempio 2: Serie TV (Batch)

```
Video: 
  - S01E01.mkv
  - S01E02.mkv
  - S01E03.mkv
  
Modalità: Batch + Auto-Genera
Lingua: Inglese
Modello: small

Risultato: 3 file .srt nella cartella output
Tempo: ~45 minuti totali
```

### Esempio 3: Video YouTube + Traduzione

```
1. Genera sottotitoli in inglese
2. Usa funzione "Traduci"
3. Seleziona: Inglese → Italiano
4. Ottieni sottotitoli in italiano
```

## 🌍 Lingue Supportate (90+)

### Europee
Italiano, Inglese, Spagnolo, Francese, Tedesco, Portoghese, Russo, Polacco, Olandese, Svedese, Norvegese, Danese, Finlandese, Greco, Ceco, Ungherese, Rumeno, Turco, Ucraino

### Asiatiche
Cinese (Mandarino), Giapponese, Coreano, Hindi, Arabo, Ebraico, Thai, Vietnamita, Indonesiano, Malese, Tagalog

### Altre
E molte altre lingue meno comuni supportate dai modelli `medium` e `large`

## 🤝 Contribuire

### Aree di Contribuzione

- **Nuovi motori AI**: Google Speech, Azure, AWS
- **Miglioramenti GUI**: Dark mode, temi personalizzati
- **Formati sottotitoli**: ASS, SSA, SUB
- **Test**: Unit test, integration test
- **Documentazione**: Tutorial, video guide
- **Traduzioni UI**: Interfaccia multilingua

### Come Contribuire

1. Fai fork del repository
2. Crea un branch: `git checkout -b feature/nuova-funzionalita`
3. Commit: `git commit -m "feat: Aggiunge nuova funzionalità"`
4. Push: `git push origin feature/nuova-funzionalita`
5. Apri una Pull Request

## 📦 Dipendenze Principali

| Libreria | Versione | Uso |
|----------|----------|-----|
| openai-whisper | latest | Speech-to-text AI |
| ffmpeg-python | 0.2.0+ | Elaborazione audio/video |
| requests | 2.31.0+ | API HTTP client |
| tkinter | built-in | Interfaccia grafica |
| deep-translator | latest | Traduzione sottotitoli |

## 📄 Licenza

**MIT License** - Libero per uso personale e commerciale

```
Copyright (c) 2026 Subtitle Generator

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🙏 Crediti

- **Whisper**: [OpenAI](https://github.com/openai/whisper)
- **FFmpeg**: [FFmpeg Team](https://ffmpeg.org)
- **OpenSubtitles**: [OpenSubtitles.com](https://www.opensubtitles.com)

## 🆘 Supporto

- 🐛 **Bug?** Apri una [Issue](https://github.com/tuo-username/subtitle_generator/issues)
- 💡 **Idea?** Apri una [Discussion](https://github.com/tuo-username/subtitle_generator/discussions)
- 📧 **Contatto diretto**: [Apri Issue su GitHub]

## 🎉 Changelog

### v1.0.0 (2026-01-23)

**Nuove Funzionalità:**
- ✨ Generazione automatica sottotitoli con Whisper AI
- ✨ Download da OpenSubtitles.com
- ✨ **Batch processing** per più video
- ✨ **Preview sottotitoli** in tempo reale
- ✨ **Editor integrato** per modifiche rapide
- ✨ **Traduzione sottotitoli** tra lingue
- ✨ **Salvataggio preferenze** utente
- ✨ GUI drag & drop intuitiva
- ✨ Supporto 90+ lingue
- ✨ Export SRT e VTT

**Miglioramenti:**
- ⚡ Performance ottimizzate per batch processing
- 🎨 Interfaccia moderna e user-friendly
- 📝 Logging dettagliato
- 🛡️ Gestione errori robusta

---

## 🚀 Roadmap Futura

### Prossime Versioni

**v1.1** (Pianificato)
- [ ] Accelerazione GPU (CUDA)
- [ ] Interfaccia web
- [ ] App mobile (Android/iOS)
- [ ] Cloud sync

**v1.2** (Futuro)
- [ ] Integrazione Google Speech API
- [ ] Integrazione Azure Cognitive Services
- [ ] Supporto formato ASS/SSA
- [ ] Auto-sync avanzato con AI

---

**🎬 Buon lavoro con i tuoi sottotitoli!**

*Sviluppato con ❤️ per semplificare la creazione di sottotitoli*
