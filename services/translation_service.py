"""
Translation service for subtitles
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from deep_translator import GoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False
    logger.warning("deep-translator not installed. Translation features will be limited.")


class TranslationService:
    """Service for translating subtitles between languages"""
    
    def __init__(self, service='google', api_key=None):
        self.service = service
        self.api_key = api_key
        
        if service == 'google' and not DEEP_TRANSLATOR_AVAILABLE:
            logger.warning("Google Translate service requires 'deep-translator' package")
    
    def translate_text(self, text, source_lang, target_lang):
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
        
        Returns:
            Translated text
        """
        if not text.strip():
            return text
            
        try:
            if self.service == 'google':
                return self._translate_google(text, source_lang, target_lang)
            elif self.service == 'deepl':
                return self._translate_deepl(text, source_lang, target_lang)
            else:
                raise ValueError(f"Unknown translation service: {self.service}")
                
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return text  # Return original text on error
    
    def _translate_google(self, text, source_lang, target_lang):
        """Translate using Google Translate"""
        if not DEEP_TRANSLATOR_AVAILABLE:
            raise ImportError("deep-translator package not installed")
        
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        # Split by newlines to preserve subtitle structure
        lines = text.split('\n')
        translated_lines = []
        
        for line in lines:
            if line.strip():
                translated = translator.translate(line)
                translated_lines.append(translated)
            else:
                translated_lines.append('')
        
        return '\n'.join(translated_lines)
    
    def _translate_deepl(self, text, source_lang, target_lang):
        """Translate using DeepL API"""
        # This requires DeepL API key and deepl package
        logger.warning("DeepL translation not yet implemented")
        return text
    
    def translate_subtitle_file(self, input_path, output_path, source_lang, target_lang, 
                                progress_callback=None):
        """
        Translate entire subtitle file
        
        Args:
            input_path: Path to input subtitle file
            output_path: Path to output subtitle file
            source_lang: Source language code
            target_lang: Target language code
            progress_callback: Function to call with progress updates
        
        Returns:
            Path to translated subtitle file
        """
        try:
            input_path = Path(input_path)
            output_path = Path(output_path)
            
            def log(msg):
                logger.info(msg)
                if progress_callback:
                    progress_callback(msg)
            
            log(f"Inizio traduzione: {source_lang} → {target_lang}")
            
            # Read subtitle file
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse subtitles
            if input_path.suffix == '.srt':
                segments = self._parse_srt(content)
            elif input_path.suffix == '.vtt':
                segments = self._parse_vtt(content)
            else:
                raise ValueError(f"Formato non supportato: {input_path.suffix}")
            
            total = len(segments)
            log(f"Trovati {total} segmenti da tradurre")
            
            # Translate each segment
            for idx, segment in enumerate(segments):
                log(f"Traduzione segmento {idx + 1}/{total}...")
                segment['text'] = self.translate_text(
                    segment['text'],
                    source_lang,
                    target_lang
                )
            
            # Write translated file
            if output_path.suffix == '.srt':
                self._write_srt(segments, output_path)
            elif output_path.suffix == '.vtt':
                self._write_vtt(segments, output_path)
            
            log(f"✓ Traduzione completata: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error translating subtitle file: {str(e)}")
            raise
    
    def _parse_srt(self, content):
        """Parse SRT format"""
        segments = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                try:
                    index = int(lines[0])
                    timecode = lines[1]
                    start, end = timecode.split(' --> ')
                    text = '\n'.join(lines[2:])
                    
                    segments.append({
                        'index': index,
                        'start': start.strip(),
                        'end': end.strip(),
                        'text': text
                    })
                except:
                    pass
                    
        return segments
    
    def _parse_vtt(self, content):
        """Parse VTT format"""
        segments = []
        lines = content.strip().split('\n')
        
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('WEBVTT'):
                start_idx = i + 1
                break
        
        blocks = '\n'.join(lines[start_idx:]).strip().split('\n\n')
        
        for idx, block in enumerate(blocks, start=1):
            lines = block.strip().split('\n')
            if len(lines) >= 2:
                try:
                    if '-->' in lines[0]:
                        timecode = lines[0]
                        text = '\n'.join(lines[1:])
                    elif len(lines) >= 3 and '-->' in lines[1]:
                        timecode = lines[1]
                        text = '\n'.join(lines[2:])
                    else:
                        continue
                    
                    start, end = timecode.split(' --> ')
                    
                    segments.append({
                        'index': idx,
                        'start': start.strip(),
                        'end': end.strip(),
                        'text': text
                    })
                except:
                    pass
                    
        return segments
    
    def _write_srt(self, segments, output_path):
        """Write SRT format"""
        content = []
        for segment in segments:
            content.append(str(segment['index']))
            content.append(f"{segment['start']} --> {segment['end']}")
            content.append(segment['text'])
            content.append('')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    
    def _write_vtt(self, segments, output_path):
        """Write VTT format"""
        content = ['WEBVTT', '']
        for segment in segments:
            content.append(str(segment['index']))
            content.append(f"{segment['start']} --> {segment['end']}")
            content.append(segment['text'])
            content.append('')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    
    @staticmethod
    def get_supported_languages():
        """Get list of supported language codes"""
        # Common language codes
        return {
            'en': 'English',
            'it': 'Italiano', 
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'pt': 'Português',
            'ru': 'Русский',
            'ja': '日本語',
            'zh-CN': '中文',
            'ar': 'العربية',
            'hi': 'हिन्दी',
            'ko': '한국어',
            'nl': 'Nederlands',
            'pl': 'Polski',
            'tr': 'Türkçe'
        }
