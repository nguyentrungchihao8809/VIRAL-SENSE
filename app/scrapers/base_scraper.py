from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseScraper(ABC):
    @abstractmethod
    async def fetch_viral_contents(self, target: str) -> List[Dict[str, Any]]:
        """
        Nhận vào mục tiêu (Channel ID hoặc Username).
        Trả về danh sách tối đa 20 dict chứa metadata và URL.
        """
        pass