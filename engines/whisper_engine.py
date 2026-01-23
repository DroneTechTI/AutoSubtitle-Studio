"""
Whisper engine for subtitle generation using OpenAI's Whisper model
"""
import logging
from pathlib import Path
import whisper
from .base_engine import SubtitleEngine

logger = logging.getLogger(__name__)


class WhisperEngine(SubtitleEngine):
    """Whisper-based subtitle generation engine"""
    
    # Whisper supported languages
    SUPPORTED_LANGUAGES = [
        "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", 
        "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi", 
        "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy", 
        "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", 
        "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", 
        "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru", 
        "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", 
        "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi", 
        "yi", "yo", "zh", "yue"
    ]
    
    def __init__(self, model_name="base", device="cpu", **kwargs):
        super().__init__(name="Whisper", **kwargs)
        self.model_name = model_name
        self.device = device
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            self.model = None
            raise
    
    def generate_subtitles(self, audio_path, language="en", task="transcribe", **kwargs):
        """
        Generate subtitles using Whisper
        
        Args:
            audio_path: Path to audio file
            language: Language code (ISO 639-1)
            task: 'transcribe' or 'translate' (translate converts to English)
            **kwargs: Additional Whisper parameters
        
        Returns:
            List of subtitle segments
        """
        if not self.is_available():
            raise RuntimeError("Whisper model not available")
        
        try:
            audio_path = Path(audio_path)
            logger.info(f"Generating subtitles with Whisper ({self.model_name})")
            logger.info(f"Language: {language}, Task: {task}")
            
            # Transcribe audio
            result = self.model.transcribe(
                str(audio_path),
                language=language if language in self.SUPPORTED_LANGUAGES else None,
                task=task,
                verbose=False,
                **kwargs
            )
            
            # Extract segments
            segments = []
            for segment in result.get('segments', []):
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text']
                })
            
            logger.info(f"Generated {len(segments)} subtitle segments")
            return segments
            
        except Exception as e:
            logger.error(f"Error generating subtitles with Whisper: {str(e)}")
            raise
    
    def is_available(self):
        """Check if Whisper model is loaded"""
        return self.model is not None
    
    def get_supported_languages(self):
        """Return list of supported languages"""
        return self.SUPPORTED_LANGUAGES
    
    def change_model(self, model_name):
        """Change the Whisper model"""
        self.model_name = model_name
        self._load_model()
