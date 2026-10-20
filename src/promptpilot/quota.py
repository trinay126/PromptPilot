"""Thread-safe ten-prompt demo quota."""

from __future__ import annotations

from threading import Lock
from typing import Callable

from promptpilot.exceptions import QuotaExceededError
from promptpilot.schemas import AppConfig


class QuotaManager:
    """Manage successful demo prompts without charging user-owned keys."""

    def __init__(self, config: AppConfig, save_config: Callable[[AppConfig], object]) -> None:
        self._config = config
        self._save_config = save_config
        self._lock = Lock()

    @property
    def limit(self) -> int:
        """Return the total number of demo prompts allowed."""
        return self._config.demo_limit

    @property
    def used(self) -> int:
        """Return how many demo prompts have already been consumed."""
        return self._config.demo_prompts_used

    @property
    def remaining(self) -> int:
        """Return how many demo prompts are still available."""
        return self._config.demo_prompts_remaining

    @property
    def exhausted(self) -> bool:
        """Report whether the demo allowance has been fully consumed."""
        return self.remaining == 0

    def can_use_demo(self) -> bool:
        """Report whether another demo prompt may run."""
        return self.remaining > 0

    def record_success(self) -> None:
        """Atomically record a successful demo prompt."""
        with self._lock:
            if not self.can_use_demo():
                raise QuotaExceededError(
                    "The ten-prompt demo allowance is finished. Configure your own Groq key."
                )
            self._config.demo_prompts_used += 1
            self._save_config(self._config)

    def reset(self) -> None:
        """Reset only local demo accounting for a private test build."""
        with self._lock:
            self._config.demo_prompts_used = 0
            self._save_config(self._config)

    def summary(self) -> dict[str, int]:
        """Return dashboard-friendly quota data."""
        return {"limit": self.limit, "used": self.used, "remaining": self.remaining}


__all__ = ["QuotaManager"]
