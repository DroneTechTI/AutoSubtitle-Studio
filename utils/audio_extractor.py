"""
Audio extraction from video files using FFmpeg
"""
import os
import logging
from pathlib import Path
import ffmpeg
from .exceptions import AudioExtractionError

logger = logging.getLogger(__name__)


class AudioExtractor:
    """Extract audio from video files"""
    
    def __init__(self, temp_dir):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    def extract_audio(self, video_path, output_format="wav", sample_rate=16000):
        """
        Extract audio from video file
        
        Args:
            video_path: Path to the video file
            output_format: Audio format (default: wav)
            sample_rate: Sample rate in Hz (default: 16000, optimal for Whisper)
        
        Returns:
            Path to the extracted audio file
        """
        try:
            video_path = Path(video_path)
            
            if not video_path.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Create output filename
            audio_filename = f"{video_path.stem}_audio.{output_format}"
            audio_path = self.temp_dir / audio_filename
            
            logger.info(f"Extracting audio from: {video_path.name}")
            
            # Extract audio using ffmpeg
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(
                stream,
                str(audio_path),
                acodec='pcm_s16le',
                ac=1,  # mono
                ar=str(sample_rate),
                loglevel='error'
            )
            
            # Overwrite if exists
            stream = ffmpeg.overwrite_output(stream)
            
            # Run the extraction
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            logger.info(f"Audio extracted successfully: {audio_path.name}")
            return audio_path
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg error: {error_msg}")
            raise AudioExtractionError(f"Errore nell'estrazione dell'audio: {error_msg}") from e
        except AudioExtractionError:
            raise
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise AudioExtractionError(f"Errore imprevisto durante l'estrazione audio: {str(e)}") from e
    
    def cleanup_temp_audio(self, audio_path):
        """Remove temporary audio file"""
        try:
            audio_path = Path(audio_path)
            if audio_path.exists():
                audio_path.unlink()
                logger.info(f"Temporary audio file removed: {audio_path.name}")
        except Exception as e:
            logger.warning(f"Could not remove temp file {audio_path}: {str(e)}")
    
    def cleanup_all(self):
        """Remove all temporary audio files"""
        try:
            for audio_file in self.temp_dir.glob("*_audio.*"):
                audio_file.unlink()
                logger.info(f"Removed: {audio_file.name}")
        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")


def check_ffmpeg_installed():
    """Check if FFmpeg is installed and accessible"""
    try:
        ffmpeg.probe("", cmd='ffmpeg')
        return True
    except:
        try:
            # Try running ffmpeg directly
            import subprocess
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, 
                         check=True)
            return True
        except:
            return False
