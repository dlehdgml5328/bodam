import os

from celery import Celery


BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis-queue-service:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis-queue-service:6379/1")

celery_app = Celery(
    "bodam",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)


@celery_app.task(name="worker.health_check")
def health_check() -> str:
    """Return simple heartbeat value for readiness probes."""
    return "ok"
