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

    def _resolve_key(self) -> 
    