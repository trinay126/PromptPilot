import httpx
import respx

from promptpilot.clients import GroqApiClient


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
