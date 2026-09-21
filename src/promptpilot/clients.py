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

    @timed
    @retry_on_api_error(attempts=3)
    def chat(self, request: ChatRequest) -> ChatResponse:
        """POST a validates JSON body and validate the JSON response"""
        try:
            response = self._client.post(
                "/chat/completions",
                json=request.model_dump(exclude_none=True),
            )    
        except httpx.TimeoutException as error:
            raise GroqAPIError("Groq request timed out") from error
        except httpx.HTTPError as error:
            raise GroqAPIError(f"network error while calling Groq: {error}") from error
        self._request_error(response)
        try:
            return ChatResponse.model_validate(response.json())
        except (ValueError, TypeError) as error:
            raise SchemaError("Groq returned an unexpected completion payload") from error

    def _build_request(
            self,
            prompt: str,
            model: str | None = None,
            system: str = "You are Promptpilot, a concise and helpful assistant.",
            temperature: float = 0.2,
            max_completions_tokens: int = 512,
            stream: bool = False,
    ) -> ChatRequest:
        return ChatRequest(
            model=model or self.model,
            messages=[
                ChatMessage(role="system", content=system),
                ChatMessage(role="user", content=prompt),
            ],
            temperature=temperature,
            max_completions_tokens=max_completions_tokens,
            stream=stream,
        )

    def ask(self, prompt: str, model:str | None = None) -> ChatResponse:
        """Convenience method for one non_streaming completion."""
        return self.chat(self._build_request(prompt, model=model))

    def stream_chat(self, request: ChatRequest) -> Iterator[str]:
        """
        Yield text deltas from Groq's server-sent Events response.

        Groq sends lines such as 'data: {"choices":[{"delta":{"content":"Hi"}}]}'
        and finishes with 'data: [DONE]', We parse the wire format explicity so 
        the CLI can display tokens immediately instead of waiting for the full answer.
        """

        payload = request.model_copy(update={"stream": True}).model_dump(exclude_none=True)

        try:
            with self._client.stream("POST", "/chat/completions", json=payload) as response:
                self._request_error(response)
                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError as error:
                        raise SchemaError("Groq returned malformed streaming JSON") from error

                    choices = event.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content") or ""
                    if content:
                        yield content
        except httpx.TimeoutException as error:
            raise GroqAPIError("Groq streaming request timed out") from error
        except httpx.HTTPError as error:
            raise GroqAPIError(f"network error while streaming from Groq: {error}") from error

    def stream(
            self,
            prompt: str,
            model: str | None = None,
            on_token: Callable[[str], None] | None = None,
    ) -> str:
        """Stream One prompt and return the complete text after the final chunk."""
        chunks: list[str] = []
        request = self._build_request(prompt, model=model, stream=True)
        for token in self.stream_chat(request):
            chunks.append(token)
            if on_token:
                on_token(token)
        return "".join(chunks)

    def list_models(self) -> ModelListResponse:
        """Return the live model catalog from Groq."""
        try:
            response = self._client.get("/models")
        except httpx.HTTPError as error:
            raise GroqAPIError(f"network error while listing models: {error}") from error
        self._request_error(response)
        try:
            return ModelListResponse.model_validate(response.json())
        except (ValueError, TypeError) as error:
            raise SchemaError("Groq returned an unexpected models payload") from error

    def ask_many_sequential(
            self, 
            prompts: Iterable[str],
            model: str | None = None,
    ) -> list[ChatResponse]:
        """Educational baseline used to compare with async gather."""
        return [self.ask(prompt, model=model) for prompt in prompts]

