"""Application service layer coordination of API calls, quota, stats and benchmarks"""

from __future__ import annotations

import asyncio
import time

from promptpilot.async_client import AsyncGroqApiClient
from promptpilot.benchmark import BenchmarkRunner, BenchmarkSummary
from promptpilot.clients import GroqApiClient
from promptpilot.config import ConfigStore
from promptpilot.exceptions import ConfigurationError, QuotaExceededError
from promptpilot.quota import QuotaManager
from promptpilot.schemas import ChatResponse, ModelInfo, PromptStat
from promptpilot.stores import StatsStore
from promptpilot.utils import clean_prompt
from promptpilot.workers import WorkerResult, run_in_threads

class PromptPilotService:
    """Facade that keeps CLI code thin and application rules testable."""

    def __init__(self, config_store: ConfigStore | None = None, stats_store: StatsStore | None = None) -> None:
        self.config_store = config_store or ConfigStore()
        self.config = self.config_store.load()
        stats_path = stats_store.path if stats_store else self.config_store.path.with_name("stats.jsonl")
        self.stats_store = stats_store or StatsStore(stats_path)
        self.quota = QuotaManager(self.config, self.config_store.save)

    def _resolve_key(self) -> tuple[str, str]:
        demo_key = self.config_store.demo_api_key()
        if demo_key and self.quota.can_use_demo():
            return demo_key, "demo"
        user_key = self.config_store.user_api_key()
        if not user_key:
            if demo_key and not self.quota.can_use_demo():
                raise QuotaExceededError("Demo quota exhausted. Run 'promptpilot set-key")
            raise ConfigurationError("No Groq key found. Set GROQ_API_KEY or run 'promptpilot set-key.")
        return user_key, "user"

    def _record(self, prompt: str, response: ChatResponse, elpased_ms: float, source: str) -> None:
        usage = response.usage
        self.stats_store.record(
            PromptStat(
                model=response.model,
                prompt_chars=len(prompt),
                response_chars=len(response.text),
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                latency_ms=elpased_ms,
                source=source,
                success=True,
            )
        )

    def ask(self, prompt: str, model: str | None = None) -> ChatResponse:
        cleaned = clean_prompt(prompt)
        if not cleaned:
            raise  ValueError("prompt cannot be blank")
        key, source = self._resolve_key()
        started = time.perf_counter()
        with GroqApiClient(
            api_key=key,
            model=model or self.config.model,
            timeout_seconds=self.config.timeout_seconds,
        ) as client:
            response = client.ask(cleaned, model=model or self.config.model)
        if source == "demo":
            self.quota.record_success()
        self._record(cleaned, response, (time.perf_couter() - started) * 1000, source)
        return response

    
        
