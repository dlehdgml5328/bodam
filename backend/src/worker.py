import os

from celery import Celery
from celery.schedules import crontab
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

# Ensure Celery loads custom task modules explicitly (namespace package without __init__)
celery_app.conf.imports = tuple(celery_app.conf.imports or ()) + (
    "src.workers.selenium_crawler_worker",
)

# Celery Beat 스케줄 설정
celery_app.conf.beat_schedule = {
    # NFDS 사이트 크롤링 (2시간마다)
    # 크롤링 → DB 저장 → 뉴스 매칭
    # YouTube API 할당량 절약: 하루 12회 (심각도 높은 화재만 검색)
    "crawl-nfds-site-every-2hours": {
        "task": "src.workers.crawler.crawl_nfds_site",
        "schedule": 7200.0,  # 2시간 = 7200초
    },
    # 동적 뉴스 소스 크롤링 (2시간마다) - Selenium 작업 생성
    "schedule-dynamic-news-crawl": {
        "task": "crawler.schedule_dynamic_news",
        "schedule": 7200.0,
    },
    # 정기결제 자동 결제 (매일 오전 2시)
    "process-recurring-donations-daily": {
        "task": "billing.process_subscriptions",
        "schedule": crontab(hour=2, minute=0),  # 매일 02:00 KST
    },
    # 뉴스/영상 재매칭 (6시간마다)
    # 최근 7일 이내 화재 중 매칭이 2개 미만인 사고를 재시도
    "retry-failed-matches-every-6hours": {
        "task": "matcher.retry_failed_matches",
        "schedule": crontab(minute=0, hour="*/6"),  # 매 6시간마다 (0시, 6시, 12시, 18시)
        "kwargs": {"max_age_days": 7}
    },
}

celery_app.conf.timezone = "Asia/Seoul"

# Task 자동 검색
celery_app.autodiscover_tasks([
    "src.workers",
])

# 명시적으로 워커 모듈 import


@celery_app.task(name="worker.health_check")
def health_check() -> str:
    """Return simple heartbeat value for readiness probes."""
    return "ok"


# ============================================================
# Celery Signal Handlers - Prometheus 메트릭 자동 수집
# ============================================================
from celery.signals import task_failure, task_retry, task_success

from src.api.observability import celery_tasks_total


@task_success.connect
def task_success_handler(sender=None, **kwargs):
    """작업 성공 시 메트릭 증가"""
    task_name = sender.name if sender else "unknown"
    celery_tasks_total.labels(task_name=task_name, status="SUCCESS").inc()


@task_failure.connect
def task_failure_handler(sender=None, **kwargs):
    """작업 실패 시 메트릭 증가"""
    task_name = sender.name if sender else "unknown"
    celery_tasks_total.labels(task_name=task_name, status="FAILURE").inc()


@task_retry.connect
def task_retry_handler(sender=None, **kwargs):
    """작업 재시도 시 메트릭 증가"""
    task_name = sender.name if sender else "unknown"
    celery_tasks_total.labels(task_name=task_name, status="RETRY").inc()
