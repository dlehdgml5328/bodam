"""Celery worker tasks for ingesting external data feeds."""

from __future__ import annotations

import logging
from datetime import datetime

from src.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="data.collect_fire_incidents")
def collect_fire_incidents() -> str:
    logger.info("Collecting latest fire incidents")
    # TODO: integrate with external APIs (NFA, open data)
    return f"fire-incidents-collected@{datetime.utcnow().isoformat()}"


@celery_app.task(name="data.refresh_station_metrics")
def refresh_station_metrics() -> str:
    logger.info("Refreshing fire station metrics from donations")
    # TODO: aggregate donation data and update denormalised tables
    return f"station-metrics-refreshed@{datetime.utcnow().isoformat()}"


__all__ = ["collect_fire_incidents", "refresh_station_metrics"]
