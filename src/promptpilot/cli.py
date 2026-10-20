"""Typer command-line interface with human and machine-readable output."""

from __future__ import annotations

from dataclasses import asdict

import typer

from promptpilot import __version__
from promptpilot.benchmark import fastest_summary
from promptpilot.constants import APP_NAME
from promptpilot.exceptions import PromptPilotError
from promptpilot.services import PromptPilotService
from promptpilot.ui import (
    console,
    ask_with_spinner,
    emit_json,
    response_dict,
    show_batch,
    show_benchmark,
    show_dashboard,
    show_models,
    show_response,
    show_workers,
    stream_to_terminal,
)

app = typer.Typer(name="promptpilot", help="A Groq AI command-line workbench.", no_args_is_help=True, add_completion=False)


def _version_callback(value: bool) -> None:
    """Print the installed version and exit."""
    if value:
        console.print(f"[bold cyan]{APP_NAME}[/bold cyan] {__version__}")
        raise typer.Exit()


@app.callback()
def root(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit one JSON document for automation."),
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the installed version and exit.",
    ),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


def wants_json(ctx: typer.Context) -> bool:
    return bool(ctx.obj and ctx.obj.get("json"))


def service() -> PromptPilotService:
    return PromptPilotService()


def _fail(ctx: typer.Context, error: Exception) -> None:
    """Report an error in the format the caller asked for."""
    if wants_json(ctx):
        emit_json({"error": str(error), "type": type(error).__name__})
    else:
        console.print(f"[bold red]Error:[/bold red] {error}")
    raise typer.Exit(code=1) from error


@app.command()
def ask(
    ctx: typer.Context,
    prompt: str = typer.Argument(...),
    model: str | None = typer.Option(None, "--model", "-m"),
    stream: bool = typer.Option(False, "--stream/--no-stream", help="Receive SSE token deltas immediately."),
) -> None:
    """Send one prompt, optionally as a real streamed response."""
    try:
        current = service()
        if stream:
            if wants_json(ctx):
                text = current.stream(prompt, model=model)
                emit_json({"model": model or current.config.model, "text": text, "streamed": True})
            else:
                stream_to_terminal(current, prompt, model=model)
            return
        response = ask_with_spinner(current, prompt, model=model) if not wants_json(ctx) else current.ask(prompt, model=model)
        emit_json(response_dict(response)) if wants_json(ctx) else show_response(response)
    except PromptPilotError as error:
        _fail(ctx, error)


@app.command()
def batch(ctx: typer.Context, prompts: list[str] = typer.Argument(...), model: str | None = typer.Option(None, "--model", "-m")) -> None:
    """Run multiple prompts concurrently with asyncio.gather."""
    if len(prompts) < 2:
        raise typer.BadParameter("provide at least two prompts")
    try:
        results = service().ask_many(prompts, model=model)
        if wants_json(ctx):
            emit_json([response_dict(result) if hasattr(result, "text") else {"error": str(result)} for result in results])
        else:
            show_batch(results)
    except PromptPilotError as error:
        _fail(ctx, error)


@app.command("models")
def models(ctx: typer.Context) -> None:
    """List the live model catalog returned by Groq."""
    try:
        result = service().list_models()
        emit_json([item.model_dump() for item in result]) if wants_json(ctx) else show_models(result)
    except PromptPilotError as error:
        _fail(ctx, error)


@app.command()
def dashboard(ctx: typer.Context) -> None:
    """Show local quota and usage statistics."""
    result = service().dashboard()
    emit_json(result) if wants_json(ctx) else show_dashboard(result)


@app.command()
def benchmark(
    ctx: typer.Context,
    models: list[str] = typer.Option(..., "--model", "-m", help="Repeat the benchmark for each model."),
    prompt: str = typer.Option("Reply with the single word OK.", "--prompt", "-p"),
    rounds: int = typer.Option(3, "--rounds", min=1, max=20),
) -> None:
    """Compare end-to-end latency for one prompt across models."""
    try:
        result = service().benchmark(models, prompt, rounds)
        if wants_json(ctx):
            emit_json([item.to_dict() for item in result])
            return
        show_benchmark(result)
        fastest = fastest_summary(result)
        if fastest is not None:
            console.print(f"[bold green]Fastest:[/bold green] {fastest.model}")
    except (PromptPilotError, ValueError) as error:
        _fail(ctx, error)


@app.command("set-key")
def set_key(api_key: str | None = typer.Option(None, prompt=True, hide_input=True)) -> None:
    """Save a personal Groq API key locally."""
    if api_key is None:
        raise typer.BadParameter("an API key is required")
    service().set_user_key(api_key)
    console.print("[green]Your Groq API key was saved locally.[/green]")


@app.command("set-model")
def set_model(model: str = typer.Argument(...)) -> None:
    """Persist the preferred model ID."""
    service().set_model(model)
    console.print(f"[green]Preferred model set to {model}.[/green]")


@app.command("reset-demo")
def reset_demo() -> None:
    service().reset_demo()
    console.print("[green]Local demo counter reset.[/green]")


@app.command("clear-stats")
def clear_stats() -> None:
    service().clear_stats()
    console.print("[green]Statistics cleared.[/green]")


@app.command()
def probe(ctx: typer.Context, models_to_probe: list[str] = typer.Argument(...)) -> None:
    """Demonstrate a thread pool with independent tiny API requests."""
    try:
        result = service().probe_models(models_to_probe)
        emit_json([asdict(item) for item in result]) if wants_json(ctx) else show_workers(result)
    except PromptPilotError as error:
        _fail(ctx, error)


def main() -> None:
    app()


if __name__ == "__main__":
    main()


__all__ = ["app", "main"]
