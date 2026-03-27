# Final Phase 6–10 Plan

_Date: March 27, 2026_

This document is the **authoritative plan** for Phases 6–10 of kinnoo. It synthesizes and resolves all prior planning discussions (phase6-planning.md through phase6-planning-4.md) into a single, ordered, dependency-aware feature list.

All prior phase plans are superseded by this document. Feature IDs are newly assigned starting from feature61 (the first feature after the 60 completed in Phases 1–5).

---

## Table of Contents

1. [Design Decisions Finalized](#1-design-decisions-finalized)
2. [Phase 6 — OpenClaw Support + Registry Improvements](#2-phase-6--openclaw-support--registry-improvements)
3. [Phase 7 — Pressure Testing with Real Agents + Battle Hardening + Analyzer Improvements](#3-phase-7--pressure-testing-with-real-agents--battle-hardening--analyzer-improvements)
4. [Phase 8 — Agent Composition and Cross-Framework Dependencies](#4-phase-8--agent-composition-and-cross-framework-dependencies)
5. [Phase 9 — Trust Ecosystem and Open Source Launch](#5-phase-9--trust-ecosystem-and-open-source-launch)
6. [Phase 10 — Agent Test and Eval Ecosystem](#6-phase-10--agent-test-and-eval-ecosystem)
7. [Feature ID Traceability](#7-feature-id-traceability)
8. [Dependency Graph](#8-dependency-graph)
9. [Key Risks and Mitigations](#9-key-risks-and-mitigations)
10. [Teaching Notes](#10-teaching-notes)

---

## 1. Design Decisions Finalized

These decisions were debated across the prior planning documents and are now **settled**:

1. **No full OpenClaw agent packaging.** The majority (13+ of ~20 components) of an OpenClaw agent is user/device-specific (channel tokens, API keys, memory, sessions). Kinnoo will NOT package or run full OpenClaw gateway configurations. (Decided in planning-3, Q3–Q5.)

2. **OpenClaw skills as a delegated packaging unit.** Kinnoo supports `type: openclaw-skill` as a thin metadata wrapper around ClawHub skills. Install and run are delegated to the OpenClaw CLI. Kinnoo adds value via normalized metadata, cross-framework discovery, and security overlays. (Decided in planning-4.)

3. **Piggyback on ClawHub, don't compete.** ClawHub is the source of truth for OpenClaw skills. Kinnoo mirrors metadata into a `kinnoo-clawhub` namespace with clear attribution. Kinnoo never pretends mirrored skills are first-party packages. (Decided in planning-4.)

4. **`kinnoo update` instead of `kinnoo sync` for agent updates.** `sync` is reserved for ClawHub mirror ingestion. Agent update semantics use `kinnoo update`. (Decided in planning-3, Q6.)

5. **Open-core model.** CLI is open-sourced (Apache 2.0). Server + web frontend remain private. This follows the npm/Docker/GitLab pattern. (Decided in planning-2, §6.)

6. **Defer full eval framework to Phase 10.** Phase 6 builds the `kinnoo test` foundation. Phase 10 builds the full eval ecosystem after post-launch user feedback. (Decided in planning-2, §7.)

7. **20-agent pressure test plan.** Five categories: Python one-shot (6), Python daemon/server (3), Node.js/TS (3), edge cases (3), OpenClaw skills (5). The detailed agent list from planning-2 §5 is the reference. (Decided in planning-2.)

8. **Run adapter behind compatibility flag.** The OpenClaw run adapter delegates to whatever invocation path is available in the installed OpenClaw version. It starts as an MVP behind a compatibility flag and evolves as OpenClaw's CLI stabilizes. (Decided in planning-4, §2.)

---

## 2. Phase 6 — OpenClaw Support + Registry Improvements

**Theme:** "Bridge kinnoo into the OpenClaw ecosystem and modernize registry UX"

**Goal:** At the end of Phase 6, a user can `kinnoo login`, discover OpenClaw skills via `kinnoo search`, import them from ClawHub, install them via delegated OpenClaw CLI, run them via the adapter, and keep the mirror up-to-date with `kinnoo sync clawhub`. The registry also gains CI-friendly auth, a reference GitHub Actions workflow, and a basic `kinnoo test` command.

### Features

| Feature | Title | Key Deliverables | Dependencies |
|---------|-------|------------------|--------------|
| feature61 | `kinnoo login` + `kinnoo logout` | Interactive login (email/password → POST `/api/auth/token` → store JWT + tenant_slug in `~/.kinnoo/config.yaml`); `--email`/`--password`/`--registry` flags for non-interactive use; logout clears stored token; `publish_command.py` updated to prefer stored token over env vars | None |
| feature62 | `openclaw-skill` schema extension | New `type: openclaw-skill` in manifest schema; new fields: `source_registry`, `source_slug`, `source_version`; validation rules (framework must be `openclaw`, type must be `openclaw-skill` when source fields present); schema reference docs updated | None |
| feature63 | ClawHub mirror index MVP | New `kinnoo-clawhub` registry namespace; metadata ingestion pipeline (ClawHub API or CLI export → normalize to kinnoo schema → store with attribution); each record stores: slug, owner, version, tags, description, install requirements, source URL, sync timestamp, kinnoo-added fields (preflight summary, compatibility flags); clear source labeling in `kinnoo search`/`kinnoo inspect` output: `Source: ClawHub (mirrored)` | feature62 |
| feature64 | ClawHub import bridge | `kinnoo import --source clawhub <slug>` (e.g., `kinnoo import --source clawhub steipete/slack`); resolves skill metadata from mirror index (live fallback if not cached); scaffolds `kinnoo.yaml` with `type: openclaw-skill` + source fields; populates known requirements (bins/env/config gates) from skill metadata; saves local import report | feature62, feature63 |
| feature65 | Delegated install bridge | `kinnoo install` for `type: openclaw-skill` packages: checks OpenClaw CLI is installed (error with install instructions if missing), checks OpenClaw version meets minimum, delegates to `openclaw skills install <slug> [--version]`, runs kinnoo-side checks (static analysis, policy checks) on installed skill directory | feature62 |
| feature66 | OpenClaw run adapter v1 | `kinnoo run <openclaw-skill> -- <args>` delegation backend; detects available OpenClaw invocation path (version-aware); if native `skills run` exists in installed version, use it; else fallback to agent invocation mode with skill-oriented prompt envelope; transparent logging (`Delegating via openclaw backend: ...`); behind `--experimental-openclaw-run` flag initially | feature65 |
| feature67 | ClawHub sync command | `kinnoo sync clawhub` pulls metadata delta from ClawHub source; `--full` flag for complete re-sync; `--since <timestamp>` for incremental; upserts into `kinnoo-clawhub` namespace; preserves source attribution; rate limiting and polite sync policy; handles failure modes (ClawHub unavailable, skill removed/hidden) | feature63 |
| feature68 | GitHub Actions reference workflow and CI story | Reference `kinnoo-publish.yml` workflow (checkout → install kinnoo → preflight → pack → publish); verify `KINNOO_REGISTRY_TOKEN` env var is read by publish command; document signing key injection via GitHub Secrets; verify non-zero exit codes on failure; document in `docs/` | feature61 |
| feature69 | `kinnoo test` foundation | New `tests` section in `kinnoo.yaml` schema (name, input, expected_output_contains, expected_exit_code, timeout_seconds); `kinnoo test <agent-dir>` command runs declared test cases sequentially, reports pass/fail per test; basic output: `N/M passed`; no publish integration yet (deferred to Phase 10) | None |
| feature70 | Landing page, docs, and ClawHub integration messaging | Update landing page tagline, sub-line, and feature cards per prior planning discussions; add ClawHub integration section to docs; source-labeling UX documentation; updated README reflecting Phase 6 capabilities | None |

### Phase 6 Design Details

#### `kinnoo login` flow

```
$ kinnoo login
Registry URL [https://registry.kinnoo.dev]: 
Email: jerry@example.com
Password: ********
✓ Logged in as jerry (tenant: jerry)
  Token stored in ~/.kinnoo/config.yaml
```

The auth endpoint already exists (`/api/auth/token` in the FastAPI server, used by `_issue_registry_token_with_admin_credentials` in `publish_command.py`). This feature adds the CLI command that calls it interactively and persists the token.

#### `openclaw-skill` manifest example

```yaml
name: steipete-slack
type: openclaw-skill
framework: openclaw
version: 1.2.0
source_registry: clawhub
source_slug: steipete/slack
source_version: 1.2.0
description: "Send Slack messages and manage channels via OpenClaw"
env_vars:
  - name: SLACK_BOT_TOKEN
    required: true
    description: "Slack bot OAuth token"
metadata:
  openclaw:
    requires:
      bins: []
      env: [SLACK_BOT_TOKEN]
      config: []
```

#### ClawHub mirror labeling in CLI

```
$ kinnoo search slack --source clawhub

Results from kinnoo-clawhub (mirrored):
  steipete/slack v1.2.0 — Send Slack messages and manage channels
    Source: ClawHub (mirrored) | Last synced: 2026-03-27T10:00:00Z
    Install: delegated to OpenClaw CLI
```

#### Run adapter delegation log

```
$ kinnoo run steipete-slack -- "send hello to #general"

[kinnoo run] Package type: openclaw-skill
[kinnoo run] Delegating via openclaw backend: agent-message
[kinnoo run] OpenClaw v2.3.1 detected
[kinnoo run] Invoking: openclaw agent --message "Use the slack skill to send hello to #general"
...
```

---

## 3. Phase 7 — Pressure Testing with Real Agents + Battle Hardening + Analyzer Improvements

**Theme:** "Test 20 real agents through the full lifecycle, fix everything that breaks, and sharpen the analyzer"

**Goal:** At the end of Phase 7, kinnoo has been validated against 20 diverse real-world agents across 5 categories. All discovered bugs are fixed, error messages are clear, and the analyzer accurately detects env vars, frameworks, and permissions for all tested agents. This phase also validates the Phase 6 OpenClaw bridge flows with real ClawHub skills.

### Features

| Feature | Title | Key Deliverables | Dependencies |
|---------|-------|------------------|--------------|
| feature71 | Pressure testing — Python one-shot agents (batch 1) | Test agents 1–6 through full 9-step lifecycle (import → check → run → pack → install → run installed → publish → install remote → inspect); per-agent report in `notes/pressure-testing/`; agent selection per planning-2 §5 reference list: (1) LangChain RAG w/ Chroma, (2) PydanticAI structured output, (3) OpenAI Agents SDK tool-calling, (4) LangGraph multi-step reasoning, (5) Vanilla Python CLI chatbot, (6) CrewAI/AutoGen multi-tool | feature61 (login needed for publish steps) |
| feature72 | Pressure testing — Python daemon/server + Node.js agents (batch 2) | Test agents 7–12: (7) Python MCP server (filesystem), (8) Streamlit agent dashboard, (9) FastAPI agent endpoint w/ WebSocket, (10) Node.js CLI chatbot, (11) TypeScript MCP server, (12) Express.js agent API; per-agent report | feature61 |
| feature73 | Pressure testing — Edge cases + OpenClaw skills (batch 3) | Test agents 13–15 (edge cases): (13) Multi-file Python w/ src/ layout, (14) Agent with 10+ env vars and 3 service deps, (15) Docker-dependent agent (Redis + Postgres — document limitations); Test agents 16–20 (OpenClaw skills via Phase 6 bridge): (16) weather (simple SKILL.md), (17) ontology (Python scripts + state), (18) github (binary dep `gh`), (19) gog (OAuth + CLI binary, scanner false positive), (20) browser automation (headless browser binary); OpenClaw skills tested through: `kinnoo import --source clawhub` → `kinnoo install` → `kinnoo run` (adapter) → `kinnoo inspect`; per-agent report | feature64, feature65, feature66 |
| feature74 | Pressure test bug fixes and battle hardening | Fix all bugs discovered in features 71–73; improve error messages for common failure modes; handle edge cases (missing runtimes, version conflicts, corrupt archives, partial installs); CLI UX polish (help text, progress indicators, consistent formatting); `kinnoo check` improvements based on findings | feature71, feature72, feature73 |
| feature75 | Analyzer enhancements from pressure test findings | `.env.example` / `.env.template` / `.env.sample` scanning for env var names; framework-to-env-var mapping (known defaults per framework: LangChain → `OPENAI_API_KEY`, etc.); JS/TS env var regex (`process.env.VAR_NAME`); constructor-to-env-var mapping (e.g., `ChatOpenAI(...)` → suggest `OPENAI_API_KEY`); import-to-permission inference (`requests` → network, `subprocess` → shell, etc.); updated per actual findings from pressure tests | feature71, feature72, feature73 |
| feature76 | Pressure testing summary and documentation | Aggregate summary report (`notes/pressure-testing/summary.md`); top-10 kinnoo improvements from findings; framework-specific quick-start guides based on tested agents; known limitations document; updated `kinnoo check` documentation | feature74, feature75 |

### 20-Agent Reference List

This is the definitive agent list for pressure testing. Sources: planning-2 §5, planning-3.

#### Category 1: Python One-Shot (agents 1–6)

| # | Description | Framework | Key Stress Points |
|---|-------------|-----------|-------------------|
| 1 | RAG agent with Chroma vector DB | LangChain | ~200MB transitive deps, vector DB service, embedding model API key |
| 2 | Structured output agent with typed responses | PydanticAI | JSON output type, typed tool definitions, async execution |
| 3 | Tool-calling agent with function definitions | OpenAI Agents SDK | Multiple API keys, function tool schema, handoff patterns |
| 4 | Multi-step reasoning workflow (plan-and-execute) | LangGraph | Graph-based execution, intermediate state, complex dependency chain |
| 5 | Simple CLI chatbot (minimal deps) | Vanilla Python | Minimal framework, baseline kinnoo functionality test |
| 6 | Multi-tool research agent | CrewAI or AutoGen | Unknown framework — tests `kinnoo import` with unrecognized framework |

#### Category 2: Python Daemon/Server (agents 7–9)

| # | Description | Framework | Key Stress Points |
|---|-------------|-----------|-------------------|
| 7 | Filesystem MCP server | MCP (Python) | Daemon runtime, MCP protocol, permission enforcement |
| 8 | Streamlit agent dashboard | Streamlit | Web UI, unusual entrypoint (`streamlit run`), port binding, assets |
| 9 | FastAPI agent endpoint with WebSocket | FastAPI | HTTP server, WebSocket, health check, multiple routes |

#### Category 3: Node.js / TypeScript (agents 10–12)

| # | Description | Framework | Key Stress Points |
|---|-------------|-----------|-------------------|
| 10 | CLI chatbot with OpenAI SDK | Node.js | node_modules size, npm install, package.json parsing |
| 11 | TypeScript MCP server | MCP (TypeScript) | tsx execution, compile step, daemon mode |
| 12 | Express.js agent API | Node.js + Express | npm deps, daemon runtime, port binding, middleware |

#### Category 4: Edge Cases (agents 13–15)

| # | Description | Framework | Key Stress Points |
|---|-------------|-----------|-------------------|
| 13 | Multi-file agent with src/ layout | Python | Subdirectory entrypoint, relative imports, `src/` layout convention |
| 14 | Agent with 10+ env vars and 3 service deps | Any | Exhaustive env var detection, service declaration, `.env.example` parsing |
| 15 | Docker-dependent agent (Redis + Postgres) | Any | Tests boundary of what kinnoo CAN'T do — documents limitations |

#### Category 5: OpenClaw Skills (agents 16–20)

| # | Skill | ClawHub Source | Key Stress Points |
|---|-------|----------------|-------------------|
| 16 | Weather (simple, SKILL.md only) | steipete/weather | Zero deps, zero API keys, simplest possible skill |
| 17 | Ontology (knowledge graph, Python scripts) | oswalpalash/ontology | SKILL.md + scripts + references, state persistence |
| 18 | GitHub (instruction-only, requires `gh` CLI) | steipete/github | Binary dependency, no supporting files |
| 19 | Gog (Gmail/Calendar, needs OAuth + CLI) | steipete/gog | OAuth credentials, external binary, flagged "suspicious" (false positive) |
| 20 | Browser automation (headless browser) | matrixy/agent-browser-clawdbot | Large binary dep, system-level requirements, cross-platform |

### Test Protocol

**For agents 1–15 (full agents), 9-step lifecycle:**

```
1. kinnoo import <agent-dir>          → record auto-detection accuracy
2. kinnoo check <agent-dir>           → record false alarms, missing checks
3. kinnoo run <agent-dir> "<input>"   → record runtime success/failure
4. kinnoo pack <agent-dir>            → record archive size, warnings
5. kinnoo install <archive.kno>       → record install time, dep failures
6. kinnoo run <installed> "<input>"   → record post-install behavior
7. kinnoo publish <name>              → record upload success
8. kinnoo install <name> --remote     → record remote install success
9. kinnoo inspect <name>              → record metadata accuracy
```

**For agents 16–20 (OpenClaw skills), adapted protocol using Phase 6 bridge:**

```
1. kinnoo import --source clawhub <slug>  → test ClawHub import bridge
2. kinnoo inspect <skill-dir>             → verify manifest metadata
3. kinnoo check <skill-dir>               → security sweep on SKILL.md + scripts
4. kinnoo install <skill-package>         → test delegated install via OpenClaw CLI
5. kinnoo run <skill> -- "<input>"        → test run adapter delegation
6. Document findings and gaps             → per-agent report
```

### Output Artifacts

```
notes/pressure-testing/
  agent-01-langchain-rag.md
  agent-02-pydanticai-structured.md
  ...
  agent-20-openclaw-browser.md
  summary.md                    → aggregate findings, ranked improvements
```

---

## 4. Phase 8 — Agent Composition and Cross-Framework Dependencies

**Theme:** "Make agents composable building blocks that work across frameworks"

**Goal:** At the end of Phase 8, an agent's `kinnoo.yaml` can declare dependencies on other agents with version constraints. `kinnoo install` recursively installs the dependency tree. Agents can invoke sub-agents as subprocesses, Python-callable tools, or MCP servers. A real cross-framework composed agent (e.g., Python parent → Node.js MCP sub-agent) is validated end-to-end.

### Features

| Feature | Title | Key Deliverables | Dependencies |
|---------|-------|------------------|--------------|
| feature77 | Agent dependency schema and resolution | `agent_dependencies` field in `kinnoo.yaml` schema; each entry: `name` (required), `version` (semver range, optional), `invoke_as` (enum: `subprocess` \| `tool` \| `mcp-server`, default: `subprocess`); version constraint parser; dependency resolver (flatten tree, detect conflicts); circular dependency detection and error reporting | None |
| feature78 | Recursive agent dependency installation | `kinnoo install` detects `agent_dependencies`, resolves each to a specific version from registry, installs sub-agents into `~/.kinnoo/agents/<name>/` (or `<agent-dir>/.kinnoo-deps/`); skips already-installed sub-agents at compatible versions; aggregated permission summary across entire dependency tree; user confirmation for combined permissions | feature77 |
| feature79 | Runtime helper — `invoke_as: subprocess` | Sub-agent invocation via `kinnoo run <sub-agent> "<input>"` subprocess call; env var sandboxing (only forward vars declared in sub-agent manifest); stdout capture as return value; stderr forwarding; exit code propagation; timeout support | feature78 |
| feature80 | Runtime helper — `invoke_as: tool` | `kinnoo.runtime.load_agent_tool(name)` Python helper; returns a callable that wraps subprocess invocation; handles serialization/deserialization of input/output; enforces sub-agent permissions; clean error propagation | feature79 |
| feature81 | Runtime helper — `invoke_as: mcp-server` | `kinnoo.runtime.start_agent_server(name)` Python helper; starts MCP server sub-agent as background process; returns connection info (port, transport); lifecycle management (start, health check, stop); integrates with kinnoo's daemon management (`kinnoo stop`) | feature78 |
| feature82 | Composition end-to-end validation | Build and test a real composed agent: Python parent agent + 2 sub-agents (one Python `invoke_as: tool`, one Node.js `invoke_as: mcp-server`); validate full lifecycle: pack parent (with agent_dependencies recorded, NOT bundled) → install (recursive) → run → verify sub-agent invocation works; document composition patterns and limitations | feature79, feature80, feature81 |

### Composition Design Highlights

#### Manifest example

```yaml
# kinnoo.yaml for earthquake-predictor (parent agent)
name: earthquake-predictor
version: 2.0.0
runtime:
  language: python
  version: ">=3.11"
  type: one-shot
entrypoint: run.py
dependencies:
  - langchain
  - langchain-openai
agent_dependencies:
  - name: seismic-data-fetcher
    version: ">=1.0,<2.0"
    invoke_as: tool
  - name: geological-model
    version: ">=3.0"
    invoke_as: subprocess
```

#### Install UX

```
$ kinnoo install earthquake-predictor

[kinnoo install] Resolving earthquake-predictor@2.0.0...
[kinnoo install] Agent dependencies detected:
  - seismic-data-fetcher >=1.0,<2.0 (resolved: 1.2.0)
  - geological-model >=3.0 (resolved: 3.1.0)

[kinnoo install] Installing seismic-data-fetcher@1.2.0...
  ✓ Archive verified (SHA256 + Ed25519)
  ✓ Dependencies installed (3 packages)

[kinnoo install] Installing geological-model@3.1.0...
  ✓ Archive verified (SHA256 + Ed25519)
  ✓ Dependencies installed (5 packages)

[kinnoo install] Installing earthquake-predictor@2.0.0...
  ✓ Archive verified (SHA256 + Ed25519)
  ✓ Dependencies installed (8 packages)
  ✓ Agent dependencies wired

[kinnoo install] Permission summary:
  earthquake-predictor: network, filesystem (read-only)
  seismic-data-fetcher: network
  geological-model: filesystem (read-only)
  Approve? [y/N]: y

✓ earthquake-predictor@2.0.0 ready to run
```

#### Key design rules

1. **`kinnoo pack` does NOT bundle sub-agent archives.** Agent dependencies are recorded in the manifest and resolved at install time from the registry. This matches the npm model (package.json lists deps, `npm install` fetches them).
2. **Start with `invoke_as: subprocess`.** It's the simplest mode — no runtime library needed, works with any language, proves the concept. `tool` and `mcp-server` are incremental additions.
3. **Env var sandboxing is strict.** Sub-agents only see the env vars declared in their own manifest. The parent agent cannot leak its env vars to sub-agents.

---

## 5. Phase 9 — Trust Ecosystem and Open Source Launch

**Theme:** "Build the trust signals that make strangers comfortable running each other's agents, then open the doors"

**Goal:** At the end of Phase 9, publishers can link their GitHub identity, agents display verified publisher badges and security scan badges in the registry, `kinnoo update` keeps installed agents current, the CLI is open-sourced on GitHub with a CONTRIBUTING guide, the registry is seeded with 10–20 agents, and kinnoo is publicly launched.

### Features

| Feature | Title | Key Deliverables | Dependencies |
|---------|-------|------------------|--------------|
| feature83 | GitHub OAuth and identity linking | GitHub OAuth flow for registry accounts; store GitHub username in identity table; link GitHub identity to registry publisher; UI to manage linked identities | None |
| feature84 | Verified publisher badges | `repository` field in `kinnoo.yaml` (optional); verification logic: if publisher's linked GitHub identity owns or is a collaborator on the declared repo → display "✓ Verified publisher" in registry UI and `kinnoo inspect`; badge stored in publish metadata | feature83 |
| feature85 | Security and signing badges in registry | Record scan results at publish time: heuristic_sweep status, dependency_audit status, archive_signed boolean, permissions_declared boolean, scan_timestamp; display badges in registry web UI and `kinnoo inspect`/`kinnoo search` CLI output | None |
| feature86 | `kinnoo update` command | `kinnoo update` checks all installed agents against registry for newer versions; `kinnoo update <name>` checks one agent; `kinnoo update --all` updates all outdated agents; shows current vs available version; re-runs install flow for updated version (preserves `state_dirs`) | feature61 |
| feature87 | CONTRIBUTING.md and community template system | Framework contribution guide (how to add a `--framework <X>` template); `templates/community/` directory for community templates; step-by-step guide with example; GitHub Discussions setup for feature requests | None |
| feature88 | Open source preparation | Extract CLI to public repo (`kinnoo` or `kinnoo-cli`); add LICENSE (Apache 2.0); write open-source README (installation, quickstart, framework support matrix, links to registry); schema reference in `docs/`; set up CI on public repo; prepare PyPI publication (`pip install kinnoo`) | feature87 |
| feature89 | Production deployment hardening | Registry server production checklist: rate limiting, logging, monitoring, backup strategy, S3 configuration, PostgreSQL migration from SQLite, health check endpoint, uptime monitoring | None |
| feature90 | Seed registry with 10–20 agents | Package and publish agents from Phase 7 pressure testing + new purpose-built examples; ensure at least 3 frameworks represented; write registry "Featured Agents" section | feature88, feature89 |
| feature91 | Public launch and open source announcement | Public access to registry; open source the CLI repo; announcement (blog post / README / social); invite first external users and testers | feature88, feature89, feature90 |

### Open Source Split

| Public repo (`kinnoo`) | Private repo (`kinnoo-platform`) |
|------------------------|----------------------------------|
| `src/kinnoo/` — entire CLI | `server/` — FastAPI registry server |
| `tests/` — all CLI tests | `web/` — Next.js web frontend |
| `pyproject.toml`, `requirements.txt` | Deployment configs, infrastructure |
| `README.md`, `LICENSE` (Apache 2.0) | `notes/`, `scratch/` — dev notes |
| `docs/` — schema reference, guides | Auth system implementation details |

---

## 6. Phase 10 — Agent Test and Eval Ecosystem

**Theme:** "Give every published agent a trust score grounded in verifiable test results"

**Goal:** At the end of Phase 10, publishers can attach test results to published versions, the registry displays test badges, and an eval framework supports both deterministic and LLM-powered evaluations. Users see at a glance: "this agent passed 5/5 tests on Python 3.12, macOS arm64, 3 days ago."

**Note:** This phase is shaped by post-launch user feedback from Phase 9. The feature list below is a starting point; scope and priorities will be refined based on real user needs.

### Features

| Feature | Title | Key Deliverables | Dependencies |
|---------|-------|------------------|--------------|
| feature92 | Test results in publish metadata | `kinnoo publish --test` runs `kinnoo test` before publishing; attaches results to version metadata (pass/fail per test, platform, timestamp); `kinnoo inspect` displays test results section | feature69 |
| feature93 | Test result badges in registry | Display test badges in registry web UI and CLI: "✓ 5/5 passed" or "✗ 3/5 passed"; badge shows platform and recency ("tested 2 days ago on Python 3.12, macOS arm64") | feature92 |
| feature94 | `kinnoo test --mock` mode for CI | Mock mode replaces LLM API calls with deterministic responses for cost-free CI testing; requires agent to support a test-safe mode; document mock pattern for agent developers | feature69 |
| feature95 | Eval framework — structured evaluations | Extend `tests` section with eval-type test cases: LLM-as-judge scoring, semantic similarity checks, structured output validation; `kinnoo eval <agent-dir>` command; eval scores (0–100) per test case | feature69 |
| feature96 | Eval scores in registry | Aggregate eval scores displayed in registry; sortable/filterable by eval score; eval score badge on agent cards; historical score tracking across versions | feature95 |
| feature97 | Test/eval documentation and best practices | Guide: how to write effective agent tests; guide: deterministic vs LLM-powered evals; cost estimation for eval runs; patterns for mock mode; example agents with comprehensive test suites | feature92, feature95 |

### Design Considerations (from planning-2 §7, planning §9c)

- **Non-deterministic outputs are the core challenge.** Substring matching (`expected_output_contains`) is pragmatic for Phase 6's foundation. Phase 10 adds LLM-as-judge and semantic similarity for more robust evaluation.
- **Test results become stale.** A test that passed on GPT-4o in March may fail in April due to model updates. Badges must convey recency.
- **Cost tracking.** Running evals costs API credits. `kinnoo eval` should report estimated cost before execution.
- **Platform-specific results.** "Passed on Python 3.12, macOS arm64" is meaningful metadata. Test results are per-version, per-platform.

---

## 7. Feature ID Traceability

This table maps the new unified feature IDs to the feature IDs used in prior planning documents, so you can trace back to the original discussion context.

### Phase 6 (feature61–feature70)

| New ID | Title | Planning-2 | Planning-3 | Planning-4 |
|--------|-------|-----------|-----------|-----------|
| feature61 | `kinnoo login` + `kinnoo logout` | — | feature66 | feature66 |
| feature62 | `openclaw-skill` schema extension | — | — | (implicit in feature67–69) |
| feature63 | ClawHub mirror index MVP | — | — | feature67 |
| feature64 | ClawHub import bridge | — | — | feature68 |
| feature65 | Delegated install bridge | — | — | feature69 |
| feature66 | OpenClaw run adapter v1 | — | — | feature71 |
| feature67 | ClawHub sync command | — | — | feature78 |
| feature68 | GitHub Actions CI story | — | feature67 | — |
| feature69 | `kinnoo test` foundation | feature67 | — | — |
| feature70 | Landing page + docs update | feature66 | feature68 | feature70 |

### Phase 7 (feature71–feature76)

| New ID | Title | Planning-2 | Planning-3 | Planning-4 |
|--------|-------|-----------|-----------|-----------|
| feature71 | Pressure testing batch 1 | feature61 | feature61 | feature61 |
| feature72 | Pressure testing batch 2 | feature62 | feature62 | feature62 |
| feature73 | Pressure testing batch 3 | feature63 | feature63 | feature63 |
| feature74 | Bug fixes + battle hardening | feature63 (partial) | feature64 | feature64 |
| feature75 | Analyzer enhancements | feature64 | feature65 | feature65 |
| feature76 | Summary + documentation | — | — | — |

### Phase 8 (feature77–feature82)

| New ID | Title | Planning-2 | Planning-3 | Planning-4 |
|--------|-------|-----------|-----------|-----------|
| feature77 | Agent dependency schema | feature68 | feature69 | feature72 |
| feature78 | Recursive dependency install | feature69 | feature70 | feature73 |
| feature79 | Runtime helper: subprocess | feature70 | feature71 | feature74 |
| feature80 | Runtime helper: tool | feature71 | feature72 | feature75 |
| feature81 | Runtime helper: mcp-server | feature72 | feature73 | feature76 |
| feature82 | Composition E2E validation | feature74 | feature74 | feature77 |

### Phase 9 (feature83–feature91)

| New ID | Title | Planning-2 | Planning-3 | Planning-4 |
|--------|-------|-----------|-----------|-----------|
| feature83 | GitHub OAuth | feature75 | feature75 | — |
| feature84 | Verified publisher badges | feature76 | feature76 | feature79 |
| feature85 | Security/signing badges | feature77 | feature77 | feature80 |
| feature86 | `kinnoo update` command | — | feature78 | — |
| feature87 | CONTRIBUTING.md + community | feature78 | feature79 | — |
| feature88 | Open source preparation | feature79 | feature80 | feature81 |
| feature89 | Production deployment hardening | — | — | — |
| feature90 | Seed registry | feature80 | feature81 | feature82 |
| feature91 | Public launch | feature81 | feature82 | feature83 |

### Phase 10 (feature92–feature97)

| New ID | Title | Source |
|--------|-------|--------|
| feature92 | Test results in publish | planning §9c |
| feature93 | Test result badges | planning §9c |
| feature94 | `kinnoo test --mock` | planning-2 §7 |
| feature95 | Eval framework | planning-2 §7 |
| feature96 | Eval scores in registry | planning §9c |
| feature97 | Test/eval documentation | — |

---

## 8. Dependency Graph

Feature dependencies within and across phases:

```
Phase 6:
  feature61 (login) ──────────┐
  feature62 (schema) ─────────┤
       │                      │
       ├─→ feature63 (mirror) ─┤
       │        │              │
       │        ├─→ feature64 (import bridge)
       │        │
       │        └─→ feature67 (sync)
       │
       └─→ feature65 (install bridge)
                │
                └─→ feature66 (run adapter)

  feature68 (CI) ←── feature61
  feature69 (test) ── standalone
  feature70 (docs) ── standalone

Phase 7:
  feature71, 72, 73 (pressure tests) ←── feature61 + Phase 6 OpenClaw features
  feature74 (bug fixes) ←── feature71, 72, 73
  feature75 (analyzer) ←── feature71, 72, 73
  feature76 (summary) ←── feature74, 75

Phase 8:
  feature77 (schema) ── standalone
  feature78 (install) ←── feature77
  feature79 (subprocess) ←── feature78
  feature80 (tool) ←── feature79
  feature81 (mcp-server) ←── feature78
  feature82 (E2E) ←── feature79, 80, 81

Phase 9:
  feature83 (OAuth) ── standalone
  feature84 (verified badges) ←── feature83
  feature85 (security badges) ── standalone
  feature86 (update) ←── feature61
  feature87 (CONTRIBUTING) ── standalone
  feature88 (open source) ←── feature87
  feature89 (production) ── standalone
  feature90 (seed) ←── feature88, 89
  feature91 (launch) ←── feature88, 89, 90

Phase 10:
  feature92 (test publish) ←── feature69
  feature93 (test badges) ←── feature92
  feature94 (mock mode) ←── feature69
  feature95 (eval framework) ←── feature69
  feature96 (eval scores) ←── feature95
  feature97 (documentation) ←── feature92, 95
```

---

## 9. Key Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ClawHub API instability or rate limiting | Mirror index becomes stale or unreliable | Implement graceful degradation: if ClawHub is unavailable, serve cached metadata with "stale" flag; use polite sync intervals |
| OpenClaw CLI changes break run adapter | `kinnoo run` for openclaw-skill fails silently | Version detection at adapter layer; pin known-compatible OpenClaw versions; behind `--experimental-openclaw-run` flag initially |
| Pressure test agents require expensive API keys | Testing is blocked or costly | Use agents with free tiers where possible; for LLM-dependent agents, test with mocked responses or short inputs; budget ~$20 for full pressure test run |
| Agent composition creates complex failure modes | Debugging recursive install/run failures is hard | Verbose logging for dependency resolution; clear error messages showing which sub-agent failed and why; `kinnoo inspect --deps` to show dependency tree |
| Open-sourcing exposes security-sensitive patterns | Attackers study kinnoo's security checks to bypass them | Security checks are defense-in-depth (multiple layers); scanner patterns are heuristic, not the only protection; signed archives and permissions model provide enforcement regardless of scan bypass |
| Phase 10 eval framework scope creep | Eval landscape evolves faster than kinnoo can adapt | Keep Phase 10 deliberately minimal; shape scope based on real post-launch user feedback; don't build a full eval platform — integrate with existing tools (Braintrust, Langfuse) if possible |

---

## 10. Teaching Notes

### Why This Phase Ordering Matters

The ordering of these phases is deliberate and follows a principle you'll want to articulate in interviews: **build the integration layer → validate with real agents → create the composition primitive → add trust signals → open to the world → measure quality.**

**Phase 6 first (OpenClaw + Registry Improvements):** You can't pressure-test the OpenClaw bridge if it doesn't exist yet. And `kinnoo login` is a prerequisite for testing against the remote registry. Building these first means Phase 7 can test the FULL system, including the new features.

**Phase 7 before Phase 8 (Pressure Testing before Composition):** Agent composition (Phase 8) is complex and builds on the install/run pipeline. If that pipeline has bugs, composition will amplify them. Pressure testing first ensures the foundation is solid before adding another layer.

**Phase 8 before Phase 9 (Composition before Open Source):** Composition is kinnoo's most differentiated feature — the thing that ClawHub and "just clone the repo" can't do. Launching without it makes kinnoo a "nice convenience tool." Launching with it makes kinnoo genuinely new. It's worth delaying the public launch to ship composition.

**Phase 9 before Phase 10 (Launch before Eval):** The eval framework should be shaped by real user feedback. Shipping first, then measuring, is the right sequence. Building evals in a vacuum risks building the wrong thing.

### The Piggyback Strategy as an Interview Concept

The ClawHub piggyback strategy (Phase 6) illustrates a pattern that comes up in system design interviews: **federated registries with delegated execution.**

The key insight: when an entrenched registry exists (ClawHub, npm, PyPI, Docker Hub), don't rebuild it. Instead:
1. Mirror metadata (not artifacts) with clear attribution
2. Delegate install/execution to the native toolchain
3. Add value at a different layer (cross-framework discovery, security overlays, trust signals)

This is how tools like Artifactory, Nexus, and GitHub Packages work — they're proxy registries that add governance on top of upstream sources. Kinnoo's `kinnoo-clawhub` namespace follows the same pattern.

### Composition as a Moat

Agent composition (Phase 8) is worth understanding deeply for AI engineer interviews. The key concept is **agent dependency resolution** — treating agents as composable units with declared interfaces, version constraints, and invocation contracts. This is analogous to:
- Package dependency resolution (npm, pip) — but for runtime agents, not libraries
- Microservice orchestration (Kubernetes) — but lightweight, no container overhead
- Unix pipes (`cmd1 | cmd2`) — but with type-safe contracts and permission boundaries

No other tool in the AI agent ecosystem does this today. When an interviewer asks "how would you scale agent development across a team?" — this is the answer: declared dependencies, automatic resolution, sandboxed invocation, aggregated permissions.
