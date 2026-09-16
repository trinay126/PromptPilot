"""Thread-safe ten-prompt demo quota."""
from __future__ import annotations

from threading import Lock

from promptpilot.exceptions import QuotaExceededError
from promptpilot.schemas import AppConfig

class QuotaManger:
    """Manage successful demo prompts without charging user-owned keys."""

    def __init__(self, config: AppConfig, save_config) -> None:
        self._config = config
        self._save_config = save_config
        self._lock = Lock()

    @property
    def limit(self) -> int:
        return self._config.demo_limit

    @property
    def used(self) -> int:
        return self._config.demo_prompts_used

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    def can_use_demo(self) -> bool:
        return self.remaining > 0

    def record_success(self) -> None:
        """Atomically record a successful demo prompt."""
        with self._lock:
            if not self.can_use_demo():
                raise QuotaExceededError(
                    "The ten-prompt demo allowance is finishes. configure your own Groq key."
                )
            self._config.demo_prompts_used += 1
            self._save_config(self._config)

    def reset(self) -> None:
        """Reset only local demo accounting for a private test build."""
        with self._lock:
            self._config.demo_prompts_used = 0
            self._save_config(self._config)

    def summary(self) -> dict[str, int]:
        """Return dashboard friendly quota data."""
        return {"limit": self.limit, "used": self.used, "remaining": self.remaining}

    