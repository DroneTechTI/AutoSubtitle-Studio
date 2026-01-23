"""
Main application controller - coordinates all components
"""
import logging
from pathlib import Path
import config
from utils.audio_extractor import AudioExtractor
from utils.subtitle_formatter import SubtitleFormatter
from engines.whisper_engine import WhisperEngine
from services.opensubtitles_service import OpenSubtitlesService

logger = logging.getLogger(__name__)


class AppController:
    """Main application controller"""
    
    def __init__(self):
        self.config = config
        
        # Initialize components
        self.audio_extractor = AudioExtractor(temp_dir=config.TEMP_DIR)
        self.subtitle_formatter = SubtitleFormatter()
        
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
        
        logger.info("AppController initialized")
    
    def _get_whisper_engine(self, model_name="base"):
        """Get or create Whisper engine with specified model"""
        if self.whisper_engine is None or self.current_whisper_model != model_name:
            logger.info(f"Loading Whisper engine with model: {model_name}")
            self.whisper_engine = WhisperEngine(model_name=model_name)
            self.current_whisper_model = model_name
        return self.whisper_engine
    
    def generate_subtitles(self, video_path, language="it", output_format="srt", 
                          model_name="base", progress_callback=None):
        """
        Generate subtitles from video file
        
        Args:
            video_path: Path to video file
            language: Language code
            output_format: Subtitle format (srt or vtt)
            model_name: Whisper model to use
            progress_callback: Function to call with progress messages
        
        Returns:
            Path to generated subtitle file
        """
        try:
            video_path = Path(video_path)
            
            def log(message):
                logger.info(message)
                if progress_callback:
                    progress_callback(message)
            
            log(f"Inizio elaborazione: {video_path.name}")
            
            # Step 1: Extract audio
            log("1/3 - Estrazione audio dal video...")
            audio_path = self.audio_extractor.extract_audio(video_path)
            log(f"✓ Audio estratto: {audio_path.name}")
            
            # Step 2: Generate subtitles with Whisper
            log(f"2/3 - Generazione sottotitoli (modello: {model_name})...")
            log("⏳ Questo potrebbe richiedere alcuni minuti...")
            
            whisper = self._get_whisper_engine(model_name)
            segments = whisper.generate_subtitles(
                audio_path=audio_path,
                language=language
            )
            log(f"✓ Generati {len(segments)} segmenti di sottotitoli")
            
            # Step 3: Export subtitles
            log(f"3/3 - Esportazione sottotitoli in formato {output_format.upper()}...")
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
            self.audio_extractor.cleanup_temp_audio(audio_path)
            
            log("=== COMPLETATO ===")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating subtitles: {str(e)}")
            if progress_callback:
                progress_callback(f"ERRORE: {str(e)}")
            raise
    
    def download_subtitles(self, video_path, language="it", progress_callback=None):
        """
        Download subtitles from OpenSubtitles
        
        Args:
            video_path: Path to video file
            language: Language code
            progress_callback: Function to call with progress messages
        
        Returns:
            Path to downloaded subtitle file or None
        """
        try:
            video_path = Path(video_path)
            
            def log(message):
                logger.info(message)
                if progress_callback:
                    progress_callback(message)
            
            log(f"Ricerca sottotitoli per: {video_path.name}")
            log(f"Lingua: {language}")
            
            # Calculate video hash
            log("Calcolo hash del video...")
            video_hash = self.opensubtitles.calculate_video_hash(video_path)
            
            if video_hash:
                log(f"[OK] Hash calcolato: {video_hash}")
            else:
                log("[!] Impossibile calcolare hash, ricerca per nome file")
            
            # Search for subtitles
            log("Ricerca su OpenSubtitles.com...")
            results = self.opensubtitles.search_subtitles(
                video_path=video_path,
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
            
            # Download
            log("Download in corso...")
            
            # Note: OpenSubtitles API requires authentication for downloads
            # This is a simplified version - users may need to provide API key
            log("⚠ NOTA: Il download da OpenSubtitles richiede un account API")
            log("Per ora, ecco le informazioni del sottotitolo trovato:")
            log(f"  - Nome: {file_name}")
            log(f"  - Lingua: {attrs.get('language', 'N/A')}")
            log(f"  - Downloads: {attrs.get('download_count', 'N/A')}")
            log("")
            log("Per scaricare manualmente:")
            log("1. Vai su https://www.opensubtitles.com")
            log("2. Cerca il tuo video")
            log(f"3. Cerca il sottotitolo: {file_name}")
            
            # For now, we'll create a placeholder
            output_path = config.OUTPUT_DIR / f"{video_path.stem}_info.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Sottotitoli trovati per: {video_path.name}\n\n")
                f.write(f"Nome: {file_name}\n")
                f.write(f"Lingua: {attrs.get('language', 'N/A')}\n")
                f.write(f"Downloads: {attrs.get('download_count', 'N/A')}\n\n")
                f.write("Per scaricare:\n")
                f.write("Visita https://www.opensubtitles.com e cerca questo sottotitolo\n")
            
            log(f"[OK] Informazioni salvate in: {output_path}")
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
