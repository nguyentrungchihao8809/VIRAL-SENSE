from fastapi import FastAPI, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.scrapers.youtube_scraper import YouTubeScraper
from app.scrapers.threads_scraper import ThreadsScraper
from app.repository.content_repo import ContentRepository

app = FastAPI(title="ViralSense Platform Collection API")

@app.get("/")
def read_root():
    return {"message": "ViralSense Core Infrastructure is fully Operational!"}

@app.post("/api/v1/collection/trigger/youtube", tags=["Manual Collection Trigger"])
async def trigger_youtube_crawl(
    channel_id: str = Query("UC_dx2gV7B-vof0aLwA_X0_A", description="Nhập YouTube Channel ID cần lấy Top 20 Shorts (Mặc định: Schannel)"),
    db: AsyncSession = Depends(get_db)
):
    scraper = YouTubeScraper()
    items = await scraper.fetch_viral_contents(channel_id)
    saved_count = await ContentRepository.save_raw_contents(db, "youtube", items)
    
    return {
        "status": "success",
        "platform": "youtube",
        "target_channel_id": channel_id,
        "total_fetched": len(items),
        "new_records_inserted": saved_count,
        "sample_data": items[:3]  # Xem trước kết quả 3 bản ghi đầu tiên
    }

@app.post("/api/v1/collection/trigger/threads", tags=["Manual Collection Trigger"])
async def trigger_threads_crawl(
    username: str = Query("schannelyoutube", description="Nhập chính xác Username Threads của tài khoản cần cào Top 20"),
    db: AsyncSession = Depends(get_db)
):
    scraper = ThreadsScraper()
    items = await scraper.fetch_viral_contents(username)
    saved_count = await ContentRepository.save_raw_contents(db, "threads", items)
    
    return {
        "status": "success",
        "platform": "threads",
        "target_username": username,
        "total_fetched": len(items),
        "new_records_inserted": saved_count,
        "sample_data": items[:3]  # Xem trước kết quả 3 bản ghi đầu tiên
    }