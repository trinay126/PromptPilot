import httpx
import respx

from promptpilot.clients import GroqApiClient


@respx.mock
def test_sse_stream_yields_each_delta() -> None:
    events = """data: {\"choices\":[{\"delta\":{\"content\":\"Hel\"}}]}\n\ndata: {\"choices\":[{\"delta\":{\"content\":\"lo\"}}]}\n\ndata: [DONE]\n\n"""
    respx.post("https://api.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, headers={"content-type": "text/event-stream"}, text=events)
    )

    received: list[str] = []
    with GroqApiClient("test-key", "test-model", base_url="https://api.test/v1") as client:
        result = client.stream("say hello", on_token=received.append)

    assert received == ["Hel", "lo"]
    assert result == "Hello"
