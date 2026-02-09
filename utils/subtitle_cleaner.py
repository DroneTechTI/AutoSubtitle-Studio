"""
Subtitle cleaning utilities - remove formatting, ads, etc.
"""
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SubtitleCleaner:
    """Clean and improve subtitle files"""
    
    def __init__(self):
        # Common advertising patterns
        self.ad_patterns = [
            r'(?i)www\.[a-z0-9\-\.]+\.[a-z]{2,}',
            r'(?i)http[s]?://[^\s]+',
            r'(?i)opensubtitles',
            r'(?i)subscene',
            r'(?i)addic7ed',
            r'(?i)subtitles by',
            r'(?i)synced.*corrected by',
            r'(?i)sync.*correction',
            r'(?i)downloaded from',
            r'(?i)please rate',
            r'(?i)support us',
        ]
        
        # Hearing impaired patterns
        self.hi_patterns = [
            r'\[.*?\]',  # [door closes], [music playing]
            r'\(.*?\)',  # (sighs), (phone rings)
            r'<.*?>',    # <i>text</i>
        ]
    
    def clean_subtitle_file(self, input_path, output_path=None, remove_ads=True, 
                           remove_hi=False, remove_formatting=False):
        """
        Clean subtitle file from ads, HI, formatting
        
        Args:
            input_path: Path to input subtitle file
            output_path: Path to output file (optional)
            remove_ads: Remove advertising lines
            remove_hi: Remove hearing impaired annotations
            remove_formatting: Remove HTML/formatting tags
        
        Returns:
            Path to cleaned subtitle file
        """
        try:
            input_path = Path(input_path)
            
            if not output_path:
                output_path = input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
            else:
                output_path = Path(output_path)
            
            logger.info(f"Cleaning subtitle file: {input_path.name}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse SRT
            blocks = content.strip().split('\n\n')
            cleaned_blocks = []
            removed_count = 0
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                
                try:
                    index = lines[0]
                    timecode = lines[1]
                    text = '\n'.join(lines[2:])
                    
                    # Apply cleaning
                    original_text = text
                    
                    if remove_ads:
                        text = self._remove_ads(text)
                    
                    if remove_hi:
                        text = self._remove_hi(text)
                    
                    if remove_formatting:
                        text = self._remove_formatting(text)
                    
                    # Clean up whitespace
                    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
                    
                    # Skip if empty after cleaning
                    if not text.strip():
                        removed_count += 1
                        continue
                    
                    # Skip if it was just an ad
                    if remove_ads and text != original_text and len(text) < 10:
                        removed_count += 1
                        continue
                    
                    # Rebuild block
                    cleaned_block = f"{index}\n{timecode}\n{text}"
                    cleaned_blocks.append(cleaned_block)
                    
                except Exception as e:
                    logger.warning(f"Error parsing block: {str(e)}")
                    continue
            
            # Write cleaned file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(cleaned_blocks))
                if cleaned_blocks:
                    f.write('\n\n')
            
            logger.info(f"Subtitle cleaned: {output_path}")
            logger.info(f"Removed {removed_count} blocks")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error cleaning subtitles: {str(e)}")
            raise
    
    def _remove_ads(self, text):
        """Remove advertising from text"""
        for pattern in self.ad_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text
    
    def _remove_hi(self, text):
        """Remove hearing impaired annotations"""
        for pattern in self.hi_patterns:
            text = re.sub(pattern, '', text)
        return text
    
    def _remove_formatting(self, text):
        """Remove HTML/formatting tags"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove formatting codes
        text = re.sub(r'\{[^\}]+\}', '', text)
        return text
    
    def fix_common_errors(self, input_path, output_path=None):
        """
        Fix common subtitle errors
        
        Args:
            input_path: Path to input subtitle
            output_path: Path to output subtitle
        
        Returns:
            Path to fixed subtitle
        """
        try:
            input_path = Path(input_path)
            
            if not output_path:
                output_path = input_path.parent / f"{input_path.stem}_fixed{input_path.suffix}"
            else:
                output_path = Path(output_path)
            
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix common OCR errors
            replacements = {
                ' l ': ' I ',  # Common OCR error
                ' l\'': ' I\'',
                'l\'m': 'I\'m',
                'l\'ve': 'I\'ve',
                'l\'ll': 'I\'ll',
                ' rn ': ' m ',  # r+n looks like m
                '>>': '',  # Remove chevrons
                '♪': '',  # Remove music notes
                '♫': '',
            }
            
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            # Fix spacing
            content = re.sub(r'\s+', ' ', content)  # Multiple spaces to single
            content = re.sub(r'\n\s+\n', '\n\n', content)  # Clean line breaks
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Fixed common errors: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error fixing subtitle errors: {str(e)}")
            raise
