<div align="center">

# PromptPilot

**A production-minded Groq AI command-line workbench.**

Real SSE streaming, an interactive multi-turn chat, live model benchmarking,
local statistics, and machine-readable output — wrapped in a polished terminal
UI and backed by a fully typed, fully tested service layer.

[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-2ea44f?logo=open-source-initiative&logoColor=white)](LICENSE)
[![CI](https://github.com/trinay126/PromptPilot/actions/workflows/release.yml/badge.svg)](https://github.com/trinay126/PromptPilot/actions/workflows/release.yml)
[![Lint: ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white)](pyproject.toml)
[![Typed](https://img.shields.io/badge/typing-annotated-2A6DB2?logo=python&logoColor=white)](src/promptpilot/schemas.py)

[**Setup**](#setup) &nbsp;·&nbsp; [**Start here**](#start-here) &nbsp;·&nbsp; [**Commands**](#command-reference) &nbsp;·&nbsp; [**How it works**](#architecture)

</div>

<div align="center">

<img src="docs/demo.svg" alt="PromptPilot demo: listing models, asking a question, streaming a response, and reading JSON statistics" width="900">

</div>

<div align="center">

**Three commands and you are running**

```bash
pip install -e ".[dev]"
promptpilot config set-key
promptpilot ask "Explain Python decorators in one paragraph."
```

</div>

---

## At a glance

| Commands | Tests | Coverage | Keys bundled |
|:--------:|:-----:|:--------:|:------------:|
| **12** | **216** | **89%** | **0** |

| Runtime deps | Test suite | Network in CI | Platforms |
|:------------:|:----------:|:-------------:|:----------:|
| **5** | **~1 second** | **0 calls** | **Linux · macOS · Windows** |

---

## Why PromptPilot

Most "AI CLI" projects are a thin wrapper around a chat endpoint. PromptPilot is
built like production software instead: a typed API-client layer, a validated
service boundary, persistent local state, a real error model, and a test suite
that mocks the HTTP transport so it never needs a key or spends anyone's quota.

It is deliberately a **CLI, not a FastAPI server**. A CLI does not need to
expose an HTTP endpoint of its own — it is already the client. PromptPilot
speaks HTTPS to Groq directly through `httpx`, so every layer of the request
(status codes, headers, timeouts, retries, JSON validation) stays visible and
explainable. The service layer is deliberately shaped so a future FastAPI
adapter could reuse it without rewriting the Groq integration.

| Capability | Why it matters |
|---|---|
| **Your key, stored once** | `promptpilot config set-key` writes it to your user config directory. It is reused forever — you are never asked again. |
| **Real streaming** | Server-Sent Events are parsed at the wire level, so tokens render the moment Groq produces them. |
| **Interactive chat** | A REPL that sends earlier turns back as context, with `/help`, `/history`, `/reset`, and `/exit`. |
| **Interactive model picker** | Browse the live catalog, grouped by owner, and search it as you type. |
| **Automation-first** | A global `--json` flag turns every command into a clean JSON document for `jq`, CI, and shell pipelines. |
| **Honest benchmarks** | Average, median, P95, min, and max latency per model, with the fastest one called out. |
| **Zero-dependency tests** | `respx` mocks the HTTPX transport, so the suite runs offline, for free, in about a second. |

---

## Table of contents

- [Setup](#setup) — [Linux](#linux) · [macOS](#macos) · [Windows](#windows)
- [Start here](#start-here)
- [What do I want?](#what-do-i-want)
- [Screenshots](#screenshots)
- [Command reference](#command-reference)
- [Automation with `--json`](#automation-with---json)
- [Configuration](#configuration)
- [Under the hood](#under-the-hood)
- [Architecture](#architecture)
- [Project layout](#project-layout)
- [Development](#development)
- [Releases](#releases)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Security model](#security-model)
- [Contributing](#contributing)
- [License](#license)

---

## Setup

**You need two things:** Python 3.11 or newer, and a free Groq API key from
[console.groq.com/keys](https://console.groq.com/keys).

> **Your key is stored once and reused forever.**
> `promptpilot config set-key` writes it to your per-user config directory
> (`~/.config/promptpilot/config.json` on Linux). Every later command picks it
> up automatically, so you are only ever asked for it once. It is never
> committed to the repository, and it is masked whenever the CLI displays it.

### Linux

#### Install

The recommended route on Linux is [`pipx`](https://pipx.pypa.io/). It installs
the tool into its own isolated environment and puts it on your `PATH` — no
`sudo`, no risk to your system Python, and it works from any directory.

```bash
# Fedora
sudo dnf install pipx
# Ubuntu / Debian
sudo apt install pipx
# Arch
sudo pacman -S python-pipx

pipx ensurepath          # adds ~/.local/bin to your PATH
```

Restart your shell, then install PromptPilot:

```bash
pipx install git+https://github.com/trinay126/PromptPilot.git
```

Verify it:

```bash
promptpilot --version
```

> **No Python at all?** Every release ships a standalone Linux binary that needs
> no interpreter — see [Releases](#releases).

> **Prefer a local checkout?** Clone the repository and use a virtual
> environment instead:
>
> ```bash
> git clone https://github.com/trinay126/PromptPilot.git
> cd PromptPilot
> python3 -m venv .venv
> source .venv/bin/activate
> python -m pip install -e ".[dev]"
> ```
>
> Note `python3` rather than `python` — most modern Linux distributions do not
> provide a bare `python` command. While the virtual environment is active,
> `promptpilot` is on your `PATH`; deactivate it with `deactivate`.

#### Store your key

```bash
promptpilot config set-key
```

The prompt hides what you type. The key is saved to
`~/.config/promptpilot/config.json` and reused by every future command, so
this is the only time you are asked for it.

```bash
promptpilot config show      # confirm it is there (always masked)
```

#### Shell completion

Tab completion works with `bash`, `zsh`, and `fish`. The script is printed to
stdout, so you can put it wherever your setup expects it.

```bash
# bash
mkdir -p ~/.local/share/bash-completion/completions
promptpilot completions bash > ~/.local/share/bash-completion/completions/promptpilot
```

```bash
# zsh
mkdir -p ~/.zfunc
promptpilot completions zsh > ~/.zfunc/_promptpilot
echo 'fpath+=~/.zfunc' >> ~/.zshrc
echo 'autoload -Uz compinit && compinit' >> ~/.zshrc
```

```bash
# fish
mkdir -p ~/.config/fish/completions
promptpilot completions fish > ~/.config/fish/completions/promptpilot.fish
```

Fedora, Debian, and Ubuntu load `~/.local/share/bash-completion/completions`
automatically once the `bash-completion` package is installed
(`sudo dnf install bash-completion`). If you would rather not manage the file
yourself, the built-in installer does it for you:

```bash
promptpilot --install-completion
```

#### Headless use, pipes, and CI

When output is piped or redirected, PromptPilot detects that it is not a
terminal and drops the interactive chrome automatically. You can also control
it explicitly:

| Need | Command |
|---|---|
| Plain text, no ANSI colour | `promptpilot --no-color dashboard` |
| Honour the `NO_COLOR` standard | `NO_COLOR=1 promptpilot dashboard` |
| Force colour back on | `promptpilot --color dashboard` |
| Pure JSON, no styling at all | `promptpilot --json dashboard` |
| Detect a non-interactive terminal | `TERM=dumb promptpilot dashboard` |

`NO_COLOR` follows the [no-color.org](https://no-color.org/) convention and is
honoured automatically, so tools like `bat`, `ripgrep`, and `ls` behave the
same way in your environment.

Exit codes follow the usual Unix convention: `0` for success, `1` for a
handled error, and `2` for a usage mistake. See
[Troubleshooting](#troubleshooting) for the full table.

A worked example — pull the average latency out of the dashboard with `jq`:

```bash
promptpilot --json dashboard | jq -r '.stats.average_latency_ms'
```

#### Run on a schedule

Because the tool is scriptable, `systemd` and `cron` both work. A **user**
timer keeps the key in your own environment rather than a system-wide secret:

```ini
# ~/.config/systemd/user/promptpilot-report.service
[Service]
Type=oneshot
Environment=GROQ_API_KEY=gsk_your_key_here
ExecStart=%h/.local/bin/promptpilot --json dashboard
```

```ini
# ~/.config/systemd/user/promptpilot-report.timer
[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl --user enable --now promptpilot-report.timer
systemctl --user list-timers
```

The same thing with `cron`:

```cron
0 9 * * * GROQ_API_KEY=gsk_your_key_here /usr/local/bin/promptpilot --json dashboard >> ~/promptpilot.log 2>&1
```

#### Run inside a container

```dockerfile
FROM python:3.12-slim
RUN pip install --no-cache-dir git+https://github.com/trinay126/PromptPilot.git
ENTRYPOINT ["promptpilot"]
```

```bash
docker run --rm -e GROQ_API_KEY promptpilot ask "Hello from a container"
```

Mount a volume at `/root/.config/promptpilot` if you want the configuration and
statistics to survive between runs.

### macOS

Everything in the Linux section above works on macOS unchanged. The only
differences are the package manager and the config location:

```bash
brew install pipx && pipx ensurepath
pipx install git+https://github.com/trinay126/PromptPilot.git
```

Your config lives in
`~/Library/Application Support/promptpilot/config.json`, and your shell
completion goes in the same place as on Linux.

### Windows

```powershell
git clone https://github.com/trinay126/PromptPilot.git
cd PromptPilot
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Or install it system-wide with `pipx` under
[Python for Windows](https://www.python.org/downloads/windows/):

```powershell
pipx install git+https://github.com/trinay126/PromptPilot.git
```

Your config lives in `%APPDATA%\promptpilot\config.json`.

Two Windows differences worth knowing:

- The interactive model picker needs a raw terminal, so on Windows it falls
  back to a numbered list you pick from by typing a number.
- Shell completion is generated for `bash`, `zsh`, and `fish`. In PowerShell,
  use `promptpilot --install-completion` if you use a compatible shell.

A ready-to-run `promptpilot.exe` is published with every release — see
[Releases](#releases).

---

## Start here

A five-minute tour. Each step works on its own.

### 1. Store your key — once

```bash
promptpilot config set-key
```

### 2. Ask a question

```bash
promptpilot ask "Explain Python decorators in one paragraph."
```

### 3. Watch it arrive token by token

```bash
promptpilot ask --stream "Write a haiku about caching"
```

### 4. Pick a model

```bash
promptpilot select-model
```

### 5. Hold a conversation

```bash
promptpilot chat
```

---

## What do I want?

| If you want to… | Run |
|---|---|
| Ask a question | `promptpilot ask "your prompt"` |
| See the answer arrive token by token | `promptpilot ask --stream "your prompt"` |
| Hold a multi-turn conversation | `promptpilot chat` |
| Ask several questions at once | `promptpilot batch "one" "two"` |
| See which models your account can use | `promptpilot models` |
| Change your default model | `promptpilot select-model` |
| Compare how fast models are | `promptpilot benchmark` |
| See what you have run recently | `promptpilot history` |
| See your settings and usage | `promptpilot dashboard` |
| Pipe results into another program | `promptpilot --json <command>` |
| Delete your local history | `promptpilot clear-stats` |
| Check or change your key and model | `promptpilot config show` |
| Print your config file locations | `promptpilot config path` |

---

## Screenshots

Every capture below is real terminal output.

**`promptpilot chat` — an interactive session that keeps the conversation in context:**

```text
╭──────────────────────────────────────╮
│                                      │
│    PromptPilot                       │
│    Groq AI command-line workbench    │
│    by Chadalavada Trinay Sai         │
│                                      │
╰──────────────────────────────────────╯
Type a prompt and press enter. Use /help to list commands, /exit to quit.

you > ╭─────────────────────────── llama-3.1-8b-instant ───────────────────────────╮
│                                                                            │
│  A decorator wraps a callable to add behaviour without changing its        │
│  signature.                                                                │
│                                                                            │
│                                                                            │
│   import functools                                                         │
│                                                                            │
│   def logged(func):                                                        │
│       @functools.wraps(func)                                               │
│       def wrapper(*args, **kwargs):                                        │
│           print(f'calling {func.__name__}')                                │
│           return func(*args, **kwargs)                                     │
│       return wrapper                                                       │
│                                                                            │
│                                                                            │
│  Read the source of the wrappers you use — most of them are a dozen lines  │
│  long.                                                                     │
│                                                                            │
╰────────────────── 18 prompt + 142 completion = 160 total ──────────────────╯
you > Bye.
```

**`promptpilot select-model` — browse the live catalog and pick one interactively:**

```text
╭───────────────────────────────────── Select a model ─────────────────────────────────────╮
│                                                                                          │
│    Search: type to filter   10 shown                                                     │
│    ↑/↓ move   enter select   esc cancel   backspace delete                               │
│                                                                                          │
│    Alibaba Cloud                                                                         │
│  ▸   qwen/qwen3.8-27b                    current                                         │
│    Canopy Labs                                                                           │
│      canopylabs/orpheus-arabic-saudi                                                     │
│      canopylabs/orpheus-v1-english                                                       │
│    Meta                                                                                  │
│      llama-3.1-8b-instant                                                                │
│      llama-3.3-70b-versatile                                                             │
│      meta-llama/llama-prompt-guard-2-22m                                                 │
│      meta-llama/llama-prompt-guard-2-86m                                                 │
│    OpenAI                                                                                │
│      openai/gpt-oss-120b                                                                 │
│      openai/gpt-oss-20b                                                                  │
│      openai/gpt-oss-safeguard-20b                                                        │
│                                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```

Type to filter as you go, move with `↑`/`↓`, confirm with `enter`, and cancel
with `esc`. The chosen model is saved as your default and used by every
subsequent command. Your current model is marked `current`.

**`promptpilot ask --stream "..."` — tokens print the moment Groq emits them:**

```text
llama-3.1-8b-instant

Caching turns a slow query into a fast one.
```

**`promptpilot models` — the live catalog, with your active model marked:**

```text
         Available Groq models
┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃   ┃ Model ID                ┃ Owner  ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ * │ llama-3.1-8b-instant    │ groq   │
│   │ llama-3.3-70b-versatile │ groq   │
│   │ openai/gpt-oss-120b     │ openai │
└───┴─────────────────────────┴────────┘
* active model   llama-3.1-8b-instant
```

**`promptpilot dashboard` — configuration and local usage in one view:**

```text
                          PromptPilot dashboard
┌─────────────────────┬─────────────────────────────────────────────────┐
│ API key             │ configured  (environment (GROQ_API_KEY))        │
│ Preferred model     │ llama-3.1-8b-instant                            │
│ Requests            │ 12                                              │
│ Successful          │ 12                                              │
│ Failed              │ 0                                               │
│ Average latency     │ 52.86 ms                                        │
│ Tokens (prompt)     │ 132                                             │
│ Tokens (completion) │ 613                                             │
│ Config file         │ ~/.config/promptpilot/config.json               │
│ Stats file          │ ~/.config/promptpilot/stats.jsonl               │
└─────────────────────┴─────────────────────────────────────────────────┘
```

**`promptpilot benchmark` — every model in your catalog, ranked fastest first:**

```text
Benchmarking 11 models x 1 round = 11 requests.
                                  Groq model benchmark
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓
┃  # ┃ Model                   ┃  OK ┃  Avg ms ┃  Med ms ┃  P95 ms ┃  Min ms ┃  Max ms ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩
│  1 │ openai/gpt-oss-safeguar │ 1/1 │  359.27 │  359.27 │  359.27 │  359.27 │  359.27 │
│    │ d-20b                   │     │         │         │         │         │         │
│  2 │ allam-2-7b              │ 1/1 │  617.20 │  617.20 │  617.20 │  617.20 │  617.20 │
│  3 │ qwen/qwen3.8-27b        │ 1/1 │  840.73 │  840.73 │  840.73 │  840.73 │  840.73 │
│  4 │ openai/gpt-oss-20b      │ 1/1 │  844.11 │  844.11 │  844.11 │  844.11 │  844.11 │
│  5 │ openai/gpt-oss-120b     │ 1/1 │ 5588.78 │ 5588.78 │ 5588.78 │ 5588.78 │ 5588.78 │
│  6 │ canopylabs/orpheus-arab │ 0/1 │       - │       - │       - │       - │       - │
│    │ ic-saudi                │     │         │         │         │         │         │
│  7 │ meta-llama/llama-prompt │ 0/1 │       - │       - │       - │       - │       - │
│    │ -guard-2-86m            │     │         │         │         │         │         │
│  8 │ whisper-large-v3-turbo  │ 0/1 │       - │       - │       - │       - │       - │
│  9 │ whisper-large-v3        │ 0/1 │       - │       - │       - │       - │       - │
│ 10 │ meta-llama/llama-prompt │ 0/1 │       - │       - │       - │       - │       - │
│    │ -guard-2-22m            │     │         │         │         │         │         │
│ 11 │ canopylabs/orpheus-v1-e │ 0/1 │       - │       - │       - │       - │       - │
│    │ nglish                  │     │         │         │         │         │         │
└────┴─────────────────────────┴─────┴─────────┴─────────┴─────────┴─────────┴─────────┘
Fastest: openai/gpt-oss-safeguard-20b
Slowest: openai/gpt-oss-120b
6 model(s) failed every round. Run with --json to see the error.
```

**An error is a panel with a next step — never a traceback:**

```text
╭─────────────────────────────────── Error ────────────────────────────────────╮
│                                                                              │
│  No Groq API key found.                                                      │
│    Set one with:  promptpilot config set-key                                 │
│    Or export it:  export GROQ_API_KEY=your_key_here                          │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Command reference

Run `promptpilot --help` for the full list, or `promptpilot <command> --help`
for the options of a single command.

```text

 Usage: promptpilot [OPTIONS] COMMAND [ARGS]...

 PromptPilot — Groq AI command-line workbench.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --json                                  Emit one JSON document for           │
│                                         automation.                          │
│ --color                 --no-color      Force colour on or off. By default   │
│                                         the NO_COLOR environment variable is │
│                                         respected.                           │
│ --version                               Show the installed version and exit. │
│ --install-completion                    Install completion for the current   │
│                                         shell.                               │
│ --show-completion                       Show completion for the current      │
│                                         shell, to copy it or customize the   │
│                                         installation.                        │
│ --help                                  Show this message and exit.          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ ask           Send one prompt and print the answer.                          │
│ chat          Start an interactive chat session that remembers the           │
│               conversation.                                                  │
│ batch         Run multiple prompts concurrently with asyncio.gather.         │
│ models        List the live model catalog returned by Groq.                  │
│ select-model  Browse the live model catalog and save the one you choose.     │
│ dashboard     Show local configuration and usage statistics.                 │
│ history       Show the most recent prompts recorded on this machine.         │
│ benchmark     Compare end-to-end latency for one prompt across models.       │
│ probe         Demonstrate a thread pool with independent tiny API requests.  │
│ clear-stats   Delete the local statistics history.                           │
│ completions   Print the shell completion script for bash, zsh, or fish.      │
│ config        Manage your local PromptPilot configuration.                   │
╰──────────────────────────────────────────────────────────────────────────────╯

 Examples
   promptpilot config set-key                 store your Groq API key
   promptpilot ask "Explain Python decorators"
   promptpilot ask --stream "Write a haiku"  show tokens as they arrive
   promptpilot chat                          start an interactive session
   promptpilot --json dashboard | jq .stats  machine-readable output
```

### `ask`

Send one prompt and print the answer.

```bash
promptpilot ask "Summarise the CAP theorem in two sentences"
promptpilot ask --model llama-3.3-70b-versatile "What is a monad?"
promptpilot ask --stream "Write a haiku about caching"
```

| Option | Default | Description |
|---|---|---|
| `--model`, `-m` | your configured model | Model to use for this request |
| `--stream` / `--no-stream` | `--no-stream` | Print SSE deltas the moment they arrive |

Answers are rendered as **Markdown**, so code blocks, lists, and tables coming
back from the model arrive formatted rather than as raw text.

### `chat`

Open an interactive session that keeps the conversation in context — a
follow-up question includes the earlier turns.

```bash
promptpilot chat
promptpilot chat --model llama-3.3-70b-versatile
```

```text
you > What is a decorator?
you > Now show me one with a timer.
you > /reset
you > /exit
```

| Command | What it does |
|---|---|
| `/help` | Show the list of chat commands |
| `/history` | Show how many messages are in the conversation |
| `/reset` | Clear the conversation history |
| `/exit` | Leave the session |

The session keeps the last 20 messages as context, so long conversations stay
cheap and focused.

### `batch`

Run several prompts concurrently with `asyncio.gather`. Results keep the order
you passed the prompts in.

```bash
promptpilot batch \
  "Summarise dependency injection in Python" \
  "Give me a short example of a decorator" \
  "Compare threads and asyncio for network calls"
```

### `models`

List the live catalog Groq returns for your account. Your configured model is
marked with `*`.

```bash
promptpilot models
```

### `select-model`

Browse the live model catalog in an interactive picker and save the one you
choose as your default.

```bash
promptpilot select-model
promptpilot models --select      # the same picker, from the models command
```

| Key | Action |
|---|---|
| any printable character | Filter the list as you type |
| `↑` / `↓` | Move the selection |
| `enter` | Save the highlighted model |
| `esc` | Cancel without changing anything |
| `backspace` | Delete a character from the search |

The catalog is grouped by owner, and your current model is marked `current`.
Because the filter matches on the model id, you can type a fragment such as
`gpt` or `llama` to narrow the list instantly.

If the terminal cannot provide raw input — a pipe, a CI job, or a Windows
console — the command falls back to a numbered list you can pick from by
typing a number.

### `dashboard`

Show the resolved configuration and the local usage statistics — request
counts, token totals, average latency, and the file locations in use.

```bash
promptpilot dashboard
```

### `history`

Show the prompts you have run on this machine, newest last, with latency and
status. Records live in `stats.jsonl`.

```bash
promptpilot history
promptpilot history --limit 25
```

### `benchmark`

Compare end-to-end latency for the same prompt across models. This issues a
real request per model per round, so keep `--rounds` small while exploring.

Run it with no arguments and it benchmarks **every model in your live
catalog**, so you can see the whole picture at once:

```bash
promptpilot benchmark
```

The results come back as a leaderboard, fastest first, with models that failed
every round listed last:

```text
┏━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓
┃ #  ┃ Model             ┃ OK ┃ Avg ms  ┃ Med ms  ┃ P95 ms  ┃ Min ms  ┃ Max ms  ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩
│ 1  │ openai/gpt-oss-   │ 1/1│  572.89 │  572.89 │  572.89 │  572.89 │  572.89 │
│    │ 20b               │    │         │         │         │         │         │
│ 2  │ openai/gpt-oss-   │ 1/1│ 1837.48 │ 1837.48 │ 1837.48 │ 1837.48 │ 1837.48 │
│    │ 120b              │    │         │         │         │         │         │
│ 3  │ whisper-large-v3  │ 0/1│       - │       - │       - │       - │       - │
└────┴───────────────────┴────┴─────────┴─────────┴─────────┴─────────┴─────────┘
Fastest: openai/gpt-oss-safeguard-20b
Slowest: openai/gpt-oss-120b
6 model(s) failed every round. Run with --json to see the error.
```

Not every model in the catalog can answer a chat completion — the Whisper
models are audio-only, and the Llama prompt guards are content filters. Those
rows show a dash instead of a misleading `0.00 ms`, and the error is in the
`--json` output.

Name the models you want to compare by repeating `--model`:

```bash
promptpilot benchmark \
  --model llama-3.1-8b-instant \
  --model llama-3.3-70b-versatile \
  --rounds 3 \
  --prompt "Reply with the single word OK."
```

| Option | Default | Description |
|---|---|---|
| `--model`, `-m` | every model in your catalog | Models to compare. Repeat the flag for each one. |
| `--prompt`, `-p` | `Reply with the single word OK.` | Prompt to send each round |
| `--rounds` | `3` | Repeats per model (1–20) |
| `--all` | on | Benchmark every model in your live catalog |

Because a full sweep means a lot of requests, PromptPilot prints the plan
first and asks for confirmation whenever the run would exceed 20 requests. You
can cancel with `n`, or use `--rounds 1` to keep it cheap.

Latency depends on network conditions, rate limits, and model warm-up, so
treat the output as an engineering observation rather than a permanent ranking.

### `probe`

Send one tiny request per model from a thread pool — a side-by-side contrast
with the `asyncio` implementation used by `batch`.

```bash
promptpilot probe llama-3.1-8b-instant llama-3.3-70b-versatile
```

### `clear-stats`

Delete the local statistics history.

```bash
promptpilot clear-stats
```

### `completions`

Print the shell completion script for `bash`, `zsh`, or `fish` to stdout.

```bash
promptpilot completions bash
promptpilot completions zsh
promptpilot completions fish
```

Printing to stdout (rather than writing to a fixed path) means the script can go
anywhere your setup expects it — see [Linux](#linux).

### `config`

Manage your local configuration.

```bash
promptpilot config set-key          # guided, hidden input
promptpilot config set-key --api-key gsk_...
promptpilot config set-model llama-3.3-70b-versatile
promptpilot config show             # key is always masked
promptpilot config path             # where config and stats live
```

---

## Automation with `--json`

The global `--json` flag swaps the Rich interface for plain JSON on stdout, so
the CLI is safe to pipe into other programs. It works with every command.

```bash
promptpilot --json ask "What is dependency injection?" > answer.json
promptpilot --json dashboard | jq .stats
promptpilot --json models | jq -r '.[] | .id'
promptpilot --json history | jq '.[0].model'
```

```json
{
  "model": "llama-3.1-8b-instant",
  "text": "A decorator wraps a callable to add reusable behaviour.",
  "usage": {
    "prompt_tokens": 18,
    "completion_tokens": 12,
    "total_tokens": 30
  }
}
```

`chat` in JSON mode is non-interactive: it reads one prompt per line from
stdin and emits one compact JSON object per line, which is easy to stream into
a log collector.

```bash
printf 'first question\nsecond question\n' | promptpilot --json chat
```

```json
{"model":"llama-3.1-8b-instant","text":"...","usage":{"prompt_tokens":18,"completion_tokens":12,"total_tokens":30}}
{"model":"llama-3.1-8b-instant","text":"...","usage":{"prompt_tokens":18,"completion_tokens":12,"total_tokens":30}}
```

Errors are reported as JSON too, and always exit with status `1`:

```json
{
  "error": "No Groq API key found.",
  "type": "MissingAPIKeyError"
}
```

---

## Configuration

PromptPilot resolves settings in this order: **saved config file** →
**environment variable** → **built-in default**.

| Variable | Purpose | Default |
|---|---|---|
| `GROQ_API_KEY` | Your personal Groq key | — |
| `PROMPTPILOT_MODEL` | Model used when `--model` is omitted | `llama-3.1-8b-instant` |
| `PROMPTPILOT_TIMEOUT_SECONDS` | HTTP timeout for every request | `45` |

You can also copy `.env.example` to `.env` and edit it — `python-dotenv` loads
it automatically, searching from the current directory upwards.

**Configuration file** — `promptpilot config path` prints the exact locations:

| Platform | Path |
|---|---|
| Linux | `$XDG_CONFIG_HOME/promptpilot/config.json` (or `~/.config/promptpilot/…`) |
| macOS | `~/Library/Application Support/promptpilot/config.json` |
| Windows | `%APPDATA%\promptpilot\config.json` |

```json
{
  "api_key": "gsk_...",
  "model": "llama-3.1-8b-instant",
  "timeout_seconds": 45.0
}
```

**Statistics file** — `stats.jsonl` sits next to the config file and holds one
validated JSON object per request. This is what `dashboard` and `history` read.

```json
{"timestamp":"2026-10-20T16:56:11.482Z","model":"llama-3.1-8b-instant","prompt_chars":42,"response_chars":512,"prompt_tokens":18,"completion_tokens":142,"latency_ms":56.34,"prompt_preview":"Explain Python decorators in one paragraph.","success":true}
```

---

## Under the hood

What actually happens between `promptpilot ask "..."` and the answer on your
screen:

```text
  promptpilot ask "..."
          │
          ▼
  ① clean_prompt()          strip ANSI escapes, collapse whitespace
          │
          ▼
  ② resolve the key         saved config → GROQ_API_KEY → MissingAPIKeyError
          │
          ▼
  ③ ChatRequest             Pydantic validates model, messages, temperature, budget
          │
          ▼
  ④ POST /chat/completions  httpx.Client, Bearer auth, 45 s timeout
          │
          ├── 408/429/5xx ──▶ retry with linear backoff (3 attempts)
          │
          ▼
  ⑤ ChatResponse            Pydantic validates the reply, or SchemaError
          │
          ▼
  ⑥ PromptStat              one JSONL record appended to stats.jsonl
          │
          ▼
  ⑦ render                  Markdown panel + token footer
```

Two details worth calling out:

- **Retries are bounded and selective.** Only transient statuses (408, 429,
  500, 502, 503, 504) are retried, with linear backoff. A `401` fails fast
  because retrying a bad key never helps.
- **The connection is always closed.** Streaming responses are consumed inside a
  `with` block, so the socket is released even if parsing raises or you hit
  `Ctrl-C` mid-answer.

---

## Architecture

```text
                       ┌──────────────────────────────┐
   promptpilot  ─────► │          cli.py              │  Typer commands
                       │  (config group, chat, ask…)  │
                       └──────────────┬───────────────┘
                                      │
                       ┌──────────────▼───────────────┐
                       │       services.py             │  application rules
                       │  PromptPilotService           │  (key resolution,
                       │                               │   stats, orchestration)
                       └───┬───────────────────────┬───┘
                           │                       │
            ┌──────────────▼─────────┐   ┌─────────▼─────────┐
            │  clients.py            │   │  async_client.py  │
            │  GroqApiClient         │   │  AsyncGroq…       │
            │  + SSE streaming        │   │  + gather batching│
            └──────────────┬─────────┘   └─────────┬─────────┘
                           │                       │
                           └───────────┬───────────┘
                                       │
                         ┌─────────────▼──────────────┐
                         │   Groq REST API (HTTPS)     │
                         └─────────────────────────────┘

     config.py ──► AppConfig (JSON)          stores.py ──► PromptStat (JSONL)
```

| Layer | Responsibility |
|---|---|
| `cli.py` | Parsing, output mode, error translation. No business rules. |
| `ui.py` | Every piece of Rich rendering. Pure presentation. |
| `picker.py` | The interactive model picker — search, grouping, raw key handling. |
| `services.py` | The application boundary: key resolution, statistics, orchestration. |
| `clients.py` / `async_client.py` | The HTTP boundary: headers, timeouts, retries, SSE parsing, schema validation. |
| `schemas.py` | Pydantic models that validate every untrusted payload. |
| `decorators.py` | `timed` and bounded retry as reusable cross-cutting behaviour. |
| `stores.py` / `config.py` | Persistence: JSONL statistics and JSON configuration. |
| `workers.py` | Thread-pool execution for I/O-bound work. |
| `benchmark.py` | Latency measurement and percentile aggregation. |

**Why the split matters:** the CLI can be replaced without touching the HTTP
code, and the HTTP code can be replaced without touching the CLI. Both are
covered by tests that never open a socket.

---

## Project layout

```text
PromptPilot/
├── pyproject.toml                 # packaging, dependencies, ruff + pytest config
├── README.md
├── LICENSE                        # MIT
├── .env.example
├── docs/
│   ├── demo.svg                   # animated terminal demo for the README
│   └── demo.cast                  # the raw asciinema recording
├── src/promptpilot/
│   ├── __init__.py                # package metadata
│   ├── __main__.py                # `python -m promptpilot`
│   ├── cli.py                     # Typer commands, `config` sub-app, completions
│   ├── ui.py                      # Rich theme, panels, tables, JSON serializers
│   ├── services.py                # PromptPilotService — the application facade
│   ├── clients.py                 # sync REST client + SSE streaming
│   ├── async_client.py            # async REST client + gather batching
│   ├── picker.py                  # interactive model picker (search + groups)
│   ├── benchmark.py               # latency benchmark primitives
│   ├── workers.py                 # thread-pool utilities
│   ├── config.py                  # JSON config + cross-platform paths
│   ├── stores.py                  # JSONL statistics store
│   ├── schemas.py                 # Pydantic request/response models
│   ├── decorators.py              # timing and retry decorators
│   ├── utils.py                   # small pure helpers
│   ├── constants.py               # shared defaults
│   └── exceptions.py              # domain error hierarchy
├── tests/                         # 216 tests, no network, no API key, no network, no API key
│   ├── conftest.py
│   ├── test_schemas.py            # validation and constraints
│   ├── test_config.py             # config round-trip and env overrides
│   ├── test_cross_platform.py     # Linux, macOS, and Windows behaviour
│   ├── test_stores.py             # JSONL persistence
│   ├── test_utils.py              # pure helpers
│   ├── test_decorators.py         # timing and retry policy
│   ├── test_clients.py            # mocked HTTP boundary
│   ├── test_streaming.py          # SSE parsing
│   ├── test_async_client.py       # async client and gather
│   ├── test_workers.py            # thread pool
│   ├── test_benchmark.py          # latency aggregation
│   ├── test_picker.py             # grouping, filtering, and key handling
│   ├── test_service.py            # application rules
│   ├── test_cli.py                # command dispatch and JSON output
│   ├── test_chat.py               # interactive session
│   └── test_ui.py                 # presentation layer
├── scripts/
│   ├── build_linux.sh             # PyInstaller release bundle for Linux
│   └── build_windows.ps1          # PyInstaller release bundle for Windows
└── .github/workflows/
    ├── release.yml                # test matrix + release publishing
    └── publish-pypi.yml           # publish the wheel and sdist to PyPI
```

---

## Development

```bash
python -m pip install -e ".[dev]"

python -m pytest                                    # run the suite
python -m pytest --cov=promptpilot --cov-report=term-missing
python -m pytest tests/test_streaming.py -v          # a single module

ruff check src tests                                 # lint
ruff check src tests --fix                           # lint and autofix
```

The suite is fast and hermetic: `respx` intercepts HTTPX at the transport
level, so **no network access and no API key are required**. That makes it
safe to run on every commit and in CI.

Current status:

```text
216 passed
89% coverage
ruff: all checks passed
```

---

## Releases

Every release publishes four things: a **Linux** standalone binary, a
**Windows** standalone executable, a **Python wheel**, and a **source
distribution**. Pick whichever suits you.

| Platform | Asset | Needs Python? |
|---|---|---|
| Linux | `promptpilot-vX.Y.Z-linux-x64.tar.gz` | no |
| Windows | `promptpilot-vX.Y.Z-windows-x64.zip` | no |
| Any | `promptpilot-X.Y.Z-py3-none-any.whl` | yes |
| Any | `promptpilot-X.Y.Z.tar.gz` | yes |

Download them from the
[Releases page](https://github.com/trinay126/PromptPilot/releases). Each bundle
contains a `SHA256SUMS.txt` file so you can verify the download:

```bash
sha256sum -c SHA256SUMS.txt
```

### Linux — standalone binary

No Python required. Download, extract, and put it on your `PATH`:

```bash
VERSION=v1.0.0
curl -LO "https://github.com/trinay126/PromptPilot/releases/download/${VERSION}/promptpilot-${VERSION}-linux-x64.tar.gz"
tar -xzf "promptpilot-${VERSION}-linux-x64.tar.gz"
sudo install -m 0755 "promptpilot-${VERSION}-linux-x64/promptpilot" /usr/local/bin/promptpilot
promptpilot --version
```

### Linux — with pipx (recommended)

Isolated from your system Python, and upgrades with `pipx upgrade`:

```bash
pipx install promptpilot
```

### Windows — standalone executable

Download `promptpilot-vX.Y.Z-windows-x64.zip`, extract it, and run
`promptpilot.exe`. Add the folder to your `PATH` to use it from anywhere.

```powershell
$env:Path += ";$PWD\promptpilot-v1.0.0-windows-x64"
promptpilot --version
```

### Any platform — Python package

```bash
pip install promptpilot
```

### Build it yourself

The same scripts the release workflow uses are in the repository:

```bash
./scripts/build_linux.sh                 # Linux bundle
.\scripts\build_windows.ps1              # Windows bundle (PowerShell)
```

Each script installs the dependencies, runs the whole test suite, builds the
binary with PyInstaller, smoke-tests it, and writes a versioned bundle:

```text
artifacts/
├── promptpilot-v1.0.0-linux-x64/
│   ├── promptpilot
│   ├── release-manifest.json
│   └── SHA256SUMS.txt
└── promptpilot-v1.0.0-linux-x64.tar.gz
```

PyInstaller is not a cross-compiler, so the Windows bundle must be built on
Windows. The `release.yml` workflow tests Linux, macOS, and Windows on every
pull request, and a `v*.*.*` tag publishes the signed bundles to a GitHub
release.

---

## Troubleshooting

### Usage errors show you what to type

If you get the syntax wrong, PromptPilot says so in its own style and prints a
command that actually works — never a raw stack trace:

```text
╭─────────────────────────────────── Usage ────────────────────────────────────╮
│                                                                              │
│  Option '--model' requires an argument.                                      │
│                                                                              │
│  Try:                                                                        │
│    promptpilot benchmark --model llama-3.1-8b-instant --rounds 3             │
│  Run 'benchmark --help' for the full list of options.                        │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Exit codes follow the usual Unix convention:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | A handled error (missing key, API failure, invalid configuration) |
| `2` | A usage error (unknown command, missing argument, bad option) |

<details>
<summary><strong>"promptpilot: command not found"</strong></summary>

The tool is installed inside the project virtual environment, which is only on
your `PATH` while that environment is active. Either activate it:

```bash
cd ~/path/to/PromptPilot
source .venv/bin/activate
promptpilot --version
```

…or install it once, system-wide, with [`pipx`](https://pipx.pypa.io/) so it
works from any directory without activating anything:

```bash
pipx install git+https://github.com/trinay126/PromptPilot.git
```

If `pipx ensurepath` is required, run it and restart your shell afterwards.
</details>

<details>
<summary><strong>The CLI says "No Groq API key found"</strong></summary>

You have not stored a key yet. Run `promptpilot config set-key`, or export
`GROQ_API_KEY` in your shell. `promptpilot config show` shows which source is
currently active. The key is stored once and reused by every later command.
</details>

<details>
<summary><strong>My key is rejected with HTTP 401</strong></summary>

The key was sent but Groq did not accept it. It may be revoked, truncated, or
from a different account. Re-store it with `promptpilot config set-key`. The
key is masked everywhere PromptPilot displays it, so check for a stray space
by re-entering it.
</details>

<details>
<summary><strong>I get HTTP 429</strong></summary>

You are being rate limited by Groq. Wait a moment and retry. PromptPilot
already retries `429` responses three times with linear backoff, so a
persistent `429` means the account itself is over its limit.
</details>

<details>
<summary><strong>A model returns "not found"</strong></summary>

Model IDs are account-specific and change over time. Run `promptpilot models`
to see the live catalog for your key, and use the exact ID.
</details>

<details>
<summary><strong>My statistics look empty</strong></summary>

Statistics are local and per-machine. They are written to `stats.jsonl` next
to your config file — run `promptpilot config path` to find it. If you have
never run a prompt, the file will not exist yet. `promptpilot clear-stats`
deletes it.
</details>

<details>
<summary><strong>How do I start completely fresh?</strong></summary>

```bash
promptpilot clear-stats
rm -f "$(promptpilot --json config path | jq -r .config_path)"
```

</details>

---

## FAQ

**Do I need a paid Groq plan?**
No. The Groq free tier is enough for everything in this README.

**Will it ask me for my key every time?**
No. `promptpilot config set-key` writes it to your user config directory and
every later command reads it from there. It is asked once, and masked in all
output.

**Is my key ever sent anywhere except Groq?**
No. It travels only in the `Authorization` header of requests to
`api.groq.com`. It is never logged, never printed unmasked, and never
committed.

**Does the test suite call the real API?**
Never. `respx` mocks the HTTPX transport, so the suite runs fully offline in
about a second.

**Why not use the official `groq` SDK?**
Because the point of this project is to show the HTTP layer directly — status
codes, headers, timeouts, retries, and SSE parsing are all visible. The
service layer is shaped so swapping in the SDK later would be a one-file
change.

**Can I use this without a Groq key?**
You can install it, run the tests, and explore `promptpilot --help`,
`promptpilot config show`, and `promptpilot dashboard`. Anything that talks to
Groq needs a key.

**Why does `benchmark` show a "Fastest" line?**
With several models, the table alone makes you do the arithmetic. The summary
line names the winner directly — but remember the numbers reflect one moment
on one network, not a permanent ranking.

**Does it work on Windows?**
Yes. Configuration lives in `%APPDATA%\promptpilot\config.json`, a prebuilt
`promptpilot.exe` ships with every release, and the test matrix covers Python
3.11–3.13 on Windows. The one difference is the interactive model picker,
which falls back to a numbered list when the console cannot provide raw input.

---

## Security model

- **Your key never leaves your machine** except in the `Authorization` header
  sent to Groq. It is never logged, never printed unmasked, and never committed.
- `promptpilot config show` always masks the key (`gsk_...7890`).
- The repository ships **no key of any kind** — there is no bundled demo key
  to extract from a released binary.
- `.env` and `.env.*` are git-ignored, and only `.env.example` is tracked.
- A key stored in the config file is written with the same permissions as the
  rest of your user config directory.

---

## Contributing

Contributions are welcome. The workflow is deliberately small:

1. Open an issue describing the change, so the design can be discussed first.
2. Create a branch: `git checkout -b feature/short-description`
3. Keep the suite green: `python -m pytest` and `ruff check src tests`
4. Add tests for anything you change — the suite is fast and does not need a key
5. Open a pull request describing what changed and why

Please keep the five runtime dependencies as they are. Adding a dependency is
a design decision, not an implementation detail.

---

## License

Released under the [MIT License](LICENSE).

```text
MIT License
Copyright (c) 2026 Chadalavada Trinay Sai
```

Built by [Chadalavada Trinay Sai](https://github.com/trinay126).
