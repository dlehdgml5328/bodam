import os
from dotenv import load_dotenv

from celery import Celery
from celery.schedules import crontab

# .env 파일 로드
load_dotenv()

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis-queue-service:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis-queue-service:6379/1")

celery_app = Celery(
    "bodam",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)

# Celery Beat 스케줄 설정
celery_app.conf.beat_schedule = {
    # Mock 사이트 크롤링 (30분마다)
    # 크롤링 → DB 저장 → 뉴스 매칭
    # YouTube API 할당량 절약: 하루 48회 × 200 units = 9,600 units (할당량 내)
    'crawl-mock-site-every-30min': {
        'task': 'src.workers.crawler.crawl_mock_site',
        'schedule': 1800.0,  # 30분 = 1800초
    },
}

celery_app.conf.timezone = 'Asia/Seoul'

# Task 자동 검색
celery_app.autodiscover_tasks([
    'src.workers',
])

# 명시적으로 워커 모듈 import
from src.workers import crawler, incident_pipeline, matcher


@celery_app.task(name="worker.health_check")
def health_check() -> str:
    """Return simple heartbeat value for readiness probes."""
    return "ok"
