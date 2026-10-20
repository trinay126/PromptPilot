# PromptPilot — Groq AI Command-Line Workbench

A production-minded Python CLI that talks directly to Groq's OpenAI-compatible
REST API. It includes real SSE streaming, an interactive chat session, a model
benchmark command, personal API-key setup, asynchronous batch prompts,
concurrent workers, persistent statistics, Pydantic validation, decorators,
exception handling, file objects, virtual-environment workflow, mocked HTTP
integration tests, machine-readable `--json` output, pytest coverage, and
polished Windows executable releases.

This project is intentionally a **CLI application**, not a FastAPI server. A CLI
does not need to expose an HTTP endpoint of its own; it is already the client.
PromptPilot sends HTTPS requests to Groq through a small typed API-client layer.
If you later want a web interface, the existing service layer can be placed
behind FastAPI without rewriting the Groq integration.

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Interactive chat](#interactive-chat)
- [JSON mode](#json-mode)
- [Testing](#testing)
- [Windows executable](#windows-executable)
- [Project layout](#project-layout)
- [License](#license)

## Features

| Capability | Where it appears | Why it matters |
|---|---|---|
| Typed API client | `clients.py`, `async_client.py` | Direct REST calls over HTTPS with `httpx` |
| Real SSE streaming | `clients.py`, `ui.py`, `ask --stream` | Incremental output instead of waiting for the full answer |
| Interactive chat | `chat` command | Multi-turn conversation that keeps earlier turns as context |
| Async batching | `async_client.py`, `services.ask_many` | `asyncio.gather` runs prompts concurrently in input order |
| Thread pool | `workers.py`, `probe` command | I/O-bound parallelism contrasted with `asyncio` |
| Benchmarking | `benchmark.py`, `benchmark` command | Average, median, P95, min, and max latency per model |
| Pydantic validation | `schemas.py` | Every untrusted payload is validated at the boundary |
| Decorators | `decorators.py` | Timing and bounded retry as reusable cross-cutting behaviour |
| Persistence | `config.py`, `stores.py` | JSON configuration and JSONL statistics |
| Local history | `stores.py`, `history` command | See the prompts you ran on this machine |
| Automation | `--json` on every command | Composable with Bash, PowerShell, CI, and `jq` |
| Mocked HTTP tests | `tests/test_clients.py`, `tests/test_streaming.py` | `respx` isolates the transport, so no key is needed |

## Architecture

```text
Typer CLI commands
        |
        v
PromptPilotService
        |
        v
Sync/Async Groq REST clients
        |                    |
        v                    v
Groq API over HTTPS   ConfigStore + StatsStore
```

The service layer is the extension point. A later FastAPI adapter could call
`PromptPilotService.ask()` from an endpoint while the CLI keeps using the same
service. This is dependency inversion in practice: the user interface depends
on an application service, not on raw HTTP code.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Configuration

PromptPilot uses **your own Groq API key**. There is no bundled key and no demo
allowance — you always authenticate as yourself.

Create a free key at [console.groq.com/keys](https://console.groq.com/keys),
then store it with the guided command:

```bash
promptpilot config set-key
```

The key is written to an OS-appropriate per-user directory (`%APPDATA%` on
Windows, `~/Library/Application Support` on macOS, `$XDG_CONFIG_HOME` on
Linux) and is never committed to the repository. Statistics are written next to
it as `stats.jsonl`.

You can also export the key as an environment variable instead:

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Your personal Groq key |
| `PROMPTPILOT_MODEL` | Default model when `--model` is omitted |
| `PROMPTPILOT_TIMEOUT_SECONDS` | HTTP timeout for every request |

Inspect what is currently active with `promptpilot config show`; the key is
always masked.

## Usage

```bash
promptpilot ask "Explain Python generators in three examples"
promptpilot ask --stream "Explain decorators as if I am preparing for an interview"
promptpilot batch "Summarise dependency injection" "Compare threads and asyncio"
promptpilot models
promptpilot dashboard
promptpilot history
promptpilot benchmark --model llama-3.1-8b-instant --model llama-3.3-70b-versatile --rounds 3
promptpilot probe llama-3.1-8b-instant llama-3.3-70b-versatile
```

`promptpilot --help` lists every command, and `promptpilot <command> --help`
documents its options.

## Interactive chat

`promptpilot chat` opens a REPL that remembers the conversation, so follow-up
questions include the earlier turns as context:

```text
you > Explain what a decorator is
you > Now show me one with a timer
you > /reset
you > /exit
```

| Command | What it does |
|---|---|
| `/help` | Show the list of chat commands |
| `/history` | Show how many messages are in the conversation |
| `/reset` | Clear the conversation history |
| `/exit` | Leave the session |

## JSON mode

The global `--json` flag replaces Rich tables and spinners with a single valid
JSON document on stdout, which makes the CLI safe to pipe into other programs:

```bash
promptpilot --json ask "What is dependency injection?" > answer.json
promptpilot --json dashboard | jq .stats
promptpilot --json models > models.json
```

A streamed JSON request buffers the final text and still emits one parseable
document, which is the only reliable contract for automation. In `--json` mode
`chat` reads one prompt per line from stdin and emits one compact JSON object
per line, which is easy to pipe into `jq`, a log collector, or another program.

## Testing

```bash
python -m pytest
python -m pytest --cov=promptpilot --cov-report=term-missing
```

The HTTP boundary is mocked with `respx`, so the suite never contacts Groq and
never needs a real key.

## Windows executable

```powershell
.\scripts\build_windows.ps1
```

The script runs the tests, builds `promptpilot.exe` with PyInstaller, and
produces a versioned bundle containing the executable, a SHA-256 checksum file,
and a release manifest. PyInstaller is not a cross-compiler, so build on
Windows.

## Project layout

```text
src/promptpilot/
├── cli.py            # Typer commands and the config sub-app
├── ui.py             # Rich presentation and JSON serializers
├── services.py       # Application service facade
├── clients.py        # Synchronous REST client with SSE streaming
├── async_client.py   # Asynchronous client with gather-based batching
├── benchmark.py      # Latency benchmark primitives
├── workers.py        # Thread-pool utilities
├── config.py         # JSON configuration and platform paths
├── stores.py         # JSONL statistics store
├── schemas.py        # Pydantic request/response models
├── decorators.py     # Timing and retry decorators
├── utils.py          # Small pure helpers
├── constants.py      # Shared defaults
└── exceptions.py     # Domain error hierarchy
```

## License

MIT. See [LICENSE](LICENSE).
