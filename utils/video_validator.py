"""
Video validation utilities to check video files before processing
"""
import logging
from pathlib import Path
import subprocess
import ffmpeg

logger = logging.getLogger(__name__)


class VideoValidationError(Exception):
    """Exception raised when video validation fails"""
    pass


class VideoValidator:
    """Validate video files before processing"""
    
    def __init__(self):
        pass
    
    def validate_video_file(self, video_path):
        """
        Comprehensive video file validation
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dict with validation results and video info
        
        Raises:
            VideoValidationError: If video is invalid
        """
        video_path = Path(video_path)
        
        # Check 1: File exists
        if not video_path.exists():
            raise VideoValidationError(f"File non trovato: {video_path}")
        
        # Check 2: File is not empty
        file_size = video_path.stat().st_size
        if file_size == 0:
            raise VideoValidationError("Il file video è vuoto (0 bytes)")
        
        # Check 3: File is not too small (likely corrupted)
        if file_size < 1024:  # Less than 1KB
            raise VideoValidationError("Il file video è troppo piccolo, probabilmente corrotto")
        
        # Check 4: File extension is supported
        from config import SUPPORTED_VIDEO_FORMATS
        if video_path.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
            raise VideoValidationError(
                f"Formato video non supportato: {video_path.suffix}\n"
                f"Formati supportati: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
            )
        
        # Check 5: File is readable
        try:
            with open(video_path, 'rb') as f:
                f.read(1024)  # Try to read first KB
        except PermissionError:
            raise VideoValidationError("Impossibile leggere il file: permessi insufficienti")
        except Exception as e:
            raise VideoValidationError(f"Impossibile leggere il file: {str(e)}")
        
        # Check 6: Probe video with FFmpeg
        try:
            probe = ffmpeg.probe(str(video_path))
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
            if 'Invalid data found' in error_msg:
                raise VideoValidationError("File video corrotto o non valido")
            elif 'No such file' in error_msg:
                raise VideoValidationError("File non trovato")
            else:
                raise VideoValidationError(f"Impossibile analizzare il video: {error_msg[:200]}")
        except Exception as e:
            raise VideoValidationError(f"Errore durante l'analisi del video: {str(e)}")
        
        # Check 7: Video has video stream
        video_streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'video']
        if not video_streams:
            raise VideoValidationError("Il file non contiene un flusso video valido")
        
        # Check 8: Video has audio stream (required for subtitle generation)
        audio_streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'audio']
        if not audio_streams:
            raise VideoValidationError(
                "Il file non contiene traccia audio.\n"
                "L'audio è necessario per generare i sottotitoli automaticamente."
            )
        
        # Check 9: Duration is valid
        try:
            duration = float(probe.get('format', {}).get('duration', 0))
            if duration <= 0:
                raise VideoValidationError("Durata del video non valida o non rilevabile")
            if duration < 1:
                raise VideoValidationError("Il video è troppo corto (meno di 1 secondo)")
        except (ValueError, TypeError):
            raise VideoValidationError("Impossibile determinare la durata del video")
        
        # Check 10: Codec is supported
        video_codec = video_streams[0].get('codec_name', 'unknown')
        audio_codec = audio_streams[0].get('codec_name', 'unknown')
        
        # Warn about uncommon codecs (but don't fail)
        uncommon_video_codecs = ['rv40', 'vp6', 'msmpeg4v3', 'wmv1', 'wmv2']
        uncommon_audio_codecs = ['cook', 'sipr', 'truespeech']
        
        warnings = []
        if video_codec in uncommon_video_codecs:
            warnings.append(f"Codec video non comune: {video_codec}. Potrebbero verificarsi problemi.")
        if audio_codec in uncommon_audio_codecs:
            warnings.append(f"Codec audio non comune: {audio_codec}. Potrebbero verificarsi problemi.")
        
        # Gather video information
        video_info = {
            'valid': True,
            'path': str(video_path),
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'duration': duration,
            'duration_formatted': self._format_duration(duration),
            'video_codec': video_codec,
            'audio_codec': audio_codec,
            'width': video_streams[0].get('width', 0),
            'height': video_streams[0].get('height', 0),
            'fps': self._get_fps(video_streams[0]),
            'audio_sample_rate': audio_streams[0].get('sample_rate', 0),
            'audio_channels': audio_streams[0].get('channels', 0),
            'has_subtitles': any(s.get('codec_type') == 'subtitle' for s in probe.get('streams', [])),
            'warnings': warnings
        }
        
        logger.info(f"Video validation successful: {video_path.name}")
        logger.info(f"  Duration: {video_info['duration_formatted']}")
        logger.info(f"  Resolution: {video_info['width']}x{video_info['height']}")
        logger.info(f"  Video codec: {video_codec}")
        logger.info(f"  Audio codec: {audio_codec}")
        
        if warnings:
            for warning in warnings:
                logger.warning(f"  ⚠️ {warning}")
        
        return video_info
    
    def _format_duration(self, seconds):
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _get_fps(self, video_stream):
        """Extract FPS from video stream"""
        try:
            fps_str = video_stream.get('r_frame_rate', '0/1')
            num, den = map(int, fps_str.split('/'))
            if den > 0:
                return round(num / den, 2)
        except:
            pass
        return 0.0
    
    def quick_check(self, video_path):
        """
        Quick validation check (less thorough, faster)
        
        Args:
            video_path: Path to video file
        
        Returns:
            True if basic checks pass
        
        Raises:
            VideoValidationError: If basic validation fails
        """
        video_path = Path(video_path)
        
        # Basic checks only
        if not video_path.exists():
            raise VideoValidationError(f"File non trovato: {video_path}")
        
        file_size = video_path.stat().st_size
        if file_size == 0:
            raise VideoValidationError("Il file video è vuoto")
        
        from config import SUPPORTED_VIDEO_FORMATS
        if video_path.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
            raise VideoValidationError(
                f"Formato video non supportato: {video_path.suffix}"
            )
        
        return True
