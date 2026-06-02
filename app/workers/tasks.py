from app.workers.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def task_crawl_youtube_shorts():
    logger.info("--- STARTED: Task cào YouTube Shorts đang chạy ngầm ---")
    # Logic cào thực tế sẽ viết ở đây
    return {"status": "success", "platform": "youtube"}

@celery_app.task
def task_crawl_threads_posts():
    logger.info("--- STARTED: Task cào Threads đang chạy ngầm ---")
    # Logic cào thực tế sẽ viết ở đây
    return {"status": "success", "platform": "threads"}