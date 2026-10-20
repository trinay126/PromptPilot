"""Application service layer coordinating API calls, stats, and benchmarks."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable

from promptpilot.async_client import AsyncGroqApiClient
from promptpilot.benchmark import BenchmarkRunner, BenchmarkSummary
from promptpilot.clients import GroqApiClient
from promptpilot.config import ConfigStore
from promptpilot.constants import DEFAULT_SYSTEM_PROMPT
from promptpilot.exceptions import ConfigurationError, MissingAPIKeyError
from promptpilot.schemas import ChatMessage, ChatResponse, ModelInfo, PromptStat
from promptpilot.stores import StatsStore
from promptpilot.utils import clean_prompt
from promptpilot.workers import WorkerResult, run_in_threads

MAX_HISTORY_MESSAGES = 20


class PromptPilotService:
    """Facade that keeps CLI code thin and application rules testable."""

    def __init__(
        self,
        config_store: ConfigStore | None = None,
        stats_store: StatsStore | None = None,
    ) -> None:
        self.config_store = config_store or ConfigStore()
        self.config = self.config_store.load()
        stats_path = stats_store.path if stats_store else self.config_store.stats_path()
        self.stats_store = stats_store or StatsStore(stats_path)

    def _resolve_key(self) -> str:
        """Return the user's own API key, or explain how to provide one."""
        key = self.config_store.user_api_key()
        if not key:
            raise MissingAPIKeyError()
        return key

    def _record(
        self,
        prompt: str,
        response: ChatResponse,
        elapsed_ms: float,
    ) -> None:
        usage = response.usage
        self.stats_store.record(
            PromptStat(
                model=response.model,
                prompt_chars=len(prompt),
                response_chars=len(response.text),
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                latency_ms=elapsed_ms,
                prompt_preview=prompt[:120],
                success=True,
            )
        )

    def ask(self, prompt: str, model: str | None = None) -> ChatResponse:
        cleaned = clean_prompt(prompt)
        if not cleaned:
            raise ValueError("prompt cannot be blank")
        key = self._resolve_key()
        target_model = model or self.config.model
        started = time.perf_counter()
        with GroqApiClient(
            api_key=key,
            model=target_model,
            timeout_seconds=self.config.timeout_seconds,
        ) as client:
            response = client.ask(cleaned, model=target_model)
        self._record(cleaned, response, (time.perf_counter() - started) * 1000)
        return response

    def ask_with_history(
        self,
        prompt: str,
        history: list[ChatMessage],
        model: str | None = None,
    ) -> ChatResponse:
        """Send one prompt with earlier turns included as context."""
        cleaned = clean_prompt(prompt)
        if not cleaned:
            raise ValueError("prompt cannot be blank")
        key = self._resolve_key()
        target_model = model or self.config.model
        messages = [ChatMessage(role="system", content=DEFAULT_SYSTEM_PROMPT)]
        messages.extend(history[-MAX_HISTORY_MESSAGES:])
        messages.append(ChatMessage(role="user", content=cleaned))
        started = time.perf_counter()
        with GroqApiClient(
            api_key=key,
            model=target_model,
            timeout_seconds=self.config.timeout_seconds,
        ) as client:
            response = client.chat(
                client.build_request(messages, model=target_model)
            )
        self._record(cleaned, response, (time.perf_counter() - started) * 1000)
        return response

    def stream(
        self,
        prompt: str,
        model: str | None = None,
        on_token: Callable[[str], None] | None = None,
    ) -> str:
        """Stream deltas to `on_token`, then persist the completed response."""
        cleaned = clean_prompt(prompt)
        if not cleaned:
            raise ValueError("prompt cannot be blank")
        key = self._resolve_key()
        target_model = model or self.config.model
        started = time.perf_counter()
        with GroqApiClient(
            api_key=key,
            model=target_model,
            timeout_seconds=self.config.timeout_seconds,
        ) as client:
            text = client.stream(cleaned, model=target_model, on_token=on_token)
        response = ChatResponse(
            id="streamed-local",
            model=target_model,
            choices=[
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
            usage=None,
        )
        self._record(cleaned, response, (time.perf_counter() - started) * 1000)
        return text

    async def ask_many_async(
        self,
        prompts: list[str],
        model: str | None = None,
    ) -> list[ChatResponse | BaseException]:
        """Send many prompts concurrently and keep the input ordering."""
        if not prompts:
            return []
        key = self._resolve_key()
        target_model = model or self.config.model
        async with AsyncGroqApiClient(
                api_key=key,
                model=target_model,
                timeout_seconds=self.config.timeout_seconds,
            ) as client:
            return await client.ask_many(prompts, model=target_model)

    def ask_many(
        self, prompts: list[str], model: str | None = None
    ) -> list[ChatResponse | BaseException]:
        """Blocking wrapper around `ask_many_async` for the CLI."""
        return asyncio.run(self.ask_many_async(prompts, model=model))

    def list_models(self) -> list[ModelInfo]:
        key = self._resolve_key()
        with GroqApiClient(
            api_key=key,
            model=self.config.model,
            timeout_seconds=self.config.timeout_seconds,
        ) as client:
            return client.list_models().data

    def benchmark(
        self, models: list[str], prompt: str, rounds: int = 3
    ) -> list[BenchmarkSummary]:
        key = self._resolve_key()
        return BenchmarkRunner(
            lambda model: GroqApiClient(
                api_key=key,
                model=model,
                timeout_seconds=self.config.timeout_seconds,
            )
        ).run(models, clean_prompt(prompt), rounds)

    def dashboard(self) -> dict[str, object]:
        return {
            "model": self.config.model,
            "stats": self.stats_store.summary(),
            "config_path": str(self.config_store.path),
            "stats_path": str(self.stats_store.path),
            "api_key_source": self.config_store.api_key_source(),
            "has_api_key": self.config_store.has_api_key(),
        }

    def set_user_key(self, api_key: str) -> None:
        cleaned = api_key.strip()
        if len(cleaned) < 10:
            raise ValueError("the API key looks too short")
        self.config.api_key = cleaned
        self.config_store.save(self.config)

    def set_model(self, model: str) -> None:
        cleaned = model.strip()
        if len(cleaned) < 2:
            raise ValueError("model cannot be blank")
        self.config.model = cleaned
        self.config_store.save(self.config)

    def clear_stats(self) -> None:
        self.stats_store.clear()

    def history(self, limit: int = 10) -> list[PromptStat]:
        """Return the most recent recorded prompts, newest last."""
        return self.stats_store.recent(limit=limit)

    def probe_models(self, models: list[str]) -> list[WorkerResult]:
        def probe(model: str) -> str:
            return self.ask("Reply with the single word OK.", model=model).text
        return run_in_threads(models, probe, max_workers=min(4, max(1, len(models))))


__all__ = ["MAX_HISTORY_MESSAGES", "PromptPilotService"]
