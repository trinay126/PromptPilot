"""Rich terminal presentation plus plain JSON serialization for automation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, is_dataclass

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from promptpilot.benchmark import BenchmarkSummary
from promptpilot.constants import APP_NAME, APP_TAGLINE
from promptpilot.schemas import ChatResponse, ModelInfo, PromptStat
from promptpilot.utils import format_latency, mask_secret, truncate
from promptpilot.workers import WorkerResult

THEME = Theme(
    {
        "brand": "bold cyan",
        "brand.dim": "dim cyan",
        "ok": "bold green",
        "warn": "bold yellow",
        "err": "bold red",
        "muted": "dim",
        "key": "bold magenta",
        "value": "bold white",
        "rule": "grey50",
    }
)

console = Console(theme=THEME)
error_console = Console(theme=THEME, stderr=True)


def emit_json(value: object) -> None:
    """Print valid JSON without Rich styling or terminal control sequences."""
    if is_dataclass(value):
        value = asdict(value)
    print(json.dumps(value, indent=2, default=str))


def show_banner() -> None:
    """Print the application banner."""
    console.print(
        Panel.fit(
            Group(
                Text(APP_NAME, style="brand"),
                Text(APP_TAGLINE, style="brand.dim"),
                Text("by Chadalavada Trinay Sai", style="muted"),
            ),
            border_style="cyan",
            padding=(1, 4),
        )
    )


def show_rule(title: str) -> None:
    """Draw a titled separator between sections."""
    console.print(Rule(title, style="rule"))


def response_dict(response: ChatResponse) -> dict[str, object]:
    """Convert a completion into a JSON-friendly dictionary."""
    usage = response.usage
    return {
        "model": response.model,
        "text": response.text,
        "usage": usage.model_dump() if usage else None,
    }


def _usage_line(response: ChatResponse) -> str:
    usage = response.usage
    if usage is None:
        return "tokens unknown"
    return (
        f"{usage.prompt_tokens} prompt + {usage.completion_tokens} completion"
        f" = {usage.total_tokens} total"
    )


def show_response(response: ChatResponse) -> None:
    """Render a completed answer with a metadata footer."""
    console.print(
        Panel(
            Markdown(response.text),
            title=f"[ok]{response.model}[/ok]",
            subtitle=f"[muted]{_usage_line(response)}[/muted]",
            border_style="green",
            padding=(1, 2),
        )
    )


def show_error(message: str, hint: str | None = None) -> None:
    """Render an error with an optional actionable hint."""
    body = Text(message, style="err")
    if hint:
        body.append("\n\n")
        body.append(hint, style="muted")
    error_console.print(Panel(body, border_style="red", title="[err]Error[/err]", padding=(1, 2)))


def show_success(message: str) -> None:
    """Render a short confirmation message."""
    console.print(f"[ok]OK[/ok]  {message}")


def show_info(message: str) -> None:
    """Render a neutral informational message."""
    console.print(f"[muted]{message}[/muted]")


def ask_with_spinner(service, prompt: str, model: str | None = None) -> ChatResponse:
    """Run a request behind a spinner so the terminal never looks frozen."""
    with console.status("[brand]PromptPilot is thinking...", spinner="dots"):
        return service.ask(prompt, model=model)


def stream_to_terminal(service, prompt: str, model: str | None = None) -> str:
    """Print each received token immediately and return the final buffer."""
    active_model = model or service.config.model
    console.print(f"[ok]{active_model}[/ok]")
    console.print()

    def on_token(token: str) -> None:
        console.print(token, end="", markup=False, highlight=False, soft_wrap=True)

    text = service.stream(prompt, model=model, on_token=on_token)
    console.print()
    return text


def show_models(models: Iterable[ModelInfo], active: str | None = None) -> None:
    """Render the live model catalog, marking the active model."""
    table = Table(
        title="Available Groq models",
        title_style="brand",
        header_style="brand.dim",
        border_style="rule",
        expand=False,
    )
    table.add_column("", width=1)
    table.add_column("Model ID", style="cyan")
    table.add_column("Owner", style="magenta")
    for model in sorted(models, key=lambda item: item.id):
        is_active = active is not None and model.id == active
        table.add_row(
            "[ok]*[/ok]" if is_active else " ",
            f"[value]{model.id}[/value]" if is_active else model.id,
            model.owned_by or "unknown",
        )
    console.print(table)
    if active:
        console.print(f"[muted]* active model   {active}[/muted]")


def show_batch(results: list[object]) -> None:
    """Render the outcome of a concurrent batch."""
    table = Table(
        title="Batch results",
        title_style="brand",
        header_style="brand.dim",
        border_style="rule",
    )
    table.add_column("#", justify="right", style="muted")
    table.add_column("Status")
    table.add_column("Result")
    for index, result in enumerate(results, start=1):
        if isinstance(result, ChatResponse):
            table.add_row(str(index), "[ok]success[/ok]", truncate(result.text, 100))
        else:
            table.add_row(str(index), "[err]error[/err]", truncate(str(result), 100))
    console.print(table)


def show_benchmark(results: list[BenchmarkSummary]) -> None:
    """Render a latency comparison across models."""
    table = Table(
        title="Groq model benchmark",
        title_style="brand",
        header_style="brand.dim",
        border_style="rule",
    )
    for column in ("Model", "Success", "Average", "Median", "P95", "Min", "Max"):
        table.add_column(column)
    for result in results:
        table.add_row(
            result.model,
            f"{result.successful}/{result.rounds}",
            format_latency(result.average_ms),
            format_latency(result.median_ms),
            format_latency(result.p95_ms),
            format_latency(result.min_ms),
            format_latency(result.max_ms),
        )
    console.print(table)


def show_workers(results: list[WorkerResult]) -> None:
    """Render thread-pool probe results."""
    table = Table(
        title="Thread worker results",
        title_style="brand",
        header_style="brand.dim",
        border_style="rule",
    )
    for column in ("Item", "Status", "Latency", "Output"):
        table.add_column(column)
    for result in results:
        table.add_row(
            result.item,
            "[ok]success[/ok]" if result.error is None else "[err]error[/err]",
            format_latency(result.elapsed_ms),
            truncate(str(result.value if result.error is None else result.error), 80),
        )
    console.print(table)


def show_dashboard(data: dict[str, object]) -> None:
    """Render the local usage dashboard."""
    stats = data["stats"]
    has_key = bool(data.get("has_api_key"))
    key_status = (
        f"[ok]configured[/ok]  ({data['api_key_source']})"
        if has_key
        else "[warn]missing[/warn]  run [value]promptpilot config set-key[/value]"
    )
    table = Table(
        title="PromptPilot dashboard",
        title_style="brand",
        header_style="brand.dim",
        border_style="rule",
        show_header=False,
    )
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value")
    rows = [
        ("API key", key_status),
        ("Preferred model", str(data["model"])),
        ("Requests", str(stats["requests"])),
        ("Successful", str(stats["successful"])),
        ("Failed", str(stats["failed"])),
        ("Average latency", format_latency(float(stats["average_latency_ms"]))),
        ("Tokens (prompt)", str(stats["prompt_tokens"])),
        ("Tokens (completion)", str(stats["completion_tokens"])),
        ("Config file", str(data["config_path"])),
        ("Stats file", str(data["stats_path"])),
    ]
    for key, value in rows:
        table.add_row(key, value)
    console.print(table)


def show_config(data: dict[str, object]) -> None:
    """Render the resolved configuration, masking the API key."""
    table = Table(
        title="PromptPilot configuration",
        title_style="brand",
        header_style="brand.dim",
        border_style="rule",
        show_header=False,
    )
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value")
    table.add_row("API key", str(data["api_key"]))
    table.add_row("Key source", str(data["api_key_source"]))
    table.add_row("Model", str(data["model"]))
    table.add_row("Timeout", f"{data['timeout_seconds']} s")
    table.add_row("Config file", str(data["config_path"]))
    table.add_row("Stats file", str(data["stats_path"]))
    console.print(table)


def show_history(records: list[PromptStat]) -> None:
    """Render the most recent prompts."""
    if not records:
        console.print("[muted]No prompts recorded yet.[/muted]")
        return
    table = Table(
        title="Recent prompts",
        title_style="brand",
        header_style="brand.dim",
        border_style="rule",
    )
    table.add_column("When", style="muted", no_wrap=True)
    table.add_column("Model", style="cyan")
    table.add_column("Prompt")
    table.add_column("Latency", justify="right")
    table.add_column("Status")
    for record in records:
        table.add_row(
            record.timestamp.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            record.model,
            truncate(record.prompt_preview or "-", 60),
            format_latency(record.latency_ms),
            "[ok]ok[/ok]" if record.success else "[err]failed[/err]",
        )
    console.print(table)


def show_setup_intro() -> None:
    """Explain how to obtain and store a Groq API key."""
    console.print(
        Panel(
            Group(
                Text("PromptPilot needs your own Groq API key.", style="value"),
                Text(),
                Text("1.  Create a key at ", style="muted"),
                Text("   https://console.groq.com/keys", style="key"),
                Text("2.  Run ", style="muted"),
                Text("   promptpilot config set-key", style="key"),
                Text("   and paste the key when prompted.", style="muted"),
                Text(),
                Text(
                    "Your key is stored in your user config directory and is never "
                    "committed to the repository.",
                    style="muted",
                ),
            ),
            title="[brand]Setup[/brand]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def show_chat_help() -> None:
    """List the slash commands available inside an interactive chat."""
    table = Table(
        title="Chat commands",
        title_style="brand",
        header_style="brand.dim",
        border_style="rule",
        show_header=False,
    )
    table.add_column("Command", style="key", no_wrap=True)
    table.add_column("What it does")
    table.add_row("/help", "Show this list")
    table.add_row("/history", "Show how many messages are in the conversation")
    table.add_row("/reset", "Clear the conversation history")
    table.add_row("/exit", "Leave the session")
    console.print(table)


def show_key_summary(api_key: str | None, source: str) -> None:
    """Render where the active API key comes from."""
    if api_key:
        console.print(f"[ok]API key[/ok]  {mask_secret(api_key)}  [muted]({source})[/muted]")
    else:
        console.print(
            "[warn]No API key configured.[/warn] Run [value]promptpilot config set-key[/value]."
        )


__all__ = [
    "THEME",
    "ask_with_spinner",
    "console",
    "emit_json",
    "error_console",
    "response_dict",
    "show_banner",
    "show_batch",
    "show_benchmark",
    "show_chat_help",
    "show_config",
    "show_dashboard",
    "show_error",
    "show_history",
    "show_info",
    "show_key_summary",
    "show_models",
    "show_response",
    "show_rule",
    "show_setup_intro",
    "show_success",
    "show_workers",
    "stream_to_terminal",
]
