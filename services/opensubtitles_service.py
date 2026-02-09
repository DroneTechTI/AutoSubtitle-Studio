"""
OpenSubtitles API integration for downloading existing subtitles
"""
import logging
import requests
from pathlib import Path
import hashlib
import struct
import time
from typing import Optional, Dict, Any

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
    
    def _retry_request(self, method: str, url: str, max_retries: int = 3, 
                      backoff_factor: float = 2.0, **kwargs) -> Optional[requests.Response]:
        """
        Execute HTTP request with automatic retry and exponential backoff
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff
            **kwargs: Additional arguments for requests
        
        Returns:
            Response object or None if all retries failed
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                # Execute request
                if method.upper() == 'GET':
                    response = self.session.get(url, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Check if we should retry based on status code
                if response.status_code in [200, 401, 406]:
                    # Success or non-retryable errors
                    return response
                elif response.status_code == 429:
                    # Rate limiting - use longer backoff
                    logger.warning(f"Rate limited by OpenSubtitles (429). Waiting before retry...")
                    wait_time = backoff_factor ** (attempt + 2)  # Longer wait for rate limits
                elif response.status_code >= 500:
                    # Server error - retry
                    logger.warning(f"Server error {response.status_code}. Attempt {attempt + 1}/{max_retries}")
                    wait_time = backoff_factor ** attempt
                else:
                    # Other client errors - don't retry
                    return response
                
                # Wait before retry
                if attempt < max_retries - 1:
                    logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"Request timeout. Attempt {attempt + 1}/{max_retries}")
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error. Attempt {attempt + 1}/{max_retries}")
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                last_exception = e
                break
        
        # All retries failed
        if last_exception:
            logger.error(f"All {max_retries} retry attempts failed. Last error: {str(last_exception)}")
        
        return None
    
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
            # Calculate hash if video path provided
            if video_path and not video_hash:
                video_path = Path(video_path)
                video_hash = self.calculate_video_hash(video_path)
                file_size = video_path.stat().st_size
                
                # Extract query from filename if not provided
                if not query:
                    query = self._extract_query_from_filename(video_path.stem)
            
            # Try multiple search strategies
            all_results = []
            
            # Strategy 1: Search by hash (most accurate)
            if video_hash and file_size:
                search_params = {
                    'languages': language,
                    'moviehash': video_hash,
                    'moviebytesize': str(file_size)
                }
                logger.info(f"Search #1: By hash - {search_params}")
                results = self._do_search(search_params)
                if results:
                    logger.info(f"Found {len(results)} results by hash")
                    return results
                all_results.extend(results)
            
            # Strategy 2: Search by query (movie/series name)
            if query:
                search_params = {
                    'languages': language,
                    'query': query
                }
                logger.info(f"Search #2: By query - {search_params}")
                results = self._do_search(search_params)
                if results:
                    logger.info(f"Found {len(results)} results by query")
                    return results
                all_results.extend(results)
            
            # Strategy 3: Search with simplified query (remove episode info)
            if query and any(x in query.lower() for x in ['s0', 's1', 's2', 'e0', 'e1', 'e2']):
                simplified = self._simplify_series_name(query)
                search_params = {
                    'languages': language,
                    'query': simplified
                }
                logger.info(f"Search #3: By simplified query - {search_params}")
                results = self._do_search(search_params)
                if results:
                    logger.info(f"Found {len(results)} results by simplified query")
                    return results
                all_results.extend(results)
            
            logger.info(f"Total results found: {len(all_results)}")
            return all_results
                
        except Exception as e:
            logger.error(f"Error searching subtitles: {str(e)}")
            return []
    
    def _do_search(self, search_params):
        """Execute search request with automatic retry"""
        try:
            response = self._retry_request(
                'GET',
                f"{self.api_url}/subtitles",
                params=search_params,
                timeout=30
            )
            
            if response is None:
                logger.error("Search failed after all retry attempts")
                return []
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            elif response.status_code == 429:
                logger.error("Rate limit exceeded. Please try again later.")
                return []
            elif response.status_code >= 500:
                logger.error(f"OpenSubtitles server error: {response.status_code}")
                return []
            else:
                logger.debug(f"Search failed with status: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Search request error: {str(e)}")
            return []
    
    def _extract_query_from_filename(self, filename):
        """Extract search query from video filename"""
        import re
        
        # Remove common patterns
        query = filename
        
        # Remove year in parentheses or brackets
        query = re.sub(r'[\(\[]?\d{4}[\)\]]?', '', query)
        
        # Remove quality markers
        query = re.sub(r'\b(1080p|720p|480p|2160p|4K|HDR|BluRay|WEB-?DL|WEBRip|DVDRip|BRRip)\b', '', query, flags=re.IGNORECASE)
        
        # Remove codec info
        query = re.sub(r'\b(x264|x265|h264|h265|HEVC|AAC|AC3|DTS|MP3)\b', '', query, flags=re.IGNORECASE)
        
        # Remove group tags
        query = re.sub(r'-[A-Z0-9]+$', '', query)
        
        # Replace dots and underscores with spaces
        query = query.replace('.', ' ').replace('_', ' ')
        
        # Clean up multiple spaces
        query = ' '.join(query.split())
        
        return query.strip()
    
    def _simplify_series_name(self, query):
        """Remove episode info from series name"""
        import re
        
        # Remove SxxExx pattern
        simplified = re.sub(r'\bS\d{1,2}E\d{1,2}\b', '', query, flags=re.IGNORECASE)
        
        # Remove season/episode separately
        simplified = re.sub(r'\bS(eason)?\s?\d{1,2}\b', '', simplified, flags=re.IGNORECASE)
        simplified = re.sub(r'\bE(pisode)?\s?\d{1,2}\b', '', simplified, flags=re.IGNORECASE)
        
        # Clean up
        simplified = ' '.join(simplified.split())
        
        return simplified.strip()
    
    def download_subtitle(self, file_id, output_path):
        """
        Download subtitle file with automatic retry
        
        Args:
            file_id: OpenSubtitles file ID
            output_path: Where to save the subtitle file
        
        Returns:
            Path to downloaded file
        """
        try:
            logger.info(f"Downloading subtitle file: {file_id}")
            
            if not self.api_key:
                raise Exception("API key required for downloads")
            
            # Get download link with API key (with retry)
            response = self._retry_request(
                'POST',
                f"{self.api_url}/download",
                json={'file_id': file_id},
                timeout=30
            )
            
            if response is None:
                raise Exception("Failed to get download link after multiple attempts. Check your internet connection.")
            
            if response.status_code == 401:
                raise Exception("Invalid API key or authentication failed")
            elif response.status_code == 406:
                raise Exception("Daily download limit reached. Try again tomorrow or upgrade your plan.")
            elif response.status_code == 429:
                raise Exception("Too many requests. Please wait a few minutes and try again.")
            elif response.status_code != 200:
                error_msg = f"Failed to get download link: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('message', 'Unknown error')}"
                except:
                    pass
                raise Exception(error_msg)
            
            download_data = response.json()
            download_link = download_data.get('link')
            
            if not download_link:
                raise Exception("No download link provided in response")
            
            logger.info(f"Got download link, downloading file...")
            
            # Download the file (with retry)
            subtitle_response = self._retry_request(
                'GET',
                download_link,
                timeout=60
            )
            
            if subtitle_response is None:
                raise Exception("Failed to download subtitle file after multiple attempts")
            
            subtitle_response.raise_for_status()
            
            output_path = Path(output_path)
            
            # Decompress if it's gzipped
            content = subtitle_response.content
            if download_link.endswith('.gz') or subtitle_response.headers.get('Content-Type') == 'application/gzip':
                import gzip
                logger.info("Decompressing gzipped subtitle...")
                content = gzip.decompress(content)
            
            with open(output_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Subtitle downloaded successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading subtitle: {str(e)}")
            raise
    
    def try_direct_download(self, subtitle_info, output_path):
        """
        Try to download subtitle directly from attributes
        
        Args:
            subtitle_info: Subtitle info from search results
            output_path: Where to save the file
        
        Returns:
            Path to downloaded file or None
        """
        try:
            attrs = subtitle_info.get('attributes', {})
            
            # Try to get direct download URL
            files = attrs.get('files', [])
            if not files:
                return None
            
            file_info = files[0]
            file_id = file_info.get('file_id')
            
            if not file_id:
                return None
            
            # Try to download with API key if available
            if self.api_key:
                try:
                    return self.download_subtitle(file_id, output_path)
                except Exception as e:
                    logger.debug(f"API download failed: {str(e)}")
            
            # If no API key or API download failed, try alternative method
            # Get subtitle URL from attributes
            url = attrs.get('url')
            if url:
                logger.info(f"Trying direct download from: {url}")
                
                # Create a proper subtitle URL
                # OpenSubtitles web format
                web_url = f"https://www.opensubtitles.com/en/subtitles/{file_id}"
                
                logger.info(f"Direct download not available without API key")
                logger.info(f"You can download manually from: {web_url}")
                return None
            
            return None
            
        except Exception as e:
            logger.debug(f"Direct download error: {str(e)}")
            return None
    
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
