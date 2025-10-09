"""Integration test for Redis queue backup CronJob (T009)."""

from __future__ import annotations

import subprocess

import pytest

CRONJOB_NAME = "redis-queue-backup"
BACKUP_POD_LABEL = "job-name=redis-queue-backup"


def test_redis_backup_cronjob_can_run_job() -> None:
    """CronJob must exist and create a backup job that produces an RDB file."""
    trigger = subprocess.run(
        [
            "kubectl",
            "create",
            "job",
            "redis-backup-test",
            "--from=cronjob/" + CRONJOB_NAME,
            "--dry-run=client",
            "-o",
            "name",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert trigger.returncode == 0, (
        "Failed to create job from cronjob: " + trigger.stderr.strip()
    )
    assert CRONJOB_NAME in trigger.stdout, "Backup CronJob did not return expected name"

    pod_check = subprocess.run(
        [
            "kubectl",
            "get",
            "pods",
            "-l",
            BACKUP_POD_LABEL,
            "-o",
            "jsonpath={.items[0].status.phase}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert pod_check.returncode == 0, (
        "kubectl get pods for backup job failed: " + pod_check.stderr.strip()
    )
    assert pod_check.stdout.strip() == "Succeeded", "Backup job did not succeed"

    file_check = subprocess.run(
        [
            "kubectl",
            "exec",
            "statefulset/redis-queue",
            "--",
            "test",
            "-f",
            "/data/dump.rdb",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert file_check.returncode == 0, (
        "Redis queue backup file not found: " + file_check.stderr.strip()
    )
