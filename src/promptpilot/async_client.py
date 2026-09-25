"""Asynchronous Groq REST client and gather - based batch execution."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

import httpx

from promptpilot.constants import GROQ_BASE_URL
from promptpilot.decorators import async_retry_on_api_error
from promptpilot.exceptions import GroqAPIError, SchemaError
from promptpilot.schemas import ChatMessage, ChatRequest, ChatResponse, ModelListResponse


class AsyncGroqApiClient:
    """Async counterpart of 'GroqApiClient' fpr I/O - bound workloads."""

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
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_seconds),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def __aenter__(self) -> "AsyncGroqApiClient":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    @async_retry_on_api_error(attempts=3)
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send one asynchronous request."""
        try:
            response = await self._client.post(
                "/chat/completions",
                json=request.model_dump(exclude_none=True),
            )
        except httpx.TimeoutException as error:
            raise GroqAPIError("Groq async request timed out") from error
        except httpx.HTTPError as error:
            raise GroqAPIError(f"async networl error while calling Groq: {error}")

        if response.is_error:
            raise GroqAPIError(
                f"Groq returned HTTP {response.status_code}:{response.text[:500]}",
                status_code=response.status_code,
            )

        try:
            return ChatResponse.model_validate(response.json())
        except (ValueError, TypeError) as error:
            raise SchemaError("Groq returned an unexpected async payload") from error
    async def ask(self, prompt: str, model: str | None = None) -> ChatResponse:
        """Build and send a single async prompt."""
        request = ChatRequest(
            model=model or self.model,
            messages=[ChatMessage(role="system", content="You are a PromptPilot, a helpful assistant."),
                      ChatMessage(role="user", content=prompt),
                      ],
            temparature=0.2,
            max_completion_tokens=512,
        )
        return await self.chat(request)

    async def many(
            self,
            prompts: Iterable[str],
            model: str | None = None,
            return_exceptions: bool =  True,
    ) -> list[ChatResponse | BaseException]:
        """Run many coroutines concurrently and preserver input order.
        'asyncio.gather' schedules all awaitables concurrently. Its result list
        follows the order of the input awiatables, not completion order.
        'return_exceptions=True' lets the CLI show partial batch results. 
        """
        jobs = [self.ask(prompt, model=model) for prompt in prompts]
        return list(await asyncio.gather(*jobs, return_exceptions=return_exceptions))

    async def list_models(self) -> ModelListResponse:
        """Fetch the live model catalog asynchronously."""
        try:
            response = await self._client.get("/models")
        except httpx.HTTPError as error:
            raise GroqAPIError(f"async network error while listing models: {error}") from error
        if response.is_error:
            raise GroqAPIError(
                f"Groq returned HTTP {response.status_code}:{response.text[:500]}",
                status_code=response.status_code
            )
        try:
            return ModelListResponse.model_validate(response.json())
        except (ValueError, TypeError) as error:
            raise SchemaError("Groq returned an unexpected async models payload") from error
        