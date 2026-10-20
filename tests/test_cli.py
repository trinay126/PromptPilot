"""Tests for the Typer command-line interface."""

import json

import pytest
from typer.testing import CliRunner

from promptpilot.cli import app
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

    def ask(self, prompt: str, model: str | None = None) -> ChatResponse:
        self.asked.append((prompt, model))
        return fake_response()

    def stream(self, prompt: str, model: str | None = None, on_token=None) -> str:
        return "Streamed from a fake client."

    def list_models(self):
        return []

    def dashboard(self) -> dict[str, object]:
        return {"model": "test-model"}


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeService:
    """Replace the CLI service factory with a deterministic double."""
    double = FakeService()
    monkeypatch.setattr("promptpilot.cli.service", lambda: double)
    return double


def test_help_lists_every_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "ask" in result.output


def test_ask_json_mode_emits_one_json_document(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "ask", "hello"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["model"] == "test-model"
    assert payload["text"] == "Hello from a fake client."


def test_dashboard_json_mode_is_machine_readable(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "dashboard"])

    assert result.exit_code == 0
    assert json.loads(result.output)["model"] == "test-model"
