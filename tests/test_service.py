import pytest

from promptpilot.exceptions import ConfigurationError, QuotaExceededError
from promptpilot.schemas import ChatResponse, Choice, ChoiceMessage, PromptStat, Usage


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

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def ask(self, prompt, model=None):
        return fake_response()

    def stream(self, prompt, model=None, on_token=None):
        text = "Hello from a fake client."
        if on_token:
            on_token(text)
        return text


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


def test_service_records_a_user_prompt_without_touching_the_quota(monkeypatch, service) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "user-key-for-tests")
    monkeypatch.setattr("promptpilot.services.GroqApiClient", FakeClient)

    service.ask("hello")

    assert service.quota.used == 0
    records = service.stats_store.all()
    assert records[0].source == "user"
    assert records[0].prompt_chars == len("hello")


def test_service_raises_when_no_key_is_configured(monkeypatch, service) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("PROMPTPILOT_DEMO_API_KEY", raising=False)

    with pytest.raises(ConfigurationError):
        service.ask("hello")


def test_service_raises_when_the_demo_quota_is_exhausted(monkeypatch, service) -> None:
    monkeypatch.setenv("PROMPTPILOT_DEMO_API_KEY", "demo-key-for-tests")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    service.config.demo_prompts_used = service.config.demo_limit

    with pytest.raises(QuotaExceededError):
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


def test_service_dashboard_reports_quota_and_paths(service) -> None:
    dashboard = service.dashboard()

    assert dashboard["model"] == "test-model"
    assert dashboard["quota"]["limit"] == 10
    assert dashboard["stats"]["requests"] == 0
    assert dashboard["config_path"].endswith("config.json")
    assert dashboard["stats_path"].endswith("stats.jsonl")


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


def test_service_resets_the_demo_counter(service) -> None:
    service.quota.record_success()
    service.reset_demo()

    assert service.quota.used == 0


def test_service_clears_the_statistics(service) -> None:
    service.stats_store.record(
        PromptStat(
            model="test-model",
            prompt_chars=1,
            response_chars=1,
            latency_ms=1.0,
            source="user",
        )
    )

    service.clear_stats()

    assert service.stats_store.all() == []
