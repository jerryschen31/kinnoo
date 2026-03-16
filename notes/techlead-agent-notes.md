

## Phase 3 Feature Definition (2026-03-13)

### Feature22 scan policy update (2026-03-15)

- Approved direction: asset credential detection during `kinnoo pack` remains warning-only because packing is a local operation.
- Follow-up design note: evaluate stricter/blocking secret scans at `kinnoo publish` time for registry-bound artifacts.

Created 10 features (feature20–feature29) for Phase 3: "Share any agent. Run it with its full stack."

### Decomposition from Phase 3 Notes (6 high-level → 10 features)

The 6 high-level features from `notes/phases/phase3-notes-opus-4-6.md` were decomposed as follows:

1. **Remote Registry** (3-4 weeks) → split into 3 features:
   - **feature27**: Registry Backend Abstraction & Remote Client (CLI-side protocol + HTTP client)
   - **feature28**: Remote Registry Server (FastAPI + S3 + JSON metadata + auth)
   - **feature29**: Registry Web UI (Jinja2 templates, session auth, browsing)

2. **Flexible Runtime Inputs** (3-5 days) → 1 feature:
   - **feature20**: No-input run + `--` pass-through arguments + `inputs.required` schema field

3. **Service Declarations & Health Checks** (1.5-2.5 weeks) → split into 2 features:
   - **feature24**: Service Declarations Schema (manifest `services` section + validation only)
   - **feature25**: Service Health Checks Runtime (preflight checks: HTTP, TCP, process)

4. **Data & Asset Bundling** (4-7 days) → 1 feature:
   - **feature22**: Manifest `data` section, pack/install integration, size warnings

5. **MCP Server Packaging & Client Templates** (2-3 weeks) → split into 2 features:
   - **feature23**: MCP Server Runtime Type (schema + supervisor lifecycle in run_command)
   - **feature26**: MCP Server Packages & Client Templates (FS MCP server, GitHub MCP server, mcp-client template, permissions)

6. **Framework & Template Expansion** (1-1.5 weeks) → 1 feature:
   - **feature21**: PydanticAI, LangGraph, OpenAI Agents SDK templates

### Implementation Order (recommended)

**Wave 1 — Quick wins, independent (parallel):**
- feature20 (Flexible Runtime Inputs) — small, high-value
- feature21 (Framework Templates) — self-contained, no cross-cutting changes
- feature22 (Data Bundling) — small, builds on existing pack/install

**Wave 2 — New runtime type:**
- feature23 (MCP Server Runtime Type) — establishes `mcp-server` in schema + supervisor

**Wave 3 — Schema extensions:**
- feature24 (Service Declarations Schema) — schema-only, clean

**Wave 4 — MCP ecosystem:**
- feature26 (MCP Packages & Client Templates) — depends on feature23 + feature21

**Wave 5 — Runtime integration:**
- feature25 (Service Health Checks) — depends on feature24, benefits from feature23

**Wave 6 — Registry (longest tail, can overlap with waves 2-5):**
- feature27 (Registry Client Abstraction) — start anytime
- feature28 (Registry Server) — depends on feature27
- feature29 (Registry Web UI) — depends on feature28

### Regression Risk Summary

| Feature | Risk | Tests to Verify |
|---------|------|-----------------|
| feature20 | HIGH — changes `kinnoo run` argparse (input is currently required positional) | test_cli.py, test_install.py |
| feature21 | MEDIUM — adds --framework choices to cli.py/init_command.py | test_init.py, test_cli.py |
| feature22 | MEDIUM — changes pack/install archive handling | test_pack.py, test_cli_install.py, test_cli_install_extract.py |
| feature23 | HIGH — adds `mcp-server` to SUPPORTED_RUNTIME_TYPES, may break validator tests that assert only `one-shot` | test_validator.py |
| feature24 | LOW — additive schema change only | test_validator.py |
| feature25 | LOW — additive runtime behavior | test_cli.py (preflight tests) |
| feature26 | MEDIUM — new --framework choice + permissions schema | test_init.py, test_validator.py |
| feature27 | HIGH — refactors publish/install/list/search internals | test_cli.py, test_cli_install.py, test_install.py |
| feature28 | NONE — new server app, separate from CLI | (new server tests) |
| feature29 | NONE — extends server app | (new server tests) |

### Key Design Decisions

- Split Remote Registry into 3 features (client → server → UI) to allow incremental delivery and review
- Split MCP into runtime type + packages to avoid a monolithic feature
- Split Service Declarations into schema + runtime for cleaner separation of concerns
- All features have explicit regression notes in YAML so SWE agents know which test suites to run
- Manifest validator passes after all additions (confirmed via `python3 src/validate_project_manifests.py`)

---

## Feature20 SWE Handoff Created (2026-03-15)

- Created dedicated handoff brief at `notes/features/feature20-notes.md`.
- Handoff includes:
  - ordered execution plan for `task121` -> `task124`
  - per-task file targets and expected tests
  - full AC-to-test mapping for feature20 (AC1-AC8)
  - explicit regression test commands and risk callouts
- Branching guidance included: `phase3/feature20/main` + per-task branches.


## Feature18 Task Breakdown (2026-03-13)

- Created 4 tasks (task116–task119) and 16 tests (test149–test164) for feature18 "Input Safety Guard".
- Updated feature18 description and ACs in FEATURES.txt to include:
  - 6 threat categories (added XSS and template injection beyond original 4)
  - Type-aware checking for future parameterized inputs (-e, -i, -d, -u)
  - `check_inputs()` multi-value method for future multi-parameter input mode
  - Non-interactive TTY fail-safe (auto-abort when stdin is not a TTY)
  - 8 ACs (expanded from original 6)
- Task execution order: task116 → task117 → task118 → task119 (strictly sequential)
- Key design decisions:
  - Protocol-based `InputGuard` with `check(value, input_type)` and `check_inputs(inputs)` for current + future input models
  - Break after first pattern match per category per value to avoid warning floods
  - Type-aware filtering: file_path → path traversal + shell only; url → SSRF + shell only; id → SQL + shell + template only
  - Non-interactive mode auto-aborts as fail-safe (requires `--no-guard` for CI)
- SWE handoff written to notes/swe-handoff.md with detailed per-task implementation guidance
- Manifest validation passed after all changes

---

## Feature17 Pre-Merge Review (2026-03-12)

- Reviewed tasks task112-task115 against AC1-AC4 with code + tests + docs.
- Feature17-targeted tests passed:
  - tests/test_pack_size_reporting.py
  - tests/test_docs.py::test_feature17_docs_cover_pack_size_reporting
- Full repository suite is currently not green (18 failures), mainly around existing pack/install expectation drift.
- Decision: do not approve feature17 merge to phase2/main until full-suite failures are resolved or formally waived.
- Traceability fix applied during review: corrected stale TESTS.txt automation_path entries for test144/test145/test146; manifest validation passes.

---

## V2 Fallback for Missing Wheels (2026-02-25)

To improve robustness and developer experience in V2:

1. If "kinnoo pack" cannot create or download a wheel for a dependency, it should issue a warning (not an error) and record the missing dependency somewhere—ideally as a "notes" field in kinnoo.yaml.
2. If "kinnoo install" does not find a wheel for a dependency listed in requirements.txt, it should warn the user and attempt to install that dependency from requirements.txt (i.e., from source or PyPI), rather than failing outright.

This fallback approach allows packaging and installation to proceed even if some dependencies cannot be built as wheels, while still alerting users to potential reproducibility or offline install issues.
# Running notes for the Tech Lead Agent (techlead.agent.md)

## feature1 — Manifest schema and validation (COMPLETED)

**Status:** Completed 2026-02-17. All 9 tests pass. Manifests validated.

### Files created / modified
| File | Purpose |
|---|---|
| `src/kinnoo/__init__.py` | Package init; re-exports `validate` |
| `src/kinnoo/schema.py` | Constants: `REQUIRED_FIELDS`, `FIELD_TYPES`, `SEMVER_PATTERN`, `NAME_PATTERN`, `SUPPORTED_RUNTIME_TYPES` |
| `src/kinnoo/validator.py` | Public `validate(path) -> (bool, list[str])` function |
| `tests/test_validator.py` | 9 unit tests covering all 7 ACs (test0–test6 plus two extra parameterized helpers) |
| `requirements.txt` | `PyYAML>=6.0`, `pytest>=7.0` |
| `FEATURES.txt` | Fixed YAML structure (added `features:` key, fixed indentation, quoted AC5 description) |
| `TASKS.txt` | Fixed YAML syntax (quoted step3 description); all tasks marked `completed` |

### Key design decisions
- Nested manifest fields (`runtime.language`, `inputs.type`, etc.) are accessed with a `_get_nested()` helper using dot-separated paths — keeps `schema.py` constants clean and `validator.py` logic uniform.
- Semver validation uses the canonical regex from semver.org; it correctly rejects `"1.0"` (missing patch) and accepts pre-release/build-metadata suffixes.
- `runtime.type` is validated against `SUPPORTED_RUNTIME_TYPES = ["one-shot"]` — extensible for V2 without changing validator logic.
- `framework` field is intentionally absent from `REQUIRED_FIELDS` and `FIELD_TYPES`; it is silently accepted when present (no extra logic needed).

### Manifest fixes made during setup
1. **FEATURES.txt**: was missing top-level `features:` key; content was not indented under it; AC5 description had an unquoted colon sequence `(is_valid: bool, ...)`.
2. **TASKS.txt**: task0 step3 had an unquoted colon sequence `validate(manifest_path: str)`.
Both files now pass `python3 src/validate_project_manifests.py`.

---


---

## Framework Support Strategy — MVP vs V2 Decision

**Decision Date:** 2026-02-18  
**Status:** Approved  
**Scope:** Features 1-3 (MVP)

### Decision Summary
Features 1-3 will remain **framework-agnostic** with black-box execution. Deep framework integration (LangChain, CrewAI, AutoGen adapters) is deferred to V2+.

### Rationale

**MVP Philosophy (from mvp.md):**
- "Treat every agent as a black-box executable. If it runs locally, you can package it."
- "Framework differences become irrelevant. Later you build adapters."
- Runtime contract: `python run.py "<input>"` → output to stdout

**Benefits of Deferring:**
1. **Clean scope** — avoids framework coupling in MVP
2. **Faster delivery** — no adapter complexity, testing matrix stays simple
3. **Already works** — any agent following the entrypoint contract runs today (LangChain, CrewAI, custom)
4. **Future-proof** — `framework` field already exists in manifest as metadata/discoverability

### What This Means for Features 1-3

**✅ Feature 1 (Manifest):**
- Optional `framework` field accepted but not used at runtime (metadata only)
- No framework-specific validation

**✅ Feature 2 (`kinnoo init`):**
- Generates vanilla Python scaffolding with minimal dependencies
- asyncio boilerplate included (see "Notes on Framework Compatibility" section)
- No framework-specific templates (e.g., no `--framework=langchain` flag)

**✅ Feature 3 (`kinnoo run`):**
- Framework-agnostic execution: blindly runs `python run.py "<input>"`
- No special handling for LangChain, CrewAI, etc.
- Works with any framework that follows the contract

### Pre-Built LangChain Agent Compatibility

**Q: Will a pre-built LangChain agent work with features 1-3?**  
**A: Yes, if structured correctly:**

```python
# run.py (user's existing LangChain agent)
from langchain import Agent
import sys

agent = Agent(...)
result = agent.run(sys.argv[1])
print(result)
```

### Requirements for any pre-built agent to work with features 1-3:

- Runnable entrypoint (run.py) that accepts input
- Framework dependencies listed in requirements.txt
- Follows input/output contract (CLI arg → stdout)
- Developer manually creates kinnoo.yaml
- This works because MVP treats agents as black boxes — no framework awareness needed.

### V2+ Framework Adapters (Post-MVP)
- When framework-specific features add value, implement as coherent V2 feature set:

- Feature N: Framework-Aware Scaffolding

```
kinnoo init --framework=langchain → LangChain-specific template
kinnoo init --framework=crewai → CrewAI-specific template
kinnoo init --framework=autogen → AutoGen-specific template with async setup
```

- Feature N+1: Framework Detection & Optimization

- Auto-detect framework from kinnoo.yaml framework field
- Framework-specific execution optimizations
- Framework-specific dependency validation
- Feature N+2: Framework Configuration Helpers

- kinnoo config langchain --model=gpt-4 → generates LangChain config
- Framework-specific tool/chain scaffolding

- Design Principle:
  - All framework features are opt-in via the framework field. Omitting it keeps black-box behavior. This ensures backward compatibility and doesn't force framework adoption.

## Notes on Framework Compatibility with `python run.py`

### ⚠️ MVP: Async entrypoint template

Two of the top 5 frameworks (AutoGen, OpenAI Agents SDK) are async-first and require
`asyncio.run()` boilerplate in the entrypoint script. The hello-world `run.py` template
generated by `kinnoo init` should include this infrastructure by default — it is harmless
for synchronous agents (LangChain, CrewAI, smolagents) and required for async ones.

Recommended default `run.py` template:

```python
import sys
import asyncio

async def main(input_text: str) -> str:
    # Agent logic here
    return "Hello from your agent!"

if __name__ == "__main__":
    input_text = sys.argv[1] if len(sys.argv) > 1 else ""
    result = asyncio.run(main(input_text))
    print(result)

## 🔮 V2+: MCP Server support

### Background
As of early 2026, GitHub Copilot, Claude, Cursor, and others have adopted
**Model Context Protocol (MCP)** as the universal standard for agent/tool extensibility.
An MCP server is a long-running process that exposes tools via structured JSON-RPC
over stdin/stdout or HTTP — it is fundamentally different from a one-shot Python script.

This means MCP servers are **not** compatible with the MVP runtime contract
(`python run.py "<input>"`), which assumes a one-shot execution model.

### Why this matters for Kinnoo
MCP is becoming the cross-platform tool standard. Supporting MCP server packages
in Kinnoo would make the platform relevant to a much broader ecosystem — any developer
building tools for Copilot, Claude, Cursor, Windsurf, or other MCP-compatible clients
could use Kinnoo to package and distribute them.

### What V2 support would require
- A new manifest field: `runtime.type: mcp-server` (vs. the default `runtime.type: one-shot`)
- A different execution model in the CLI: `kinnoo run` would launch the server as a
  long-running process rather than invoking a one-shot script
- A different entrypoint contract: the server listens on stdin/stdout or a local HTTP port
  rather than accepting a CLI argument and printing to stdout

### MVP stance
MCP support is explicitly out of scope for MVP. The `runtime.language` and entrypoint
fields in `kinnoo.yaml` are designed to be extensible to support this in V2 without
breaking the manifest schema.

## 🔮 V2+: Manifest schema expansions

The following fields are **not** in scope for MVP. They are documented here for
forward planning. All additions are designed to be additive — MVP manifests remain
valid in V2+.

---

### 1. Runtime type — long-running processes

```yaml
runtime:
  language: python
  version: ">=3.10"
  type: one-shot        # MVP — python run.py "<input>", process exits
  # type: server        # Long-running HTTP server (FastAPI, Flask)
  # type: mcp-server    # Long-running MCP protocol server (stdin/stdout or HTTP)
  # type: worker        # Long-running background worker (queue consumer)
  port: 8080            # Required when type: server or mcp-server
```

For `type: server`, `kinnoo run` would launch the process and keep it alive.
For `type: mcp-server`, the CLI would handle the MCP handshake.

---

### 2. Memory / context

```yaml
memory:
  type: none            # MVP default — stateless
  # type: in-process   # Agent manages state internally within a session
  # type: vector        # External vector store (semantic search / RAG)
  # type: key-value     # Simple persistent state (Redis, DynamoDB)
  # type: episodic      # Conversation/episode history

  # When type: vector or episodic:
  backend: pinecone     # pinecone | chroma | weaviate | pgvector | qdrant
  embedding_model: text-embedding-3-small
  collection: my-agent-memory
  retention_policy: 30d
```

---

### 3. Tools, MCP servers, databases

```yaml
tools:
  - name: web_search
    type: builtin         # Kinnoo-native tool

  - name: github
    type: mcp             # MCP server
    server: github/github-mcp-server
    version: ">=1.0.0"
    auth: env.GITHUB_TOKEN

  - name: customer_db
    type: database
    engine: postgres
    connection: env.DATABASE_URL
    permissions:
      - SELECT            # read-only for safety

  - name: internal_api
    type: http
    base_url: https://api.internal.company.com
    auth:
      type: bearer
      token: env.INTERNAL_API_KEY
    endpoints:
      - GET /orders/{id}
      - POST /refunds
```

---

### 4. File store / RAG vector store

```yaml
storage:
  files:
    - name: documents
      type: local           # local | s3 | gcs | azure-blob
      path: ./data/
      permissions: read     # read | write | read-write

    - name: output_store
      type: s3
      bucket: env.OUTPUT_BUCKET
      prefix: agents/my-agent/outputs/
      permissions: write

  vector_stores:
    - name: product_catalog
      type: pinecone        # pinecone | chroma | weaviate | pgvector | qdrant
      index: product-embeddings
      embedding_model: text-embedding-3-small
      connection: env.PINECONE_API_KEY
      permissions: read
```

---

### Design principles for all V2+ fields

- `type:` field on every block — keeps the schema extensible without breaking existing manifests
- `env.*` references for all secrets — never hardcoded values
- `permissions:` wherever the agent touches external systems — foundation for the future sandboxing/permission model
- MVP fields remain unchanged — all V2+ fields are purely additive

---

## Agent Portability & Sharing — Current State and Kinnoo Solution

**Analysis Date:** 2026-02-18

### Current State of Agent Sharing (2026)

#### The Reality: Still Fragmented and Frustrating

**Typical workflow today:**

1. Clone repo
2. Read README (if it exists)
3. Figure out Python version, create venv
4. `pip install -r requirements.txt` (pray for no conflicts)
5. Hunt for required env vars / API keys
6. Discover missing system tools (ffmpeg, poppler, etc.)
7. Debug framework-specific config files
8. Finally run... and hit a runtime error

**Pain points by framework:**

| Framework | Typical Friction |
|-----------|------------------|
| LangChain | Heavy deps, version sensitivity, config spread across files |
| CrewAI | Crew/agent YAML configs, role definitions, tool wiring |
| AutoGen | Async setup, conversation patterns, multi-agent orchestration |

**What makes sharing hard today:**
- No standard manifest → every repo is a snowflake
- No standard entrypoint → `main.py`? `run.py`? `agent.py`? `python -m agent`?
- Implicit dependencies → "oh you need Redis running" buried in code
- API key management → scattered .env patterns, no validation
- Framework lock-in → CrewAI agent can't easily run LangChain tools

---

### How Kinnoo Solves This

#### Core Insight

The problem isn't technical complexity—it's **lack of convention**. Kinnoo provides:

1. **Standard manifest** → predictable metadata
2. **Standard entrypoint** → `python run.py "<input>"`
3. **Bundled dependencies** → reproducible installs
4. **Declarative requirements** → explicit runtime needs

#### Solving Runtime Assumptions (Pragmatic Approach)

**Not complicated. Here's the plan:**

##### Layer 1: Declare It (Manifest Extensions)

````yaml
# filepath: kinnoo.yaml
name: my-agent
version: 1.0.0
entrypoint: run.py

# New fields (simple additions)
runtime:
  python: "3.11"
  
tools:
  - name: ffmpeg
    required: false
  - name: tesseract
    required: true

services:
  - name: redis
    mock: true  # kinnoo can provide a mock

resources:
  gpu: optional  # or "required" or "none"
````

**Implementation effort:** Extend existing schema validator. ~1-2 tasks.

##### Layer 2: Check It (Preflight)

````bash
$ kinnoo run my-agent --preflight

✓ Python 3.11 found
✓ ffmpeg found (optional)
✗ tesseract not found (required)
  → Fix: brew install tesseract
✓ redis mock available
✓ GPU not required
````

**Implementation:** Simple Python checks using `shutil.which()`, `subprocess`, `platform`. ~2-3 tasks.

##### Layer 3: Bundle It (Wheel Cache)

````bash
$ kinnoo pack

Downloading wheels for platform: macosx_arm64
Bundling 47 packages into my-agent-1.0.0.kno
````

**Implementation:** Use `pip wheel` + `pip download`. Store in archive. Install with `pip install --find-links`. ~2-3 tasks.

##### Layer 4: Mock It (Service Stubs)

For common services, provide drop-in mocks:

| Service | Kinnoo Mock |
|---------|-------------|
| Redis | `fakeredis` (pure Python) |
| PostgreSQL | SQLite with compatibility shim |
| S3 | `moto` or local filesystem |

**Implementation:** Ship a small `kinnoo.mocks` module with these. Inject via env vars. ~3-4 tasks.

##### Layer 5: Escape Hatch (Docker/Remote)

When local won't work:

````bash
$ kinnoo run my-agent --docker    # Use bundled Dockerfile
$ kinnoo run my-agent --remote    # Send to configured runner
````

**Implementation:** Generate Dockerfile from manifest. Remote runner is V2+. ~2-3 tasks for Docker.

---

### Complexity Assessment

| Component | Effort | Builds On |
|-----------|--------|-----------|
| Manifest extensions | Low | Existing schema (feature1) |
| Preflight checker | Low | stdlib: shutil, subprocess, platform |
| Wheel bundling | Medium | pip wheel, pip download |
| Service mocks | Medium | Existing libs: fakeredis, moto |
| Docker generation | Low | Template Dockerfile from manifest |
| Remote runner | Higher | Defer to V2 |

**Total for MVP portability:** ~10-15 tasks, spread across 2-3 features

**For a Senior Engineer with AI agent assistance:** Very doable. You're orchestrating existing tools, not building from scratch.

---

### What Makes Kinnoo Unique (vs "just use Docker")

| Docker Approach | Kinnoo Approach |
|-----------------|-----------------|
| Heavy images (GB) | Lightweight bundles (MB) |
| Requires Docker installed | Native Python, Docker optional |
| Opaque blob | Inspectable manifest + wheels |
| All-or-nothing isolation | Graduated: venv → sandbox → container |
| Slow iteration | Fast local runs |
| Hard to customize | Easy to extend/mock |

**Kinnoo philosophy:** Docker is an escape hatch, not the default. Most agents don't need full containerization—they need reproducible Python environments with clear contracts.

---

### Recommended Roadmap

**MVP (Features 1-5):**
- Manifest with runtime/tools/services fields
- Preflight checker with actionable output
- Wheel bundling in `.kno` archive
- Basic service mocks (redis, sqlite-as-postgres)

**V1.1:**
- Dockerfile generation from manifest
- GPU detection and warnings
- Tool auto-install suggestions

**V2:**
- Remote runner for GPU/heavy workloads
- Framework adapters (LangChain, CrewAI templates)
- Registry with capability filtering

---

### Summary

| Question | Answer |
|----------|--------|
| Is sharing agents hard today? | Yes—no conventions, implicit deps, framework sprawl |
| Can kinnoo solve this? | Yes—standard manifest + entrypoint + bundling |
| Is it complicated to build? | No—mostly glue code over existing tools |
| Doable for Senior Engineer + AI? | Absolutely—10-15 focused tasks |

The hard part isn't the code—it's the design decisions. You've already made the key ones (black-box execution, framework-agnostic MVP, declarative manifest). Implementation is straightforward integration work.

---

## Packaging Kinnoo for Pip Installation — MVP Requirement

**Decision Date:** 2026-02-18  
**Status:** **Required for MVP** (likely the final feature)  
**Context:** User feedback

### Problem Statement

**Q: How would a user install `kinnoo`?**  
**A:** The most common way to install Python packages like `kinnoo` is via `pip`. This requires packaging the project as a Python package and making it available through either:
- **PyPI** (Python Package Index) — public registry, `pip install kinnoo`
- **Git repository** — direct install, `pip install git+https://github.com/username/kinnoo.git`

### Why This Must Be Part of the MVP

**Core principle:** If kinnoo is a tool for making agents easy to install and run, then **kinnoo itself must be easy to install and run.**

Without proper packaging:
- Other developers can't easily try kinnoo
- Installation requires manual cloning, venv setup, dependency installation
- No version management or updates
- Violates the "batteries included" philosophy

### Current State

The groundwork is already in place:
- ✅ `pyproject.toml` exists in the project
- ✅ Package structure already set up (`src/kinnoo/`)
- ✅ Console script entry point already specified (task4 for feature2)

### What's Required (Implementation Plan)

#### 1. Complete `pyproject.toml` Metadata

Add the necessary metadata fields:

```toml
[project]
name = "kinnoo"
version = "0.1.0"  # Start with MVP version
description = "A lightweight package manager for AI agents"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}  # or appropriate license
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["ai", "agents", "packaging", "cli"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.urls]
Homepage = "https://github.com/username/kinnoo"
Repository = "https://github.com/username/kinnoo"
Issues = "https://github.com/username/kinnoo/issues"

dependencies = [
    "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
]

[project.scripts]
kinnoo = "kinnoo.cli:main"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

#### 2. Test Local Installation

Before publishing, verify the package installs correctly:

```bash
# Build the package
python3 -m build

# Install locally from the built wheel
pip install dist/kinnoo-0.1.0-py3-none-any.whl

# Test the CLI
kinnoo --help
kinnoo init test-agent
```

#### 3. Build and Share Wheel Files (MVP Distribution Method)

**Strategy:** Start simple—build wheels and share directly with early users.

```bash
# Build the package
python3 -m build

# This creates dist/kinnoo-0.1.0-py3-none-any.whl
# Share this file with early users via email, Slack, Dropbox, etc.

# Users install locally:
pip install kinnoo-0.1.0-py3-none-any.whl
```

**Pros:**
- ✅ **Simplest possible distribution** — no servers, no infrastructure
- ✅ **Complete privacy** — only people you explicitly send the file to can install
- ✅ **No Git access needed** — just a .whl file
- ✅ **Fast iteration** — build and share new versions instantly
- ✅ **Perfect for MVP validation** — get feedback before investing in infrastructure

**Cons:**
- Manual distribution (acceptable for small group of early users)
- No automatic updates (users install new .whl files manually)
- Not scalable beyond ~10-20 users

**Privacy considerations:**
- ✅ **Maximum privacy** — you control exactly who gets the file
- ✅ **No public exposure** — not indexed by AI bots or search engines
- ✅ **No Git repo needed** — can even work with completely private/local development

#### 4. Private Git-Based Installation (Post-V2, For Scaling Private Testing)

**Deferred to post-V2** when ready to scale beyond direct file sharing:

```bash
# Invited collaborators with repo access can install:
pip install git+https://github.com/username/kinnoo.git@v0.2.0
```

This requires:
- Private Git repository with controlled access
- Access control via GitHub collaborators/teams
- Users need Git access (SSH keys or tokens)

**When to transition:** When manual wheel sharing becomes cumbersome (~10-20+ users), or when you want automatic version tracking.

Alternative: **GitHub Packages** (PyPI-compatible private hosting)

#### 5. Public PyPI Publication (V3/V4+, After Product-Market Fit)

**Deferred to V3/V4+** when kinnoo has achieved product-market fit with private users:

```bash
# Build distribution packages
python3 -m build

# Upload to public PyPI (makes it publicly accessible)
python3 -m twine upload dist/*

# Anyone can then install:
pip install kinnoo
```

⚠️ **PyPI is completely public** — only publish when ready for full public release.

Optional pre-release testing with **TestPyPI**:

```bash
python3 -m twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ kinnoo
```

### Recommended Approach for MVP

**MVP (Private Wheel Distribution):**
1. Complete `pyproject.toml` metadata
2. Test local installation (`pip install .`)
3. Build wheel: `python3 -m build`
4. Test wheel installation: `pip install dist/kinnoo-0.1.0-py3-none-any.whl`
5. Document wheel installation in README.md
6. Share .whl file directly with early users (email, Slack, etc.)

**Post-V2 (Scale Private Distribution):**
7. Set up private GitHub repo (if not already)
8. Test Git-based installation
9. Document Git installation method
10. Transition users to Git-based installs
11. Alternative: Consider GitHub Packages for PyPI-like private hosting

**V3/V4+ (Public Release, After Product-Market Fit):**
12. Optional: Test on TestPyPI first
13. Publish to public PyPI
14. Update README with `pip install kinnoo`
15. Public announcement

### Implementation Effort

| Task | Effort | Priority | Phase |
|------|--------|----------|-------|
| Complete pyproject.toml metadata | Low (1 task) | **Required** | MVP |
| Test local installation (`pip install .`) | Low (validation) | **Required** | MVP |
| Build wheel (`python3 -m build`) | Low (validation) | **Required** | MVP |
| Test wheel installation | Low (validation) | **Required** | MVP |
| Update README with wheel install instructions | Low (documentation) | **Required** | MVP |
| Set up Git-based installation | Low (validation) | Optional | Post-V2 |
| GitHub Packages setup | Medium (1-2 tasks) | Optional | Post-V2 |
| Publish to TestPyPI | Medium (1-2 tasks) | Optional | V3/V4+ |
| Publish to public PyPI | Medium (1-2 tasks) | Deferred | V3/V4+ |

**Total MVP effort:** 2-3 tasks for wheel-based distribution

### Where This Fits in the MVP

**Recommendation:** Make this the **last feature** before declaring MVP complete.

**Rationale:**
1. All other features (manifest validation, init, run, list, etc.) must be implemented first
2. Packaging is the final step that proves kinnoo is ready for users
3. Enables dogfooding—use kinnoo to package kinnoo
4. Natural completion milestone—"kinnoo can now be distributed as a wheel"
5. Maximum privacy for early validation—you control exactly who gets access
6. Simple to scale up later (Git → PyPI) as project matures

### Success Criteria

**MVP (Wheel Distribution):**

When complete, you should be able to:

```bash
# Build kinnoo
python3 -m build

# Install and test locally
pip install dist/kinnoo-0.1.0-py3-none-any.whl
kinnoo --version
kinnoo init my-agent
cd my-agent
kinnoo run "Hello, world!"

# Share with early users
# They can install the same way:
pip install kinnoo-0.1.0-py3-none-any.whl
```

**Post-V2 (Git-Based Distribution, When Scaling):**

```bash
# Users with repo access install:
pip install git+https://github.com/username/kinnoo.git@v0.2.0

# Same commands work
kinnoo --version
kinnoo init my-agent
```

**V3/V4+ (Public PyPI, After Product-Market Fit):**

```bash
# Public installation
pip install kinnoo

# Same commands work
kinnoo --version
kinnoo init my-agent
```

### Distribution Strategy Summary

| Phase | Method | Target Audience | Privacy Level |
|-------|--------|-----------------|---------------|
| **MVP** | **Wheel files** | Early testers (1-10) | **Maximum** — you control file sharing |
| Post-V2 | Git-based or GitHub Packages | Private beta (10-100) | High — invite-only via repo access |
| V3/V4+ | Public PyPI | General public | Public — anyone can install |

**This is essential for the MVP vision: making AI agents as easy to install as any other Python package, while starting with the simplest distribution method and maintaining maximum privacy during early validation.**

---

## V2 Strategy: LangChain Adapter + MCP Server Integration

**Decision Date:** 2026-02-18  
**Status:** Planned (post-MVP)  
**Scope:** V2

### V2 Goal

**One framework, done extremely well, with real tool support.**

Enable a LangChain developer to package an agent that uses MCP tools, share it, and have another developer run it with minimal friction.

### Why LangChain First?

- Largest community (most users to validate with)
- Most documentation/examples
- LangChain has native MCP support
- If kinnoo works for LangChain, others will ask for their framework
- Demand-driven expansion > speculative expansion

### MCP Support Levels

| Level | What | V2? | Complexity |
|-------|------|-----|------------|
| **Declare** | List MCP servers in manifest | ✅ Yes | Low |
| **Verify** | Preflight checks ("is this server available?") | ✅ Yes | Low |
| **Launch** | `kinnoo run` starts required MCP servers | ✅ Yes | Medium |
| **Bundle** | Package MCP server binaries into .kno | ❌ V3+ | High |

**V2 Scope:** Declare + Verify + Launch (not Bundle)

### MCP Manifest Schema

```yaml
# kinnoo.yaml
name: my-research-agent
version: 1.0.0
framework: langchain

mcp_servers:
  - name: filesystem
    package: "@anthropics/mcp-filesystem"  # npm package
    config:
      allowed_directories:
        - "./data"
    required: true
    
  - name: brave-search
    package: "@anthropics/mcp-brave-search"
    config:
      api_key: env.BRAVE_API_KEY
    required: true
    
  - name: github
    package: "@anthropics/mcp-github"
    config:
      token: env.GITHUB_TOKEN
    required: false  # optional tool
    
  - name: postgres
    package: "@anthropics/mcp-postgres"
    config:
      connection_string: env.DATABASE_URL
    required: false
```

### What `kinnoo run` Does in V2

```bash
$ kinnoo run my-agent "research topic X"

Preflight checks:
✓ Python 3.11 found
✓ Node.js/npx available
✓ MCP server: filesystem (npx @anthropics/mcp-filesystem)
✓ MCP server: brave-search (npx @anthropics/mcp-brave-search)
  → BRAVE_API_KEY set
✗ MCP server: github (optional, skipping)
  → GITHUB_TOKEN not set

Starting MCP servers...
✓ filesystem listening on stdio
✓ brave-search listening on stdio

Running agent...
[agent output]

Shutting down MCP servers...
```

### Why This Works

1. **Most MCP servers are npm packages** → `npx @anthropics/mcp-xxx` just works
2. **Stdio-based** → No port management, just spawn processes
3. **Config is declarative** → User fills in env vars, kinnoo wires it up
4. **Credentials via env** → No secrets in manifest, standard pattern
5. **LangChain has MCP support** → Native integration, no custom wiring

### Supported MCP Servers (V2 Initial Set)

Focus on stable, well-documented npm packages:

| Server | Package | Use Case |
|--------|---------|----------|
| Filesystem | `@anthropics/mcp-filesystem` | Read/write local files |
| Brave Search | `@anthropics/mcp-brave-search` | Web search |
| GitHub | `@anthropics/mcp-github` | Repo operations |
| Postgres | `@anthropics/mcp-postgres` | Database queries |
| Supabase | `@supabase/mcp-server` | Supabase integration |
| SQLite | `@anthropics/mcp-sqlite` | Local database |

### What We're NOT Doing in V2

- **Bundling server binaries** → User must have npx/node installed (acceptable)
- **Custom MCP servers** → Only well-known packages with stable APIs
- **HTTP-based MCP servers** → Stdio only (simpler lifecycle)
- **Server versioning/pinning** → Use latest (add pinning in V3)
- **Memory abstraction** → Too complex, framework-specific (defer to V3)
- **Other framework adapters** → CrewAI, AutoGen, etc. deferred to V3

### V2 Developer Workflow

```bash
# Create agent with LangChain + MCP tools
kinnoo init my-agent --framework=langchain --mcp=filesystem,brave-search

# Edit agent logic, configure API keys in .env
cd my-agent && edit...

# Run with MCP servers auto-launched
kinnoo run . "search for X and save to ./data/results.txt"
# → Starts filesystem + brave-search MCP servers
# → Runs agent
# → Agent uses tools
# → Shuts down servers

# Package and share
kinnoo pack
# → my-agent.kno includes manifest with MCP requirements

# Recipient
kinnoo install my-agent.kno
# Preflight warns: "This agent requires BRAVE_API_KEY, Node.js"
kinnoo run my-agent "query"
# → Same MCP server launch flow
```

### V2 Implementation Estimate

| Task | Effort | Notes |
|------|--------|-------|
| `framework` manifest field | Low | Schema extension |
| `mcp_servers` manifest field | Low | Schema extension |
| `kinnoo init --framework=langchain` | Medium | LangChain-specific scaffold |
| `kinnoo init --mcp=...` flag | Medium | MCP server config templates |
| MCP server preflight checks | Low | `which npx`, env var checks |
| MCP server launcher/lifecycle | Medium | Spawn processes, manage stdio |
| Wire to LangChain MCP client | Medium | LangChain has MCP support |
| Common server config templates | Low | 5-6 server configs |
| Documentation | Medium | User guide for LangChain + MCP |

**Total V2 effort:** ~8-12 tasks (4-6 weeks with AI assistance)

### V3+ Roadmap (Deferred)

| Feature | Why Deferred |
|---------|--------------|
| CrewAI adapter | Wait for V2 LangChain validation |
| AutoGen adapter | Wait for V2 LangChain validation |
| MCP server bundling | Complex; requires Node.js packaging |
| Memory abstraction | Framework-specific, needs research |
| Server version pinning | Wait for ecosystem to stabilize |
| HTTP MCP servers | More complex lifecycle management |

### Success Criteria for V2

When complete, this workflow should work end-to-end:

1. Developer A creates LangChain agent with MCP tools
2. Developer A runs `kinnoo pack` → gets `.kno` file
3. Developer A shares `.kno` file with Developer B
4. Developer B runs `kinnoo install` + `kinnoo run`
5. MCP servers launch automatically
6. Agent executes with tools working
7. Developer B did not need to understand MCP, LangChain internals, or manual setup

**Key metric:** Time from receiving `.kno` to running agent < 5 minutes (assuming deps installed).

### Possible additional frameworks to support for V2

Here are some **single-agent frameworks** that would be relatively easy to support in kinnoo V2 (after LangChain and possibly LlamaIndex):

---

### 1. **LlamaIndex**
- **Why easy:** Pythonic, simple agent API, minimal dependencies, similar entrypoint pattern to LangChain.
- **What’s needed:** Template with `llama_index` in `requirements.txt`, example agent in `main.py`.

---

### 2. **Haystack**
- **Why easy:** Well-documented, supports pipeline/agent pattern, can expose a simple `run(input)` interface.
- **What’s needed:** Template with `haystack` in `requirements.txt`, example pipeline/agent in `main.py`.

---

### 3. **Semantic Kernel (Python)**
- **Why easy:** Has a Python SDK, supports function calling and skills, can be wrapped in a simple entrypoint.
- **What’s needed:** Template with `semantic-kernel` in `requirements.txt`, example kernel in `main.py`.

---

### 4. **AutoGPT (as a library)**
- **Why easy:** Recent versions can be used as a Python package, can expose a single-agent workflow.
- **What’s needed:** Template with `autogpt` in `requirements.txt`, example agent in `main.py`.

---

### 5. **OpenAI Function Calling (barebones)**
- **Why easy:** Just needs `openai` package, a prompt, and a function call handler.
- **What’s needed:** Template with `openai` in `requirements.txt`, example function-calling agent in `main.py`.

---

**Summary:**  
LlamaIndex and Haystack are the easiest after LangChain, as they have clear agent APIs and minimal setup.  
Semantic Kernel and barebones OpenAI function-calling are also straightforward.  
Choose frameworks with simple, well-documented APIs and minimal external dependencies for the smoothest V2 integration.
Multi-Agent (LangGraph, CrewAI) is harder

---

## Onboarding Existing Agents — Q&A (2026-03-01)

Great questions. You’re focusing on exactly the right onboarding friction points.

**1) Existing LangChain agent → package with kinnoo pack**
- Keep your existing project; you do not need to rewrite it for Kinnoo.
- Ensure there is a single runnable entrypoint that accepts one input argument and prints output.
- Ensure requirements.txt lists your dependencies.
- Add kinnoo.yaml (or bootstrap it with kinnoo init and adapt it).
- Verify locally with kinnoo run path/to/agent "test input".
- Package with kinnoo pack path/to/agent.
- Result: a .kno archive that others can install/run.

**2) Do they need to write kinnoo.yaml manually?**
- Not strictly. Today, easiest path is bootstrap with kinnoo init, then copy in existing code.
- For required fields and format, developers can use:
  - `README.md`
  - `docs/manifest-schema-reference.md`
- If fields are wrong/missing, runtime/pack validation returns concrete errors, so it is discoverable.
- Typical values:
  - name: project slug
  - version: semantic version like 0.1.0
  - entrypoint: relative path to your run file
  - runtime: python, version constraint, type one-shot
  - dependencies: list from requirements
  - inputs/outputs: usually text for one-shot agents
  - env_vars/framework: optional, as needed

**3) “Easy creation” options (current + near-term)**
- Option A (available now, lowest effort): init-first migration
  - Run kinnoo init, replace run.py with your existing entrypoint, copy deps, tweak kinnoo.yaml.
- Option B (available now): copy/paste minimal manifest template from docs + validator-driven fixes.
- Option C (easy implementation, best UX): add kinnoo import existing-agent-path
  - Auto-detect entrypoint and requirements, generate kinnoo.yaml, then show interactive confirmation.
- Option D (easy implementation): add kinnoo wizard
  - Prompt for each field, validate immediately, and write a correct manifest in one flow.
- Option E (easy implementation): add kinnoo validate --explain
  - Same validation, but with fix suggestions and examples for each failing field.

If you want, I can draft a concrete UX spec for Option C (kinnoo import) with command behavior, prompts, and error handling so SWE can implement it quickly.

### Recommendation note
- Recommended Option C command shape: "kinnoo import <existing-agent-path> <new-agent-dir>"


### Clarification: V1 vs V2 Functionality (LangChain Project Structure)

## V1: Generic Template (Framework-Agnostic)
- `kinnoo init` creates a minimal Python agent scaffold: `run.py`, `kinnoo.yaml`, `requirements.txt`, etc.
- You can use this scaffold to build a LangChain agent, but you must manually add LangChain-specific code, dependencies, and structure.
- V1 does **not** provide LangChain boilerplate, example agent code, or recommended project layout.

### Example: Generic Python Agent Template (V1)

```
my-agent/
├── kinnoo.yaml
├── run.py
├── requirements.txt
├── README.md
├── tools/
└── prompts/
```

**run.py** (example):
```python
import sys

def main(input_text):
    print(f"Hello, you said: {input_text}")

if __name__ == "__main__":
    main(sys.argv[1])
```

---

## V2: Framework-Aware Template (Ready-to-Use)
- `kinnoo init --framework=langchain` creates a project with:
  - LangChain-specific directory structure (e.g., `src/agent.py`, `src/tools.py`)
  - Example LangChain agent code (pre-filled scripts using LangChain classes)
  - LangChain dependencies in `requirements.txt`
  - Example prompts and tool definitions tailored for LangChain
  - Manifest fields pre-populated for LangChain conventions
- You can immediately run or extend the agent without needing to research LangChain setup or copy boilerplate from docs.

### Example: LangChain-Specific Agent Template (V2)

```
my-langchain-agent/
├── kinnoo.yaml
├── src/
│   ├── main.py
│   ├── agent.py
│   └── tools.py
├── requirements.txt
├── README.md
├── prompts/
│   └── system_prompt.txt
└── tools/
```

**src/agent.py** (example):
```python
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI

def build_agent():
    llm = OpenAI()
    tools = [Tool(name="search", func=lambda x: "result", description="Dummy search tool")]
    return initialize_agent(tools, llm, agent="zero-shot-react-description")
```

**src/main.py** (example):
```python
import sys
from agent import build_agent

def run(input_text):
    agent = build_agent()
    return agent.run(input_text)

if __name__ == "__main__":
    print(run(sys.argv[1]))
```

**requirements.txt** (example):
```
langchain
openai
```

---

**Summary:**
- The **generic template** is minimal and framework-agnostic.
- The **LangChain template** includes a structured `src/` directory, agent/tool definitions, and LangChain-specific dependencies and code patterns.
- V2 reduces friction for new users and helps ensure agents are built correctly for their framework.

### Phase1 Features 5 and 6

After feature3 (`kinnoo run`) and feature4 (add support for LLM APIs), the next natural steps are:

1. **feature5: `kinnoo pack`**
    - Packages the agent project (code, manifest, dependencies) into a distributable archive (like a `.kno` or `.whl` file).
    - This makes it easy to share the agent with others.

2. **feature6: `kinnoo install`**
    - Lets another developer install the packaged agent on their own machine from the archive.
    - Sets up the environment and dependencies so they can immediately use `kinnoo run`.

You don’t need another feature in between unless you want to add advanced checks or preflight validation before packaging.

---

**The basic flow is:**
- Dev A: `kinnoo pack` → share file
- Dev B: `kinnoo install agent.kno` → `kinnoo run agent "input"`

This sequence covers the core agent sharing workflow.

### Design Principles

1. **Declare, don't embed** — MCP servers declared in manifest, not bundled
2. **Env vars for secrets** — No credentials in manifest or package
3. **Fail fast with helpful errors** — Preflight checks before running
4. **One framework first** — Prove the model before expanding
5. **User has Node.js** — Acceptable prerequisite for V2 (can bundle in V3)

---

## Model Selection Flag Exploration (2026-02-24)

- Consider allowing developers to specify a model when initializing an agent via a `--model` flag (e.g., `kinnoo init --framework chatgpt --model gpt-5-nano`).
- This would provide more flexibility for advanced users and future-proof the CLI as new models are released.
- Needs design discussion: Should the flag be required for some frameworks? How to validate model names? How to surface available models?
- Action: Explore feasibility and user experience impact in future planning sessions.

---

## CLI Help Command & Model Discovery (2026-02-24)

- Explore adding an explicit `kinnoo help` command for detailed help, including listing available models and framework-specific info.
- Default usage prompt should highlight that `kinnoo help` provides detailed help (e.g., `kinnoo help --framework gemini` to list Gemini models).
- Consider supporting subcommands/flags for command-specific and framework/model-specific help (e.g., `kinnoo help init`, `kinnoo help gemini models`).
- Optionally, reserve `kinnoo info` for future project/agent metadata queries.
- Implementation should dynamically surface available models/frameworks from a registry/config for up-to-date info.
- Action: Track this for future CLI/UX improvements and discuss design in planning sessions.

---

## Pack/Publish Responsibility Refactor Feedback (2026-03-05)

### Decision Summary
- Feedback accepted: `kinnoo pack` should own local versioned artifact archival.
- `kinnoo publish` should represent publication to an online-style registry flow (mocked locally for now).

### Why this is a better split
- Clarifies responsibilities:
  - `pack` = produce + organize local build artifacts for developer workflows.
  - `publish` = push selected artifact to registry namespace/workspace.
- Removes ambiguity in “local registry” semantics and aligns with common container/package mental models.
- Enables future auth (`kinnoo login`) and remote backend swap with minimal CLI behavior changes.

### Agreed behavior targets
- Local archive root: `~/.kinnoo/archive/<agent>/<version>/<agent>.kno`
- Publish target (V1 mock): `registry-scratch/jerry/<agent>/<version>/<agent>.kno`
- Overwrite protection for publish tags via untagged rollover (`untagged-1`, `untagged-2`, ...)

### Recommended implementation improvements
1. Add reusable path resolver helpers (archive source + publish target) to avoid hardcoded path drift.
2. Add explicit publish manifest metadata validation before copy (agent name/version consistency checks).
3. Emit deterministic, parse-friendly output lines for CI and future UX tooling.
4. Keep untagged rollover logic isolated in a small utility to simplify future remote-registry adapter parity.
5. Mark old feature12 local-registry install/list/search scope as deprecated or explicitly out-of-scope after refactor to avoid dual-behavior confusion.