import os
from dotenv import load_dotenv

from celery import Celery
from dotenv import load_dotenv

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
    # NFDS 사이트 크롤링 (2시간마다)
    # 크롤링 → DB 저장 → 뉴스 매칭
    # YouTube API 할당량 절약: 하루 12회 (심각도 높은 화재만 검색)
    'crawl-nfds-site-every-2hours': {
        'task': 'src.workers.crawler.crawl_nfds_site',
        'schedule': 7200.0,  # 2시간 = 7200초
    },
    # 정기결제 자동 결제 (매일 오전 2시)
    'process-recurring-donations-daily': {
        'task': 'billing.process_subscriptions',
        'schedule': crontab(hour=2, minute=0),  # 매일 02:00 KST
    },
}

celery_app.conf.timezone = "Asia/Seoul"

# Task 자동 검색
celery_app.autodiscover_tasks([
    "src.workers",
])

# 명시적으로 워커 모듈 import
from src.workers import crawler, incident_pipeline, matcher, billing_processor


@celery_app.task(name="worker.health_check")
def health_check() -> str:
    """Return simple heartbeat value for readiness probes."""
    return "ok"
