"""
Main application controller - coordinates all components
"""
import logging
from pathlib import Path
import threading
import config
from utils.audio_extractor import AudioExtractor
from utils.subtitle_formatter import SubtitleFormatter
from utils.video_validator import VideoValidator, VideoValidationError
from engines.whisper_engine import WhisperEngine
from services.opensubtitles_service import OpenSubtitlesService

logger = logging.getLogger(__name__)


class CancellationToken:
    """Thread-safe cancellation token for long-running operations"""
    
    def __init__(self):
        self._cancelled = False
        self._lock = threading.Lock()
    
    def cancel(self):
        """Request cancellation"""
        with self._lock:
            self._cancelled = True
            logger.info("Cancellation requested")
    
    def is_cancelled(self):
        """Check if cancellation was requested"""
        with self._lock:
            return self._cancelled
    
    def check_cancelled(self):
        """Raise exception if cancelled"""
        if self.is_cancelled():
            raise OperationCancelledException("Operation cancelled by user")


class OperationCancelledException(Exception):
    """Exception raised when operation is cancelled by user"""
    pass


class AppController:
    """Main application controller"""
    
    def __init__(self):
        self.config = config
        
        # Initialize components
        self.audio_extractor = AudioExtractor(temp_dir=config.TEMP_DIR)
        self.subtitle_formatter = SubtitleFormatter()
        self.video_validator = VideoValidator()
        
        # Initialize engines (lazy loading for Whisper)
        self.whisper_engine = None
        self.current_whisper_model = None
        
        # Initialize OpenSubtitles service
        api_key = getattr(config, 'OPENSUBTITLES_API_KEY', None)
        self.opensubtitles = OpenSubtitlesService(
            api_url=config.OPENSUBTITLES_API_URL,
            user_agent=config.OPENSUBTITLES_USER_AGENT,
            api_key=api_key
        )
        
        # Cancellation token for current operation
        self.current_cancellation_token = None
        
        logger.info("AppController initialized")
    
    def create_cancellation_token(self):
        """Create a new cancellation token for an operation"""
        self.current_cancellation_token = CancellationToken()
        return self.current_cancellation_token
    
    def cancel_current_operation(self):
        """Cancel the current operation if any"""
        if self.current_cancellation_token:
            self.current_cancellation_token.cancel()
            logger.info("Current operation cancellation requested")
    
    def _get_whisper_engine(self, model_name="base"):
        """Get or create Whisper engine with specified model"""
        if self.whisper_engine is None or self.current_whisper_model != model_name:
            logger.info(f"Loading Whisper engine with model: {model_name}")
            self.whisper_engine = WhisperEngine(model_name=model_name)
            self.current_whisper_model = model_name
        return self.whisper_engine
    
    def generate_subtitles(self, video_path, language="it", output_format="srt", 
                          model_name="base", progress_callback=None, cancellation_token=None):
        """
        Generate subtitles from video file
        
        Args:
            video_path: Path to video file
            language: Language code
            output_format: Subtitle format (srt or vtt)
            model_name: Whisper model to use
            progress_callback: Function to call with progress messages
            cancellation_token: Token to check for cancellation requests
        
        Returns:
            Path to generated subtitle file
        """
        audio_path = None
        
        try:
            video_path = Path(video_path)
            
            def log(message):
                logger.info(message)
                if progress_callback:
                    progress_callback(message)
            
            # Check cancellation before starting
            if cancellation_token:
                cancellation_token.check_cancelled()
            
            log(f"Inizio elaborazione: {video_path.name}")
            
            # Step 0: Validate video file
            log("0/3 - Validazione file video...")
            try:
                video_info = self.video_validator.validate_video_file(video_path)
                log(f"✓ Video valido - Durata: {video_info['duration_formatted']}, "
                    f"Risoluzione: {video_info['width']}x{video_info['height']}")
                
                # Show warnings if any
                for warning in video_info.get('warnings', []):
                    log(f"⚠️ {warning}")
                    
            except VideoValidationError as e:
                log(f"✗ Validazione fallita: {str(e)}")
                raise
            
            # Step 1: Extract audio
            log("1/3 - Estrazione audio dal video...")
            if cancellation_token:
                cancellation_token.check_cancelled()
            
            audio_path = self.audio_extractor.extract_audio(video_path)
            log(f"✓ Audio estratto: {audio_path.name}")
            
            # Step 2: Generate subtitles with Whisper
            log(f"2/3 - Generazione sottotitoli (modello: {model_name})...")
            log("⏳ Questo potrebbe richiedere alcuni minuti...")
            if cancellation_token:
                cancellation_token.check_cancelled()
            
            whisper = self._get_whisper_engine(model_name)
            segments = whisper.generate_subtitles(
                audio_path=audio_path,
                language=language
            )
            log(f"✓ Generati {len(segments)} segmenti di sottotitoli")
            
            # Step 3: Export subtitles
            log(f"3/3 - Esportazione sottotitoli in formato {output_format.upper()}...")
            if cancellation_token:
                cancellation_token.check_cancelled()
            
            output_filename = f"{video_path.stem}.{output_format}"
            output_path = config.OUTPUT_DIR / output_filename
            
            self.subtitle_formatter.export(
                segments=segments,
                output_path=output_path,
                format_type=output_format
            )
            log(f"✓ Sottotitoli salvati: {output_path}")
            
            # Cleanup
            log("Pulizia file temporanei...")
            if audio_path:
                self.audio_extractor.cleanup_temp_audio(audio_path)
            
            log("=== COMPLETATO ===")
            return output_path
            
        except OperationCancelledException:
            logger.info("Operation cancelled by user")
            if progress_callback:
                progress_callback("⚠️ Operazione annullata dall'utente")
            
            # Cleanup on cancellation
            if audio_path:
                try:
                    self.audio_extractor.cleanup_temp_audio(audio_path)
                except:
                    pass
            
            raise
            
        except Exception as e:
            logger.error(f"Error generating subtitles: {str(e)}")
            if progress_callback:
                progress_callback(f"ERRORE: {str(e)}")
            
            # Cleanup on error
            if audio_path:
                try:
                    self.audio_extractor.cleanup_temp_audio(audio_path)
                except:
                    pass
            
            raise
    
    def download_subtitles(self, video_path, language="it", progress_callback=None, cancellation_token=None):
        """
        Download subtitles from OpenSubtitles
        
        Args:
            video_path: Path to video file
            language: Language code
            progress_callback: Function to call with progress messages
            cancellation_token: Token to check for cancellation requests
        
        Returns:
            Path to downloaded subtitle file or None
        """
        try:
            video_path = Path(video_path)
            
            def log(message):
                logger.info(message)
                if progress_callback:
                    progress_callback(message)
            
            # Check cancellation before starting
            if cancellation_token:
                cancellation_token.check_cancelled()
            
            log(f"Ricerca sottotitoli per: {video_path.name}")
            log(f"Lingua: {language}")
            
            # Quick validation (just check file exists and format)
            try:
                self.video_validator.quick_check(video_path)
                log("✓ File video valido")
            except VideoValidationError as e:
                log(f"✗ Validazione fallita: {str(e)}")
                raise
            
            # Calculate video hash
            log("Calcolo hash del video...")
            if cancellation_token:
                cancellation_token.check_cancelled()
            
            video_hash = self.opensubtitles.calculate_video_hash(video_path)
            
            if video_hash:
                log(f"[OK] Hash calcolato: {video_hash}")
            else:
                log("[!] Impossibile calcolare hash, ricerca per nome file")
            
            # Extract search query from filename
            query = video_path.stem
            
            # Search for subtitles with multiple strategies
            log("Ricerca su OpenSubtitles.com...")
            log(f"Termine di ricerca: '{query}'")
            if cancellation_token:
                cancellation_token.check_cancelled()
            results = self.opensubtitles.search_subtitles(
                video_path=video_path,
                query=query,
                language=language,
                video_hash=video_hash
            )
            
            if not results:
                log("[X] Nessun sottotitolo trovato")
                log("")
                log("=== NOTA IMPORTANTE ===")
                log("OpenSubtitles.com richiede una API KEY per il download automatico.")
                log("")
                log("Come ottenere una API KEY (GRATUITA):")
                log("1. Vai su https://www.opensubtitles.com")
                log("2. Crea un account gratuito")
                log("3. Vai su: Profilo > API")
                log("4. Genera una API Key")
                log("5. Apri il file 'config.py'")
                log("6. Cerca 'OPENSUBTITLES_API_KEY'")
                log("7. Inserisci la tua API key")
                log("")
                log("Suggerimento: cerca manualmente su opensubtitles.com")
                return None
            
            log(f"[OK] Trovati {len(results)} risultati")
            
            # Get best match
            best_match = results[0]
            attrs = best_match.get('attributes', {})
            file_name = attrs.get('release', 'Unknown')
            log(f"Migliore corrispondenza: {file_name}")
            
            # Determine output path
            output_dir = config.OUTPUT_DIR
            output_path = output_dir / f"{video_path.stem}.srt"
            
            # Try to download subtitle
            log("Tentativo di download...")
            if cancellation_token:
                cancellation_token.check_cancelled()
            
            # Check if we have API key
            if self.opensubtitles.api_key:
                try:
                    files = attrs.get('files', [])
                    if files and files[0].get('file_id'):
                        file_id = files[0]['file_id']
                        result = self.opensubtitles.download_subtitle(file_id, output_path)
                        log(f"[OK] Sottotitolo scaricato: {result}")
                        return result
                except Exception as e:
                    log(f"[!] Errore download con API: {str(e)}")
            
            # No API key or download failed - provide manual instructions
            log("")
            log("=== DOWNLOAD MANUALE RICHIESTO ===")
            log("")
            log("Per scaricare automaticamente serve una API Key.")
            log("Puoi scaricare manualmente in 30 secondi:")
            log("")
            
            # Get subtitle URL
            subtitle_id = attrs.get('subtitle_id') or attrs.get('id')
            if subtitle_id:
                manual_url = f"https://www.opensubtitles.com/en/subtitleserve/sub/{subtitle_id}"
                log(f"LINK DIRETTO: {manual_url}")
                log("")
                log("Oppure:")
            
            log(f"1. Vai su: https://www.opensubtitles.com")
            log(f"2. Cerca: '{video_path.stem}'")
            log(f"3. Trova sottotitolo: {file_name}")
            log(f"4. Click Download")
            log(f"5. Salva in: {output_dir}")
            log("")
            
            # Save info to file
            info_path = output_dir / f"{video_path.stem}_download_info.txt"
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write(f"SOTTOTITOLI PER: {video_path.name}\n\n")
                f.write(f"Trovato: {file_name}\n")
                f.write(f"Lingua: {attrs.get('language', 'N/A')}\n")
                f.write(f"Downloads: {attrs.get('download_count', 'N/A')}\n\n")
                if subtitle_id:
                    f.write(f"LINK DIRETTO:\n{manual_url}\n\n")
                    f.write(f"Copia e incolla questo link nel browser per scaricare!\n\n")
                f.write(f"RICERCA MANUALE:\n")
                f.write(f"1. Vai su: https://www.opensubtitles.com\n")
                f.write(f"2. Cerca: '{video_path.stem}'\n")
                f.write(f"3. Scarica: {file_name}\n\n")
                f.write(f"ALTERNATIVA - USA AUTO-GENERAZIONE:\n")
                f.write(f"1. Riapri l'applicazione\n")
                f.write(f"2. Seleziona 'Auto-Genera' (non 'Scarica')\n")
                f.write(f"3. Nessuna API key necessaria\n")
                f.write(f"4. Sottotitoli perfetti in 5-10 minuti!\n")
            
            log(f"[OK] Istruzioni salvate in: {info_path}")
            log("")
            log("=== COME CONFIGURARE OPENSUBTITLES ===")
            log("1. Registrati gratis su: https://www.opensubtitles.com")
            log("2. Vai su: Profilo > API")
            log("3. Genera una API Key")
            log("4. Apri il file: config.py")
            log("5. Trova la riga: OPENSUBTITLES_API_KEY = None")
            log("6. Modificala in: OPENSUBTITLES_API_KEY = 'tua_api_key_qui'")
            log("7. Salva e riavvia l'applicazione")
            log("")
            log("Dopo la configurazione potrai scaricare sottotitoli automaticamente!")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading subtitles: {str(e)}")
            if progress_callback:
                progress_callback(f"ERRORE: {str(e)}")
            raise
    
    def validate_video_file(self, video_path):
        """Check if video file is valid and supported"""
        video_path = Path(video_path)
        
        if not video_path.exists():
            return False, "File non trovato"
        
        if video_path.suffix.lower() not in config.SUPPORTED_VIDEO_FORMATS:
            return False, f"Formato non supportato: {video_path.suffix}"
        
        return True, "OK"
    
    def get_output_directory(self):
        """Get the output directory path"""
        return config.OUTPUT_DIR
    
    def cleanup(self):
        """Cleanup temporary files"""
        logger.info("Cleaning up temporary files...")
        self.audio_extractor.cleanup_all()
