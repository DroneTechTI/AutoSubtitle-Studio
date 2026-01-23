"""
Automatic subtitle synchronization using audio analysis
"""
import logging
import numpy as np
from pathlib import Path
import subprocess
import json

logger = logging.getLogger(__name__)


class AutoSync:
    """Automatically synchronize subtitles with video audio"""
    
    def __init__(self):
        pass
    
    def detect_speech_timestamps(self, audio_path, max_duration=300):
        """
        Detect speech timestamps in audio using Whisper
        
        Args:
            audio_path: Path to audio file
            max_duration: Maximum duration to analyze (seconds)
        
        Returns:
            List of speech timestamps
        """
        try:
            import whisper
            
            logger.info("Detecting speech patterns in audio...")
            
            # Load small model for quick analysis
            model = whisper.load_model("tiny")
            
            # Transcribe with timestamps
            result = model.transcribe(
                str(audio_path),
                task="transcribe",
                language=None,
                verbose=False
            )
            
            # Extract timestamps
            speech_times = []
            for segment in result.get('segments', []):
                speech_times.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text']
                })
            
            logger.info(f"Detected {len(speech_times)} speech segments")
            return speech_times
            
        except Exception as e:
            logger.error(f"Error detecting speech: {str(e)}")
            return []
    
    def calculate_offset(self, subtitle_path, audio_path):
        """
        Calculate optimal offset between subtitles and audio
        
        Args:
            subtitle_path: Path to subtitle file
            audio_path: Path to audio file
        
        Returns:
            Optimal offset in seconds
        """
        try:
            logger.info("Calculating optimal subtitle offset...")
            
            # Parse subtitle file
            subtitle_times = self._parse_subtitle_times(subtitle_path)
            
            if not subtitle_times:
                logger.warning("No subtitle times found")
                return 0.0
            
            # Detect speech in audio
            speech_times = self.detect_speech_timestamps(audio_path)
            
            if not speech_times:
                logger.warning("No speech detected in audio")
                return 0.0
            
            # Find best offset by comparing patterns
            offset = self._find_best_offset(subtitle_times, speech_times)
            
            logger.info(f"Optimal offset calculated: {offset:.2f} seconds")
            return offset
            
        except Exception as e:
            logger.error(f"Error calculating offset: {str(e)}")
            return 0.0
    
    def auto_sync_subtitles(self, subtitle_path, video_path, output_path=None):
        """
        Automatically synchronize subtitles with video
        
        Args:
            subtitle_path: Path to subtitle file
            video_path: Path to video file
            output_path: Output path for synced subtitles
        
        Returns:
            Tuple of (output_path, offset_applied)
        """
        try:
            from utils.audio_extractor import AudioExtractor
            from utils.video_processor import VideoProcessor
            import tempfile
            
            subtitle_path = Path(subtitle_path)
            video_path = Path(video_path)
            
            if not output_path:
                output_path = subtitle_path.parent / f"{subtitle_path.stem}_synced{subtitle_path.suffix}"
            else:
                output_path = Path(output_path)
            
            logger.info("Starting automatic subtitle synchronization...")
            
            # Extract audio from video
            logger.info("Extracting audio for analysis...")
            audio_extractor = AudioExtractor(tempfile.gettempdir())
            audio_path = audio_extractor.extract_audio(video_path)
            
            try:
                # Calculate offset
                offset = self.calculate_offset(subtitle_path, audio_path)
                
                if abs(offset) < 0.1:
                    logger.info("Subtitles already in sync!")
                    # Just copy the file
                    import shutil
                    shutil.copy(subtitle_path, output_path)
                    return output_path, 0.0
                
                # Apply offset
                logger.info(f"Applying offset: {offset:.2f}s")
                processor = VideoProcessor()
                synced_path = processor.sync_subtitles(subtitle_path, offset, output_path)
                
                logger.info("Auto-sync completed successfully!")
                return synced_path, offset
                
            finally:
                # Cleanup temp audio
                audio_extractor.cleanup_temp_audio(audio_path)
                
        except Exception as e:
            logger.error(f"Error in auto-sync: {str(e)}")
            raise
    
    def _parse_subtitle_times(self, subtitle_path):
        """Parse timestamps from subtitle file"""
        try:
            import re
            
            times = []
            
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all timestamps (SRT format)
            pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})'
            matches = re.findall(pattern, content)
            
            for match in matches:
                start_h, start_m, start_s, start_ms = map(int, match[:4])
                end_h, end_m, end_s, end_ms = map(int, match[4:])
                
                start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
                end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
                
                times.append({
                    'start': start_time,
                    'end': end_time
                })
            
            return times
            
        except Exception as e:
            logger.error(f"Error parsing subtitle times: {str(e)}")
            return []
    
    def _find_best_offset(self, subtitle_times, speech_times, max_offset=10):
        """
        Find best offset by comparing subtitle and speech patterns
        
        Args:
            subtitle_times: List of subtitle timestamps
            speech_times: List of detected speech timestamps
            max_offset: Maximum offset to try (seconds)
        
        Returns:
            Best offset in seconds
        """
        try:
            if not subtitle_times or not speech_times:
                return 0.0
            
            # Sample first few segments for comparison
            sample_size = min(10, len(subtitle_times), len(speech_times))
            
            sub_starts = [s['start'] for s in subtitle_times[:sample_size]]
            speech_starts = [s['start'] for s in speech_times[:sample_size]]
            
            # Calculate gaps between segments
            sub_gaps = [sub_starts[i+1] - sub_starts[i] for i in range(len(sub_starts)-1)]
            speech_gaps = [speech_starts[i+1] - speech_starts[i] for i in range(len(speech_starts)-1)]
            
            # Try different offsets and find best match
            best_offset = 0.0
            best_score = float('inf')
            
            # Try offsets from -max_offset to +max_offset
            for offset in np.arange(-max_offset, max_offset, 0.1):
                # Calculate score for this offset
                score = 0
                
                for i, sub_start in enumerate(sub_starts[:min(5, len(sub_starts))]):
                    adjusted_sub = sub_start + offset
                    
                    # Find closest speech segment
                    if speech_starts:
                        closest_speech = min(speech_starts, key=lambda x: abs(x - adjusted_sub))
                        diff = abs(adjusted_sub - closest_speech)
                        score += diff
                
                if score < best_score:
                    best_score = score
                    best_offset = offset
            
            # Refine with gap analysis if possible
            if len(sub_gaps) > 0 and len(speech_gaps) > 0:
                # Compare gap patterns
                avg_sub_gap = np.mean(sub_gaps)
                avg_speech_gap = np.mean(speech_gaps)
                
                # If gaps are very different, might indicate different pacing
                # Adjust offset based on first segment alignment
                if abs(avg_sub_gap - avg_speech_gap) < 1.0:
                    # Gaps are similar, use first segment alignment
                    first_sub = subtitle_times[0]['start']
                    first_speech = speech_times[0]['start']
                    best_offset = first_speech - first_sub
            
            # Round to nearest 0.1 second
            best_offset = round(best_offset, 1)
            
            return best_offset
            
        except Exception as e:
            logger.error(f"Error finding best offset: {str(e)}")
            return 0.0
    
    def quick_sync_check(self, subtitle_path, video_path, sample_duration=60):
        """
        Quick check if subtitles are synchronized
        
        Args:
            subtitle_path: Path to subtitle file
            video_path: Path to video file
            sample_duration: Duration to check (seconds)
        
        Returns:
            Tuple of (is_synced, estimated_offset)
        """
        try:
            from utils.audio_extractor import AudioExtractor
            import tempfile
            
            logger.info("Quick sync check...")
            
            # Extract short audio sample
            audio_extractor = AudioExtractor(tempfile.gettempdir())
            audio_path = audio_extractor.extract_audio(video_path)
            
            try:
                # Calculate offset
                offset = self.calculate_offset(subtitle_path, audio_path)
                
                # Consider synced if offset is less than 0.5 seconds
                is_synced = abs(offset) < 0.5
                
                return is_synced, offset
                
            finally:
                audio_extractor.cleanup_temp_audio(audio_path)
                
        except Exception as e:
            logger.error(f"Error in quick sync check: {str(e)}")
            return False, 0.0
