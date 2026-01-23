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
            logger.info("This may take 1-2 minutes for accurate analysis...")
            
            # Load base model for better accuracy (tiny was too imprecise)
            model = whisper.load_model("base")
            
            # Transcribe with timestamps and word-level timing
            result = model.transcribe(
                str(audio_path),
                task="transcribe",
                language=None,
                verbose=False,
                word_timestamps=False  # Segment-level is more stable
            )
            
            # Extract timestamps with filtering
            speech_times = []
            for segment in result.get('segments', []):
                # Filter out very short segments (likely noise)
                duration = segment['end'] - segment['start']
                if duration > 0.3:  # At least 0.3 seconds
                    speech_times.append({
                        'start': segment['start'],
                        'end': segment['end'],
                        'text': segment['text'].strip()
                    })
            
            logger.info(f"Detected {len(speech_times)} speech segments (filtered)")
            
            # Log first few for debugging
            if speech_times:
                logger.info(f"First speech: {speech_times[0]['start']:.2f}s - '{speech_times[0]['text'][:30]}'")
                if len(speech_times) > 1:
                    logger.info(f"Second speech: {speech_times[1]['start']:.2f}s - '{speech_times[1]['text'][:30]}'")
            
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
    
    def _find_best_offset(self, subtitle_times, speech_times, max_offset=30):
        """
        Find best offset by comparing subtitle and speech patterns
        Uses multiple methods for maximum accuracy
        
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
            
            logger.info(f"Analyzing {len(subtitle_times)} subtitle segments vs {len(speech_times)} speech segments")
            
            # Use more segments for better accuracy
            sample_size = min(20, len(subtitle_times), len(speech_times))
            
            sub_starts = np.array([s['start'] for s in subtitle_times[:sample_size]])
            speech_starts = np.array([s['start'] for s in speech_times[:sample_size]])
            
            # METHOD 1: Direct alignment of first segments
            first_sub = subtitle_times[0]['start']
            first_speech = speech_times[0]['start']
            # If subtitle starts before speech, we need to ADD time (delay subtitles)
            # If subtitle starts after speech, we need to SUBTRACT time (advance subtitles)
            offset_method1 = first_speech - first_sub
            
            logger.info(f"Method 1 (first segment): subtitle at {first_sub:.2f}s, speech at {first_speech:.2f}s")
            logger.info(f"Method 1 offset: {offset_method1:.2f}s ({'+' if offset_method1 > 0 else ''}{offset_method1:.2f}s)")
            
            # Explanation in log
            if offset_method1 > 0:
                logger.info(f"  → Subtitles start BEFORE speech, need to DELAY by {offset_method1:.2f}s")
            elif offset_method1 < 0:
                logger.info(f"  → Subtitles start AFTER speech, need to ADVANCE by {abs(offset_method1):.2f}s")
            else:
                logger.info(f"  → Perfect alignment!")
            
            # METHOD 2: Cross-correlation with multiple samples
            best_offset = offset_method1
            best_score = float('inf')
            
            # Expand search range if first method suggests large offset
            search_range = max(max_offset, abs(offset_method1) + 10)
            
            # Try offsets with higher resolution
            test_offsets = np.arange(-search_range, search_range, 0.05)
            
            for offset in test_offsets:
                # Calculate alignment score
                score = 0
                matched = 0
                
                for sub_start in sub_starts:
                    adjusted_sub = sub_start + offset
                    
                    # Find closest speech segment
                    if len(speech_starts) > 0:
                        distances = np.abs(speech_starts - adjusted_sub)
                        min_dist = np.min(distances)
                        
                        # Only count if within 2 seconds
                        if min_dist < 2.0:
                            score += min_dist
                            matched += 1
                
                # Penalize if too few matches
                if matched < sample_size * 0.5:
                    score += 1000
                else:
                    score = score / matched  # Average distance
                
                if score < best_score:
                    best_score = score
                    best_offset = offset
            
            logger.info(f"Method 2 (cross-correlation): offset = {best_offset:.2f}s, score = {best_score:.3f}")
            
            # METHOD 3: Gap pattern analysis
            if len(sub_starts) > 3 and len(speech_starts) > 3:
                sub_gaps = np.diff(sub_starts)
                speech_gaps = np.diff(speech_starts)
                
                # Use correlation of gaps to validate
                min_len = min(len(sub_gaps), len(speech_gaps))
                if min_len > 2:
                    # Normalize gaps for comparison
                    sub_gaps_norm = (sub_gaps[:min_len] - np.mean(sub_gaps[:min_len])) / (np.std(sub_gaps[:min_len]) + 1e-6)
                    speech_gaps_norm = (speech_gaps[:min_len] - np.mean(speech_gaps[:min_len])) / (np.std(speech_gaps[:min_len]) + 1e-6)
                    
                    # Calculate correlation
                    correlation = np.corrcoef(sub_gaps_norm, speech_gaps_norm)[0, 1]
                    
                    logger.info(f"Method 3 (gap correlation): {correlation:.3f}")
                    
                    # If correlation is good and method 2 score is good, trust it
                    if correlation > 0.5 and best_score < 0.5:
                        logger.info(f"High confidence in offset: {best_offset:.2f}s")
                    elif correlation < 0.3:
                        logger.warning("Low correlation - subtitles might not match audio")
            
            # METHOD 4: Validate with middle and end segments
            if len(subtitle_times) > 10 and len(speech_times) > 10:
                mid_sub = subtitle_times[len(subtitle_times)//2]['start']
                mid_speech = speech_times[len(speech_times)//2]['start']
                mid_offset = mid_speech - mid_sub
                
                logger.info(f"Method 4 (middle segment): offset = {mid_offset:.2f}s")
                
                # If middle offset is very different, average them
                if abs(mid_offset - best_offset) > 5:
                    logger.warning(f"Large discrepancy between start and middle offset")
                    # Use weighted average (more weight to cross-correlation)
                    best_offset = (best_offset * 0.7 + mid_offset * 0.3)
            
            # Round to nearest 0.05 second for precision
            best_offset = round(best_offset * 20) / 20
            
            logger.info(f"=" * 60)
            logger.info(f"FINAL OFFSET: {best_offset:+.2f}s")
            
            if best_offset > 0:
                logger.info(f"ACTION: DELAY subtitles by {best_offset:.2f} seconds")
            elif best_offset < 0:
                logger.info(f"ACTION: ADVANCE subtitles by {abs(best_offset):.2f} seconds")
            else:
                logger.info(f"ACTION: Subtitles already in sync!")
            
            logger.info(f"=" * 60)
            
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
