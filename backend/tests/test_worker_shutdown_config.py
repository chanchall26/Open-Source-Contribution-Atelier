"""Guards the settings that let Django-Q workers drain on SIGTERM."""

import re
from pathlib import Path

import yaml
from django.conf import settings

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seconds(value: str) -> int:
    return int(re.fullmatch(r"(\d+)s", value.strip()).group(1))


def test_worker_grace_period_exceeds_task_timeout():
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text("utf-8"))
    worker = compose["services"]["worker"]
    assert worker["command"].startswith("python manage.py qcluster")
    assert _seconds(str(worker["stop_grace_period"])) > settings.Q_TASK_TIMEOUT
