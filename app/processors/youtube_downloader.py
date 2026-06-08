import logging
import os
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import yt_dlp

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """Tải video YouTube Shorts và trích xuất âm thanh"""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Khởi tạo downloader
        
        Args:
            output_dir: Thư mục lưu video/audio. Mặc định dùng temp folder
        """
        self.output_dir = output_dir or tempfile.gettempdir()
        self.executor = ThreadPoolExecutor(max_workers=2)
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def download_video(
        self,
        video_url: str,
        video_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Tải video YouTube về máy
        
        Args:
            video_url: URL của video YouTube (https://www.youtube.com/watch?v=...)
            video_id: ID video (để naming)
        
        Returns:
            Đường dẫn tệp video được tải, hoặc None nếu lỗi
        """
        try:
            loop = asyncio.get_event_loop()
            file_path = await loop.run_in_executor(
                self.executor,
                self._download_video_sync,
                video_url,
                video_id
            )
            return file_path
        except Exception as e:
            logger.error(f"❌ Lỗi tải video: {str(e)}")
            return None
    
    def _download_video_sync(self, video_url: str, video_id: Optional[str]) -> str:
        """Hàm tải video (chạy trong executor thread)"""
        
        # Tạo tên file
        output_name = f"{video_id or 'video'}_%(ext)s"
        output_template = os.path.join(self.output_dir, output_name)
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'socket_timeout': 30,
            'retries': 3,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"📥 Đang tải: {video_url}")
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            logger.info(f"✓ Tải xong: {file_path}")
            return file_path
    
    async def extract_audio(
        self,
        video_path: str,
        audio_format: str = "mp3"
    ) -> Optional[str]:
        """
        Trích xuất âm thanh từ video
        
        Args:
            video_path: Đường dẫn tệp video
            audio_format: Định dạng audio ('mp3', 'm4a', 'wav', ...)
        
        Returns:
            Đường dẫn tệp âm thanh, hoặc None nếu lỗi
        """
        try:
            if not os.path.exists(video_path):
                logger.error(f"❌ Tệp video không tồn tại: {video_path}")
                return None
            
            loop = asyncio.get_event_loop()
            audio_path = await loop.run_in_executor(
                self.executor,
                self._extract_audio_sync,
                video_path,
                audio_format
            )
            return audio_path
        except Exception as e:
            logger.error(f"❌ Lỗi trích xuất âm thanh: {str(e)}")
            return None
    
    def _extract_audio_sync(self, video_path: str, audio_format: str) -> str:
        """Hàm trích xuất audio (chạy trong executor thread)"""
        
        # Tạo tên file audio
        base_name = Path(video_path).stem
        audio_path = os.path.join(self.output_dir, f"{base_name}.{audio_format}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self.output_dir, base_name),
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 30,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"🔊 Đang trích xuất âm thanh: {video_path}")
            # ydl.extract_info(video_path, download=True)
            # logger.info(f"✓ Trích xuất âm thanh xong: {audio_path}")
        
        # Fallback: Dùng ffmpeg trực tiếp (yêu cầu ffmpeg được cài)
        import subprocess
        cmd = [
            'ffmpeg', '-i', video_path,
            '-q:a', '0',  # Chất lượng âm thanh cao nhất
            '-map', 'a',
            '-y',  # Overwrite output file
            audio_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=300)
            logger.info(f"✓ Trích xuất âm thanh xong: {audio_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        
        return audio_path
    
    async def download_and_extract_audio(
        self,
        video_url: str,
        video_id: str,
        audio_format: str = "mp3"
    ) -> Optional[Dict[str, str]]:
        """
        Tải video và trích xuất âm thanh trong một bước
        
        Returns:
            Dict với keys: 'video_path', 'audio_path', 'video_id'
        """
        video_path = await self.download_video(video_url, video_id)
        if not video_path:
            return None
        
        audio_path = await self.extract_audio(video_path, audio_format)
        if not audio_path:
            return None
        
        return {
            "video_id": video_id,
            "video_path": video_path,
            "audio_path": audio_path
        }
    
    def cleanup_local_files(self, file_path: str):
        """Xóa tệp tạm sau khi xử lý xong"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"✓ Đã xóa: {file_path}")
        except Exception as e:
            logger.error(f"❌ Lỗi xóa tệp: {str(e)}")
    
    def shutdown(self):
        """Tắt executor"""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("✓ YouTubeDownloader đã shutdown")
