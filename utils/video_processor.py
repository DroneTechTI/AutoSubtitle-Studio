"""
Video processing utilities for subtitle integration
"""
import logging
from pathlib import Path
import subprocess
import ffmpeg

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process videos with subtitle integration"""
    
    def __init__(self):
        pass
    
    def embed_subtitles_soft(self, video_path, subtitle_path, output_path=None, language='ita'):
        """
        Embed subtitles as a soft subtitle track (can be toggled on/off)
        
        Args:
            video_path: Path to video file
            subtitle_path: Path to subtitle file
            output_path: Output video path (optional)
            language: Subtitle language code
        
        Returns:
            Path to output video
        """
        try:
            video_path = Path(video_path)
            subtitle_path = Path(subtitle_path)
            
            if not output_path:
                output_path = video_path.parent / f"{video_path.stem}_with_subs{video_path.suffix}"
            else:
                output_path = Path(output_path)
            
            logger.info(f"Embedding subtitles (soft) into: {video_path.name}")
            
            # Use FFmpeg to add subtitle stream
            input_video = ffmpeg.input(str(video_path))
            input_subtitle = ffmpeg.input(str(subtitle_path))
            
            # Add subtitle as a stream with metadata
            output = ffmpeg.output(
                input_video,
                input_subtitle,
                str(output_path),
                vcodec='copy',  # Don't re-encode video
                acodec='copy',  # Don't re-encode audio
                scodec='mov_text' if output_path.suffix == '.mp4' else 'srt',
                **{'metadata:s:s:0': f'language={language}'}
            )
            
            # Run the command
            ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            logger.info(f"Subtitles embedded successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error embedding subtitles: {str(e)}")
            raise
    
    def embed_subtitles_hard(self, video_path, subtitle_path, output_path=None, 
                            font_size=24, font_color='white', position='bottom'):
        """
        Burn subtitles directly into video (permanent, always visible)
        
        Args:
            video_path: Path to video file
            subtitle_path: Path to subtitle file
            output_path: Output video path (optional)
            font_size: Subtitle font size
            font_color: Subtitle color
            position: Subtitle position (bottom, top, middle)
        
        Returns:
            Path to output video
        """
        try:
            video_path = Path(video_path)
            subtitle_path = Path(subtitle_path)
            
            if not output_path:
                output_path = video_path.parent / f"{video_path.stem}_hardcoded{video_path.suffix}"
            else:
                output_path = Path(output_path)
            
            logger.info(f"Burning subtitles into: {video_path.name}")
            logger.info("This may take several minutes...")
            
            # Convert subtitle path to use forward slashes and escape special characters
            subtitle_path_str = str(subtitle_path).replace('\\', '/').replace(':', '\\:')
            
            # Build subtitles filter
            position_y = {
                'bottom': '(h-text_h-10)',
                'top': '10',
                'middle': '(h-text_h)/2'
            }.get(position, '(h-text_h-10)')
            
            # Use FFmpeg to burn subtitles
            input_video = ffmpeg.input(str(video_path))
            
            # Apply subtitle filter
            video = input_video.video.filter(
                'subtitles',
                filename=subtitle_path_str,
                force_style=f'FontSize={font_size},PrimaryColour=&H{self._color_to_hex(font_color)}'
            )
            
            audio = input_video.audio
            
            output = ffmpeg.output(
                video,
                audio,
                str(output_path),
                vcodec='libx264',
                acodec='copy',
                preset='medium',
                crf=23
            )
            
            # Run the command
            ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            logger.info(f"Hardcoded subtitles created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error burning subtitles: {str(e)}")
            raise
    
    def extract_subtitles(self, video_path, output_path=None, track_index=0):
        """
        Extract embedded subtitles from video
        
        Args:
            video_path: Path to video file
            output_path: Output subtitle path (optional)
            track_index: Subtitle track index (default: 0)
        
        Returns:
            Path to extracted subtitle file
        """
        try:
            video_path = Path(video_path)
            
            if not output_path:
                output_path = video_path.parent / f"{video_path.stem}_extracted.srt"
            else:
                output_path = Path(output_path)
            
            logger.info(f"Extracting subtitles from: {video_path.name}")
            
            # Use FFmpeg to extract subtitle stream
            input_video = ffmpeg.input(str(video_path))
            
            output = ffmpeg.output(
                input_video[f's:{track_index}'],
                str(output_path),
                format='srt'
            )
            
            ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            logger.info(f"Subtitles extracted: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error extracting subtitles: {str(e)}")
            raise
    
    def get_video_info(self, video_path):
        """
        Get information about video file
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dictionary with video information
        """
        try:
            probe = ffmpeg.probe(str(video_path))
            
            video_info = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
            audio_info = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            subtitle_streams = [s for s in probe['streams'] if s['codec_type'] == 'subtitle']
            
            info = {
                'duration': float(probe['format'].get('duration', 0)),
                'size': int(probe['format'].get('size', 0)),
                'format': probe['format'].get('format_name', 'unknown'),
                'has_video': video_info is not None,
                'has_audio': audio_info is not None,
                'has_subtitles': len(subtitle_streams) > 0,
                'subtitle_count': len(subtitle_streams)
            }
            
            if video_info:
                info['video_codec'] = video_info.get('codec_name', 'unknown')
                info['width'] = int(video_info.get('width', 0))
                info['height'] = int(video_info.get('height', 0))
                info['fps'] = eval(video_info.get('r_frame_rate', '0/1'))
            
            if audio_info:
                info['audio_codec'] = audio_info.get('codec_name', 'unknown')
                info['sample_rate'] = int(audio_info.get('sample_rate', 0))
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return {}
    
    def _color_to_hex(self, color):
        """Convert color name to BGR hex for FFmpeg"""
        colors = {
            'white': 'FFFFFF',
            'black': '000000',
            'yellow': '00FFFF',
            'red': '0000FF',
            'green': '00FF00',
            'blue': 'FF0000'
        }
        return colors.get(color.lower(), 'FFFFFF')
    
    def sync_subtitles(self, subtitle_path, offset_seconds, output_path=None):
        """
        Adjust subtitle timing by offset
        
        Args:
            subtitle_path: Path to subtitle file
            offset_seconds: Offset in seconds (positive = delay, negative = advance)
            output_path: Output subtitle path (optional)
        
        Returns:
            Path to synced subtitle file
        """
        try:
            from datetime import timedelta
            import re
            
            subtitle_path = Path(subtitle_path)
            
            if not output_path:
                output_path = subtitle_path.parent / f"{subtitle_path.stem}_synced{subtitle_path.suffix}"
            else:
                output_path = Path(output_path)
            
            logger.info(f"Syncing subtitles with offset: {offset_seconds}s")
            
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse and adjust timestamps
            def adjust_timestamp(match):
                time_str = match.group(0)
                # Parse timestamp
                hours, minutes, seconds, milliseconds = re.match(
                    r'(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                    time_str
                ).groups()
                
                # Convert to total milliseconds
                total_ms = (
                    int(hours) * 3600000 +
                    int(minutes) * 60000 +
                    int(seconds) * 1000 +
                    int(milliseconds)
                )
                
                # Add offset
                total_ms += int(offset_seconds * 1000)
                
                # Convert back to timestamp
                if total_ms < 0:
                    total_ms = 0
                
                hours = total_ms // 3600000
                minutes = (total_ms % 3600000) // 60000
                seconds = (total_ms % 60000) // 1000
                milliseconds = total_ms % 1000
                
                return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
            
            # Replace all timestamps
            synced_content = re.sub(
                r'\d{2}:\d{2}:\d{2},\d{3}',
                adjust_timestamp,
                content
            )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(synced_content)
            
            logger.info(f"Synced subtitles saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error syncing subtitles: {str(e)}")
            raise
