"""Tests for the Rich presentation layer and JSON serializers."""

import json
from dataclasses import dataclass

from promptpilot.benchmark import BenchmarkSample, BenchmarkSummary
from promptpilot.schemas import ChatResponse, Choice, ChoiceMessage, ModelInfo, Usage
from promptpilot.ui import emit_json, response_dict
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
