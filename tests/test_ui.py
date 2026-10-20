"""Tests for the Rich presentation layer and JSON serializers."""

import json
from dataclasses import dataclass

from promptpilot.benchmark import BenchmarkSample, BenchmarkSummary
from promptpilot.schemas import ChatResponse, Choice, ChoiceMessage, ModelInfo, Usage
from promptpilot.ui import (
    emit_json,
    response_dict,
    show_batch,
    show_benchmark,
    show_dashboard,
    show_models,
    show_response,
    show_workers,
)
from promptpilot.workers import WorkerResult


def test_emit_json_prints_a_valid_document(capsys) -> None:
    emit_json({"model": "test-model", "text": "hello"})

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"model": "test-model", "text": "hello"}


def test_emit_json_serializes_dataclasses(capsys) -> None:
    @dataclass
    class Payload:
        name: str
        count: int

    emit_json(Payload(name="promptpilot", count=2))

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"name": "promptpilot", "count": 2}


def test_emit_json_never_writes_ansi_escape_codes(capsys) -> None:
    emit_json({"text": "plain"})

    captured = capsys.readouterr()
    assert "\x1b[" not in captured.out


def test_response_dict_includes_usage_when_present() -> None:
    response = ChatResponse(
        id="test-id",
        model="test-model",
        choices=[
            Choice(index=0, message=ChoiceMessage(role="assistant", content="Hello"))
        ],
        usage=Usage(prompt_tokens=2, completion_tokens=3, total_tokens=5),
    )

    payload = response_dict(response)

    assert payload["model"] == "test-model"
    assert payload["text"] == "Hello"
    assert payload["usage"]["total_tokens"] == 5


def test_response_dict_reports_missing_usage_as_none() -> None:
    response = ChatResponse(
        id="test-id",
        model="test-model",
        choices=[
            Choice(index=0, message=ChoiceMessage(role="assistant", content="Hello"))
        ],
    )

    assert response_dict(response)["usage"] is None


def test_show_models_lists_every_model(capsys) -> None:
    show_models([ModelInfo(id="model-b", owned_by="groq"), ModelInfo(id="model-a")])

    captured = capsys.readouterr()
    assert "model-a" in captured.out
    assert "model-b" in captured.out


def test_show_batch_marks_failures(capsys) -> None:
    show_batch([ChatResponse(
        id="test-id",
        model="test-model",
        choices=[Choice(index=0, message=ChoiceMessage(role="assistant", content="ok"))],
    ), RuntimeError("boom")])

    captured = capsys.readouterr()
    assert "success" in captured.out
    assert "error" in captured.out


def test_show_benchmark_renders_the_latency_columns(capsys) -> None:
    show_benchmark([BenchmarkSummary(
        model="test-model",
        rounds=1,
        successful=1,
        failed=0,
        average_ms=1.5,
        median_ms=1.5,
        p95_ms=1.5,
        min_ms=1.5,
        max_ms=1.5,
        samples=(),
    )])

    captured = capsys.readouterr()
    assert "test-model" in captured.out
    assert "1.50 ms" in captured.out


def test_show_workers_reports_the_error_column(capsys) -> None:
    show_workers(
        [
            WorkerResult("item-a", "value", None, 2.0),
            WorkerResult("item-b", None, "failed", 3.0),
        ]
    )

    captured = capsys.readouterr()
    assert "item-a" in captured.out
    assert "item-b" in captured.out


def test_show_dashboard_renders_every_metric(capsys) -> None:
    show_dashboard({
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
    })

    captured = capsys.readouterr()
    assert "test-model" in captured.out
    assert "/tmp/stats.jsonl" in captured.out


def test_show_response_falls_back_when_usage_is_missing(capsys) -> None:
    show_response(ChatResponse(
        id="test-id",
        model="test-model",
        choices=[Choice(index=0, message=ChoiceMessage(role="assistant", content="Hello"))],
    ))

    captured = capsys.readouterr()
    assert "unknown" in captured.out


def test_benchmark_summary_serializes_samples() -> None:
    summary = BenchmarkSummary(
        model="test-model",
        rounds=1,
        successful=1,
        failed=0,
        average_ms=1.0,
        median_ms=1.0,
        p95_ms=1.0,
        min_ms=1.0,
        max_ms=1.0,
        samples=(BenchmarkSample(model="test-model", run=1, latency_ms=1.0, success=True),),
    )

    payload = summary.to_dict()

    assert payload["samples"][0]["success"] is True


def test_worker_result_reports_success() -> None:
    assert WorkerResult("item", "value", None, 1.0).succeeded is True
    assert WorkerResult("item", None, "failed", 1.0).succeeded is False
