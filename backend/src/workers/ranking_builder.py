"""Ranking builder worker."""

from __future__ import annotations

import logging

from src.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="ranking.build")
def build_rankings() -> str:
    logger.info("Recomputing donation rankings")
    return "rankings-built"


__all__ = ["build_rankings"]
