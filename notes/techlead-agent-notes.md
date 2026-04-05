

## Phase 3 Feature Definition (2026-03-13)

### Feature22 scan policy update (2026-03-15)

- Approved direction: asset credential detection during `kinnoo pack` remains warning-only because packing is a local operation.
- Follow-up design note: evaluate stricter/blocking secret scans at `kinnoo publish` time for registry-bound artifacts.

### Onboarding complexity strategy update (2026-03-16)

- Captured Phase 3 onboarding strategy in `notes/phases/phase3-notes-schema-complexity-thoughts.md`.
- Decision recorded from user: proceed with Strategy 1 (smart defaults/inference) and Strategy 2 (analyzer + wizard), defer Strategy 3 (`--ai` manifest generation).
- `feature19` redesigned as analyzer-backed `kinnoo import` with confirm-first wizard UX.
- Added new `feature27` for reusable analyzer module and detector set (`entrypoint`, `runtime`, `framework`, `dependencies`, `env_vars`, `assets`, `services`).
- Registry roadmap IDs were shifted forward to avoid collision after adding feature27:
  - `feature28`: Registry Backend Abstraction & Remote Client
  - `feature29`: Remote Registry Server
  - `feature30`: Registry Web UI
- Sequencing update (explicit): implement feature23-feature26 first, then feature27, then feature19.
- Manifest updates validated with `python3 src/validate_project_manifests.py` (pass).

### Feature19 import model refinement (2026-03-16)

- Updated `feature19` to in-place onboarding: `kinnoo import [path]` (default `.`), no `<new-agent-dir>` argument.
- Removed copy/scaffold-clone expectation from ACs; import now writes `kinnoo.yaml` into target project without modifying existing source files.
- Added explicit acceptance criterion for entrypoint compatibility handling: warning-first, non-blocking default, optional wrapper generation path.
- Directional rationale: maximize adoption by adding kinnoo metadata to existing projects instead of requiring a duplicate project tree.

### Feature19 implementation planning (2026-03-16)

- Added task decomposition for feature19: `task163`-`task167` in `TASKS.txt`.
- Added test plan for feature19: `test252`-`test262` in `TESTS.txt` with AC coverage mapping for AC1-AC10.
- Updated `FEATURES.txt` feature19 `tasks` list to include `task163`-`task167`.
- Corrected feature19 AC5 wording to reflect in-place rollback semantics (no `<new-agent-dir>` model).
- Replaced `notes/swe-handoff.md` with a dedicated feature19 SWE handoff brief.

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

## Feature40 Review Snapshot (2026-03-19)

- Reviewed feature40 (Archive Signing & Publisher Verification) implementation against tasks `task219`-`task223` and tests `test317`-`test321`.
- Feature40 focused AC gate passes (`5 passed`) for keygen, pack signing, install signature verification, unsigned warning/confirmation, and registry publisher key association.
- Required full regression command `python3 -m pytest --testmon` is currently red with cross-feature install regressions caused by stricter unsigned publisher enforcement defaults.
- Merge recommendation: blocked until install compatibility policy is reconciled and full regression returns green.
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

---

## What You Have After Feature 1–41 (Pre-1.0 Assessment)

### What kinnoo is at that point

After all 41 features are implemented, kinnoo is a **multi-runtime, security-conscious CLI tool for packaging, distributing, inspecting, and running AI agents** — essentially `npm`/`pip` meets `docker` for the agent ecosystem.

Here is what a developer can do with it:

**Core lifecycle (Python and Node.js):**
- `kinnoo init <name>` — scaffold a new agent project from a growing library of framework templates (vanilla Python, Gemini, ChatGPT, Claude, PydanticAI, LangGraph, OpenAI Agents SDK, OpenClaw, MCP client/server)
- `kinnoo run <dir> "<input>"` — validate manifest, resolve env vars, install deps, execute entrypoint, stream output — one command
- `kinnoo pack <dir>` — bundle code + deps + assets + state snapshots + checksums + signature into a portable `.kno` archive (zip-based)
- `kinnoo install <archive.kno>` or `kinnoo install <name>` — extract, verify integrity/signature, install deps, run security sweep, ready to run
- `kinnoo publish <name>` — push a versioned archive to a registry (local mock in v1, remote in feature28-30)

**Transparency and trust (the real differentiator):**
- `kinnoo inspect` — read-only metadata preview for archives and directories, including env var name disclosure, dependency summary, checksum, archive size, and heuristic security sweep
- `kinnoo run --preflight` — non-destructive readiness checklist (runtime version, env vars, entrypoint, deps, service health) before execution
- Input safety guard — regex-based injection detection (SQL, shell, path traversal, SSRF, XSS, template injection) with pluggable Protocol design
- Heuristic code sweep at pack and inspect time — flags env var exposure patterns across Python, JS/TS, and JSON files
- Archive checksums (SHA256 sidecar) and Ed25519 signing for integrity + publisher authenticity
- Manifest permissions model — declared capabilities (network, filesystem, shell, browser) with install-time consent and sandbox enforcement
- Runtime behavior monitoring with kill-switch — policy enforcement, resource limits, behavioral telemetry
- Node.js dependency audit with CVE gating and lifecycle script visibility

**Multi-runtime support:**
- Python: venv-based isolation, pip/wheel offline install, one-shot and MCP server runtime types
- Node.js: npm/pnpm package manager awareness, node_modules exclusion from archives, .js/.mjs execution, daemon runtime type
- OpenClaw: framework-aware scaffold, import detection, skill/memory/identity conventions, state directory snapshots

**Onboarding for existing projects:**
- `kinnoo import [path]` — analyzer-backed wizard that infers manifest fields from project structure (entrypoint, runtime, framework, deps, env vars, assets, services) with confidence-aware output

**Registry (partially implemented — features 28-30 paused):**
- Local archive management with `kinnoo list`, `kinnoo search`
- Mock registry publish/install with versioning and overwrite protection
- Remote registry client abstraction ready but server not built yet

### How to describe it to a developer

> **Kinnoo is a CLI tool that lets you package, share, and run AI agents — like Docker for agent projects.** You define a manifest (`kinnoo.yaml`), and kinnoo handles dependency isolation, environment setup, security scanning, and reproducible execution across Python and Node.js runtimes. It works with any LLM framework (LangChain, PydanticAI, OpenAI Agents SDK, OpenClaw, etc.) and provides built-in input safety guards, archive signing, and a permissions model that keeps humans in control of what agents can do.

### What is genuinely missing before a 1.0 release

This is the honest gap list, ordered roughly by priority for external adoption:

#### 1. Remote registry (features 28-30) — currently paused
Without a real remote registry, there is no `pip install <agent>` equivalent. Developers can share `.kno` files manually, but there is no `kinnoo install my-cool-agent` from a hosted source. This is the **single biggest gap** for adoption. Features 28-30 cover the backend abstraction, FastAPI server, and web UI. They are paused, not cancelled — but they are the bridge between "useful personal tool" and "developer platform."

#### 2. Real-world testing with actual agents
Every feature has unit and integration tests, but kinnoo has not yet been battle-tested against a diverse set of real-world agents across different frameworks and dependency trees. Before 1.0 you need:
- A handful of non-trivial agents (multi-dep, framework-heavy, MCP servers, daemon processes) packed, published, installed, and run through the full lifecycle
- Edge case exposure: large dependency trees, platform-specific wheels, slow network installs, agents with mutable state
- At least one external developer (not you) trying `kinnoo init` → `kinnoo pack` → `kinnoo install` cold, with no guidance beyond the README

#### 3. Documentation for humans
The README is functional but internal-facing. A 1.0 needs:
- **Quickstart guide** — 5 minutes from install to running your first agent
- **Manifest reference** — complete field-by-field docs (you have `docs/manifest-schema-reference.md` but it needs to stay current with V4 schema additions)
- **Security model explainer** — what kinnoo checks, when, and what it does not protect against (honest threat model)
- **Framework guides** — one page per supported framework showing init → configure → pack → share flow
- **CLI reference** — every command, every flag, one-line description, example

#### 4. Polish and UX cleanup
- Error messages should be reviewed end-to-end for consistency (capitalization, formatting, actionable guidance)
- Output formatting across commands should feel like one tool, not 41 features bolted together
- `--help` text for every subcommand needs to be useful and accurate
- Exit codes should be documented and consistent (0 = success, 1 = user error, 2 = internal error, etc.)
- Consider adding `--json` output mode for commands like `inspect`, `list`, `search` for CI/tooling integration

#### 5. Packaging and distribution of kinnoo itself
- `pip install kinnoo` should work from PyPI (you have pyproject.toml but need to verify the publish pipeline)
- `brew install kinnoo` or `npx kinnoo` would lower friction significantly
- Verify the tool works on Linux and Windows (you have been developing on macOS)

#### 6. TypeScript entrypoint support
Feature31 explicitly defers TS transpilation — only `.js/.mjs` execution. If you are targeting OpenClaw and the broader JS/TS ecosystem, many agents will be written in TypeScript. You need either `tsx`/`ts-node` integration or a pre-run transpile step. This is a gap that real Node.js developers will hit immediately.

#### 7. Versioning and upgrade story
- What happens when you `kinnoo install agent-v2` and already have `agent-v1` installed? Side-by-side? Overwrite? Currently this is partially handled but the UX around versioned agent management on disk is not fully cohesive.
- Schema versioning: when the manifest schema changes, what happens to old `.kno` archives? Forward/backward compatibility story needs to be explicit.

#### 8. CI/CD integration story
You have `--yes` flags and non-interactive modes, but there is no documented GitHub Actions / CI pipeline example showing: lint manifest → pack → publish → install → run → verify exit code. This is table-stakes for developer adoption.

### What you do NOT need for 1.0

To keep scope honest, these are things that are **nice-to-have but not blocking**:
- Full OpenClaw gateway orchestration (explicitly deferred)
- ML-based input guard (Protocol is ready, regex is fine for 1.0)
- Channel/QR onboarding UX
- Deep syscall-level runtime monitoring (baseline process monitoring is enough)
- Marketplace / monetization / agent ratings
- GPU/hardware requirement declarations
- Multi-agent orchestration or composition primitives

### Honest self-assessment

After feature 1-41, kinnoo is a **genuinely useful and differentiated tool** that solves a real problem no one else is solving well. The security posture (input guard, code sweep, permissions, signing, monitoring) is far ahead of anything in the agent ecosystem today. The multi-runtime story (Python + Node.js + OpenClaw) covers the two ecosystems where 95%+ of agents live.

The gap between "feature-complete" and "1.0 release" is mostly **distribution, documentation, and real-world validation** — not more features. The registry (features 28-30) is the one significant missing feature set, and even without it, kinnoo is useful for local and team workflows with manual `.kno` file sharing.

If you are preparing for AI Engineer interviews, kinnoo already demonstrates: manifest-driven packaging, multi-runtime orchestration, Protocol-based extensibility (input guard, registry backend, health checks), defense-in-depth security design, and a CLI architecture that follows the same patterns as Docker, npm, and pip. That is a strong portfolio piece regardless of whether the registry ships before your interviews.

5. Mark old feature12 local-registry install/list/search scope as deprecated or explicitly out-of-scope after refactor to avoid dual-behavior confusion.

#### Summary of the section:

After all 41 features, kinnoo is a multi-runtime, security-conscious CLI tool for packaging, distributing, inspecting, and running AI agents — covering the full lifecycle across Python, Node.js, and OpenClaw with 9 framework templates, archive signing, input safety guards, a permissions model, and runtime monitoring.

#### The 8 gaps before a real 1.0 release:

- Remote registry (features 28-30, paused) — the single biggest adoption blocker
- Real-world testing with diverse, non-trivial agents
- Human-facing documentation — quickstart, manifest reference, security model, framework guides
- UX polish — consistent error messages, help text, exit codes, --json output mode
- Distribution of kinnoo itself — PyPI publish pipeline, cross-platform verification
- TypeScript entrypoint support — .ts execution is deferred but Node devs will expect it
- Versioning/upgrade story — side-by-side installs, schema forward-compatibility
- CI/CD integration examples — documented GitHub Actions pipeline
- The takeaway: the gap from feature-complete to 1.0 is distribution, docs, and validation — not more features. You already have a genuinely differentiated tool.

## AI Workflow Strategy Guidance (2026-03-22)

This is a great question and worth thinking through carefully. I'll give you a direct assessment based on what I've observed in the kinnoo codebase.

## Your Current Approach

You're running a **task-serial pipeline**: Tech Lead defines feature -> breaks into tasks -> SWE agent does one task -> review -> next task. Looking at your manifest files, feature3 (`kinnoo run`) was 8 tasks (task7-task14), each individually implemented and reviewed. Feature10 (`env_vars`) was 6 tasks (task53-task58). That's 6-8 round trips per feature, each with a handoff brief, implementation, review, status updates, and manifest bookkeeping.

## The Spec-Driven One-Shot Alternative

The idea: instead of 8 serial agent sessions for feature3, you write one comprehensive spec document that includes:
- Full feature description with all edge cases
- All acceptance criteria
- All test specifications (inputs, expected outputs, pass criteria)
- Architectural constraints and file-change scope

Then hand the entire bundle to an SWE agent and say: "Implement until all tests pass."

## Concrete Kinnoo Example: How You'd Do It

Take **feature3 (kinnoo run)** as a retrospective example. Instead of 8 separate tasks, you'd produce one spec file like this:

```markdown
# Feature Spec: kinnoo run — Agent Execution from Source

## Scope
Implement `kinnoo run <path> "<input>"` end-to-end in a single pass.

## Files to Create/Modify
- src/kinnoo/cli.py (add run subcommand)
- src/kinnoo/run_command.py (new module)
- tests/test_cli.py (add run tests)

## Behavioral Contract
1. Validate kinnoo.yaml via existing validator; abort with errors if invalid/missing
2. Create .venv/ in agent dir if absent; skip if present
3. Install requirements.txt into .venv/ via pip
4. Execute entrypoint with input as sys.argv[1]
5. Stream stdout+stderr in real-time
6. Propagate exit code
7. Print usage error if args missing
8. Print error if entrypoint file missing

## Test Specifications

### test_run_invalid_manifest
- Setup: agent dir with invalid kinnoo.yaml
- Run: python src/kinnoo/cli.py run <dir> "input"
- Assert: exit != 0, stderr contains "Error"

### test_run_creates_venv
- Setup: valid agent dir, no .venv/
- Run: python src/kinnoo/cli.py run <dir> "input"
- Assert: .venv/ exists after run

### test_run_installs_requirements
- Setup: agent dir with requirements.txt containing `requests`
- Run: python src/kinnoo/cli.py run <dir> "input"
- Assert: requests importable from .venv/

### test_run_entrypoint_input
- Setup: entrypoint that prints sys.argv[1]
- Run: python src/kinnoo/cli.py run <dir> "hello world"
- Assert: stdout contains "hello world"

### test_run_streams_output
- Setup: entrypoint that writes to stdout and stderr
- Assert: both captured in output

### test_run_exit_code
- Setup: entrypoint that exits with code 42
- Assert: CLI exits with 42

### test_run_missing_args
- Run: python src/kinnoo/cli.py run (no args)
- Assert: exit != 0, output contains "Usage"

### test_run_missing_entrypoint
- Setup: manifest declares run.py but file doesn't exist
- Assert: exit != 0, output contains error about missing entrypoint

## Constraints
- Use validator from src/kinnoo/validator.py (no duplicate validation)
- CLI invocation in tests: python src/kinnoo/cli.py, not python -m kinnoo
- No file modifications outside agent directory
- No secret values in output
```

Then you'd give the SWE agent one instruction: **"Implement this spec. Iterate until all 8 tests pass. Run `python3 -m pytest tests/test_cli.py -k test_run` after each change."**

## Pros and Cons

### Your Current Approach (Task-Serial)

**Pros:**
- Maximum control and visibility at every step
- Easy to catch architectural drift early - you review after each small unit
- Natural learning cadence - you see each piece land and understand it
- Low blast radius when an agent goes sideways (one task, not an entire feature)
- Manifest/status tracking gives you a paper trail of exactly what happened when

**Cons:**
- Slow: 8 round trips for feature3, each with handoff overhead, context reload, manifest bookkeeping
- Context fragmentation: agent loses state between sessions; you compensate with handoff briefs
- Manifest management tax: updating TASKS.txt, TESTS.txt, FEATURES.txt, running validator, writing task-notes.md files for every atomic unit is real overhead
- Over-decomposition risk: some tasks (like task11 "stream stdout" and task12 "propagate exit code") are 5-line changes that don't need their own task lifecycle

### Spec-Driven One-Shot

**Pros:**
- Dramatically faster for well-scoped features - one session instead of 8
- Agent has full context in one pass, so implementation decisions are globally coherent
- Test-driven: agent has concrete pass/fail signals and can self-correct
- Less manifest/bookkeeping overhead per feature
- Better utilization of agent capability - LLMs are good at implementing against a complete spec

**Cons:**
- Requires higher up-front investment in spec quality - vague specs produce vague code
- Larger blast radius: if the agent goes down a wrong architectural path, it taints the whole feature
- Harder to review: a 400-line PR is harder to evaluate than six 50-line PRs
- Debugging failures takes longer - "test 6 of 8 fails" could be a deep structural issue
- Less learning opportunity for you per unit of output - you see the finished product, not the construction process

## My Assessment

**You should use both approaches, depending on the work.**

Here's the heuristic:

| Characteristic | One-Shot Friendly | Task-Serial Friendly |
|---|---|---|
| Well-understood domain | Yes | — |
| Clear input/output contract | Yes | — |
| Isolated module (few cross-cutting deps) | Yes | — |
| Novel architecture or design decisions | — | Yes |
| Security-sensitive (secrets, auth, permissions) | — | Yes |
| Multi-system integration (server + client + UI) | — | Yes |
| You want to learn the internals | — | Yes |

**Concrete kinnoo examples:**

**One-shot candidates** (you already know the shape; it's execution, not design):
- feature3 (`kinnoo run`) - 8 tasks that are really one coherent module
- feature5 (`kinnoo pack`) - 6 tasks, well-defined archive contract
- feature6 (`kinnoo install`) - extraction/venv/deps, clear input->output
- feature9 (optional V2 manifest fields) - schema extension, straightforward
- feature11 (inspect command) - read-only query command, simple contract
- **task255** (the corpus matrix you just defined) - perfect one-shot candidate: clear inputs (agents-map.txt), clear outputs (test pass/fail), isolated test file

**Task-serial candidates** (design decisions, security boundaries, multi-system):
- feature43 (auth/user/tenant management) - security-critical, needs review at each boundary
- features 28-30 (registry backend/server/web UI) - cross-system integration, architectural choices
- feature39 (permission declarations) - security policy design requires iterative review
- feature10 (env_vars resolution chain) - secret-handling code where you explicitly want to review each resolution layer

**Hybrid approach for maximum leverage:**

For your next feature, try this workflow:
1. **You** (or Tech Lead agent) write the spec + test specifications up front - invest the time here
2. **One SWE agent session** implements the full spec and iterates until tests pass
3. **You review the PR as a whole** - one review instead of 8
4. Reserve task-serial for security-sensitive or architecturally novel work where you need per-step oversight

The key insight: **the bottleneck in your current workflow isn't the AI agent's capability - it's the context-reload and handoff overhead between sessions.** A well-written spec eliminates that overhead by giving the agent everything it needs in one shot.

Your manifest system (FEATURES.txt / TASKS.txt / TESTS.txt) is still valuable as a planning and tracking tool. You'd still define the feature and tests up front. You'd just collapse the execution from N serial sessions into 1 session with a comprehensive spec.

---

## Phase 7 — OpenClaw CLI Wrapper Architecture (2026-03-31)

### Context
User installed OpenClaw v2026.3.28, tested the CLI directly, and determined that the existing bridge/scaffold approach (features 62-67) is inadequate. OpenClaw now has a full CLI surface for agent management, and kinnoo should wrap it rather than reimplementing internals.

### OpenClaw CLI Surface (confirmed via docs at github.com/openclaw/openclaw)
- **Agent management**: `openclaw agents add/list/delete/bind/unbind/set-identity`
- **Agent execution**: `openclaw agent --agent <name> --message "..." [--thinking <level>]`
- **Skills**: `openclaw skills search/install/update/list/info/check` (ClawHub-backed)
- **Gateway lifecycle**: `openclaw gateway run/status/health/probe/install/start/stop/restart`
- **Logs**: `openclaw logs [--follow] [--json] [--local-time]`
- **Daemon**: `openclaw daemon ...` (legacy alias for gateway service commands)
- **Doctor**: `openclaw doctor` — surface misconfigurations
- **Config**: `~/.openclaw/openclaw.json`, Gateway port default 18789
- **Workspace**: `~/.openclaw/workspace` (default), per-agent via `~/.openclaw/workspace-<name>/`
- **Latest version**: 2026.4.1 (bumped from 2026.3.31)

### Key Design Decisions

1. **kinnoo wraps openclaw CLI** — no reimplementation of agent registration, skill install, or Gateway interaction.
2. **Preflight is mandatory** — every OpenClaw command checks CLI presence + version >= 2026.3.28.
3. **Gateway check is conditional** — only required for run/logs, not init/import/install.
4. **`kinnoo attach` deferred** — OpenClaw agents run via persistent Gateway daemon, not standalone processes. No "process" to attach to.
5. **`kinnoo stop` deferred** — stopping individual agents isn't supported by OpenClaw. `openclaw gateway stop` stops everything. Too blunt for a wrapper.
6. **Version format is date-based** — YYYY.M.D, not semver. Parser must handle this.

### Feature Map (76-85)
| Feature | Title | Replaces | Gateway Required? |
|---------|-------|----------|-------------------|
| 76 | CLI preflight & version gate | (new) | Optional probe |
| 77 | Init via CLI wrapper | feature34 | No |
| 78 | Import via CLI wrapper | feature36, feature64 | No |
| 79 | Workspace pack | (extends existing) | No |
| 80 | Install via CLI wrapper | feature65 | No |
| 81 | Run via CLI wrapper | feature66 | Yes |
| 82 | Logs passthrough | (new) | Yes |
| 83 | Skill install for agents | (new, user req) | Yes |
| 84 | Skill search via ClawHub | (new, user req) | Yes |
| 85 | Deprecate features 62-67 | (cleanup) | N/A |

### Deprecation Plan
- Features 62-67 are marked deprecated, NOT removed
- Deprecated code paths emit warnings pointing to Phase 7 replacements
- `--experimental-openclaw-adapter` flag removed or warns
- Tests preserved but annotated as deprecated coverage
- Feature34 scaffold approach superseded by feature77 (init via CLI)
- Feature36 analysis logic is reusable — only scaffold output is deprecated
- Full removal deferred to future cleanup phase

### Phase 7 Manifest Planning Execution (2026-04-01)

- Added task decomposition for feature76-feature85:
  - `task362`-`task381` appended to `TASKS.txt`
- Added test decomposition for feature76-feature85 with AC coverage:
  - `test521`-`test540` appended to `TESTS.txt`
- Updated feature task links in `FEATURES.txt`:
  - feature76 -> `[task362, task363]`
  - feature77 -> `[task364, task365]`
  - feature78 -> `[task366, task367]`
  - feature79 -> `[task368, task369]`
  - feature80 -> `[task370, task371]`
  - feature81 -> `[task372, task373]`
  - feature82 -> `[task374, task375]`
  - feature83 -> `[task376, task377]`
  - feature84 -> `[task378, task379]`
  - feature85 -> `[task380, task381]`
- Created SWE handoff briefs:
  - `notes/features/feature76-swe-handoff.md` through `notes/features/feature85-swe-handoff.md`
- JS/TS testing note:
  - Added Vitest automation path for JS/TS-specific workspace fixture contract in `test528`:
    - `web/__tests__/openclaw-pack-fixtures.test.ts::it_preserves_openclaw_workspace_pack_contract`
- Validation:
  - `python src/validate_project_manifests.py` -> pass
- Full `python -m pytest` run from repo root currently fails due unrelated workspace test-collection conflicts (example-scratch and server/mock-server module collisions); no failures tied to the manifest edits above.

## Phase 9 Tech Lead Review 1 (2026-04-04)

- Reviewed feature89-feature91 and feature100-feature102 against Phase 9 plan in `notes/phases/phase8-planning-3.md`.
- Created formal review write-up in `notes/phases/phase9-features-review-notes.md` under section "Tech Lead Review 1".
- Full regression executed and passing:
  - `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests` -> `516 passed, 10 skipped`
- Manifest validation executed and passing:
  - `/Users/jerry/.pyenv/versions/3.11.12/bin/python src/validate_project_manifests.py` -> pass
- Key decision notes:
  - feature100 is still partial (task410 done; task411/task412 not started), so it should not be treated as complete.
  - feature101 and feature102 are implemented but have AC-depth gaps in current tests.
- Minor fixes applied during review:
  - `server/cli.py`: fixed user-list tenant slug derivation bug.
  - `docker-compose.yml`: removed inline secret literals; now requires env vars.
  - `src/kinnoo/templates.py`: made dotenv import optional for generated MCP client template.
  - `tests/test_registry.py`: updated legacy publish fixtures to include `framework` field.