# kinnoo.yaml Manifest Schema Reference

This document explains the fields in the `kinnoo.yaml` manifest — the heart of every Kinnoo agent package. It covers what each field specifies and provides concrete examples.

Archive note: Kinnoo package files use the `.kno` extension and are stored as ZIP archives.

---

## Field Definitions

### `entrypoint`

This is the file the `kinnoo` runtime executes when someone runs your agent. It's the "front door" of your agent — the single file that receives the input, runs the agent logic, and emits the output.

Think of it exactly like:
- `main.py` in a Python script
- `index.js` in a Node app
- `CMD` in a Dockerfile

Unlike a web server that stays alive, an agent entrypoint typically runs once per invocation: receive input → do agentic work → return output → exit.

**The MVP runtime contract is:** `python <entrypoint> "<input string>"`

So if `entrypoint: run.py`, the CLI executes:
```bash
python run.py "Help me refund an order"
```

---

### `dependencies`

This is the list of Python packages required to run the agent — equivalent to `requirements.txt` but declared inline in the manifest so the CLI can read and display them without inspecting the filesystem.

These are the same pip package names you'd write in `requirements.txt`:
- `openai` — to call GPT-4
- `langchain` — the orchestration framework
- `requests` — HTTP calls to external APIs

The CLI uses this list for two things: showing users what they're about to install (security warning), and driving `pip install` into the managed virtual environment.

---

### `inputs.type`

This describes the **shape of data the agent expects to receive**. For the MVP, only `text` is supported — meaning the agent receives a plain string as its only input (passed as a command-line argument).

This exists as a field because in future versions it will expand to:
- `json` — structured data object
- `file` — a file path
- `image` — multimodal input
- `conversation` — a chat history array

Declaring this upfront makes agents self-describing and enables the CLI to validate input before invoking the agent, and enables future composition (chaining agents together).

---

### `outputs.type`

Same idea, but for what the agent **produces**. For the MVP, `text` means the agent prints a plain string to stdout and exits.

Future values would include `json`, `file`, `stream` (for streaming token output), etc.

Declaring output type is what makes agents composable — if agent A outputs `json` and agent B accepts `json` as input, the CLI can eventually wire them together automatically.

---

### `runtime.type`

Declares the execution model of the agent. For the MVP, the only supported value is `one-shot` — meaning the agent process starts, receives input, produces output, and exits. The CLI will invoke it as `python <entrypoint> "<input>"` and wait for the process to terminate.

This field exists because future versions will support other execution models:
- `server` — a long-running HTTP server (FastAPI, Flask) that handles multiple requests
- `mcp-server` — a long-running Model Context Protocol server, compatible with GitHub Copilot, Claude, Cursor, etc.
- `worker` — a background queue consumer

The CLI's behavior on `kinnoo run` is determined entirely by this field.

---

### Feature9 optional fields (`description`, `author`, `license`, `env_vars`)

Feature9 adds optional metadata fields to `kinnoo.yaml`. These fields are optional-only and do not change validity for existing V1 manifests.

- `description` (optional): string
- `author` (optional): string
- `license` (optional): string
- `env_vars` (optional): list[string]

`env_vars` item constraints:
- each item must be a string
- each item must be non-empty (empty or whitespace-only values are invalid)

V1 compatibility note:
- manifests that omit `description`, `author`, `license`, and `env_vars` remain valid
- legacy validation behavior is unchanged when these fields are absent

Valid example:

```yaml
description: "Customer support agent"
author: "Kinnoo Team"
license: "MIT"
env_vars:
  - OPENAI_API_KEY
  - ANTHROPIC_API_KEY
```

Invalid `env_vars` example:

```yaml
env_vars:
  - OPENAI_API_KEY
  - ""
  - "   "
```

### Feature10 env_vars runtime security contract

When `env_vars` is declared, runtime resolution order is:

1. process environment
2. agent-local `.env`
3. masked interactive prompt (for unresolved names)

Non-disclosure invariant:

- secret values must never be printed, logged, or persisted
- diagnostics must reference variable names only

Safe troubleshooting:

- verify that required names are present in `env_vars`
- confirm those names are set in process environment or `.env`
- when prompted, enter values interactively without echoing values into logs

---

## Concrete Examples

### Example 1 — Simple LangChain customer support agent

```yaml
name: customer-support-agent
version: 0.1.0
entrypoint: run.py
runtime:
  language: python
  version: ">=3.10"
  type: one-shot
dependencies:
  - langchain
  - langchain-openai
  - requests
framework: langchain
inputs:
  type: text
outputs:
  type: text
```

**What happens at runtime:**
```bash
kinnoo run customer-support-agent "I need to cancel my order #1234"
# Internally: python run.py "I need to cancel my order #1234"
# Agent uses LangChain + OpenAI to reason and respond
# Prints answer to stdout
```

---

### Example 2 — CrewAI research agent

```yaml
name: research-summarizer
version: 0.2.1
entrypoint: agent.py
runtime:
  language: python
  version: ">=3.11"
  type: one-shot
dependencies:
  - crewai
  - openai
  - duckduckgo-search
framework: crewai
inputs:
  type: text
outputs:
  type: text
```

**What happens at runtime:**
```bash
kinnoo run research-summarizer "Summarize recent advances in fusion energy"
# Internally: python agent.py "Summarize recent advances in fusion energy"
# CrewAI orchestrates multiple sub-agents (researcher, writer)
# Final summary printed to stdout
```

---

## Key Insight: Framework Agnosticism

Notice that both examples look nearly identical from the CLI's perspective — `kinnoo` doesn't know or care that one uses LangChain and the other uses CrewAI. That's the entire point of the `entrypoint` + `inputs/outputs` contract: **the runtime abstraction makes the framework irrelevant to the platform.** The complexity lives inside `run.py` / `agent.py`, not in the manifest.

---

## Full Schema Reference Table

| Field            | Required | Type         | Constraints                                     |
|------------------|----------|--------------|-------------------------------------------------|
| name             | yes      | string       | non-empty, alphanumeric and hyphens             |
| version          | yes      | string       | valid semver (e.g., "0.1.0", "1.2.3")           |
| entrypoint       | yes      | string       | non-empty file path                             |
| runtime.language | yes      | string       | e.g., "python"                                  |
| runtime.version  | yes      | string       | version constraint (e.g., ">=3.10")             |
| runtime.type     | yes      | string       | must be `"one-shot"` for MVP                    |
| dependencies     | yes      | list[string] | can be empty list                               |
| inputs.type      | yes      | string       | e.g., "text"                                    |
| outputs.type     | yes      | string       | e.g., "text"                                    |
| framework        | no       | string       | optional, e.g., "langchain", "crewai"           |
| description      | no       | string       | optional metadata                                 |
| author           | no       | string       | optional metadata                                 |
| license          | no       | string       | optional metadata                                 |
| env_vars         | no       | list[string] | optional; each item must be a non-empty string    |

---

## Manifest Cross-File Rule (TESTS.txt and TASKS.txt)

For project manifest consistency:

- In `TESTS.txt`, each item in `covers` must reference acceptance criteria only, using:
  - `feature: featureX`
  - `ac: ACY`
- Do not place `task: taskX` entries inside `TESTS.txt` `covers`.
- Task-to-test linkage belongs in `TASKS.txt` via each task's `tests: [testA, testB]` list.

This matches the manifest validator behavior in `src/validate_project_manifests.py`.

---

## `kinnoo inspect` command (Feature11)

`kinnoo inspect` displays manifest metadata from either a source directory or a packaged `.kno` archive.

Usage:

- `kinnoo inspect <agent-dir>`
- `kinnoo inspect <archive.kno>`

Examples:

```bash
kinnoo inspect ./my-agent
kinnoo inspect ./my-agent.kno
```

Output semantics:

- human-readable formatted text (not raw YAML)
- missing optional fields are omitted
- `env_vars` are names-only (never values)

Directory guidance behavior:

- if `kinnoo.yaml` is missing, inspect prints guidance with a minimal manifest example and exits non-zero
- if `requirements.txt` is missing, inspect prints guidance with:
  - `pip install uv`
  - `uv export --format requirements-txt > requirements.txt`

Common failure cases:

- missing target argument → `Usage: kinnoo inspect <target>`
- invalid archive format → clear invalid zip-based `.kno` error
- invalid manifest content → `Error: Manifest validation failed.` plus field-level validator messages

---

## Pack/Publish Refactor commands (Feature13)

Feature13 refactors command responsibilities to an archive-first packaging source plus mock-registry publishing target.

### Pack destination

- `kinnoo pack <agent-dir>` writes to local archive by default:
  - `~/.kinnoo/archive/<agent>/<version>/<agent>.kno`
- Test/custom override:
  - `KINNOO_ARCHIVE_ROOT`

### Publish semantics

Canonical publish commands:

- `kinnoo publish <agent-name>`
- `kinnoo publish <agent-name> --local`

Behavior:

- source resolves latest local archive artifact for `<agent-name>`
- target path in mock registry:
  - `~/kinnoo-mock-registry-scratch/jerry/<agent>/<version>/<agent>.kno`
- if tagged target exists, prior payload rolls to:
  - `~/kinnoo-mock-registry-scratch/jerry/<agent>/untagged-<n>/`

### Install selectors

Supported forms:

- `kinnoo install <name>` (latest from mock registry)
- `kinnoo install <name>==<version>` (exact from mock registry)
- `kinnoo install <file-path/file.kno>` (backward-compatible direct file install)

### List source modes

- `kinnoo list` (default local archive)
- `kinnoo list --local` (same as default)
- `kinnoo list --remote` (mock registry)

### Search source modes

- `kinnoo search <query>` (default local archive)
- `kinnoo search --local <query>` (same as default)
- `kinnoo search --remote <query>` (mock registry)

Search behavior remains case-insensitive substring matching across name and description fields.

### Migration guidance from Feature12

- Previous publish form:
  - `kinnoo publish <archive.kno>`
- Feature13 canonical form:
  - `kinnoo publish <agent-name>`

- Previous docs centered on `~/.kinnoo/registry/` as primary source/target.
- Feature13 split of responsibilities:
  - packaging source-of-truth: local archive (`~/.kinnoo/archive/...`)
  - publish/install remote target: mock registry (`~/kinnoo-mock-registry-scratch/jerry/...`)
