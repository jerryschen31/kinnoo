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