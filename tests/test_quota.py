import pytest

from promptpilot.exceptions import QuotaExceededError
from promptpilot.quota import QuotaManager
from promptpilot.schemas import AppConfig


def test_quota_counts_successful_prompts() -> None:
    config = AppConfig(demo_limit=2)
    saved = []
    quota = QuotaManager(config, saved.append)

    quota.record_success()
    quota.record_success()

    assert quota.used == 2
    assert quota.remaining == 0
    assert len(saved) == 2


def test_quota_raises_after_limit() -> None:
    config = AppConfig(demo_limit=1)
    quota = QuotaManager(config, lambda _: None)
    quota.record_success()

    with pytest.raises(QuotaExceededError):
        quota.record_success()
