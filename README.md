<div align="center">

# PromptPilot

**A production-minded Groq AI command-line workbench.**

Real SSE streaming · interactive multi-turn chat · live model benchmarking ·
local statistics · machine-readable `--json` output — wrapped in a polished
terminal UI and backed by a fully typed, fully tested service layer.

[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-2ea44f?logo=open-source-initiative&logoColor=white)](LICENSE)
[![CI](https://github.com/trinay126/PromptPilot/actions/workflows/release-windows.yml/badge.svg)](https://github.com/trinay126/PromptPilot/actions/workflows/release-windows.yml)
[![Lint: ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white)](pyproject.toml)
[![Typed](https://img.shields.io/badge/typing-annotated-2A6DB2?logo=python&logoColor=white)](src/promptpilot/schemas.py)

[**Install**](#quick-start) &nbsp;·&nbsp; [**Commands**](#command-reference) &nbsp;·&nbsp; [**Configure**](#configuration) &nbsp;·&nbsp; [**Architecture**](#architecture) &nbsp;·&nbsp; [**Develop**](#development)

</div>

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ ●  ●  ●   promptpilot — Groq AI command-line workbench                     │
├────────────────────────────────────────────────────────────────────────────┤
│ ╭───────────────────────── llama-3.1-8b-instant ─────────────────────────╮ │
│ │                                                                        │ │
│ │  A decorator wraps a callable to add behaviour without changing its    │ │
│ │  signature.                                                            │ │
│ │                                                                        │ │
│ │                                                                        │ │
│ │   import functools                                                     │ │
│ │                                                                        │ │
│ │   def logged(func):                                                    │ │
│ │       @functools.wraps(func)                                           │ │
│ │       def wrapper(*args, **kwargs):                                    │ │
│ │           print(f'calling {func.__name__}')                            │ │
│ │           return func(*args, **kwargs)                                 │ │
│ │       return wrapper                                                   │ │
│ │                                                                        │ │
│ │                                                                        │ │
│ │  Read the source of the wrappers you use — most of them are a dozen    │ │
│ │  lines long.                                                           │ │
│ │                                                                        │ │
│ ╰──────────────── 18 prompt + 142 completion = 160 total ────────────────╯ │
└────────────────────────────────────────────────────────────────────────────┘
```

<div align="center">

**Get started in three commands**

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
| **11** | **164** | **88%** | **0** |

| Runtime deps | Test suite | Network in CI | License |
|:------------:|:----------:|:-------------:|:-------:|
| **5** | **~1 second** | **0 calls** | **MIT** |

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
| **Zero-configuration onboarding** | One guided command stores your key. No bundled key and no demo allowance — you always authenticate as yourself. |
| **Real streaming** | Server-Sent Events are parsed at the wire level, so tokens render the moment Groq produces them. |
| **Interactive chat** | A REPL that sends earlier turns back as context, with `/help`, `/history`, `/reset`, and `/exit`. |
| **Automation-first** | A global `--json` flag turns every command into a clean JSON document for `jq`, CI, and shell pipelines. |
| **Honest benchmarks** | Average, median, P95, min, and max latency per model, with the fastest one called out. |
| **Zero-dependency tests** | `respx` mocks the HTTPX transport, so the suite runs offline, for free, in about a second. |

---

## Table of contents

- [At a glance](#at-a-glance)
- [Why PromptPilot](#why-promptpilot)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Linux and other Unix systems](#linux-and-other-unix-systems)
- [Command cheat sheet](#command-cheat-sheet)
- [Command reference](#command-reference)
  - [ask](#ask) · [chat](#chat) · [batch](#batch) · [models](#models)
  - [dashboard](#dashboard) · [history](#history) · [benchmark](#benchmark) · [probe](#probe)
  - [clear-stats](#clear-stats) · [completions](#completions) · [config](#config)
- [Automation with `--json`](#automation-with---json)
- [Configuration](#configuration)
- [Under the hood](#under-the-hood)
- [Architecture](#architecture)
- [Project layout](#project-layout)
- [Development](#development)
- [Windows executable](#windows-executable)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Security model](#security-model)
- [Contributing](#contributing)
- [License](#license)

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
└───┴────────────────━━━━━━━━─┴────────┘
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

**`promptpilot benchmark` — end-to-end latency compared across models:**

```text
                                Groq model benchmark
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Model           ┃ Success ┃ Average  ┃ Median   ┃ P95      ┃ Min      ┃ Max      ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ llama-3.1-8b-i… │ 2/2     │ 46.66 ms │ 46.66 ms │ 15.88 ms │ 15.88 ms │ 77.45 ms │
│ llama-3.3-70b-… │ 2/2     │ 18.58 ms │ 18.58 ms │ 17.76 ms │ 17.76 ms │ 19.41 ms │
└─────────────────┴─────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
Fastest: llama-3.3-70b-versatile
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

## Requirements

| | |
|---|---|
| **Python** | 3.11 or newer (uses PEP 604 union syntax, `datetime.UTC`, `ParamSpec`) |
| **A Groq account** | A free key from [console.groq.com/keys](https://console.groq.com/keys) |
| **OS** | Linux, macOS, or Windows — configuration paths adapt per platform |

Runtime dependencies: `httpx`, `pydantic`, `python-dotenv`, `rich`, `typer`.
That is the whole list.

On Linux, [pipx](https://pipx.pypa.io/) is the recommended way to install the
tool, and shell completion is supported for `bash`, `zsh`, and `fish` — see
[Linux and other Unix systems](#linux-and-other-unix-systems).

---

## Quick start

**1 — Install**

```bash
git clone https://github.com/trinay126/PromptPilot.git
cd PromptPilot
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

**2 — Add your key**

Create a free key at [console.groq.com/keys](https://console.groq.com/keys), then:

```bash
promptpilot config set-key
```

The prompt hides what you type. The key is written to your user config
directory and is never committed to the repository. Exporting `GROQ_API_KEY`
works too — PromptPilot prefers a saved key and falls back to the environment.

**3 — Say something**

```bash
promptpilot ask "Explain Python decorators in one paragraph."
```

> **Note** — PromptPilot uses **your own** API key. There is no bundled key and
> no demo allowance, so nothing you run is metered against someone else's
> account.

---

## Linux and other Unix systems

PromptPilot is a native Unix citizen: it uses XDG paths, reads `.env` files,
speaks your shell's completion protocol, and stays quiet and machine-readable
when it is not attached to a terminal.

### Install

Two supported routes, depending on whether you want to *use* the tool or
*develop* it.

**As a user — [`pipx`](https://pipx.pypa.io/).** `pipx` installs the tool into
its own isolated virtual environment and puts it on your `PATH`. No `sudo`, no
`pip install --user`, and no risk of breaking the system Python:

```bash
# Debian/Ubuntu
sudo apt install pipx && pipx ensurepath

# Fedora
sudo dnf install pipx && pipx ensurepath

# Arch
sudo pacman -S python-pipx && pipx ensurepath

# from source, straight from git
pipx install git+https://github.com/trinay126/PromptPilot.git
```

`pipx ensurepath` adds `~/.local/bin` to your `PATH`; restart the shell
afterwards.

**As a developer — a local virtual environment:**

```bash
git clone https://github.com/trinay126/PromptPilot.git
cd PromptPilot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Use `python3` rather than `python` on distributions where `python` is not
mapped to Python 3 — most modern Linux systems do not provide a bare `python`
command at all.

### Shell completion

Tab completion for commands, subcommands, and options works with `bash`,
`zsh`, and `fish`.

```bash
# bash — the standard bash-completion location
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

Because the script goes to **stdout**, you can place it wherever your setup
expects it — a dotfiles repository, a Debian package, a container image, or a
Nix/Home Manager configuration:

```bash
# dotfiles repository, managed by chezmoi / stow / yadm
promptpilot completions bash > ~/.local/share/bash-completion/completions/promptpilot

# container image
RUN promptpilot completions bash > /etc/bash_completion.d/promptpilot

# Nix (Home Manager)
programs.bash.enableCompletion = true;
programs.bash.completions.promptpilot = "${pkgs.promptpilot}/share/bash-completion/completions/promptpilot";
```

If you would rather not manage the file yourself, the built-in installer writes
it for you:

```bash
promptpilot --install-completion     # writes to the default location for your shell
promptpilot --show-completion        # print it without installing
```

### Where configuration lives

On Linux, PromptPilot follows the **XDG Base Directory** specification:

```text
$XDG_CONFIG_HOME/promptpilot/config.json     # default: ~/.config/promptpilot/config.json
$XDG_CONFIG_HOME/promptpilot/stats.jsonl     # local request history
```

Override the location for a single run, or for a whole CI job:

```bash
XDG_CONFIG_HOME=/tmp/promptpilot-config promptpilot config show
```

A `.env` file in the working directory is loaded automatically, which is handy
for a project checkout:

```bash
cat > .env <<'EOF'
GROQ_API_KEY=gsk_your_key_here
PROMPTPILOT_MODEL=llama-3.3-70b-versatile
EOF
```

`.env` is git-ignored by default. Remember that `GROQ_API_KEY` in the
environment takes precedence over nothing else — a key saved with
`promptpilot config set-key` wins over the environment variable.

### Headless, pipes, and CI

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

Exit codes follow the usual Unix convention:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | A handled error (missing key, API failure, invalid configuration) |
| `2` | A usage error (unknown command, missing argument, bad option) |

A worked example — pull the average latency out of the dashboard with `jq`:

```bash
promptpilot --json dashboard | jq -r '.stats.average_latency_ms'
```

### Running on a schedule

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

### Running inside a container

The project installs cleanly into a slim image:

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

---

## Command cheat sheet

```bash
# one-shot
promptpilot ask "your prompt"
promptpilot ask --stream "your prompt"            # live token stream
promptpilot ask -m llama-3.3-70b-versatile "..."   # pick a model

# conversation
promptpilot chat                                   # multi-turn REPL

# concurrency
promptpilot batch "prompt one" "prompt two"        # asyncio.gather
promptpilot probe model-a model-b                  # thread pool

# discovery
promptpilot models                                 # live catalog
promptpilot benchmark -m model-a -m model-b --rounds 3

# local state
promptpilot dashboard                              # config + usage
promptpilot history --limit 25                     # recent prompts
promptpilot clear-stats                            # wipe history

# configuration
promptpilot config set-key
promptpilot config set-model llama-3.3-70b-versatile
promptpilot config show
promptpilot config path

# shell integration
promptpilot completions bash > ~/.local/share/bash-completion/completions/promptpilot

# automation
promptpilot --json dashboard | jq .stats
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
│ ask          Send one prompt and print the answer.                           │
│ chat         Start an interactive chat session that remembers the            │
│              conversation.                                                   │
│ batch        Run multiple prompts concurrently with asyncio.gather.          │
│ models       List the live model catalog returned by Groq.                   │
│ dashboard    Show local configuration and usage statistics.                  │
│ history      Show the most recent prompts recorded on this machine.          │
│ benchmark    Compare end-to-end latency for one prompt across models.        │
│ probe        Demonstrate a thread pool with independent tiny API requests.   │
│ clear-stats  Delete the local statistics history.                            │
│ completions  Print the shell completion script for bash, zsh, or fish.       │
│ config       Manage your local PromptPilot configuration.                    │
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

```bash
promptpilot benchmark \
  --model llama-3.1-8b-instant \
  --model llama-3.3-70b-versatile \
  --rounds 3 \
  --prompt "Reply with the single word OK."
```

| Option | Default | Description |
|---|---|---|
| `--model`, `-m` | *required* | Repeat the benchmark for each model |
| `--prompt`, `-p` | `Reply with the single word OK.` | Prompt to send each round |
| `--rounds` | `3` | Repeats per model (1–20) |

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
anywhere your setup expects it — see [Linux and other Unix systems](#linux-and-other-unix-systems).

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
it automatically.

**Configuration file** — `promptpilot config path` prints the exact locations:

| Platform | Path |
|---|---|
| Windows | `%APPDATA%\promptpilot\config.json` |
| macOS | `~/Library/Application Support/promptpilot/config.json` |
| Linux | `$XDG_CONFIG_HOME/promptpilot/config.json` (or `~/.config/…`) |

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
├── src/promptpilot/
│   ├── __init__.py                # package metadata
│   ├── __main__.py                # `python -m promptpilot`
│   ├── cli.py                     # Typer commands, `config` sub-app, completions
│   ├── ui.py                      # Rich theme, panels, tables, JSON serializers
│   ├── services.py                # PromptPilotService — the application facade
│   ├── clients.py                 # sync REST client + SSE streaming
│   ├── async_client.py            # async REST client + gather batching
│   ├── benchmark.py               # latency benchmark primitives
│   ├── workers.py                 # thread-pool utilities
│   ├── config.py                  # JSON config + cross-platform paths
│   ├── stores.py                  # JSONL statistics store
│   ├── schemas.py                 # Pydantic request/response models
│   ├── decorators.py              # timing and retry decorators
│   ├── utils.py                   # small pure helpers
│   ├── constants.py               # shared defaults
│   └── exceptions.py              # domain error hierarchy
├── tests/                         # 164 tests, no network, no API key
│   ├── conftest.py
│   ├── test_schemas.py            # validation and constraints
│   ├── test_config.py             # config round-trip and env overrides
│   ├── test_stores.py             # JSONL persistence
│   ├── test_utils.py              # pure helpers
│   ├── test_decorators.py         # timing and retry policy
│   ├── test_clients.py            # mocked HTTP boundary
│   ├── test_streaming.py          # SSE parsing
│   ├── test_async_client.py       # async client and gather
│   ├── test_workers.py            # thread pool
│   ├── test_benchmark.py          # latency aggregation
│   ├── test_service.py            # application rules
│   ├── test_cli.py                # command dispatch and JSON output
│   ├── test_chat.py               # interactive session
│   └── test_ui.py                 # presentation layer
├── scripts/
│   └── build_windows.ps1          # PyInstaller release bundle
└── .github/workflows/
    └── release-windows.yml        # test matrix + release publishing
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
164 passed
88% coverage
ruff: all checks passed
```

---

## Windows executable

```powershell
.\scripts\build_windows.ps1
```

The script installs dependencies, runs the test suite, builds `promptpilot.exe`
with PyInstaller, smoke-tests the binary, and produces a versioned bundle:

```text
artifacts/
└── promptpilot-v1.0.0-windows-x64/
    ├── promptpilot.exe
    ├── release-manifest.json
    └── SHA256SUMS.txt
```

PyInstaller is not a cross-compiler, so the build runs on Windows. The
`release-windows.yml` workflow tests Python 3.11, 3.12, and 3.13 on every pull
request, and a `v*.*.*` tag publishes the signed bundle to a GitHub release.

---

## Troubleshooting

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
currently active.
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
