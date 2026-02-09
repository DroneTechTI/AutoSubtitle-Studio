"""
Subtitle formatting utilities for SRT and VTT formats
"""
import logging
from pathlib import Path
from typing import List, Dict, Union

logger = logging.getLogger(__name__)


class SubtitleFormatter:
    """Format and export subtitles in different formats"""

    @staticmethod
    def format_timestamp_srt(seconds: float) -> str:
        """Format timestamp for SRT format (HH:MM:SS,mmm)"""
        # Convert float seconds to integer seconds and milliseconds
        total_seconds = int(seconds)
        millis = int((seconds - total_seconds) * 1000)

        # Calculate hours, minutes, seconds from total
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def format_timestamp_vtt(seconds: float) -> str:
        """Format timestamp for VTT format (HH:MM:SS.mmm)"""
        # Convert float seconds to integer seconds and milliseconds
        total_seconds = int(seconds)
        millis = int((seconds - total_seconds) * 1000)

        # Calculate hours, minutes, seconds from total
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def export_srt(self, segments: List[Dict[str, Union[float, str]]], output_path: Union[str, Path]) -> Path:
        """
        Export subtitles in SRT format
        
        Args:
            segments: List of segments with 'start', 'end', and 'text' keys
            output_path: Path to save the SRT file
        """
        try:
            output_path = Path(output_path)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, start=1):
                    start_time = self.format_timestamp_srt(segment['start'])
                    end_time = self.format_timestamp_srt(segment['end'])
                    text = segment['text'].strip()
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
            
            logger.info(f"SRT file created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating SRT file: {str(e)}")
            raise
    
    def export_vtt(self, segments: List[Dict[str, Union[float, str]]], output_path: Union[str, Path]) -> Path:
        """
        Export subtitles in VTT (WebVTT) format
        
        Args:
            segments: List of segments with 'start', 'end', and 'text' keys
            output_path: Path to save the VTT file
        """
        try:
            output_path = Path(output_path)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                
                for i, segment in enumerate(segments, start=1):
                    start_time = self.format_timestamp_vtt(segment['start'])
                    end_time = self.format_timestamp_vtt(segment['end'])
                    text = segment['text'].strip()
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
            
            logger.info(f"VTT file created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating VTT file: {str(e)}")
            raise
    
    def export(self, segments: List[Dict[str, Union[float, str]]], output_path: Union[str, Path], format_type: str = "srt") -> Path:
        """
        Export subtitles in specified format
        
        Args:
            segments: List of segments
            output_path: Output file path
            format_type: 'srt' or 'vtt'
        """
        format_type = format_type.lower()
        
        if format_type == "srt":
            return self.export_srt(segments, output_path)
        elif format_type == "vtt":
            return self.export_vtt(segments, output_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
