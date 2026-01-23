"""
Subtitle statistics and analysis
"""
import re
import logging
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)


class SubtitleStats:
    """Analyze and provide statistics about subtitle files"""
    
    def __init__(self):
        pass
    
    def analyze(self, subtitle_path):
        """
        Analyze subtitle file and return statistics
        
        Args:
            subtitle_path: Path to subtitle file
        
        Returns:
            Dictionary with statistics
        """
        try:
            subtitle_path = Path(subtitle_path)
            
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse SRT
            blocks = content.strip().split('\n\n')
            
            total_segments = 0
            total_duration = 0
            total_characters = 0
            total_words = 0
            words_list = []
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                
                try:
                    # Parse timecode
                    timecode = lines[1]
                    if '-->' not in timecode:
                        continue
                    
                    start, end = timecode.split(' --> ')
                    start_seconds = self._parse_time(start)
                    end_seconds = self._parse_time(end)
                    
                    duration = end_seconds - start_seconds
                    
                    # Parse text
                    text = '\n'.join(lines[2:])
                    words = re.findall(r'\b\w+\b', text.lower())
                    
                    total_segments += 1
                    total_duration += duration
                    total_characters += len(text)
                    total_words += len(words)
                    words_list.extend(words)
                    
                except Exception as e:
                    logger.warning(f"Error parsing block: {str(e)}")
                    continue
            
            # Calculate stats
            stats = {
                'total_segments': total_segments,
                'total_duration': total_duration,
                'total_characters': total_characters,
                'total_words': total_words,
                'avg_segment_duration': total_duration / total_segments if total_segments > 0 else 0,
                'avg_chars_per_segment': total_characters / total_segments if total_segments > 0 else 0,
                'avg_words_per_segment': total_words / total_segments if total_segments > 0 else 0,
                'reading_speed_wpm': (total_words / (total_duration / 60)) if total_duration > 0 else 0,
                'most_common_words': Counter(words_list).most_common(10) if words_list else []
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error analyzing subtitles: {str(e)}")
            return {}
    
    def _parse_time(self, timestr):
        """Parse SRT time string to seconds"""
        # Format: HH:MM:SS,mmm
        timestr = timestr.strip()
        time_part, ms_part = timestr.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        
        total_seconds = h * 3600 + m * 60 + s + ms / 1000
        return total_seconds
    
    def get_summary(self, stats):
        """Get human-readable summary of stats"""
        if not stats:
            return "Nessuna statistica disponibile"
        
        summary = []
        summary.append(f"Segmenti totali: {stats['total_segments']}")
        summary.append(f"Durata totale: {int(stats['total_duration'] // 60)}m {int(stats['total_duration'] % 60)}s")
        summary.append(f"Parole totali: {stats['total_words']}")
        summary.append(f"Caratteri totali: {stats['total_characters']}")
        summary.append(f"\nMedia per segmento:")
        summary.append(f"  • Durata: {stats['avg_segment_duration']:.1f}s")
        summary.append(f"  • Parole: {stats['avg_words_per_segment']:.1f}")
        summary.append(f"  • Caratteri: {stats['avg_chars_per_segment']:.0f}")
        summary.append(f"\nVelocità di lettura: {stats['reading_speed_wpm']:.0f} parole/minuto")
        
        if stats.get('most_common_words'):
            summary.append(f"\nParole più comuni:")
            for word, count in stats['most_common_words'][:5]:
                summary.append(f"  • {word}: {count}")
        
        return '\n'.join(summary)
