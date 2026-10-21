"""Typer command-line interface with human and machine-readable output."""

from __future__ import annotations

import os
import sys
from dataclasses import asdict

import typer
from typer._click import exceptions as click_exceptions
from typer.completion import get_completion_script

from promptpilot import __version__
from promptpilot.benchmark import fastest_summary
from promptpilot.constants import APP_NAME, APP_TAGLINE, COMPLETE_ENV_VAR, SUPPORTED_SHELLS
from promptpilot.exceptions import (
    ConfigurationError,
    GroqAPIError,
    MissingAPIKeyError,
    PromptPilotError,
)
from promptpilot.picker import pick_model, picker_available
from promptpilot.schemas import ChatMessage
from promptpilot.services import PromptPilotService
from promptpilot.ui import (
    ask_with_spinner,
    console,
    emit_json,
    emit_json_line,
    error_console,
    response_dict,
    show_banner,
    show_batch,
    show_benchmark,
    show_chat_help,
    show_config,
    show_dashboard,
    show_error,
    show_history,
    show_info,
    show_key_summary,
    show_models,
    show_response,
    show_rule,
    show_setup_intro,
    show_success,
    show_usage_error,
    show_workers,
    stream_to_terminal,
)
from promptpilot.utils import mask_secret

EPILOG = """
[bold]Examples[/bold]
  promptpilot config set-key                 store your Groq API key
  promptpilot ask "Explain Python decorators"
  promptpilot ask --stream "Write a haiku"  show tokens as they arrive
  promptpilot chat                          start an interactive session
  promptpilot --json dashboard | jq .stats  machine-readable output
"""

_COMMAND_PATH: list[str] = []


class PromptPilotGroup(typer.core.TyperGroup):
    """A command group that renders usage mistakes in the PromptPilot style."""

    def resolve_command(self, ctx, args):
        """Record the resolved command path so usage errors can name it."""
        name, command, rest = super().resolve_command(ctx, args)
        path = list(ctx.meta.get("promptpilot_path", ()))
        path.append(name)
        ctx.meta["promptpilot_path"] = path
        _COMMAND_PATH[:] = path
        return name, command, rest

    def main(self, *args, **kwargs):
        kwargs.setdefault("standalone_mode", False)
        try:
            result = super().main(*args, **kwargs)
        except BrokenPipeError:
            # The reader closed the pipe, for example `promptpilot --help | head`.
            # Point stdout at devnull so the interpreter does not report the
            # broken pipe again while shutting down, then exit quietly.
            try:
                devnull = os.open(os.devnull, os.O_WRONLY)
                os.dup2(devnull, sys.stdout.fileno())
            except (OSError, ValueError):
                pass
            raise SystemExit(141) from None
        except click_exceptions.NoArgsIsHelpError:
            # Typer already rendered the help page, so nothing left to show.
            raise SystemExit(0) from None
        except typer.Abort:
            console.print("[muted]Aborted.[/muted]")
            raise SystemExit(1) from None
        except click_exceptions.UsageError as error:
            show_usage_error(error.format_message(), _command_name(error))
            raise SystemExit(error.exit_code) from None
        except click_exceptions.ClickException as error:
            show_error(error.format_message())
            raise SystemExit(error.exit_code) from None
        if isinstance(result, int):
            raise SystemExit(result)
        return result


def _command_name(error: Exception) -> str | None:
    """Return the command path an error refers to, for example 'config set-key'."""
    context = getattr(error, "ctx", None)
    if context is not None:
        path = context.meta.get("promptpilot_path")
        if path:
            return " ".join(path)
    if _COMMAND_PATH:
        return " ".join(_COMMAND_PATH)
    return None


app = typer.Typer(
    name="promptpilot",
    help=f"{APP_NAME} — {APP_TAGLINE}.",
    epilog=EPILOG,
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,
    cls=PromptPilotGroup,
)

config_app = typer.Typer(
    name="config",
    help="Manage your local PromptPilot configuration.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    cls=PromptPilotGroup,
)
app.add_typer(config_app)


def _version_callback(value: bool) -> None:
    """Print the installed version and exit."""
    if value:
        console.print(f"[brand]{APP_NAME}[/brand] [muted]v{__version__}[/muted]")
        raise typer.Exit()


@app.callback()
def root(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False, "--json", help="Emit one JSON document for automation."
    ),
    color: bool | None = typer.Option(
        None,
        "--color/--no-color",
        help="Force colour on or off. By default the NO_COLOR environment variable is respected.",
    ),
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the installed version and exit.",
    ),
) -> None:
    """Root callback that stores global options on the context."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output
    if color is not None:
        # Rich resolves no_color when the console is built, so set it directly.
        console.no_color = not color
        error_console.no_color = not color
        if color:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = "1"


def wants_json(ctx: typer.Context) -> bool:
    """Return whether the caller asked for machine-readable output."""
    return bool(ctx.obj and ctx.obj.get("json"))


def service() -> PromptPilotService:
    """Build the application service used by every command."""
    return PromptPilotService()


def _fail(ctx: typer.Context, error: Exception) -> None:
    """Report an error in the format the caller asked for."""
    if wants_json(ctx):
        emit_json({"error": str(error), "type": type(error).__name__})
    else:
        show_error(str(error))
    raise typer.Exit(code=1) from error


def _api_error_hint(error: Exception) -> str | None:
    """Return an actionable hint for the most common API failures."""
    if isinstance(error, MissingAPIKeyError):
        return None
    if isinstance(error, GroqAPIError):
        if error.is_auth_failure:
            return "Your API key was rejected. Update it with: promptpilot config set-key"
        if error.status_code == 429:
            return "You are being rate limited. Wait a moment and try again."
        if error.status_code == 404:
            return "That model may not exist. Check the catalog with: promptpilot models"
    if isinstance(error, ConfigurationError):
        return "Store your key with: promptpilot config set-key"
    return None


def _run(ctx: typer.Context, action) -> None:
    """Run a service action, translating expected errors into friendly output."""
    try:
        action()
    except (PromptPilotError, ValueError) as error:
        if wants_json(ctx):
            _fail(ctx, error)
        hint = _api_error_hint(error)
        show_error(str(error), hint)
        raise typer.Exit(code=1) from error


@app.command()
def ask(
    ctx: typer.Context,
    prompt: str = typer.Argument(..., help="The question to send to the model."),
    model: str | None = typer.Option(None, "--model", "-m", help="Model to use."),
    stream: bool = typer.Option(
        False, "--stream/--no-stream", help="Receive SSE token deltas immediately."
    ),
) -> None:
    """Send one prompt and print the answer."""
    current = service()

    if wants_json(ctx):
        payload: dict = {}

        def perform_json() -> None:
            if stream:
                text = current.stream(prompt, model=model)
                payload.update(
                    {
                        "model": model or current.config.model,
                        "text": text,
                        "streamed": True,
                    }
                )
                return
            response = current.ask(prompt, model=model)
            payload.update(response_dict(response))

        _run(ctx, perform_json)
        emit_json(payload)
        return

    if stream:
        _run(ctx, lambda: stream_to_terminal(current, prompt, model=model))
        return

    holder: list = []

    def perform() -> None:
        holder.append(ask_with_spinner(current, prompt, model=model))

    _run(ctx, perform)
    show_response(holder[0])


@app.command()
def chat(
    ctx: typer.Context,
    model: str | None = typer.Option(None, "--model", "-m", help="Model to use."),
) -> None:
    """Start an interactive chat session that remembers the conversation."""
    current = service()
    if not current.config_store.has_api_key():
        show_setup_intro()
        raise typer.Exit(code=1)

    if wants_json(ctx):
        _chat_json(current, model=model)
        return

    show_banner()
    show_info(
        "Type a prompt and press enter. Use /help to list commands, /exit to quit."
    )
    console.print()

    history: list[ChatMessage] = []
    while True:
        try:
            user_input = typer.prompt("you", prompt_suffix=" > ")
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        command = user_input.strip()
        if not command:
            continue
        if command in {"/exit", "/quit"}:
            break
        if command == "/help":
            show_chat_help()
            continue
        if command == "/reset":
            history.clear()
            show_info("Conversation history cleared.")
            continue
        if command == "/history":
            show_info(f"{len(history)} message(s) in this conversation.")
            continue

        try:
            answer = current.ask_with_history(command, history, model=model)
        except (PromptPilotError, ValueError) as error:
            show_error(str(error), _api_error_hint(error))
            continue

        history.append(ChatMessage(role="user", content=command))
        history.append(ChatMessage(role="assistant", content=answer.text))
        show_response(answer)

    console.print("[muted]Bye.[/muted]")


def _chat_json(current: PromptPilotService, model: str | None = None) -> None:
    """Read one prompt per line from stdin and emit one JSON object per line."""
    history: list[ChatMessage] = []
    for line in sys.stdin:
        command = line.strip()
        if not command:
            continue
        try:
            answer = current.ask_with_history(command, history, model=model)
        except (PromptPilotError, ValueError) as error:
            emit_json_line({"error": str(error), "type": type(error).__name__})
            continue
        history.append(ChatMessage(role="user", content=command))
        history.append(ChatMessage(role="assistant", content=answer.text))
        emit_json_line(response_dict(answer))


@app.command()
def batch(
    ctx: typer.Context,
    prompts: list[str] = typer.Argument(..., help="Two or more prompts to run."),
    model: str | None = typer.Option(None, "--model", "-m", help="Model to use."),
) -> None:
    """Run multiple prompts concurrently with asyncio.gather."""
    if len(prompts) < 2:
        raise typer.BadParameter("provide at least two prompts")
    current = service()
    results: list = []
    _run(ctx, lambda: results.extend(current.ask_many(prompts, model=model)))
    if wants_json(ctx):
        emit_json(
            [
                response_dict(result)
                if hasattr(result, "text")
                else {"error": str(result)}
                for result in results
            ]
        )
    else:
        show_batch(results)


@app.command("models")
def models(
    ctx: typer.Context,
    select: bool = typer.Option(
        False, "--select", "-s", help="Pick a model interactively and save it."
    ),
    show_all: bool = typer.Option(
        False, "--all", help="Also show models that cannot answer a chat prompt."
    ),
) -> None:
    """List the chat models available to your account."""
    current = service()
    result: list = []
    _run(ctx, lambda: result.extend(current.list_models()))
    usable = [model for model in result if model.is_chat_capable]
    hidden = len(result) - len(usable)
    if select:
        _select_and_save(ctx, current, usable)
        return
    if wants_json(ctx):
        emit_json([item.model_dump() for item in (result if show_all else usable)])
        return
    show_models(result if show_all else usable, active=current.config.model)
    if hidden and not show_all:
        console.print(
            f"[muted]{hidden} non-chat model(s) hidden "
            "(audio, speech, and classifiers). Use --all to see them.[/muted]"
        )


@app.command("select-model")
def select_model(ctx: typer.Context) -> None:
    """Browse the live model catalog and save the one you choose."""
    current = service()
    result: list = []
    _run(ctx, lambda: result.extend(current.chat_models()))
    _select_and_save(ctx, current, result)


def _select_and_save(ctx: typer.Context, current: PromptPilotService, models_list: list) -> None:
    """Open the picker and persist the chosen model."""
    if picker_available():
        chosen = pick_model(console, models_list, active=current.config.model)
    else:
        chosen = _select_with_prompt(models_list, current.config.model)

    if chosen is None:
        if wants_json(ctx):
            emit_json({"selected": None, "cancelled": True})
        else:
            show_info("No model selected.")
        return

    _run(ctx, lambda: current.set_model(chosen))
    if wants_json(ctx):
        emit_json({"selected": chosen, "cancelled": False})
    else:
        show_success(f"Preferred model set to {chosen}.")


def _select_with_prompt(models_list: list, active: str | None) -> str | None:
    """Fall back to a numbered list when the terminal cannot provide raw input."""
    if not models_list:
        return None
    console.print()
    for index, model in enumerate(sorted(models_list, key=lambda item: item.id), start=1):
        marker = " [dim](current)[/dim]" if model.id == active else ""
        console.print(f"  [value]{index:>2}[/value]. {model.id}{marker}")
    try:
        answer = typer.prompt("Number", prompt_suffix=" > ", default="1")
    except (EOFError, KeyboardInterrupt):
        return None
    try:
        index = int(answer.strip())
    except ValueError:
        return None
    ordered = sorted(models_list, key=lambda item: item.id)
    if 1 <= index <= len(ordered):
        return ordered[index - 1].id
    return None


@app.command()
def dashboard(ctx: typer.Context) -> None:
    """Show local configuration and usage statistics."""
    result = service().dashboard()
    if wants_json(ctx):
        emit_json(result)
    else:
        show_dashboard(result)


@app.command()
def history(
    ctx: typer.Context,
    limit: int = typer.Option(10, "--limit", "-n", min=1, max=200),
) -> None:
    """Show the most recent prompts recorded on this machine."""
    records = service().history(limit=limit)
    if wants_json(ctx):
        emit_json([record.model_dump(mode="json") for record in records])
    else:
        show_history(records)


@app.command()
def benchmark(
    ctx: typer.Context,
    models: list[str] = typer.Option(
        None,
        "--model",
        "-m",
        help=(
            "Models to compare. Repeat the flag for each one. "
            "Defaults to every model in your catalog."
        ),
    ),
    prompt: str = typer.Option(
        "Reply with the single word OK.", "--prompt", "-p", help="Prompt to send."
    ),
    rounds: int = typer.Option(3, "--rounds", min=1, max=20),
    all_models: bool = typer.Option(
        False, "--all", help="Benchmark every model in your live catalog. This is the default."
    ),
) -> None:
    """Compare end-to-end latency for one prompt across models.

    With no `--model` the whole live catalog is benchmarked, so you can see
    every model your account can use.
    """
    current = service()

    if all_models or not models:
        available: list = []
        _run(ctx, lambda: available.extend(current.chat_models()))
        catalog = [model.id for model in available]
        if not catalog:
            show_error("Your account has no chat models available to benchmark.")
            raise typer.Exit(code=1)
        if not _confirm_benchmark_plan(len(catalog), rounds):
            show_info("Benchmark cancelled.")
            return
        models = catalog

    result: list = []
    _run(ctx, lambda: result.extend(current.benchmark(models, prompt, rounds)))
    if wants_json(ctx):
        emit_json([item.to_dict() for item in result])
        return
    show_benchmark(result)
    fastest = fastest_summary(result)
    if fastest is not None:
        console.print(f"[ok]Fastest:[/ok] {fastest.model}")
    succeeded = [item for item in result if item.successful]
    if succeeded:
        slowest = max(succeeded, key=lambda item: item.average_ms)
        if slowest is not fastest:
            console.print(f"[muted]Slowest:[/muted] {slowest.model}")
    failed = [item for item in result if not item.successful]
    if failed:
        console.print(
            f"[warn]{len(failed)} model(s) failed every round.[/warn] "
            "[muted]Run with --json to see the error.[/muted]"
        )


def _confirm_benchmark_plan(model_count: int, rounds: int) -> bool:
    """Show what a benchmark will cost and ask before a large run."""
    total = model_count * rounds
    console.print(
        f"[muted]Benchmarking {model_count} models x {rounds} "
        f"{'round' if rounds == 1 else 'rounds'} = {total} requests.[/muted]"
    )
    if total <= 20:
        return True
    console.print(f"[warn]That is {total} API requests.[/warn]")
    try:
        return typer.confirm("Continue?", default=False)
    except (EOFError, KeyboardInterrupt):
        return False


@app.command()
def probe(
    ctx: typer.Context,
    models_to_probe: list[str] = typer.Argument(..., help="Models to probe."),
) -> None:
    """Demonstrate a thread pool with independent tiny API requests."""
    current = service()
    result: list = []
    _run(ctx, lambda: result.extend(current.probe_models(models_to_probe)))
    if wants_json(ctx):
        emit_json([asdict(item) for item in result])
    else:
        show_workers(result)


@app.command("clear-stats")
def clear_stats(ctx: typer.Context) -> None:
    """Delete the local statistics history."""
    service().clear_stats()
    if wants_json(ctx):
        emit_json({"cleared": True})
    else:
        show_success("Statistics cleared.")


@app.command()
def completions(
    ctx: typer.Context,
    shell: str = typer.Argument(
        "bash", help="Shell to generate completion for: bash, zsh, or fish."
    ),
) -> None:
    """Print the shell completion script for bash, zsh, or fish.

    Write the output to the file your shell reads, for example:

        promptpilot completions bash > ~/.local/share/bash-completion/completions/promptpilot
        promptpilot completions zsh  > ~/.zfunc/_promptpilot
    """
    name = shell.strip().lower()
    if name not in SUPPORTED_SHELLS:
        supported = ", ".join(SUPPORTED_SHELLS)
        raise typer.BadParameter(f"unsupported shell {shell!r}; choose one of: {supported}")
    script = get_completion_script(
        prog_name="promptpilot",
        complete_var=COMPLETE_ENV_VAR,
        shell=name,
    )
    if wants_json(ctx):
        emit_json({"shell": name, "script": script})
        return
    print(script)


@config_app.command("show")
def config_show(ctx: typer.Context) -> None:
    """Show the resolved configuration with a masked API key."""
    current = service()
    key = current.config_store.user_api_key()
    data = {
        "api_key": mask(key),
        "api_key_source": current.config_store.api_key_source(),
        "model": current.config.model,
        "timeout_seconds": current.config.timeout_seconds,
        "config_path": str(current.config_store.path),
        "stats_path": str(current.stats_store.path),
    }
    if wants_json(ctx):
        emit_json(data)
    else:
        show_config(data)


@config_app.command("set-key")
def config_set_key(
    ctx: typer.Context,
    api_key: str | None = typer.Option(
        None, "--api-key", prompt=True, hide_input=True, help="Your Groq API key."
    ),
) -> None:
    """Save your personal Groq API key locally."""
    if api_key is None:
        raise typer.BadParameter("an API key is required")
    current = service()
    _run(ctx, lambda: current.set_user_key(api_key))
    if wants_json(ctx):
        emit_json({"saved": True, "config_path": str(current.config_store.path)})
    else:
        show_success("API key saved to your local configuration.")
        show_key_summary(api_key, "config file")


@config_app.command("set-model")
def config_set_model(
    ctx: typer.Context,
    model: str = typer.Argument(..., help="Model ID to use by default."),
) -> None:
    """Persist the preferred model ID."""
    current = service()
    _run(ctx, lambda: current.set_model(model))
    if wants_json(ctx):
        emit_json({"model": current.config.model})
    else:
        show_success(f"Preferred model set to {current.config.model}.")


@config_app.command("path")
def config_path(ctx: typer.Context) -> None:
    """Print the paths PromptPilot uses for configuration and statistics."""
    current = service()
    data = {
        "config_path": str(current.config_store.path),
        "stats_path": str(current.stats_store.path),
    }
    if wants_json(ctx):
        emit_json(data)
    else:
        show_rule("Paths")
        console.print(f"config  {data['config_path']}")
        console.print(f"stats   {data['stats_path']}")


def mask(value: str | None) -> str:
    """Mask an API key so it can be shown safely."""
    return mask_secret(value)


def main() -> None:
    """Entry point used by the console script."""
    app()


if __name__ == "__main__":
    main()


__all__ = ["app", "config_app", "main"]
