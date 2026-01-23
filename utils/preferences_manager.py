"""
User preferences management
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PreferencesManager:
    """Manage user preferences"""
    
    def __init__(self, prefs_file="user_preferences.json"):
        self.prefs_file = Path(prefs_file)
        self.preferences = self._load_preferences()
        
    def _load_preferences(self):
        """Load preferences from file"""
        if self.prefs_file.exists():
            try:
                with open(self.prefs_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    logger.info("Preferences loaded successfully")
                    return prefs
            except Exception as e:
                logger.error(f"Error loading preferences: {str(e)}")
                return self._default_preferences()
        else:
            return self._default_preferences()
    
    def _default_preferences(self):
        """Return default preferences"""
        return {
            'language': 'it',
            'model': 'base',
            'format': 'srt',
            'output_dir': '',
            'last_videos': [],
            'window_geometry': '900x700',
            'theme': 'default',
            'auto_save': True,
            'show_preview': True,
            'translation_service': 'google'
        }
    
    def save_preferences(self):
        """Save preferences to file"""
        try:
            with open(self.prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=4, ensure_ascii=False)
            logger.info("Preferences saved successfully")
        except Exception as e:
            logger.error(f"Error saving preferences: {str(e)}")
    
    def get(self, key, default=None):
        """Get preference value"""
        return self.preferences.get(key, default)
    
    def set(self, key, value):
        """Set preference value"""
        self.preferences[key] = value
        if self.preferences.get('auto_save', True):
            self.save_preferences()
    
    def update_last_videos(self, video_path, max_recent=10):
        """Update list of recently used videos"""
        last_videos = self.preferences.get('last_videos', [])
        
        # Remove if already exists
        if video_path in last_videos:
            last_videos.remove(video_path)
        
        # Add to front
        last_videos.insert(0, video_path)
        
        # Keep only max_recent items
        self.preferences['last_videos'] = last_videos[:max_recent]
        
        if self.preferences.get('auto_save', True):
            self.save_preferences()
    
    def get_last_videos(self):
        """Get list of recently used videos"""
        return self.preferences.get('last_videos', [])
    
    def reset_to_defaults(self):
        """Reset all preferences to defaults"""
        self.preferences = self._default_preferences()
        self.save_preferences()
        logger.info("Preferences reset to defaults")
