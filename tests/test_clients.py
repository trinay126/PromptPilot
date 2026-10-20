import httpx
import pytest
import respx

from promptpilot.clients import GroqApiClient
from promptpilot.exceptions import GroqAPIError, SchemaError


@respx.mock
def test_chat_mocks_real_http_boundary() -> None:
    route = respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "model": "test-model",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "pong"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
            },
        )
    )

    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        response = client.ask("ping")

    assert response.text == "pong"
    assert route.called
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer test-key"
    assert request.content and b"test-model" in request.content


@respx.mock
def test_api_error_is_translated() -> None:
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(401, text="invalid key")
    )
    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        try:
            client.ask("ping")
        except Exception as error:
            assert "HTTP 401" in str(error)
        else:
            raise AssertionError("expected API error")


@respx.mock
def test_api_error_keeps_the_status_code() -> None:
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(401, text="invalid key")
    )

    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        with pytest.raises(GroqAPIError) as caught:
            client.ask("ping")

    assert caught.value.status_code == 401
    assert caught.value.is_retryable is False


@respx.mock
def test_unexpected_payload_raises_a_schema_error() -> None:
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"unexpected": "shape"})
    )

    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        with pytest.raises(SchemaError):
            client.ask("ping")


@respx.mock
def test_list_models_returns_the_live_catalog() -> None:
    respx.get("https://api.test/v1/models").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {"id": "model-a", "object": "model", "owned_by": "groq"},
                    {"id": "model-b", "object": "model", "owned_by": "groq"},
                ],
            },
        )
    )

    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        catalog = client.list_models()

    assert [model.id for model in catalog.data] == ["model-a", "model-b"]


@respx.mock
def test_ask_many_sequential_returns_one_response_per_prompt() -> None:
    route = respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "model": "test-model",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "pong"}, "finish_reason": "stop"}],
            },
        )
    )

    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        responses = client.ask_many_sequential(["one", "two"])

    assert len(responses) == 2
    assert route.call_count == 2


def test_a_blank_api_key_is_rejected() -> None:
    with pytest.raises(ValueError):
        GroqApiClient("   ", "test-model")
