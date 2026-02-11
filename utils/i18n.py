"""
Internationalization (i18n) support for AutoSubtitle Studio
"""
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class I18n:
    """Internationalization manager"""
    
    # Translation dictionaries
    TRANSLATIONS = {
        'it': {
            # Menu items
            'menu_file': 'File',
            'menu_open_video': 'Apri Video',
            'menu_recent_files': 'File Recenti',
            'menu_open_output': 'Apri Cartella Output',
            'menu_exit': 'Esci',
            'menu_tools': 'Strumenti',
            'menu_multilang': '🌍 Multi-Lingua',
            'menu_batch': 'Batch Processing',
            'menu_integrate': 'Integra Video',
            'menu_clean': 'Pulisci Sottotitoli',
            'menu_stats': 'Statistiche Sottotitoli',
            'menu_compare': 'Confronta Sottotitoli',
            'menu_merge': 'Unisci Sottotitoli',
            'menu_options': 'Opzioni',
            'menu_preferences': 'Preferenze',
            'menu_clean_cache': 'Pulisci Cache',
            'menu_check_ffmpeg': 'Verifica FFmpeg',
            'menu_view': 'Visualizza',
            'menu_log': '📋 Log Completo',
            'menu_refresh': 'Aggiorna',
            'menu_help': 'Aiuto',
            'menu_quick_guide': 'Guida Rapida',
            'menu_shortcuts': 'Shortcuts Tastiera',
            'menu_about': 'Info',
            
            # Main window
            'app_title': 'AutoSubtitle Studio',
            'subtitle': 'Studio Professionale per Sottotitoli',
            'select_video': 'File Video:',
            'browse': 'Sfoglia...',
            'drag_drop_hint': '💡 Oppure trascina il video qui sopra',
            'mode': 'Modalità:',
            'mode_auto': '🤖 Auto-Genera (Intelligenza Artificiale)',
            'mode_download': '🌐 Scarica da OpenSubtitles',
            'options': 'Opzioni',
            'language': 'Lingua:',
            'format': 'Formato:',
            'model_quality': 'Qualità Modello:',
            'model_hint': '(tiny=veloce, large=migliore qualità)',
            'progress': 'Progresso',
            'status_ready': 'Pronto. Seleziona un video per iniziare.',
            'log': 'Log',
            'start': '▶ Avvia',
            'cancel': '⏹ Annulla',
            'batch': '📂 Batch',
            'preview': '👁 Anteprima',
            'translate': '🌐 Traduci',
            'integrate_video': '🎬 Integra Video',
            'clean_log': '🗑 Pulisci Log',
            'view_log': '📋 Visualizza Log',
            'open_output_folder': '📁 Apri Cartella Output',
            'preferences_btn': '⚙ Preferenze',
            
            # Messages
            'error': 'Errore',
            'success': 'Successo',
            'warning': 'Attenzione',
            'info': 'Informazione',
            'confirm': 'Conferma',
            'select_video_error': 'Seleziona un file video!',
            'video_not_found': 'Il file video non esiste!',
            'processing': 'Elaborazione in corso...',
            'completed': 'Completato con successo!',
            'cancelled': 'Operazione annullata',
            'confirm_cancel': 'Vuoi annullare l\'operazione in corso?',
            
            # Multi-language window
            'multilang_title': '🌍 Generazione Sottotitoli Multi-Lingua',
            'multilang_subtitle': 'Genera sottotitoli in più lingue contemporaneamente',
            'video_label': 'Video',
            'languages_label': 'Lingue da Generare',
            'quick_select': 'Selezione rapida:',
            'select_all': 'Seleziona Tutto',
            'deselect_all': 'Deseleziona Tutto',
            'parallel_mode': '⚡ Parallela (veloce, usa più RAM)',
            'sequential_mode': '🔄 Sequenziale (lenta, meno RAM)',
            'mode_label': 'Modalità:',
            'estimate_time': '⏱️ Stima Tempo',
            'generate_subs': '▶ Genera Sottotitoli',
            'close': '❌ Chiudi',
            'select_language_error': 'Seleziona almeno una lingua!',
            
            # Settings
            'change_language': '🌍 Lingua Interfaccia',
            'language_changed': 'Lingua cambiata! Riavvia l\'applicazione per applicare le modifiche.',
        },
        'en': {
            # Menu items
            'menu_file': 'File',
            'menu_open_video': 'Open Video',
            'menu_recent_files': 'Recent Files',
            'menu_open_output': 'Open Output Folder',
            'menu_exit': 'Exit',
            'menu_tools': 'Tools',
            'menu_multilang': '🌍 Multi-Language',
            'menu_batch': 'Batch Processing',
            'menu_integrate': 'Integrate Video',
            'menu_clean': 'Clean Subtitles',
            'menu_stats': 'Subtitle Statistics',
            'menu_compare': 'Compare Subtitles',
            'menu_merge': 'Merge Subtitles',
            'menu_options': 'Options',
            'menu_preferences': 'Preferences',
            'menu_clean_cache': 'Clean Cache',
            'menu_check_ffmpeg': 'Check FFmpeg',
            'menu_view': 'View',
            'menu_log': '📋 Full Log',
            'menu_refresh': 'Refresh',
            'menu_help': 'Help',
            'menu_quick_guide': 'Quick Guide',
            'menu_shortcuts': 'Keyboard Shortcuts',
            'menu_about': 'About',
            
            # Main window
            'app_title': 'AutoSubtitle Studio',
            'subtitle': 'Professional Subtitle Studio',
            'select_video': 'Video File:',
            'browse': 'Browse...',
            'drag_drop_hint': '💡 Or drag the video here',
            'mode': 'Mode:',
            'mode_auto': '🤖 Auto-Generate (Artificial Intelligence)',
            'mode_download': '🌐 Download from OpenSubtitles',
            'options': 'Options',
            'language': 'Language:',
            'format': 'Format:',
            'model_quality': 'Model Quality:',
            'model_hint': '(tiny=fast, large=best quality)',
            'progress': 'Progress',
            'status_ready': 'Ready. Select a video to start.',
            'log': 'Log',
            'start': '▶ Start',
            'cancel': '⏹ Cancel',
            'batch': '📂 Batch',
            'preview': '👁 Preview',
            'translate': '🌐 Translate',
            'integrate_video': '🎬 Integrate Video',
            'clean_log': '🗑 Clean Log',
            'view_log': '📋 View Log',
            'open_output_folder': '📁 Open Output Folder',
            'preferences_btn': '⚙ Preferences',
            
            # Messages
            'error': 'Error',
            'success': 'Success',
            'warning': 'Warning',
            'info': 'Information',
            'confirm': 'Confirm',
            'select_video_error': 'Select a video file!',
            'video_not_found': 'Video file does not exist!',
            'processing': 'Processing...',
            'completed': 'Completed successfully!',
            'cancelled': 'Operation cancelled',
            'confirm_cancel': 'Do you want to cancel the current operation?',
            
            # Multi-language window
            'multilang_title': '🌍 Multi-Language Subtitle Generation',
            'multilang_subtitle': 'Generate subtitles in multiple languages simultaneously',
            'video_label': 'Video',
            'languages_label': 'Languages to Generate',
            'quick_select': 'Quick select:',
            'select_all': 'Select All',
            'deselect_all': 'Deselect All',
            'parallel_mode': '⚡ Parallel (fast, uses more RAM)',
            'sequential_mode': '🔄 Sequential (slow, less RAM)',
            'mode_label': 'Mode:',
            'estimate_time': '⏱️ Estimate Time',
            'generate_subs': '▶ Generate Subtitles',
            'close': '❌ Close',
            'select_language_error': 'Select at least one language!',
            
            # Settings
            'change_language': '🌍 Interface Language',
            'language_changed': 'Language changed! Restart the application to apply changes.',
        }
    }
    
    def __init__(self):
        self.current_language = 'it'  # Default to Italian
        self.load_preferences()
    
    def load_preferences(self):
        """Load language preference from file"""
        try:
            pref_file = Path.home() / '.autosubtitle_studio' / 'preferences.json'
            if pref_file.exists():
                with open(pref_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    self.current_language = prefs.get('ui_language', 'it')
                    logger.info(f"Loaded language preference: {self.current_language}")
        except Exception as e:
            logger.error(f"Error loading language preference: {str(e)}")
    
    def save_preferences(self):
        """Save language preference to file"""
        try:
            pref_dir = Path.home() / '.autosubtitle_studio'
            pref_dir.mkdir(exist_ok=True)
            pref_file = pref_dir / 'preferences.json'
            
            prefs = {}
            if pref_file.exists():
                with open(pref_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
            
            prefs['ui_language'] = self.current_language
            
            with open(pref_file, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved language preference: {self.current_language}")
        except Exception as e:
            logger.error(f"Error saving language preference: {str(e)}")
    
    def set_language(self, language_code):
        """
        Set current language
        
        Args:
            language_code: Language code ('it' or 'en')
        """
        if language_code in self.TRANSLATIONS:
            self.current_language = language_code
            self.save_preferences()
            logger.info(f"Language set to: {language_code}")
        else:
            logger.warning(f"Language not supported: {language_code}")
    
    def get(self, key, default=None):
        """
        Get translated string for current language
        
        Args:
            key: Translation key
            default: Default value if key not found
        
        Returns:
            Translated string
        """
        translations = self.TRANSLATIONS.get(self.current_language, {})
        return translations.get(key, default or key)
    
    def get_available_languages(self):
        """
        Get list of available UI languages
        
        Returns:
            Dictionary of language_code: language_name
        """
        return {
            'it': 'Italiano',
            'en': 'English'
        }
    
    def get_current_language(self):
        """Get current language code"""
        return self.current_language


# Global instance
_i18n_instance = None

def get_i18n():
    """Get global I18n instance"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n()
    return _i18n_instance

def t(key, default=None):
    """
    Shorthand for translation
    
    Args:
        key: Translation key
        default: Default value
    
    Returns:
        Translated string
    """
    return get_i18n().get(key, default)
