"""Celery worker sending queued notifications."""

from __future__ import annotations

import logging
from datetime import datetime

from src.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="notifications.dispatch")
def dispatch_notifications() -> str:
    logger.info("Dispatching queued notifications")
    # TODO: integrate with email, KakaoTalk, and web push
    return f"notifications-dispatched@{datetime.utcnow().isoformat()}"


__all__ = ["dispatch_notifications"]
