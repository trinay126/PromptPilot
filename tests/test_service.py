import pytest

from promptpilot.exceptions import MissingAPIKeyError
from promptpilot.schemas import ChatMessage, ChatResponse, Choice, ChoiceMessage, PromptStat, Usage


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


class FakeClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.requests = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def ask(self, prompt, model=None):
        self.requests.append(prompt)
        return fake_response()

    def stream(self, prompt, model=None, on_token=None):
        text = "Hello from a fake client."
        if on_token:
            on_token(text)
        return text

    def build_request(self, messages, model=None):
        from promptpilot.schemas import ChatRequest

        return ChatRequest(model=model or "test-model", messages=messages)

    def chat(self, request):
        return fake_response()


def test_service_uses_dependency_injected_client(monkeypatch, service) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "user-key-for-tests")
    monkeypatch.setattr("promptpilot.services.GroqApiClient", FakeClient)
    response = service.ask("  hello   world ")

    assert response.text == "Hello from a fake client."
    assert service.stats_store.summary()["requests"] == 1


def test_service_records_the_prompt_and_latency(monkeypatch, service) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "user-key-for-tests")
    monkeypatch.setattr("promptpilot.services.GroqApiClient", FakeClient)

    service.ask("hello")

    records = service.stats_store.all()
    assert records[0].prompt_chars == len("hello")
    assert records[0].prompt_preview == "hello"
    assert records[0].latency_ms >= 0
    assert records[0].success is True


def test_service_raises_when_no_key_is_configured(monkeypatch, service) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError):
        service.ask("hello")


def test_service_rejects_a_blank_prompt(service) -> None:
    with pytest.raises(ValueError):
        service.ask("   ")


def test_service_streams_and_records_the_response(monkeypatch, service) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "user-key-for-tests")
    monkeypatch.setattr("promptpilot.services.GroqApiClient", FakeClient)
    received: list[str] = []

    text = service.stream("hello", on_token=received.append)

    assert text == "Hello from a fake client."
    assert received == ["Hello from a fake client."]
    assert service.stats_store.summary()["requests"] == 1


def test_service_sends_earlier_turns_as_context(monkeypatch, service) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "user-key-for-tests")
    captured = {}

    class RecordingClient(FakeClient):
        def chat(self, request):
            captured["messages"] = request.messages
            return fake_response()

    monkeypatch.setattr("promptpilot.services.GroqApiClient", RecordingClient)
    history = [
        ChatMessage(role="user", content="first question"),
        ChatMessage(role="assistant", content="first answer"),
    ]

    service.ask_with_history("second question", history)

    roles = [message.role for message in captured["messages"]]
    assert roles == ["system", "user", "assistant", "user"]
    assert captured["messages"][-1].content == "second question"


def test_service_dashboard_reports_paths_and_key_state(service) -> None:
    dashboard = service.dashboard()

    assert dashboard["model"] == "test-model"
    assert dashboard["stats"]["requests"] == 0
    assert dashboard["config_path"].endswith("config.json")
    assert dashboard["stats_path"].endswith("stats.jsonl")
    assert "has_api_key" in dashboard
    assert "api_key_source" in dashboard


def test_service_persists_the_user_key(service) -> None:
    service.set_user_key("gsk_live_key_value")

    assert service.config.api_key == "gsk_live_key_value"
    assert service.config_store.load().api_key == "gsk_live_key_value"


def test_service_rejects_a_short_api_key(service) -> None:
    with pytest.raises(ValueError):
        service.set_user_key("short")


def test_service_persists_the_preferred_model(service) -> None:
    service.set_model("llama-3.3-70b-versatile")

    assert service.config.model == "llama-3.3-70b-versatile"
    assert service.config_store.load().model == "llama-3.3-70b-versatile"


def test_service_rejects_a_blank_model(service) -> None:
    with pytest.raises(ValueError):
        service.set_model(" ")


def test_service_history_returns_recent_prompts(monkeypatch, service) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "user-key-for-tests")
    monkeypatch.setattr("promptpilot.services.GroqApiClient", FakeClient)

    service.ask("first")
    service.ask("second")

    records = service.history(limit=5)

    assert len(records) == 2
    assert records[-1].prompt_preview == "second"


def test_service_clears_the_statistics(service) -> None:
    service.stats_store.record(
        PromptStat(
            model="test-model",
            prompt_chars=1,
            response_chars=1,
            latency_ms=1.0,
        )
    )

    service.clear_stats()

    assert service.stats_store.all() == []
