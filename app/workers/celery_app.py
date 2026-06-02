from celery import Celery
from celery.schedules import crontab
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "viralsense_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    imports=["app.workers.tasks"]  # Trỏ tới file định nghĩa task ngầm
)

# Lập lịch cào tự động (Celery Beat)
celery_app.conf.beat_schedule = {
    "crawl-youtube-shorts-every-6-hours": {
        "task": "app.workers.tasks.task_crawl_youtube_shorts",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "crawl-threads-posts-every-6-hours": {
        "task": "app.workers.tasks.task_crawl_threads_posts",
        "schedule": crontab(minute=30, hour="*/6"),
    },
}