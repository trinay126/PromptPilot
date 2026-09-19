"""Synchronous Groq REST Client with JSON and SSE Streaming support."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Iterator

import httpx

from promptpilot.constants import GROQ_BASE_URL
from promptpilot.decorators import retry_on_api_error, timed
from promptpilot.exceptions import GroqAPIError, SchemaError
from promptpilot.schemas import ChatMessage, ChatRequest, ChatResponse, ModelListResponse

class GroqApiClient:
    """Typed client for Groq's OpenAI - compatible REST endpoints."""

    def __init__(
            self,
            api_key: str,
            model: str,
            timeout_seconds: float = 45.0,
            base_url: str = GROQ_BASE_URL,
    ) -> None:
        if not api_key.strip():
            raise ValueError("api_key cannot be blank")
        self.api_key = api_key.strip()
        self.model = model
        self._client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_seconds),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "GroqApiClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _request_error(self, response: httpx.Response) -> None:
        if response.is_error:
            raise GroqAPIError(
                f"Groq returned HTTP {response.status_code}: {response.text[:500]}",
                status_code=response.status_code,
            )
        
    