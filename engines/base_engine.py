"""
Base class for subtitle generation engines
This allows easy addition of new engines in the future
"""
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class SubtitleEngine(ABC):
    """Abstract base class for subtitle generation engines"""
    
    def __init__(self, name, **kwargs):
        self.name = name
        self.config = kwargs
        logger.info(f"Initialized {self.name} engine")
    
    @abstractmethod
    def generate_subtitles(self, audio_path, language="en", **kwargs):
        """
        Generate subtitles from audio file
        
        Args:
            audio_path: Path to the audio file
            language: Language code (ISO 639-1)
            **kwargs: Additional engine-specific parameters
        
        Returns:
            List of segments with 'start', 'end', and 'text' keys
        """
        pass
    
    @abstractmethod
    def is_available(self):
        """Check if the engine is available and properly configured"""
        pass
    
    @abstractmethod
    def get_supported_languages(self):
        """Return list of supported language codes"""
        pass
    
    def get_info(self):
        """Return engine information"""
        return {
            "name": self.name,
            "available": self.is_available(),
            "languages": self.get_supported_languages()
        }
