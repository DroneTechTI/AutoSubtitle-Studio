"""
OpenSubtitles API integration for downloading existing subtitles
"""
import logging
import requests
from pathlib import Path
import hashlib
import struct

logger = logging.getLogger(__name__)


class OpenSubtitlesService:
    """Service for searching and downloading subtitles from OpenSubtitles.com"""
    
    def __init__(self, api_url, user_agent, api_key=None):
        self.api_url = api_url
        self.user_agent = user_agent
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Content-Type': 'application/json'
        })
        if api_key:
            self.session.headers.update({'Api-Key': api_key})
    
    def calculate_video_hash(self, video_path):
        """
        Calculate OpenSubtitles hash for video file
        This helps find exact matches for subtitles
        """
        try:
            video_path = Path(video_path)
            longlongformat = 'q'  # long long
            bytesize = struct.calcsize(longlongformat)
            
            with open(video_path, "rb") as f:
                filesize = video_path.stat().st_size
                hash_value = filesize
                
                if filesize < 65536 * 2:
                    logger.warning("File too small for hash calculation")
                    return None
                
                # Read first and last 64kb
                for _ in range(65536 // bytesize):
                    buffer = f.read(bytesize)
                    (l_value,) = struct.unpack(longlongformat, buffer)
                    hash_value += l_value
                    hash_value &= 0xFFFFFFFFFFFFFFFF
                
                f.seek(max(0, filesize - 65536), 0)
                for _ in range(65536 // bytesize):
                    buffer = f.read(bytesize)
                    (l_value,) = struct.unpack(longlongformat, buffer)
                    hash_value += l_value
                    hash_value &= 0xFFFFFFFFFFFFFFFF
                
                return "%016x" % hash_value
                
        except Exception as e:
            logger.error(f"Error calculating video hash: {str(e)}")
            return None
    
    def search_subtitles(self, video_path=None, query=None, language="it", 
                        video_hash=None, file_size=None):
        """
        Search for subtitles on OpenSubtitles
        
        Args:
            video_path: Path to video file (for hash calculation)
            query: Search query (movie/series name)
            language: Language code
            video_hash: Pre-calculated video hash
            file_size: Video file size
        
        Returns:
            List of subtitle results
        """
        try:
            search_params = {
                'languages': language
            }
            
            # Calculate hash if video path provided
            if video_path and not video_hash:
                video_path = Path(video_path)
                video_hash = self.calculate_video_hash(video_path)
                file_size = video_path.stat().st_size
            
            if video_hash:
                search_params['moviehash'] = video_hash
            
            if file_size:
                search_params['moviebytesize'] = str(file_size)
            
            if query:
                search_params['query'] = query
            
            logger.info(f"Searching subtitles on OpenSubtitles: {search_params}")
            
            # Note: OpenSubtitles API v1 requires authentication
            # For now, we'll implement a basic search
            # Users may need to provide their own API key
            
            response = self.session.get(
                f"{self.api_url}/subtitles",
                params=search_params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', [])
                logger.info(f"Found {len(results)} subtitle results")
                return results
            else:
                logger.warning(f"OpenSubtitles search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching subtitles: {str(e)}")
            return []
    
    def download_subtitle(self, file_id, output_path):
        """
        Download subtitle file
        
        Args:
            file_id: OpenSubtitles file ID
            output_path: Where to save the subtitle file
        
        Returns:
            Path to downloaded file
        """
        try:
            logger.info(f"Downloading subtitle file: {file_id}")
            
            # Get download link
            response = self.session.post(
                f"{self.api_url}/download",
                json={'file_id': file_id},
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get download link: {response.status_code}")
            
            download_data = response.json()
            download_link = download_data.get('link')
            
            if not download_link:
                raise Exception("No download link provided")
            
            # Download the file
            subtitle_response = self.session.get(download_link, timeout=60)
            subtitle_response.raise_for_status()
            
            output_path = Path(output_path)
            with open(output_path, 'wb') as f:
                f.write(subtitle_response.content)
            
            logger.info(f"Subtitle downloaded: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading subtitle: {str(e)}")
            raise
    
    def search_and_download(self, video_path, language="it", output_dir=None):
        """
        Search and download best matching subtitle
        
        Args:
            video_path: Path to video file
            language: Subtitle language
            output_dir: Directory to save subtitle
        
        Returns:
            Path to downloaded subtitle or None
        """
        try:
            video_path = Path(video_path)
            
            # Extract movie name from filename
            query = video_path.stem
            
            # Search for subtitles
            results = self.search_subtitles(
                video_path=video_path,
                query=query,
                language=language
            )
            
            if not results:
                logger.warning("No subtitles found")
                return None
            
            # Get the best match (first result)
            best_match = results[0]
            file_id = best_match.get('attributes', {}).get('files', [{}])[0].get('file_id')
            
            if not file_id:
                logger.warning("No file ID found in results")
                return None
            
            # Determine output path
            if not output_dir:
                output_dir = video_path.parent
            else:
                output_dir = Path(output_dir)
            
            output_path = output_dir / f"{video_path.stem}.srt"
            
            # Download subtitle
            return self.download_subtitle(file_id, output_path)
            
        except Exception as e:
            logger.error(f"Error in search_and_download: {str(e)}")
            return None
