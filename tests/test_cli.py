"""Tests for the Typer command-line interface."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from promptpilot.cli import app
from promptpilot.exceptions import ConfigurationError
from promptpilot.schemas import AppConfig, ChatResponse, Choice, ChoiceMessage, ModelInfo

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


class FakeConfigStore:
    """Config store double that reports a stored key."""

    path = Path("/tmp/config.json")

    def user_api_key(self) -> str:
        return "gsk_live_key_value"

    def api_key_source(self) -> str:
        return "config file"

    def has_api_key(self) -> bool:
        return True


class FakeStatsStore:
    """Stats store double with no recorded prompts."""

    path = Path("/tmp/stats.jsonl")


class FakeService:
    """Minimal service double that records the calls the CLI makes."""

    def __init__(self) -> None:
        self.config = AppConfig(model="test-model")
        self.config_store = FakeConfigStore()
        self.stats_store = FakeStatsStore()
        self.asked: list[tuple[str, str | None]] = []
        self.streamed: list[tuple[str, str | None]] = []
        self.benchmarked: list[tuple[list[str], str, int]] = []
        self.probed: list[list[str]] = []

    def ask(self, prompt: str, model: str | None = None) -> ChatResponse:
        self.asked.append((prompt, model))
        return fake_response()

    def stream(self, prompt: str, model: str | None = None, on_token=None) -> str:
        self.streamed.append((prompt, model))
        text = "Streamed from a fake client."
        if on_token:
            on_token(text)
        return text

    def ask_many(self, prompts: list[str], model: str | None = None) -> list[ChatResponse]:
        return [fake_response() for _ in prompts]

    def list_models(self):
        return []

    def history(self, limit: int = 10) -> list:
        return []

    def dashboard(self) -> dict[str, object]:
        return {
            "model": "test-model",
            "stats": {
                "requests": 1,
                "successful": 1,
                "failed": 0,
                "average_latency_ms": 12.5,
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "last_model": "test-model",
            },
            "config_path": "/tmp/config.json",
            "stats_path": "/tmp/stats.jsonl",
            "api_key_source": "config file",
            "has_api_key": True,
        }

    def benchmark(self, models: list[str], prompt: str, rounds: int = 3):
        from promptpilot.benchmark import BenchmarkSummary

        self.benchmarked.append((models, prompt, rounds))
        return [
            BenchmarkSummary(
                model=model,
                rounds=rounds,
                successful=rounds,
                failed=0,
                average_ms=1.0,
                median_ms=1.0,
                p95_ms=1.0,
                min_ms=1.0,
                max_ms=1.0,
                samples=(),
            )
            for model in models
        ]

    def probe_models(self, models: list[str]):
        from promptpilot.workers import WorkerResult

        self.probed.append(models)
        return [WorkerResult(model, "OK", None, 1.0) for model in models]

    def set_user_key(self, api_key: str) -> None:
        self.saved_key = api_key

    def set_model(self, model: str) -> None:
        self.saved_model = model

    def clear_stats(self) -> None:
        self.was_cleared = True

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
    assert payload["stats"]["requests"] == 1
    assert payload["has_api_key"] is True


def test_batch_requires_two_prompts(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["batch", "only-one"])

    assert result.exit_code != 0
    assert "at least two prompts" in result.output


def test_batch_json_mode_returns_one_entry_per_prompt(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "batch", "one", "two"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert len(payload) == 2
    assert payload[0]["text"] == "Hello from a fake client."


def test_models_json_mode_returns_a_list(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "models"])

    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_benchmark_json_mode_returns_the_summaries(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "benchmark", "--model", "model-a", "--rounds", "2"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload[0]["model"] == "model-a"
    assert fake_service.benchmarked == [(["model-a"], "Reply with the single word OK.", 2)]


def test_probe_json_mode_returns_the_worker_results(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "probe", "model-a", "model-b"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert [item["item"] for item in payload] == ["model-a", "model-b"]
    assert fake_service.probed == [["model-a", "model-b"]]


def test_config_set_key_saves_the_key(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["config", "set-key", "--api-key", "gsk_live_key_value"])

    assert result.exit_code == 0
    assert fake_service.saved_key == "gsk_live_key_value"


def test_config_set_key_can_prompt_for_the_key(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["config", "set-key"], input="gsk_live_key_value\n")

    assert result.exit_code == 0
    assert fake_service.saved_key == "gsk_live_key_value"


def test_config_set_model_saves_the_model(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["config", "set-model", "llama-3.3-70b-versatile"])

    assert result.exit_code == 0
    assert fake_service.saved_model == "llama-3.3-70b-versatile"


def test_config_show_masks_the_api_key(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert "gsk_..." in result.output
    assert "gsk_live_key_value" not in result.output


def test_config_show_json_mode_is_machine_readable(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "config", "show"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["model"] == "test-model"
    assert payload["api_key_source"] == "config file"


def test_config_path_prints_both_locations(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "config", "path"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["config_path"].endswith("config.json")
    assert payload["stats_path"].endswith("stats.jsonl")


def test_clear_stats_removes_the_history(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["clear-stats"])

    assert result.exit_code == 0
    assert fake_service.was_cleared is True


def test_history_json_mode_returns_the_records(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["--json", "history", "--limit", "3"])

    assert result.exit_code == 0
    assert json.loads(result.output) == []


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


def test_errors_are_reported_as_text_in_human_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingService(FakeService):
        def ask(self, prompt: str, model: str | None = None) -> ChatResponse:
            raise ConfigurationError("No Groq key found.")

    monkeypatch.setattr("promptpilot.cli.service", lambda: FailingService())
    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 1
    assert "No Groq key found." in result.output


def test_completions_prints_a_bash_script() -> None:
    result = runner.invoke(app, ["completions", "bash"])

    assert result.exit_code == 0
    assert "_promptpilot_completion" in result.output
    assert "_PROMPTPILOT_COMPLETE=complete_bash" in result.output


def test_completions_prints_a_zsh_script() -> None:
    result = runner.invoke(app, ["completions", "zsh"])

    assert result.exit_code == 0
    assert "#compdef promptpilot" in result.output


def test_completions_prints_a_fish_script() -> None:
    result = runner.invoke(app, ["completions", "fish"])

    assert result.exit_code == 0
    assert "complete --command promptpilot" in result.output


def test_completions_rejects_an_unsupported_shell() -> None:
    result = runner.invoke(app, ["completions", "powershell"])

    assert result.exit_code != 0
    assert "unsupported shell" in result.output


def test_completions_json_mode_returns_the_script() -> None:
    result = runner.invoke(app, ["--json", "completions", "bash"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["shell"] == "bash"
    assert "_promptpilot_completion" in payload["script"]


def test_no_color_flag_disables_colour(monkeypatch: pytest.MonkeyPatch) -> None:
    from promptpilot import ui

    monkeypatch.setattr(ui.console, "no_color", False)
    result = runner.invoke(app, ["--no-color", "dashboard"])

    assert result.exit_code == 0
    assert ui.console.no_color is True


def test_color_flag_re_enables_colour(monkeypatch: pytest.MonkeyPatch) -> None:
    from promptpilot import ui

    monkeypatch.setattr(ui.console, "no_color", True)
    result = runner.invoke(app, ["--color", "dashboard"])

    assert result.exit_code == 0
    assert ui.console.no_color is False


def test_select_model_saves_the_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("promptpilot.cli.picker_available", lambda: True)
    monkeypatch.setattr(
        "promptpilot.cli.pick_model",
        lambda console, models, active=None: "openai/gpt-oss-120b",
    )

    result = runner.invoke(app, ["select-model"])

    assert result.exit_code == 0
    assert "openai/gpt-oss-120b" in result.output


def test_select_model_reports_cancellation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("promptpilot.cli.picker_available", lambda: True)
    monkeypatch.setattr("promptpilot.cli.pick_model", lambda console, models, active=None: None)

    result = runner.invoke(app, ["select-model"])

    assert result.exit_code == 0
    assert "No model selected" in result.output


def test_select_model_json_mode_reports_the_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("promptpilot.cli.picker_available", lambda: True)
    monkeypatch.setattr(
        "promptpilot.cli.pick_model",
        lambda console, models, active=None: "openai/gpt-oss-120b",
    )

    result = runner.invoke(app, ["--json", "select-model"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["selected"] == "openai/gpt-oss-120b"
    assert payload["cancelled"] is False


def test_models_select_flag_opens_the_picker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("promptpilot.cli.picker_available", lambda: True)
    monkeypatch.setattr(
        "promptpilot.cli.pick_model",
        lambda console, models, active=None: "openai/gpt-oss-120b",
    )

    result = runner.invoke(app, ["models", "--select"])

    assert result.exit_code == 0
    assert "openai/gpt-oss-120b" in result.output


def test_select_model_falls_back_to_a_numbered_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without a raw-capable terminal the picker degrades to a numbered list."""
    monkeypatch.setattr("promptpilot.cli.picker_available", lambda: False)

    result = runner.invoke(app, ["select-model"], input="1\n")

    assert result.exit_code == 0
    assert "No model selected." not in result.output


def test_select_model_fallback_handles_an_invalid_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("promptpilot.cli.picker_available", lambda: False)

    result = runner.invoke(app, ["select-model"], input="not-a-number\n")

    assert result.exit_code == 0
    assert "No model selected." in result.output


def test_select_model_fallback_rejects_an_out_of_range_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("promptpilot.cli.picker_available", lambda: False)

    result = runner.invoke(app, ["select-model"], input="999\n")

    assert result.exit_code == 0
    assert "No model selected." in result.output


def test_benchmark_without_a_model_uses_the_preferred_model(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["benchmark"])

    assert result.exit_code == 0
    assert fake_service.benchmarked[0][0] == ["test-model"]


def test_benchmark_with_explicit_models(fake_service: FakeService) -> None:
    result = runner.invoke(app, ["benchmark", "-m", "model-a", "-m", "model-b"])

    assert result.exit_code == 0
    assert fake_service.benchmarked[0][0] == ["model-a", "model-b"]


def test_benchmark_all_uses_the_live_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    double = FakeService()
    double.list_models = lambda: [
        ModelInfo(id="model-a", owned_by="OpenAI"),
        ModelInfo(id="model-b", owned_by="OpenAI"),
    ]
    monkeypatch.setattr("promptpilot.cli.service", lambda: double)

    result = runner.invoke(app, ["benchmark", "--all", "--rounds", "1"])

    assert result.exit_code == 0
    assert double.benchmarked[0][0] == ["model-a", "model-b"]


def test_benchmark_all_asks_before_a_large_run(monkeypatch: pytest.MonkeyPatch) -> None:
    double = FakeService()
    double.list_models = lambda: [
        ModelInfo(id=f"model-{index}", owned_by="OpenAI") for index in range(30)
    ]
    monkeypatch.setattr("promptpilot.cli.service", lambda: double)

    result = runner.invoke(app, ["benchmark", "--all", "--rounds", "3"], input="n\n")

    assert result.exit_code == 0
    assert "Benchmark cancelled." in result.output
    assert double.benchmarked == []


def test_usage_error_shows_a_working_example() -> None:
    result = runner.invoke(app, ["config", "set-model"])

    assert result.exit_code == 2
    assert "promptpilot config set-model llama-3.3-70b-versatile" in result.output


def test_unknown_command_reports_a_suggestion() -> None:
    result = runner.invoke(app, ["bencmark"])

    assert result.exit_code == 2
    assert "benchmark" in result.output
