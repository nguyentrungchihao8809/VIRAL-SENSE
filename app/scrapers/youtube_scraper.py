# import httpx
# import re
# from typing import List, Dict, Any
# from app.scrapers.base_scraper import BaseScraper
# import logging

# logger = logging.getLogger(__name__)

# YOUTUBE_API_KEY = "AIzaSyAzSt1kuN2X1IY_coKaSl7JVE8G4exUhqU" 

# class YouTubeScraper(BaseScraper):
#     def _safe_int(self, value: Any) -> int:
#         if value is None:
#             return 0
#         try:
#             return int(value)
#         except (ValueError, TypeError):
#             return 0

#     def _parse_duration_to_seconds(self, duration_str: str) -> int:
#         """Parse hoàn hảo mọi định dạng ISO 8601 từ YouTube: PT45S, PT1M2S, PT1H2M3S..."""
#         if not duration_str:
#             return 0
        
#         # Biểu thức chính quy bắt chính xác Giờ, Phút, Giây
#         pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
#         match = pattern.match(duration_str)
#         if not match:
#             return 0
            
#         hours = int(match.group(1)) if match.group(1) else 0
#         minutes = int(match.group(2)) if match.group(2) else 0
#         seconds = int(match.group(3)) if match.group(3) else 0
        
#         return hours * 3600 + minutes * 60 + seconds

#     async def fetch_viral_contents(self, channel_id: str) -> List[Dict[str, Any]]:
#         results = []
        
#         if not YOUTUBE_API_KEY or YOUTUBE_API_KEY.startswith("YOUR_"):
#             logger.error("YOUTUBE_API_KEY chưa được cấu hình hợp lệ!")
#             return results

#         # 1. Gọi Endpoint Search ổn định nhất (Bỏ bớt tham số videoDuration gây lỗi index của Google)
#         search_url = "https://www.googleapis.com/youtube/v3/search"
#         search_params = {
#             "key": YOUTUBE_API_KEY,
#             "channelId": channel_id,
#             "part": "snippet",
#             "order": "date",  
#             "maxResults": 20,
#             "type": "video"
#         }
        
#         async with httpx.AsyncClient(timeout=15.0) as client:
#             try:
#                 search_response = await client.get(search_url, params=search_params)
#                 if search_response.status_code != 200:
#                     logger.error(f"Lỗi gọi API Search YouTube: {search_response.status_code} - {search_response.text}")
#                     return results
                
#                 search_data = search_response.json()
#                 items = search_data.get("items", [])
                
#                 if not items:
#                     logger.warning(f"Không tìm thấy bất kỳ video nào cho Channel ID: {channel_id}")
#                     return results
                
#                 video_ids = [item["id"]["videoId"] for item in items]
                
#                 # 2. Gọi Endpoint Videos để lấy thông tin chi tiết
#                 videos_url = "https://www.googleapis.com/youtube/v3/videos"
#                 videos_params = {
#                     "key": YOUTUBE_API_KEY,
#                     "id": ",".join(video_ids),
#                     "part": "snippet,statistics,contentDetails"
#                 }
                
#                 videos_response = await client.get(videos_url, params=videos_params)
#                 if videos_response.status_code != 200:
#                     logger.error(f"Lỗi gọi API Video Detail YouTube: {videos_response.status_code}")
#                     return results
                    
#                 videos_data = videos_response.json()
                
#                 for video_item in videos_data.get("items", []):
#                     v_id = video_item["id"]
#                     snippet = video_item.get("snippet", {})
#                     stats = video_item.get("statistics", {})
#                     duration_raw = video_item.get("contentDetails", {}).get("duration", "")
                    
#                     duration_seconds = self._parse_duration_to_seconds(duration_raw)
                    
#                     # Ghi log chẩn đoán nội bộ để theo dõi thời lượng thực tế đổ về
#                     logger.info(f"[DIAGNOSTIC] Video {v_id} - Duration Raw: {duration_raw} -> {duration_seconds}s")
                    
#                     # Tiêu chuẩn lọc Shorts: thời lượng dưới hoặc bằng 60 giây
#                     if duration_seconds <= 0 or duration_seconds > 60:
#                         continue
                        
#                     video_url = f"https://www.youtube.com/shorts/{v_id}"
                    
#                     results.append({
#                         "external_id": v_id,
#                         "content_type": "video",
#                         "raw_json": {
#                             "title": snippet.get("title"),
#                             "url": video_url,
#                             "published_at": snippet.get("publishedAt"),
#                             "view_count": self._safe_int(stats.get("viewCount")),
#                             "like_count": self._safe_int(stats.get("likeCount")),
#                             "comment_count": self._safe_int(stats.get("commentCount")),
#                             "duration_seconds": duration_seconds,
#                             "duration_raw": duration_raw
#                         }
#                     })
                    
#                 logger.info(f"[{channel_id}] Kết quả cuối cùng: Lọc được {len(results)} Shorts hợp lệ từ danh sách gần đây.")
#             except Exception as e:
#                 logger.error(f"Lỗi xử lý gọi Official API YouTube: {str(e)}", exc_info=True)
                
#         return results

import httpx
import re
from typing import List, Dict, Any
from app.scrapers.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

# KHUYẾN NGHỊ: Nên đưa API Key vào file .env (ví dụ: os.getenv("YOUTUBE_API_KEY"))
YOUTUBE_API_KEY = "AIzaSyAzSt1kuN2X1IY_coKaSl7JVE8G4exUhqU" 

class YouTubeScraper(BaseScraper):
    def _safe_int(self, value: Any) -> int:
        if value is None:
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    def _parse_duration_to_seconds(self, duration_str: str) -> int:
        """Parse định dạng ISO 8601 từ YouTube: PT45S, PT1M2S, PT1H2M3S..."""
        if not duration_str:
            return 0
        
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration_str)
        if not match:
            return 0
            
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        
        return hours * 3600 + minutes * 60 + seconds

    # SỬA TẠI ĐÂY: Đổi tên hàm về khớp lớp cha và cho phép channel_id nhận giá trị mặc định là None
    async def fetch_viral_contents(self, channel_id: str = None) -> List[Dict[str, Any]]:
        """Săn lùng chính xác các Shorts đang hot tại Việt Nam bằng phương pháp Search Query"""
        results = []
        
        if not YOUTUBE_API_KEY or YOUTUBE_API_KEY.startswith("YOUR_"):
            logger.error("YOUTUBE_API_KEY chưa được cấu hình hợp lệ!")
            return results

        # Sử dụng endpoint search để quét diện rộng các video gắn tag #shorts
        search_url = "https://www.googleapis.com/youtube/v3/search"
        search_params = {
            "key": YOUTUBE_API_KEY,
            "part": "snippet",
            "q": "shorts",               # Từ khóa tìm kiếm cơ bản
            "type": "video",
            "videoDuration": "short",    # Ép API search chỉ tìm video dưới 4 phút (giúp loại bỏ bớt video dài)
            "regionCode": "VN",          # Định vị quốc gia Việt Nam
            "relevanceLanguage": "vi",   # Ngôn ngữ liên quan: Tiếng Việt
            "lr": "lang_vi",             # KHÓA CHÍNH: Ép kết quả trả về PHẢI thuộc ngôn ngữ Tiếng Việt
            "maxResults": 50,            # Lấy tối đa 50 kết quả để sàng lọc
            "order": "viewCount"         # Sắp xếp theo lượt xem cao nhất (Viral)
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                search_response = await client.get(search_url, params=search_params)
                if search_response.status_code != 200:
                    logger.error(f"Lỗi API Search: {search_response.status_code}")
                    return results
                
                search_data = search_response.json()
                video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]
                
                if not video_ids:
                    return results

                # Gọi API chi tiết để lấy thời lượng và lượt tương tác thực tế
                videos_url = "https://www.googleapis.com/youtube/v3/videos"
                videos_params = {
                    "key": YOUTUBE_API_KEY,
                    "id": ",".join(video_ids),
                    "part": "snippet,statistics,contentDetails"
                }
                
                videos_response = await client.get(videos_url, params=videos_params)
                if videos_response.status_code != 200:
                    return results
                    
                videos_data = videos_response.json()
                
                for video_item in videos_data.get("items", []):
                    if len(results) >= 20:
                        break

                    v_id = video_item["id"]
                    snippet = video_item.get("snippet", {})
                    stats = video_item.get("statistics", {})
                    duration_raw = video_item.get("contentDetails", {}).get("duration", "")
                    duration_seconds = self._parse_duration_to_seconds(duration_raw)
                    
                    # Lọc nghiêm ngặt thời lượng Shorts
                    if duration_seconds <= 0 or duration_seconds > 60:
                        continue
                        
                    results.append({
                        "external_id": v_id,
                        "content_type": "shorts",
                        "raw_json": {
                            "title": snippet.get("title"),
                            "url": f"https://www.youtube.com/shorts/{v_id}",
                            "channel_title": snippet.get("channelTitle"),
                            "published_at": snippet.get("publishedAt"),
                            "view_count": self._safe_int(stats.get("viewCount")),
                            "like_count": self._safe_int(stats.get("likeCount")),
                            "comment_count": self._safe_int(stats.get("commentCount")),
                            "duration_seconds": duration_seconds
                        }
                    })
                    
                logger.info(f"Đã quét diện rộng và tìm thấy {len(results)} Shorts Việt Nam đạt tiêu chuẩn.")
            except Exception as e:
                logger.error(f"Lỗi xử lý gọi API: {str(e)}", exc_info=True)
                
        return results