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

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Usage

```bash
promptpilot ask "Explain Python generators in three examples"
promptpilot ask --stream "Explain decorators as if I am preparing for an interview"
promptpilot batch "Summarise dependency injection" "Compare threads and asyncio"
promptpilot models
promptpilot dashboard
promptpilot benchmark --model llama-3.1-8b-instant --rounds 3
```

## License

MIT. See [LICENSE](LICENSE).
