import httpx
import re
from typing import List, Dict, Any
from app.scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

class ThreadsScraper(BaseScraper):
    async def fetch_viral_contents(self, username: str) -> List[Dict[str, Any]]:
        url = f"https://www.threads.net/@{username}"
        results = []
        
        # Bắt buộc phải fake User-Agent sạch để tránh Meta chặn lỗi 401
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    logger.error(f"Lỗi truy cập Threads profile @{username}: {response.status_code}")
                    return results
                
                html_content = response.text
                
                # Quét tất cả các pattern URL bài viết /post/ hoặc /@username/post/ có trong HTML
                post_paths = re.findall(r'\/post\/([A-Za-z0-9_-]+)', html_content)
                
                # Lọc trùng cục bộ bằng set và lấy tối đa 20 ID bài đăng mới nhất
                unique_posts = list(set(post_paths))[:20]
                
                for path in unique_posts:
                    results.append({
                        "external_id": path,
                        "content_type": "post",
                        "raw_json": {
                            "url": f"https://www.threads.net/post/{path}",
                            "username": username,
                            "scraped_from_profile": f"https://www.threads.net/@{username}"
                        }
                    })
            except Exception as e:
                logger.error(f"Lỗi xử lý cào Threads @{username}: {str(e)}")
                
        return results