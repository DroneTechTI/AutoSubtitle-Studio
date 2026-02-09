"""
Audio preprocessing utilities for improved sync accuracy
"""
import logging
import subprocess
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """Preprocess audio for better synchronization accuracy"""
    
    def __init__(self):
        pass
    
    def preprocess_for_sync(self, audio_path, output_path=None):
        """
        Preprocess audio for better sync detection
        
        Improvements:
        - Remove silence at beginning and end
        - Normalize audio levels
        - Remove background noise (optional)
        - Enhance speech frequencies
        
        Args:
            audio_path: Input audio file path
            output_path: Output audio file path (optional)
        
        Returns:
            Path to preprocessed audio file
        """
        try:
            audio_path = Path(audio_path)
            
            if not output_path:
                output_path = audio_path.parent / f"{audio_path.stem}_preprocessed{audio_path.suffix}"
            else:
                output_path = Path(output_path)
            
            logger.info("Preprocessing audio for better sync accuracy...")
            
            # Build FFmpeg filter chain
            filters = []
            
            # 1. Remove silence from start (detect silence threshold)
            filters.append("silenceremove=start_periods=1:start_duration=0.1:start_threshold=-50dB")
            
            # 2. Normalize audio (make volume consistent)
            filters.append("loudnorm=I=-16:LRA=11:TP=-1.5")
            
            # 3. High-pass filter to remove very low frequencies (rumble, etc.)
            filters.append("highpass=f=80")
            
            # 4. Enhance speech frequencies (300Hz - 3400Hz)
            filters.append("equalizer=f=1000:width_type=h:width=2000:g=3")
            
            # 5. Dynamic audio compression for better consistency
            filters.append("acompressor=threshold=-20dB:ratio=4:attack=5:release=50")
            
            filter_chain = ",".join(filters)
            
            # Execute FFmpeg
            cmd = [
                'ffmpeg',
                '-i', str(audio_path),
                '-af', filter_chain,
                '-ar', '16000',  # 16kHz sample rate (sufficient for speech)
                '-ac', '1',       # Mono (easier to analyze)
                '-y',             # Overwrite output
                str(output_path)
            ]
            
            logger.debug(f"Running FFmpeg with filters: {filter_chain}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg preprocessing failed: {result.stderr}")
                # Return original if preprocessing fails
                return audio_path
            
            logger.info(f"✓ Audio preprocessed successfully: {output_path.name}")
            logger.info(f"  Filters applied: silence removal, normalization, speech enhancement")
            
            return output_path
            
        except subprocess.TimeoutExpired:
            logger.error("Audio preprocessing timed out")
            return audio_path
        except Exception as e:
            logger.error(f"Error preprocessing audio: {str(e)}")
            return audio_path
    
    def remove_silence(self, audio_path, output_path=None, threshold_db=-40, min_silence_duration=0.5):
        """
        Remove silence from audio file
        
        Args:
            audio_path: Input audio file
            output_path: Output audio file (optional)
            threshold_db: Silence threshold in dB
            min_silence_duration: Minimum silence duration to remove (seconds)
        
        Returns:
            Path to processed audio
        """
        try:
            audio_path = Path(audio_path)
            
            if not output_path:
                output_path = audio_path.parent / f"{audio_path.stem}_nosilence{audio_path.suffix}"
            else:
                output_path = Path(output_path)
            
            logger.info(f"Removing silence (threshold: {threshold_db}dB)...")
            
            # FFmpeg silenceremove filter
            cmd = [
                'ffmpeg',
                '-i', str(audio_path),
                '-af', f'silenceremove=start_periods=1:start_duration={min_silence_duration}:start_threshold={threshold_db}dB:detection=peak',
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                logger.warning(f"Silence removal failed, using original audio")
                return audio_path
            
            logger.info(f"✓ Silence removed: {output_path.name}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error removing silence: {str(e)}")
            return audio_path
    
    def normalize_audio(self, audio_path, output_path=None):
        """
        Normalize audio levels for consistent volume
        
        Args:
            audio_path: Input audio file
            output_path: Output audio file (optional)
        
        Returns:
            Path to normalized audio
        """
        try:
            audio_path = Path(audio_path)
            
            if not output_path:
                output_path = audio_path.parent / f"{audio_path.stem}_normalized{audio_path.suffix}"
            else:
                output_path = Path(output_path)
            
            logger.info("Normalizing audio levels...")
            
            # Use loudnorm filter for EBU R128 normalization
            cmd = [
                'ffmpeg',
                '-i', str(audio_path),
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
                '-ar', '16000',
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                logger.warning(f"Audio normalization failed")
                return audio_path
            
            logger.info(f"✓ Audio normalized: {output_path.name}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error normalizing audio: {str(e)}")
            return audio_path
    
    def enhance_speech(self, audio_path, output_path=None):
        """
        Enhance speech frequencies in audio
        
        Args:
            audio_path: Input audio file
            output_path: Output audio file (optional)
        
        Returns:
            Path to enhanced audio
        """
        try:
            audio_path = Path(audio_path)
            
            if not output_path:
                output_path = audio_path.parent / f"{audio_path.stem}_enhanced{audio_path.suffix}"
            else:
                output_path = Path(output_path)
            
            logger.info("Enhancing speech frequencies...")
            
            # Apply filters to enhance speech (300Hz - 3400Hz range)
            filters = [
                "highpass=f=80",  # Remove very low frequencies
                "lowpass=f=8000",  # Remove very high frequencies
                "equalizer=f=1000:width_type=h:width=2000:g=3"  # Boost speech range
            ]
            
            filter_chain = ",".join(filters)
            
            cmd = [
                'ffmpeg',
                '-i', str(audio_path),
                '-af', filter_chain,
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                logger.warning(f"Speech enhancement failed")
                return audio_path
            
            logger.info(f"✓ Speech enhanced: {output_path.name}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error enhancing speech: {str(e)}")
            return audio_path
    
    def get_audio_stats(self, audio_path):
        """
        Get statistics about audio file
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dictionary with audio statistics
        """
        try:
            import ffmpeg
            
            probe = ffmpeg.probe(str(audio_path))
            audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            
            if not audio_stream:
                return {}
            
            stats = {
                'codec': audio_stream.get('codec_name', 'unknown'),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'duration': float(probe['format'].get('duration', 0)),
                'bit_rate': int(probe['format'].get('bit_rate', 0))
            }
            
            logger.debug(f"Audio stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting audio stats: {str(e)}")
            return {}
    
    def detect_silence_periods(self, audio_path, threshold_db=-40):
        """
        Detect silence periods in audio
        
        Args:
            audio_path: Path to audio file
            threshold_db: Silence threshold in dB
        
        Returns:
            List of silence periods (start, end) in seconds
        """
        try:
            logger.info("Detecting silence periods...")
            
            cmd = [
                'ffmpeg',
                '-i', str(audio_path),
                '-af', f'silencedetect=n={threshold_db}dB:d=0.5',
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            # Parse silence detection output
            silence_periods = []
            lines = result.stderr.split('\n')
            
            silence_start = None
            for line in lines:
                if 'silence_start' in line:
                    try:
                        silence_start = float(line.split('silence_start: ')[1].split()[0])
                    except:
                        pass
                elif 'silence_end' in line and silence_start is not None:
                    try:
                        silence_end = float(line.split('silence_end: ')[1].split()[0])
                        silence_periods.append((silence_start, silence_end))
                        silence_start = None
                    except:
                        pass
            
            logger.info(f"Detected {len(silence_periods)} silence periods")
            return silence_periods
            
        except Exception as e:
            logger.error(f"Error detecting silence: {str(e)}")
            return []
