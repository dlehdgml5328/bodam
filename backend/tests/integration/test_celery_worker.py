"""Integration test for Celery worker task execution (T006)."""

from __future__ import annotations

import pytest

from src.worker import celery_app


def test_celery_worker_health_check_executes() -> None:
    """Celery worker must execute the health_check task successfully."""
    try:
        result = celery_app.send_task("worker.health_check")
        output = result.get(timeout=5)
    except Exception as exc:  # pragma: no cover - intentional failure before infra ready
        pytest.fail(f"Celery health_check task failed: {exc}")

    assert output == "ok"
