import os

from celery import Celery
from celery.schedules import crontab


BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis-queue-service:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis-queue-service:6379/1")

celery_app = Celery(
    "bodam",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)

# Celery Beat 스케줄 설정
celery_app.conf.beat_schedule = {
    # Mock 사이트 크롤링 (5분마다)
    'crawl-mock-site-every-5min': {
        'task': 'src.workers.crawler.crawl_mock_site',
        'schedule': 300.0,  # 5분 = 300초
    },
}

celery_app.conf.timezone = 'Asia/Seoul'

# Task 자동 검색
celery_app.autodiscover_tasks([
    'src.workers',
])


@celery_app.task(name="worker.health_check")
def health_check() -> str:
    """Return simple heartbeat value for readiness probes."""
    return "ok"
