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

