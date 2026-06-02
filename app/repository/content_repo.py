from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models.platform_content import PlatformContent
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ContentRepository:
    @staticmethod
    async def save_raw_contents(db: AsyncSession, platform: str, items: List[Dict[str, Any]]) -> int:
        if not items:
            return 0
            
        saved_count = 0
        for item in items:
            # Tạo câu lệnh Insert thô
            stmt = insert(PlatformContent).values(
                platform=platform,
                external_id=item["external_id"],
                content_type=item["content_type"],
                raw_json=item["raw_json"],
                is_processed=False
            )
            
            # Cấu hình Ràng buộc duy nhất (Unique Constraint) chống cào trùng lặp
            stmt = stmt.on_conflict_do_nothing(index_elements=["platform", "external_id"])
            
            result = await db.execute(stmt)
            # rowcount > 0 nghĩa là dòng này hoàn toàn mới và đã được nạp vào DB thành công
            if result.rowcount > 0:
                saved_count += 1
                
        await db.commit()
        logger.info(f"[{platform.upper()}] Thành công ghi mới {saved_count}/{len(items)} bài viết vào Core DB.")
        return saved_count