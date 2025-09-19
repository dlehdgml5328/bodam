"""Celery worker bridging AI analysis service."""

from __future__ import annotations

import logging
from datetime import datetime

from src.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="ai.analyze_news")
def analyze_news_batch(job_id: str) -> str:
    logger.info("Triggering AI analysis for job %s", job_id)
    # TODO: call AIAnalysisService to process queued job entries
    return f"ai-analysis-triggered@{job_id}@{datetime.utcnow().isoformat()}"


__all__ = ["analyze_news_batch"]
