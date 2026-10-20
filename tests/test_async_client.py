"""Tests for the asynchronous Groq client."""

import asyncio

import httpx
import pytest
import respx

from promptpilot.async_client import AsyncGroqApiClient
from promptpilot.exceptions import GroqAPIError, SchemaError

CHAT_PAYLOAD = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "model": "test-model",
    "choices": [
        {"index": 0, "message": {"role": "assistant", "content": "pong"}, "finish_reason": "stop"}
    ],
    "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
}


@respx.mock
def test_ask_sends_one_request_and_validates_the_response() -> None:
    route = respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=CHAT_PAYLOAD)
    )

    async def run() -> str:
        async with AsyncGroqApiClient(
            "test-key", "test-model", base_url="https://api.test/v1"
        ) as client:
            response = await client.ask("ping")
            return response.text

    assert asyncio.run(run()) == "pong"
    assert route.call_count == 1
    assert route.calls.last.request.headers["authorization"] == "Bearer test-key"


@respx.mock
def test_ask_many_preserves_the_input_order() -> None:
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=CHAT_PAYLOAD)
    )

    async def run() -> list:
        async with AsyncGroqApiClient(
            "test-key", "test-model", base_url="https://api.test/v1"
        ) as client:
            return await client.ask_many(["one", "two", "three"])

    results = asyncio.run(run())

    assert len(results) == 3
    assert all(isinstance(result, str) or hasattr(result, "text") for result in results)


@respx.mock
def test_ask_many_reports_failures_instead_of_raising() -> None:
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(401, text="invalid key")
    )

    async def run() -> list:
        async with AsyncGroqApiClient(
            "test-key", "test-model", base_url="https://api.test/v1"
        ) as client:
            return await client.ask_many(["one"], return_exceptions=True)

    results = asyncio.run(run())

    assert len(results) == 1
    assert isinstance(results[0], BaseException)


@respx.mock
def test_list_models_returns_the_live_catalog() -> None:
    respx.get("https://api.test/v1/models").mock(
        return_value=httpx.Response(
            200,
            json={"object": "list", "data": [{"id": "model-a", "object": "model"}]},
        )
    )

    async def run() -> list[str]:
        async with AsyncGroqApiClient(
            "test-key", "test-model", base_url="https://api.test/v1"
        ) as client:
            catalog = await client.list_models()
            return [model.id for model in catalog.data]

    assert asyncio.run(run()) == ["model-a"]


@respx.mock
def test_unexpected_payload_raises_a_schema_error() -> None:
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"unexpected": "shape"})
    )

    async def run() -> None:
        async with AsyncGroqApiClient(
            "test-key", "test-model", base_url="https://api.test/v1"
        ) as client:
            await client.ask("ping")

    with pytest.raises(SchemaError):
        asyncio.run(run())


@respx.mock
def test_api_error_keeps_the_status_code() -> None:
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(401, text="invalid key")
    )

    async def run() -> None:
        async with AsyncGroqApiClient(
            "test-key", "test-model", base_url="https://api.test/v1"
        ) as client:
            await client.ask("ping")

    with pytest.raises(GroqAPIError) as caught:
        asyncio.run(run())

    assert caught.value.status_code == 401


def test_a_blank_api_key_is_rejected() -> None:
    with pytest.raises(ValueError):
        AsyncGroqApiClient("   ", "test-model")


@respx.mock
def test_ask_many_runs_every_prompt() -> None:
    route = respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=CHAT_PAYLOAD)
    )

    async def run() -> list:
        async with AsyncGroqApiClient(
            "test-key", "test-model", base_url="https://api.test/v1"
        ) as client:
            return await client.ask_many(["one", "two", "three"])

    asyncio.run(run())

    assert route.call_count == 3


@respx.mock
def test_ask_sends_the_requested_model() -> None:
    route = respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=CHAT_PAYLOAD)
    )

    async def run() -> None:
        async with AsyncGroqApiClient(
            "test-key", "test-model", base_url="https://api.test/v1"
        ) as client:
            await client.ask("ping", model="other-model")

    asyncio.run(run())

    assert b"other-model" in route.calls.last.request.content


@respx.mock
def test_list_models_error_is_translated() -> None:
    respx.get("https://api.test/v1/models").mock(
        return_value=httpx.Response(500, text="server error")
    )

    async def run() -> None:
        async with AsyncGroqApiClient(
            "test-key", "test-model", base_url="https://api.test/v1"
        ) as client:
            await client.list_models()

    with pytest.raises(GroqAPIError):
        asyncio.run(run())
