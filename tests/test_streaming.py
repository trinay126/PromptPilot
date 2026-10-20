import httpx
import pytest
import respx

from promptpilot.clients import GroqApiClient
from promptpilot.exceptions import GroqAPIError, SchemaError

STREAM_EVENTS = (
    'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
    'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n'
    "data: [DONE]\n\n"
)


@respx.mock
def test_sse_stream_yields_each_delta() -> None:
    events = (
        'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, headers={"content-type": "text/event-stream"}, text=events)
    )

    received: list[str] = []
    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        result = client.stream("say hello", on_token=received.append)

    assert received == ["Hel", "lo"]
    assert result == "Hello"


@respx.mock
def test_stream_request_asks_the_api_for_a_streamed_response() -> None:
    route = respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(
            200, headers={"content-type": "text/event-stream"}, text=STREAM_EVENTS
        )
    )

    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        client.stream("say hello")

    request = route.calls.last.request
    assert request.content and b'"stream":true' in request.content


@respx.mock
def test_stream_chat_skips_events_without_content() -> None:
    events = (
        'data: {"choices":[{"delta":{}}]}\n\n'
        'data: {"choices":[]}\n\n'
        'data: {"choices":[{"delta":{"content":"ok"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, headers={"content-type": "text/event-stream"}, text=events)
    )

    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        chunks = list(client.stream_chat(client._build_request("hello", stream=True)))

    assert chunks == ["ok"]


@respx.mock
def test_malformed_streaming_json_raises_a_schema_error() -> None:
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(
            200, headers={"content-type": "text/event-stream"}, text="data: {not json}\n\n"
        )
    )

    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        with pytest.raises(SchemaError):
            client.stream("say hello")


@respx.mock
def test_streaming_error_status_is_translated() -> None:
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(429, text="rate limited")
    )

    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        with pytest.raises(GroqAPIError) as caught:
            client.stream("say hello")

    assert caught.value.status_code == 429
