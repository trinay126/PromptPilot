"""Tests for the interactive chat session."""

import json

import pytest
from typer.testing import CliRunner

from promptpilot.cli import app
from promptpilot.exceptions import MissingAPIKeyError
from promptpilot.schemas import ChatResponse, Choice, ChoiceMessage

runner = CliRunner()


def fake_response(text: str = "Hello from a fake client.") -> ChatResponse:
    return ChatResponse(
        id="test-id",
        model="test-model",
        choices=[
            Choice(
                index=0,
                message=ChoiceMessage(role="assistant", content=text),
                finish_reason="stop",
            )
        ],
    )


class FakeConfigStore:
    path = None

    def __init__(self, has_key: bool = True) -> None:
        self._has_key = has_key

    def user_api_key(self) -> str | None:
        return "gsk_live_key_value" if self._has_key else None

    def api_key_source(self) -> str:
        return "config file" if self._has_key else "not configured"

    def has_api_key(self) -> bool:
        return self._has_key


class FakeService:
    def __init__(self, has_key: bool = True) -> None:
        self.config_store = FakeConfigStore(has_key)
        self.turns: list[tuple[str, list]] = []

    def ask_with_history(self, prompt, history, model=None):
        self.turns.append((prompt, list(history)))
        return fake_response()


@pytest.fixture
def chat_service(monkeypatch: pytest.MonkeyPatch) -> FakeService:
    double = FakeService()
    monkeypatch.setattr("promptpilot.cli.service", lambda: double)
    return double


def test_chat_requires_an_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    double = FakeService(has_key=False)
    monkeypatch.setattr("promptpilot.cli.service", lambda: double)

    result = runner.invoke(app, ["chat"])

    assert result.exit_code == 1
    assert "API key" in result.output


def test_chat_sends_the_prompt_and_keeps_history(chat_service: FakeService) -> None:
    result = runner.invoke(app, ["chat"], input="hello\n/exit\n")

    assert result.exit_code == 0
    assert chat_service.turns[0][0] == "hello"
    assert chat_service.turns[0][1] == []


def test_chat_passes_earlier_turns_as_context(chat_service: FakeService) -> None:
    result = runner.invoke(app, ["chat"], input="first\nsecond\n/exit\n")

    assert result.exit_code == 0
    assert len(chat_service.turns) == 2
    assert chat_service.turns[1][1][0].role == "user"
    assert chat_service.turns[1][1][0].content == "first"


def test_chat_reset_clears_the_conversation(chat_service: FakeService) -> None:
    result = runner.invoke(app, ["chat"], input="first\n/reset\nsecond\n/exit\n")

    assert result.exit_code == 0
    assert chat_service.turns[1][1] == []


def test_chat_help_lists_the_commands(chat_service: FakeService) -> None:
    result = runner.invoke(app, ["chat"], input="/help\n/exit\n")

    assert result.exit_code == 0
    assert "/reset" in result.output
    assert "/exit" in result.output


def test_chat_history_reports_the_message_count(chat_service: FakeService) -> None:
    result = runner.invoke(app, ["chat"], input="/history\n/exit\n")

    assert result.exit_code == 0
    assert "message(s)" in result.output


def test_chat_ignores_blank_input(chat_service: FakeService) -> None:
    result = runner.invoke(app, ["chat"], input="\n   \n/exit\n")

    assert result.exit_code == 0
    assert chat_service.turns == []


def test_chat_stops_on_an_api_error(chat_service: FakeService) -> None:
    class FailingService(FakeService):
        def ask_with_history(self, prompt, history, model=None):
            raise MissingAPIKeyError()

    chat_service.__class__ = FailingService
    result = runner.invoke(app, ["chat"], input="hello\n/exit\n")

    assert result.exit_code == 0
    assert "API key" in result.output


def test_chat_json_mode_reads_prompts_from_stdin(chat_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "chat"], input="hello\n")

    assert result.exit_code == 0
    payload = json.loads(result.output.strip().splitlines()[-1])
    assert payload["text"] == "Hello from a fake client."


def test_chat_json_mode_emits_one_object_per_prompt(chat_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "chat"], input="one\ntwo\n")

    assert result.exit_code == 0
    lines = [line for line in result.output.strip().splitlines() if line]
    assert len(lines) == 2
    assert all(json.loads(line)["text"] for line in lines)
