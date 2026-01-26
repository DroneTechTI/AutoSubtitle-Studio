"""
Multi-language subtitle generator
"""
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)


class MultiLanguageGenerator:
    """Generate subtitles in multiple languages simultaneously"""
    
    def __init__(self, controller):
        """
        Initialize multi-language generator
        
        Args:
            controller: Application controller instance
        """
        self.controller = controller
        self.results = {}
        self.errors = {}
        self.lock = threading.Lock()
    
    def generate_multiple_languages(self, video_path, languages, model_name="base", 
                                    output_format="srt", progress_callback=None,
                                    cancellation_token=None, parallel=True):
        """
        Generate subtitles in multiple languages
        
        Args:
            video_path: Path to video file
            languages: List of language codes (e.g., ['it', 'en'])
            model_name: Whisper model to use
            output_format: Subtitle format
            progress_callback: Progress callback function
            cancellation_token: Cancellation token
            parallel: Generate in parallel (faster) or sequential (less memory)
        
        Returns:
            Dictionary with language: subtitle_path pairs
        """
        try:
            video_path = Path(video_path)
            
            def log(message):
                logger.info(message)
                if progress_callback:
                    progress_callback(message)
            
            log(f"🌍 Generazione multi-lingua attivata")
            log(f"   Lingue selezionate: {', '.join(languages)}")
            log(f"   Modalità: {'Parallela (veloce)' if parallel else 'Sequenziale (usa meno memoria)'}")
            log("")
            
            # Reset results
            self.results = {}
            self.errors = {}
            
            if parallel:
                # Generate in parallel (faster but uses more memory)
                log("⚡ Avvio generazione parallela...")
                self._generate_parallel(
                    video_path, languages, model_name, 
                    output_format, progress_callback, cancellation_token
                )
            else:
                # Generate sequentially (slower but uses less memory)
                log("🔄 Avvio generazione sequenziale...")
                self._generate_sequential(
                    video_path, languages, model_name,
                    output_format, progress_callback, cancellation_token
                )
            
            # Summary
            log("")
            log("=" * 60)
            log("📊 RIEPILOGO GENERAZIONE MULTI-LINGUA")
            log("=" * 60)
            
            if self.results:
                log(f"✅ Sottotitoli generati con successo: {len(self.results)}/{len(languages)}")
                for lang, path in self.results.items():
                    log(f"   • {lang.upper()}: {Path(path).name}")
            
            if self.errors:
                log(f"❌ Errori: {len(self.errors)}/{len(languages)}")
                for lang, error in self.errors.items():
                    log(f"   • {lang.upper()}: {str(error)[:50]}")
            
            log("=" * 60)
            
            return self.results
            
        except Exception as e:
            logger.error(f"Error in multi-language generation: {str(e)}")
            raise
    
    def _generate_parallel(self, video_path, languages, model_name, 
                          output_format, progress_callback, cancellation_token):
        """Generate subtitles in parallel using ThreadPoolExecutor"""
        try:
            # Use ThreadPoolExecutor for parallel execution
            max_workers = min(len(languages), 3)  # Max 3 parallel to avoid memory issues
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_lang = {}
                for lang in languages:
                    future = executor.submit(
                        self._generate_single_language,
                        video_path, lang, model_name, output_format,
                        progress_callback, cancellation_token
                    )
                    future_to_lang[future] = lang
                
                # Wait for completion
                for future in as_completed(future_to_lang):
                    lang = future_to_lang[future]
                    try:
                        result = future.result()
                        with self.lock:
                            self.results[lang] = result
                        logger.info(f"✓ Completed: {lang}")
                    except Exception as e:
                        with self.lock:
                            self.errors[lang] = str(e)
                        logger.error(f"✗ Failed: {lang} - {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error in parallel generation: {str(e)}")
            raise
    
    def _generate_sequential(self, video_path, languages, model_name,
                            output_format, progress_callback, cancellation_token):
        """Generate subtitles sequentially (one at a time)"""
        try:
            for idx, lang in enumerate(languages, 1):
                try:
                    if progress_callback:
                        progress_callback(f"\n[{idx}/{len(languages)}] Generazione {lang.upper()}...")
                    
                    result = self._generate_single_language(
                        video_path, lang, model_name, output_format,
                        progress_callback, cancellation_token
                    )
                    
                    self.results[lang] = result
                    logger.info(f"✓ Completed: {lang}")
                    
                except Exception as e:
                    self.errors[lang] = str(e)
                    logger.error(f"✗ Failed: {lang} - {str(e)}")
                    # Continue with next language even if one fails
                    
        except Exception as e:
            logger.error(f"Error in sequential generation: {str(e)}")
            raise
    
    def _generate_single_language(self, video_path, language, model_name,
                                  output_format, progress_callback, cancellation_token):
        """
        Generate subtitles for a single language
        
        Args:
            video_path: Path to video file
            language: Language code
            model_name: Whisper model
            output_format: Subtitle format
            progress_callback: Progress callback
            cancellation_token: Cancellation token
        
        Returns:
            Path to generated subtitle file
        """
        try:
            # Create language-specific callback
            def lang_callback(message):
                if progress_callback:
                    progress_callback(f"[{language.upper()}] {message}")
            
            # Generate subtitles using controller
            result = self.controller.generate_subtitles(
                video_path=video_path,
                language=language,
                output_format=output_format,
                model_name=model_name,
                progress_callback=lang_callback,
                cancellation_token=cancellation_token
            )
            
            # Rename file to include language code
            if result:
                result_path = Path(result)
                new_name = f"{result_path.stem}_{language}{result_path.suffix}"
                new_path = result_path.parent / new_name
                
                # Rename if needed
                if result_path != new_path:
                    result_path.rename(new_path)
                    logger.info(f"Renamed to: {new_path.name}")
                    return new_path
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating {language} subtitles: {str(e)}")
            raise
    
    def estimate_time(self, video_duration, num_languages, model_name="base", parallel=True):
        """
        Estimate processing time for multi-language generation
        
        Args:
            video_duration: Video duration in seconds
            num_languages: Number of languages
            model_name: Whisper model name
            parallel: Parallel or sequential mode
        
        Returns:
            Estimated time in seconds
        """
        # Base processing speed (seconds of video per second of processing)
        speeds = {
            'tiny': 20,
            'base': 15,
            'small': 10,
            'medium': 5,
            'large': 3
        }
        
        speed = speeds.get(model_name, 10)
        single_lang_time = video_duration / speed
        
        if parallel:
            # Parallel mode: time ≈ slowest language + overhead
            # Assume max 3 parallel workers
            batches = (num_languages + 2) // 3  # Ceiling division
            estimated = single_lang_time * batches * 1.2  # 20% overhead
        else:
            # Sequential mode: sum of all languages
            estimated = single_lang_time * num_languages * 1.1  # 10% overhead
        
        return estimated
    
    def get_supported_languages(self):
        """
        Get list of supported languages
        
        Returns:
            Dictionary of language_code: language_name
        """
        return {
            'it': 'Italiano',
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'pt': 'Português',
            'ru': 'Русский',
            'zh': '中文',
            'ja': '日本語',
            'ko': '한국어',
            'ar': 'العربية',
            'hi': 'हिन्दी',
            'nl': 'Nederlands',
            'pl': 'Polski',
            'tr': 'Türkçe',
            'sv': 'Svenska',
            'no': 'Norsk',
            'da': 'Dansk',
            'fi': 'Suomi',
            'cs': 'Čeština',
            'uk': 'Українська',
            'ro': 'Română',
            'el': 'Ελληνικά',
            'hu': 'Magyar',
            'th': 'ไทย',
            'id': 'Bahasa Indonesia',
            'vi': 'Tiếng Việt',
            'he': 'עברית',
            'fa': 'فارسی',
        }
