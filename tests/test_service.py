from pathlib import Path

from promptpilot.schemas import ChatResponse, Choice, ChoiceMessage, Usage


def fake_response() -> ChatResponse:
    return ChatResponse(
        id="test-id",
        model="test-model",
        choices=[
            Choice(
                index=0,
                message=ChoiceMessage(role="assistant", content="Hello from a fake client."),
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=3, completion_tokens=5, total_tokens=8),
    )


def test_service_uses_dependency_injected_client(monkeypatch, service) -> None:
    monkeypatch.setenv("PROMPTPILOT_DEMO_API_KEY", "demo-key-for-tests")

    class FakeClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def ask(self, prompt, model=None):
            return fake_response()

    monkeypatch.setattr("promptpilot.services.GroqApiClient", FakeClient)
    response = service.ask("  hello   world ")

    assert response.text == "Hello from a fake client."
    assert service.quota.used == 1
    assert service.stats_store.summary()["requests"] == 1
