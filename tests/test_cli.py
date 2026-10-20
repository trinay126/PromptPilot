"""Tests for the Typer command-line interface."""

import json

import pytest
from typer.testing import CliRunner

from promptpilot.cli import app
from promptpilot.exceptions import ConfigurationError
from promptpilot.schemas import AppConfig, ChatResponse, Choice, ChoiceMessage

runner = CliRunner()


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
    )


class FakeService:
    """Minimal service double that records the calls the CLI makes."""

    def __init__(self) -> None:
        self.config = AppConfig(model="test-model")
        self.asked: list[tuple[str, str | None]] = []
        self.streamed: list[tuple[str, str | None]] = []

    def ask(self, prompt: str, model: str | None = None) -> ChatResponse:
        self.asked.append((prompt, model))
        return fake_response()

    def stream(self, prompt: str, model: str | None = None, on_token=None) -> str:
        self.streamed.append((prompt, model))
        text = "Streamed from a fake client."
        if on_token:
            on_token(text)
        return text

    def list_models(self):
        return []

    def dashboard(self) -> dict[str, object]:
        return {
            "model": "test-model",
            "quota": {"limit": 10, "used": 1, "remaining": 9},
            "stats": {
                "requests": 1,
                "successful": 1,
                "failed": 0,
                "average_latency_ms": 12.5,
            },
            "config_path": "/tmp/config.json",
            "stats_path": "/tmp/stats.jsonl",
        }


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeService:
    """Replace the CLI service factory with a deterministic double."""
    double = FakeService()
    monkeypatch.setattr("promptpilot.cli.service", lambda: double)
    return double


def test_help_lists_every_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("ask", "batch", "models", "dashboard", "benchmark"):
        assert command in result.output


def test_version_option_prints_the_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "PromptPilot" in result.output


def test_ask_json_mode_emits_one_json_document(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "ask", "hello"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["model"] == "test-model"
    assert payload["text"] == "Hello from a fake client."


def test_ask_passes_the_model_option(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "ask", "hello", "--model", "other-model"])

    assert result.exit_code == 0
    assert fake_service.asked == [("hello", "other-model")]


def test_ask_stream_json_mode_reports_the_streamed_flag(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "ask", "--stream", "hello"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["streamed"] is True
    assert payload["text"] == "Streamed from a fake client."


def test_dashboard_json_mode_is_machine_readable(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "dashboard"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["model"] == "test-model"
    assert payload["quota"]["remaining"] == 9


def test_batch_requires_two_prompts(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["batch", "only-one"])

    assert result.exit_code != 0
    assert "at least two prompts" in result.output


def test_errors_are_reported_as_json_in_json_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingService(FakeService):
        def ask(self, prompt: str, model: str | None = None) -> ChatResponse:
            raise ConfigurationError("No Groq key found.")

    monkeypatch.setattr("promptpilot.cli.service", lambda: FailingService())
    result = runner.invoke(app, ["--json", "ask", "hello"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["type"] == "ConfigurationError"
    assert "No Groq key found." in payload["error"]
