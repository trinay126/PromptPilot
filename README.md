# PromptPilot — Groq AI Command-Line Workbench

A production-minded Python CLI that talks directly to Groq's OpenAI-compatible
REST API. It includes real SSE streaming, a model benchmark command, a safe
ten-prompt demo quota, user API-key setup, asynchronous batch prompts,
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
| Async batching | `async_client.py`, `services.ask_many` | `asyncio.gather` runs prompts concurrently in input order |
| Thread pool | `workers.py`, `probe` command | I/O-bound parallelism contrasted with `asyncio` |
| Benchmarking | `benchmark.py`, `benchmark` command | Average, median, P95, min, and max latency per model |
| Pydantic validation | `schemas.py` | Every untrusted payload is validated at the boundary |
| Decorators | `decorators.py` | Timing and bounded retry as reusable cross-cutting behaviour |
| Persistence | `config.py`, `stores.py` | JSON configuration and JSONL statistics |
| Demo quota | `quota.py` | Thread-safe ten-prompt allowance for a private build |
| Automation | `--json` on every command | Composable with Bash, PowerShell, CI, and `jq` |
| Mocked HTTP tests | `tests/test_clients.py`, `tests/test_streaming.py` | `respx` isolates the transport, so no key or quota is needed |

## Architecture

```text
Typer CLI commands
        |
        v
PromptPilotService  ----  QuotaManager
        |                      |
        v                      v
Sync/Async Groq REST clients  ConfigStore + StatsStore
        |
        v
Groq API over HTTPS
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

Copy the example environment file and add your key:

```bash
cp .env.example .env
```

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Your personal Groq key |
| `PROMPTPILOT_DEMO_API_KEY` | Optional shared key for a private demo build |
| `PROMPTPILOT_MODEL` | Default model when `--model` is omitted |
| `PROMPTPILOT_TIMEOUT_SECONDS` | HTTP timeout for every request |
| `PROMPTPILOT_DEMO_LIMIT` | Successful demo prompts allowed before a personal key is required |

You can also store the key through the CLI:

```bash
promptpilot set-key
promptpilot set-model llama-3.3-70b-versatile
```

Configuration lives in an OS-appropriate per-user directory (`%APPDATA%` on
Windows, `~/Library/Application Support` on macOS, `$XDG_CONFIG_HOME` on
Linux). Statistics are written next to it as `stats.jsonl`.

## Usage

```bash
promptpilot ask "Explain Python generators in three examples"
promptpilot ask --stream "Explain decorators as if I am preparing for an interview"
promptpilot batch "Summarise dependency injection" "Compare threads and asyncio"
promptpilot models
promptpilot dashboard
promptpilot benchmark --model llama-3.1-8b-instant --model llama-3.3-70b-versatile --rounds 3
promptpilot probe llama-3.1-8b-instant llama-3.3-70b-versatile
```

`promptpilot --help` lists every command, and `promptpilot <command> --help`
documents its options.

## JSON mode

The global `--json` flag replaces Rich tables and spinners with a single valid
JSON document on stdout, which makes the CLI safe to pipe into other programs:

```bash
promptpilot --json ask "What is dependency injection?" > answer.json
promptpilot --json dashboard | jq .stats
promptpilot --json models > models.json
```

A streamed JSON request buffers the final text and still emits one parseable
document, which is the only reliable contract for automation.

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
├── cli.py            # Typer commands
├── ui.py             # Rich presentation and JSON serializers
├── services.py       # Application service facade
├── clients.py        # Synchronous REST client with SSE streaming
├── async_client.py   # Asynchronous client with gather-based batching
├── benchmark.py      # Latency benchmark primitives
├── workers.py        # Thread-pool utilities
├── config.py         # JSON configuration and platform paths
├── quota.py          # Thread-safe demo quota
├── stores.py         # JSONL statistics store
├── schemas.py        # Pydantic request/response models
├── decorators.py     # Timing and retry decorators
├── utils.py          # Small pure helpers
├── constants.py      # Shared defaults
└── exceptions.py     # Domain error hierarchy
```

## License

MIT. See [LICENSE](LICENSE).
