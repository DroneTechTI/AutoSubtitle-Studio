"""
Configuration settings for Subtitle Generator
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output_subtitles"
TEMP_DIR = BASE_DIR / "temp_audio"
MODELS_DIR = BASE_DIR / "models"
CACHE_DIR = BASE_DIR / "cache"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Whisper settings
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
DEFAULT_WHISPER_MODEL = "base"

# Supported video formats
SUPPORTED_VIDEO_FORMATS = [
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", 
    ".flv", ".webm", ".m4v", ".mpg", ".mpeg"
]

# Supported subtitle formats
SUBTITLE_FORMATS = ["srt", "vtt"]
DEFAULT_SUBTITLE_FORMAT = "srt"

# OpenSubtitles settings
OPENSUBTITLES_API_URL = "https://api.opensubtitles.com/api/v1"
OPENSUBTITLES_USER_AGENT = "SubtitleGenerator v1.0"

# OpenSubtitles API Key (required for downloads)
# IMPORTANT: Don't commit your real API key to GitHub!
# 
# OPTION 1 - Use .env file (recommended):
#   1. Copy .env.example to .env
#   2. Put your key in .env file
#   3. The .env file is gitignored (safe)
#
# OPTION 2 - Set here directly (less safe):
#   Replace None with your key in quotes
#   Remember: Don't push to public repositories!

# Try to load from .env file first
try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    OPENSUBTITLES_API_KEY = os.getenv('OPENSUBTITLES_API_KEY', None)
except:
    # Fallback: set your key here (not recommended for public repos)
    OPENSUBTITLES_API_KEY = None  # Replace None with "your_key_here"

# If you really want to hardcode it (not recommended):
# OPENSUBTITLES_API_KEY = "your_api_key_here"

# Supported languages (ISO 639-1 codes)
LANGUAGES = {
    "it": "Italiano",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "pt": "Português",
    "ru": "Русский",
    "ja": "日本語",
    "zh": "中文",
    "ar": "العربية",
    "hi": "हिन्दी",
    "ko": "한국어",
    "nl": "Nederlands",
    "pl": "Polski",
    "tr": "Türkçe",
    "sv": "Svenska",
    "no": "Norsk",
    "da": "Dansk",
    "fi": "Suomi",
    "el": "Ελληνικά",
    "cs": "Čeština",
    "hu": "Magyar",
    "ro": "Română",
    "th": "ไทย",
    "vi": "Tiếng Việt",
}

DEFAULT_LANGUAGE = "it"

# Application settings
APP_NAME = "Subtitle Generator"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "1100x900"
