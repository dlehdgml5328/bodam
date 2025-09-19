"""Celery worker for handling asynchronous payment confirmations."""

from __future__ import annotations

import logging
from datetime import datetime

from src.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="payments.confirm_pending")
def confirm_pending_payments() -> str:
    logger.info("Confirming pending Toss payments")
    # TODO: pull pending donations and confirm via Toss API
    return f"payments-confirmed@{datetime.utcnow().isoformat()}"


@celery_app.task(name="payments.issue_receipts")
def issue_receipts() -> str:
    logger.info("Issuing donation receipts")
    # TODO: generate PDF receipts and email donors
    return f"receipts-issued@{datetime.utcnow().isoformat()}"


__all__ = ["confirm_pending_payments", "issue_receipts"]
