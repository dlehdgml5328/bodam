"""Integration tests for Celery Beat deployment (T007)."""

from __future__ import annotations

import subprocess

from src.worker import celery_app


def test_celery_beat_has_required_schedule() -> None:
    """Beat schedule must include the crawl-news task."""
    schedule = getattr(celery_app.conf, "beat_schedule", {})
    assert "crawl-news-every-30min" in schedule, "Beat schedule missing crawl-news task"


def test_celery_beat_single_instance_running() -> None:
    """Exactly one beat pod should be running in the cluster."""
    result = subprocess.run(
        [
            "kubectl",
            "get",
            "pods",
            "-l",
            "app=celery-beat",
            "--no-headers",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "kubectl get pods for celery-beat failed: " + result.stderr.strip()
    )

    pods = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(pods) == 1, f"Expected exactly one beat pod, found {len(pods)}"
    assert "Running" in pods[0], "Celery beat pod is not running"
