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
    
    def generate_subtitles(self, audio_path, language="en", task="transcribe", 
                          progress_callback=None, **kwargs):
        """
        Generate subtitles using Whisper
        
        Args:
            audio_path: Path to audio file
            language: Language code (ISO 639-1)
            task: 'transcribe' or 'translate' (translate converts to English)
            progress_callback: Callback function(current, total, message) for progress updates
            **kwargs: Additional Whisper parameters
        
        Returns:
            List of subtitle segments
        """
        if not self.is_available():
            raise RuntimeError("Whisper model not available")
        
        try:
            import time
            audio_path = Path(audio_path)
            logger.info(f"Generating subtitles with Whisper ({self.model_name})")
            logger.info(f"Language: {language}, Task: {task}")
            
            # Get audio duration for progress estimation
            audio_duration = self._get_audio_duration(audio_path)
            logger.info(f"Audio duration: {audio_duration:.1f} seconds")
            
            # Estimate processing time (rough approximation)
            # Whisper processes at roughly 10x-20x real-time depending on model
            processing_speed_factor = {
                'tiny': 20,
                'base': 15,
                'small': 10,
                'medium': 5,
                'large': 3
            }.get(self.model_name, 10)
            
            estimated_time = audio_duration / processing_speed_factor
            logger.info(f"Estimated processing time: {estimated_time:.1f} seconds")
            
            if progress_callback:
                progress_callback(0, 100, "Inizializzazione trascrizione...")
            
            start_time = time.time()
            
            # Transcribe audio with verbose for progress
            result = self.model.transcribe(
                str(audio_path),
                language=language if language in self.SUPPORTED_LANGUAGES else None,
                task=task,
                verbose=False,
                **kwargs
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Transcription completed in {elapsed_time:.1f} seconds")
            
            if progress_callback:
                progress_callback(90, 100, "Elaborazione segmenti...")
            
            # Extract segments
            segments = []
            total_segments = len(result.get('segments', []))
            
            for idx, segment in enumerate(result.get('segments', [])):
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text']
                })
                
                # Update progress during segment extraction
                if progress_callback and idx % 10 == 0:
                    progress = 90 + int((idx / total_segments) * 10)
                    progress_callback(progress, 100, f"Elaborazione segmento {idx+1}/{total_segments}")
            
            if progress_callback:
                progress_callback(100, 100, "Trascrizione completata!")
            
            logger.info(f"Generated {len(segments)} subtitle segments")
            return segments
            
        except Exception as e:
            logger.error(f"Error generating subtitles with Whisper: {str(e)}")
            raise
    
    def _get_audio_duration(self, audio_path):
        """Get audio file duration in seconds"""
        try:
            import ffmpeg
            probe = ffmpeg.probe(str(audio_path))
            duration = float(probe['format']['duration'])
            return duration
        except Exception as e:
            logger.warning(f"Could not get audio duration: {str(e)}")
            return 0.0
    
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
