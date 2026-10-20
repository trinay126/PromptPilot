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


def test_quota_reports_exhaustion_state() -> None:
    quota = QuotaManager(AppConfig(demo_limit=1), lambda _: None)

    assert quota.exhausted is False
    assert quota.can_use_demo() is True

    quota.record_success()

    assert quota.exhausted is True
    assert quota.can_use_demo() is False


def test_quota_reset_clears_the_counter() -> None:
    config = AppConfig(demo_limit=5)
    quota = QuotaManager(config, lambda _: None)
    quota.record_success()
    quota.record_success()

    quota.reset()

    assert quota.used == 0
    assert quota.remaining == 5


def test_quota_summary_reports_dashboard_values() -> None:
    quota = QuotaManager(AppConfig(demo_limit=4), lambda _: None)
    quota.record_success()

    assert quota.summary() == {"limit": 4, "used": 1, "remaining": 3}
