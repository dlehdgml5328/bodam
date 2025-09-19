from celery import Celery

celery_app = Celery(
    "bodam",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


@celery_app.task(name="worker.health_check")
def health_check() -> str:
    """Return simple heartbeat value for readiness probes."""
    return "ok"
