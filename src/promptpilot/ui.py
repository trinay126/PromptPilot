"""Rich terminal presentation plus plain JSON serialization for automation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, is_dataclass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from promptpilot.benchmark import BenchmarkSummary
from promptpilot.schemas import ChatResponse, ModelInfo
from promptpilot.utils import truncate
from promptpilot.workers import WorkerResult

console = Console()


def show_banner() -> None:
    console.print(Panel.fit("[bold cyan]PromptPilot[/bold cyan]\n[dim]Groq AI CLI[/dim]", border_style="cyan"))


def emit_json(value: object) -> None:
    """Print valid JSON without Rich styling or terminal control sequences."""
    if is_dataclass(value):
        value = asdict(value)
    print(json.dumps(value, indent=2, default=str))


def response_dict(response: ChatResponse) -> dict[str, object]:
    usage = response.usage
    return {
        "model": response.model,
        "text": response.text,
        "usage": usage.model_dump() if usage else None,
    }


def ask_with_spinner(service, prompt: str, model: str | None = None) -> ChatResponse:
    with console.status("[bold cyan]PromptPilot is thinking...", spinner="dots"):
        return service.ask(prompt, model=model)


def show_response(response: ChatResponse) -> None:
    usage = response.usage
    token_text = "unknown" if usage is None else f"{usage.total_tokens} total"
    console.print(Panel(response.text, title=f"[bold green]{response.model}[/bold green]", border_style="green"))
    console.print(f"[dim]Tokens: {token_text}[/dim]")


def stream_to_terminal(service, prompt: str, model: str | None = None) -> str:
    """Print each received token immediately and return the final buffer."""
    console.print(f"[bold green]{model or service.config.model}[/bold green]\n")
    print("Assistant: ", end="", flush=True)
    text = service.stream(prompt, model=model, on_token=lambda token: print(token, end="", flush=True))
    print("\n")
    return text


def show_models(models: Iterable[ModelInfo]) -> None:
    table = Table(title="Available Groq models")
    table.add_column("Model ID", style="cyan")
    table.add_column("Owner", style="magenta")
    for model in sorted(models, key=lambda item: item.id):
        table.add_row(model.id, model.owned_by or "unknown")
    console.print(table)


def show_batch(results: list[object]) -> None:
    table = Table(title="Batch results")
    table.add_column("#", justify="right")
    table.add_column("Status")
    table.add_column("Result")
    for index, result in enumerate(results, start=1):
        if isinstance(result, ChatResponse):
            table.add_row(str(index), "[green]success[/green]", truncate(result.text, 100))
        else:
            table.add_row(str(index), "[red]error[/red]", truncate(str(result), 100))
    console.print(table)


def show_benchmark(results: list[BenchmarkSummary]) -> None:
    table = Table(title="Groq model benchmark")
    for column in ("Model", "Success", "Average", "Median", "P95", "Min", "Max"):
        table.add_column(column)
    for result in results:
        table.add_row(
            result.model,
            f"{result.successful}/{result.rounds}",
            f"{result.average_ms:.2f} ms",
            f"{result.median_ms:.2f} ms",
            f"{result.p95_ms:.2f} ms",
            f"{result.min_ms:.2f} ms",
            f"{result.max_ms:.2f} ms",
        )
    console.print(table)


def show_workers(results: list[WorkerResult]) -> None:
    table = Table(title="Thread worker results")
    for column in ("Item", "Status", "Latency", "Output"):
        table.add_column(column)
    for result in results:
        table.add_row(
            result.item,
            "[green]success[/green]" if result.error is None else "[red]error[/red]",
            f"{result.elapsed_ms:.1f} ms",
            truncate(str(result.value if result.error is None else result.error), 80),
        )
    console.print(table)


def show_dashboard(data: dict[str, object]) -> None:
    table = Table(title="PromptPilot dashboard")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")
    quota = data["quota"]
    stats = data["stats"]
    rows = {
        "Preferred model": data["model"],
        "Demo prompts": f"{quota['used']} used / {quota['limit']} limit",
        "Demo remaining": quota["remaining"],
        "Requests": stats["requests"],
        "Successful": stats["successful"],
        "Failed": stats["failed"],
        "Average latency": f"{stats['average_latency_ms']} ms",
        "Config file": data["config_path"],
        "Stats file": data["stats_path"],
    }
    for key, value in rows.items():
        table.add_row(str(key), str(value))
    console.print(table)
