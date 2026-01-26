# AutoSubtitle Studio 🎬

> 🌍 **[English version](README_EN.md)** | **[Versione Italiana](README.md)**

**Professional studio for automatic subtitle generation** with artificial intelligence, OpenSubtitles download, advanced synchronization and much more.

Complete and professional application for automatically generating subtitles from your videos using artificial intelligence, or downloading existing subtitles from OpenSubtitles.

## ✨ Key Features

### 🤖 Automatic Generation
- **AI Speech-to-Text** with Whisper (OpenAI) - one of the best open-source models
- **90+ supported languages** (Italian, English, Spanish, French, German, Chinese, Japanese, etc.)
- **5 quality levels**: tiny (fast) → large (maximum quality)
- **Batch processing**: process multiple videos simultaneously
- **Auto-sync**: automatic timing adjustment

### 🌐 Subtitle Download
- **OpenSubtitles.com integration** for downloading existing subtitles
- **Smart search** via video hash for precise matches
- **Multi-language**: search subtitles in any available language

### 🎨 User Interface
- **Intuitive GUI** with drag & drop
- **Real-time subtitle preview**
- **Integrated editor** for quick edits
- **Progress bar and logs** to monitor processing
- **Preferences saving** for quick usage

### 📁 Formats and Compatibility
- **Video**: MP4, MKV, AVI, MOV, WMV, FLV, WEBM, M4V, MPG, MPEG
- **Subtitles**: SRT, VTT (compatible with VLC, YouTube, Plex, Kodi, etc.)
- **Translation**: translate subtitles between different languages

## 📋 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, macOS 10.15, Linux | Windows 11, macOS 13+, Recent Linux |
| **RAM** | 4 GB | 8 GB+ |
| **Disk Space** | 3 GB | 5 GB+ |
| **CPU** | Dual-core | Quad-core+ |
| **Internet** | For setup and model download | - |

## 🚀 Installation and Launch

### ⚡ Quick Start (5 minutes)

#### First Installation

**Windows:**
```bash
# Double-click on:
setup.bat
```

**macOS/Linux:**
```bash
chmod +x setup.sh start.sh
./setup.sh
```

⏳ Installation takes 5-10 minutes and automatically installs all dependencies.

#### Normal Launch

**Windows:**
```bash
# Double-click on:
start.bat
```

**macOS/Linux:**
```bash
./start.sh
```

### 🔧 FFmpeg Installation (if required)

**Windows - AUTOMATIC METHOD (Recommended):**

If FFmpeg is not installed during setup, you'll be asked if you want to install it automatically.

Or you can launch it manually:
1. **Right-click** on `install_ffmpeg_windows.bat`
2. Select **"Run as administrator"**
3. Follow the instructions
4. Close and reopen the terminal
5. Run `setup.bat` again

**Windows - CHOCOLATEY METHOD (Alternative):**
```powershell
# Install Chocolatey (if you don't have it)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install FFmpeg
choco install ffmpeg
```

**Windows - MANUAL METHOD:**
1. Go to https://github.com/BtbN/FFmpeg-Builds/releases
2. Download `ffmpeg-master-latest-win64-gpl-shared.zip` (latest version)
3. Extract to `C:\ffmpeg`
4. Add `C:\ffmpeg\bin` to system PATH:
   - Search "Environment variables" in Start menu
   - Click "Edit system environment variables"
   - Click "Environment Variables"
   - Select "Path" and click "Edit"
   - Click "New" and add `C:\ffmpeg\bin`
   - OK on everything
5. Close and reopen the terminal

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg
```

## 📖 Usage Guide

### 1️⃣ Automatic Generation

1. **Launch the application** (`start.bat` or `start.sh`)
2. **Select mode**: "🤖 Auto-Generate (Artificial Intelligence)"
3. **Choose video file** (click "Browse..." or drag & drop)
4. **Configure options**:
   - **Language**: Select the video's spoken language
   - **Model**: Choose quality (recommended: `base` or `small`)
   - **Format**: SRT (recommended) or VTT
5. **Click "Generate Subtitles"**
6. **Wait for completion** ⏳ (can take several minutes for long videos)

**Model Recommendations:**
- `tiny`: Very fast, good for tests (1GB RAM)
- `base`: **Recommended** - good balance between speed and quality (1.5GB RAM)
- `small`: Better quality, slower (2.5GB RAM)
- `medium`: Excellent quality, requires powerful PC (5GB RAM)
- `large`: Maximum quality, very slow (10GB RAM)

### 2️⃣ Download from OpenSubtitles

1. **Get FREE API Key**:
   - Go to https://www.opensubtitles.com
   - Create free account
   - Go to: Profile > API
   - Generate API Key
   - Copy `.env.example` to `.env`
   - Paste your key in `.env`

2. **Use the application**:
   - Launch application
   - Select mode: "🌐 Download from OpenSubtitles"
   - Choose video file
   - Select language
   - Click "Download Subtitles"

### 3️⃣ Advanced Tools

Access from **Tools** menu:

#### 📦 Batch Processing
- Process multiple videos at once
- Automatic queue management
- Resume on error

#### 🎬 Video Integration
- **Soft subtitles**: Add subtitles to video (toggleable)
- **Hard subtitles**: Burn subtitles into video (permanent)
- Extract subtitles from video

#### 🔄 Auto-Sync
- Automatic subtitle synchronization with audio
- Advanced algorithms with machine learning
- Manual timing correction

#### 📊 Statistics
- Subtitle analysis (duration, speed, readability)
- Quality report
- Export statistics to CSV/PDF

## 🆘 Troubleshooting

### ❌ "Out of memory" / Insufficient Memory

**Solution**:
1. Use smaller model: `tiny` or `base`
2. Close other applications
3. Restart computer
4. For very long videos (>2 hours): split into parts

### ❌ "FFmpeg not found"

**Solution**:
1. Follow installation section above
2. Verify with: `ffmpeg -version` (terminal)
3. Make sure to restart terminal after installation

### ❌ "No subtitles found" (OpenSubtitles)

**Reasons**:
1. No subtitles exist for that video
2. No exact hash match
3. API key not configured

**Solutions**:
- Try searching manually on opensubtitles.com
- Configure API key (see section above)
- Use automatic generation instead

### ❌ "ModuleNotFoundError"

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### ❌ GUI doesn't open / Black screen

**Solution**:
1. Check Python version: `python --version` (requires 3.8+)
2. Reinstall tkinter:
   - **Ubuntu/Debian**: `sudo apt install python3-tk`
   - **macOS**: Should be included
   - **Windows**: Should be included

## 🔧 Configuration

### config.py

Customize application settings:

```python
# Output directory
OUTPUT_DIR = BASE_DIR / "output_subtitles"

# Default model
DEFAULT_WHISPER_MODEL = "base"  # Change to: tiny, small, medium, large

# Supported languages
LANGUAGES = {
    "it": "Italiano",
    "en": "English",
    # Add more languages here
}
```

### .env File

For OpenSubtitles API key:

```bash
OPENSUBTITLES_API_KEY=your_api_key_here
```

## 📚 Examples

### Example 1: Italian Movie

```
Video: my_movie.mp4 (Italian audio)
Settings:
  - Mode: Auto-generate
  - Language: it (Italian)
  - Model: base
  - Format: SRT

Result: my_movie.srt
```

### Example 2: English Series (Download)

```
Video: series_s01e01.mkv
Settings:
  - Mode: Download OpenSubtitles
  - Language: en (English)

Result: series_s01e01.srt (downloaded)
```

### Example 3: Batch Processing

```
Folder: /movies/
  - movie1.mp4
  - movie2.mkv
  - movie3.avi

Use: Tools > Batch Processing
Result: Subtitles for all videos
```

## 🎯 Tips for Best Quality

1. **Better audio = better subtitles**
   - Clear audio without background noise
   - Good volume level
   - No overlapping voices

2. **Choose right model**
   - Tests/quick checks: `tiny` or `base`
   - Production/final: `small` or `medium`
   - Professional quality: `large` (requires powerful PC)

3. **Language optimization**
   - Specify correct language for better results
   - For mixed languages, use dominant language
   - For automatic detection, leave blank

4. **Post-processing**
   - Use "Clean Subtitles" tool for formatting
   - Verify with "Preview" before exporting
   - Use "Auto-sync" if out of sync

## 🛠️ Development

### Architecture

```
subtitle_generator/
├── main.py                 # Entry point
├── app_controller.py       # Main controller
├── config.py              # Configuration
├── engines/               # Subtitle engines
│   ├── base_engine.py
│   └── whisper_engine.py
├── services/              # External services
│   ├── opensubtitles_service.py
│   └── translation_service.py
├── gui/                   # Graphical interface
│   ├── main_window.py
│   ├── batch_processor.py
│   └── preview_window.py
├── utils/                 # Utilities
│   ├── audio_extractor.py
│   ├── video_validator.py
│   ├── memory_manager.py
│   ├── checkpoint_manager.py
│   └── notification_manager.py
└── tests/                # Unit tests
```

### Running Tests

```bash
python -m pytest tests/
```

### Adding New Engines

1. Create new class in `engines/`
2. Inherit from `SubtitleEngine`
3. Implement required methods
4. Register in `app_controller.py`

## 📝 License

MIT License - See [LICENSE](LICENSE) file

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 🌟 Credits

- **Whisper** by OpenAI - Speech recognition model
- **OpenSubtitles.com** - Subtitle database
- **FFmpeg** - Audio/video processing

## 📮 Support

Having issues? 
1. Check [Troubleshooting](#-troubleshooting) section
2. Search existing [Issues](../../issues)
3. Open new issue with:
   - Operating system
   - Python version
   - Error description
   - Log file (`subtitle_generator.log`)

## 🗺️ Roadmap

### Next Versions

- [ ] GPU acceleration support (CUDA/Metal)
- [ ] Cloud processing for heavy models
- [ ] More subtitle formats (ASS, SSA)
- [ ] Real-time subtitle generation
- [ ] Speech recognition training for custom domains
- [ ] Multi-language subtitle generation
- [ ] Advanced subtitle editor
- [ ] Docker container

---

Made with ❤️ for the subtitle community

**Star this repo if you find it useful!** ⭐
