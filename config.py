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
# Get your free API key from: https://www.opensubtitles.com/consumers
# 1. Create a free account on opensubtitles.com
# 2. Go to your profile -> API
# 3. Generate a new API key
# 4. Paste it here (replace None with your key in quotes)
OPENSUBTITLES_API_KEY = None  # Example: "your_api_key_here"

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
WINDOW_SIZE = "900x700"
