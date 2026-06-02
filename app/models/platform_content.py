from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base

class PlatformContent(Base):
    __tablename__ = "platform_contents"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False)        # 'youtube', 'threads'
    external_id = Column(String(100), nullable=False)   # Video ID hoặc Post ID
    content_type = Column(String(10), nullable=False)   # 'video', 'post'
    raw_json = Column(JSONB, nullable=False)            # Lưu toàn bộ metadata cào được
    video_r2_key = Column(String, nullable=True)
    audio_r2_key = Column(String, nullable=True)
    is_processed = Column(Boolean, default=False)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Đảm bảo không cào trùng một nội dung trên cùng 1 nền tảng
    __table_args__ = (
        _UniqueConstraint_placeholder_ if False else None, 
        # Sẽ được cấu hình UniqueConstraint('platform', 'external_id', name='uix_platform_external_id')
    )