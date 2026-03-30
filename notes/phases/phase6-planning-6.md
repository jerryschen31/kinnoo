# Phase 6–10 Plan (Revised)

_Date: March 28, 2026_

This document **supersedes phase6-planning-5.md** based on competitive market research findings (see `notes/market-research-thoughts-scratch.md`) and follow-up analysis. Key changes:

1. **Phase 6 expanded** with 5 new features: strict CI signed-package enforcement, lockfile, `kinnoo diff`, `kinnoo uninstall`, and framework-specific import adapters
2. **Phase 7 significantly reduced** from 20 agents to 8, with a shortened test protocol
3. **Phase 8 trimmed** — defer `invoke_as: mcp-server` to post-launch
4. **Phase 9 accelerated** — merge some Phase 8 and Phase 9 work, target public beta sooner
5. **Phase 10 unchanged** — still shaped by post-launch feedback

---

## Table of Contents

1. [Changes from Planning-5](#1-changes-from-planning-5)
2. [Phase 6 — OpenClaw Support + Registry Improvements + Competitive Response](#2-phase-6)
3. [Phase 7 — Focused Pressure Testing + Battle Hardening](#3-phase-7)
4. [Phase 8 — Agent Composition (Trimmed)](#4-phase-8)
5. [Phase 9 — Trust Ecosystem and Open Source Launch](#5-phase-9)
6. [Phase 10 — Agent Test and Eval Ecosystem](#6-phase-10)
7. [Feature ID Traceability](#7-feature-id-traceability)
8. [Dependency Graph](#8-dependency-graph)
9. [Risks and Mitigations](#9-risks-and-mitigations)

---

## 1. Changes from Planning-5

### Phase 6 additions (competitive response)

These features were identified through market research as high-ROI, relatively low-effort additions that strengthen kinnoo's position before public launch:

| New Feature | Rationale | Effort Estimate | Inspired By |
|-------------|-----------|-----------------|-------------|
| feature71: Strict CI signed-package mode | Automation should fail closed: CI must not install or publish unsigned packages. This strengthens supply-chain trust now without changing the current signing backend. | Easy-Medium (1 day) | Kinnoo trust model |
| feature72: Lockfile (`kinnoo-lock.yaml`) | Reproducible installs. APM has `apm.lock.yaml`. Essential for CI/CD workflows. | Easy (1 day) | Microsoft APM |
| feature73: `kinnoo diff` | Compare two `.kno` archives. Obvious-in-retrospect utility. | Easy (1 day) | AgentPK |
| feature74: `kinnoo uninstall` | Currently no way to cleanly remove installed agents. Table-stakes feature. | Easy (0.5 day) | — |
| feature75: Framework import adapters | `kinnoo import --from langchain|langgraph|openai` with framework-specific templates. Reduces onboarding friction. | Medium (2-3 days for 3 adapters) | GitAgent |

> **Note on feature IDs**: This plan uses strict sequential numbering.

> **Sigstore decision:** Moved to post-launch. Phase 6 keeps the current Ed25519-based signing and adds strict CI enforcement on top.

### Phase 7 reduction

| Aspect | Planning-5 | Planning-6 (this doc) |
|--------|-----------|----------------------|
| Agent count | 20 | 8 |
| Lifecycle steps | 9 (import → inspect) | 5 (import → run) |
| OpenClaw skills tested | 5 | 2 |
| Estimated duration | 3-4 weeks | 1-1.5 weeks |
| Remaining agents | — | Moved to post-launch backlog |

### Phase 8 trimming

| Aspect | Planning-5 | Planning-6 (this doc) |
|--------|-----------|----------------------|
| Features | 6 (feature77-82) | 4 (feature80-83) |
| Deferred | — | `invoke_as: mcp-server` and full E2E validation moved to post-launch |
| Rationale | — | `subprocess` and `tool` invocation cover 80%+ of composition use cases. MCP server composition adds complexity without corresponding user demand signal yet. |

### Overall timeline impact

Planning-5 implied ~12-16 weeks for Phases 6-9. This revision targets **~8-10 weeks** to public beta by:
- Doing the new Phase 6 features in parallel with OpenClaw work (they're independent)
- Cutting Phase 7 scope by 60%
- Deferring Phase 8 MCP server composition
- Running Phase 9 open-source prep in parallel with late Phase 8

---

## 2. Phase 6 — OpenClaw Support + Registry Improvements + Competitive Response

**Theme:** "Bridge to OpenClaw, modernize registry, and close competitive gaps"

**Goal:** At the end of Phase 6, a user can: `kinnoo login`, discover OpenClaw skills via `kinnoo search`, import them from ClawHub, install via delegated OpenClaw CLI, run via the adapter, keep the mirror up-to-date with `kinnoo sync clawhub`. Additionally, kinnoo gains strict CI signed-package enforcement, a lockfile for reproducible installs, `kinnoo diff`, `kinnoo uninstall`, and framework-specific import adapters — closing the most important gaps identified in competitive analysis.

### Features (original from planning-5, unchanged)

| Feature | Title | Dependencies |
|---------|-------|--------------|
| feature61 | `kinnoo login` + `kinnoo logout` | None |
| feature62 | `openclaw-skill` schema extension | None |
| feature63 | ClawHub mirror index MVP | feature62 |
| feature64 | ClawHub import bridge | feature62, feature63 |
| feature65 | Delegated install bridge | feature62 |
| feature66 | OpenClaw run adapter v1 | feature65 |
| feature67 | ClawHub sync command | feature63 |
| feature68 | GitHub Actions CI story | feature61 |
| feature69 | `kinnoo test` foundation | None |
| feature70 | Landing page + docs update | None |

> Full design details for features 61-70 are in planning-5, except the feature62/64 manifest contract updates below.

### Alignment Update: Feature62/64 Manifest Contract (authoritative)

These updates align planning with FEATURES/TASKS/TESTS and are now the source-of-truth contract for Phase 6 implementation.

- `feature62` (`openclaw-skill` schema extension) uses a `provenance` object (not flat source fields).
- Required provenance rule: `source_registry`, `source_version`, and at least one of `source_slug` or `source_url`.
- Metadata minimalism rule: do not include `channels`, `skills`, or `state_dirs` as schema metadata fields in Phase 6.
- Validator behavior: reject disallowed metadata fields with deterministic, actionable guidance.
- `feature64` (`clawhub` import bridge) generated manifests must include the same provenance object contract above.
- Canonical examples are recorded in `FEATURES.txt` notes under `feature62` and should be used for implementation and test fixtures.

### Features (new — competitive response)

#### feature71: Strict CI Signed-Package Mode

**What changes:** Add strict automation enforcement so install/publish paths fail when signature requirements are not met.

**Why:** This provides immediate supply-chain hardening for CI/CD while keeping the current Ed25519 signing backend for first release.

**Scope:**
- Add a strict mode flag for automation:
  - `kinnoo install --strict`
  - `kinnoo publish --strict`
- In strict mode, reject unsigned archives (no `.sig` / `.sig.json`) with deterministic non-zero exit codes
- In strict mode, disallow unverified publisher overrides
- In strict mode, reject checksum-missing paths for remote artifacts unless explicit policy allows them
- Add CI examples showing strict mode usage in GitHub Actions
- Add tests for strict pass/fail cases on both install and publish paths

**Example:**
```
$ kinnoo install my-agent.kno --strict
Error: Strict mode requires valid signature metadata; unsigned artifacts are not allowed.
```

**Dependencies:** None (can be built independently of OpenClaw features)

#### feature72: Lockfile (`kinnoo-lock.yaml`)

**What changes:** After `kinnoo install`, write a `kinnoo-lock.yaml` file recording the exact resolved state. Support `kinnoo install --frozen` to reproduce exact installations from the lockfile.

**Why:** Lockfiles are table-stakes for any package manager (npm has `package-lock.json`, pip has `requirements.txt` with pinned versions, APM has `apm.lock.yaml`). Without one, CI/CD pipelines can't guarantee reproducible agent environments.

**Scope:**
- Write `kinnoo-lock.yaml` after successful install (agent name, exact version, source, SHA256, signature fingerprint, install timestamp, platform info)
- `kinnoo install --frozen` reads lockfile and installs exact versions (errors if lockfile missing or version unavailable)
- `kinnoo install` with existing lockfile updates it (additive, not destructive)
- Lockfile stored in the working directory (alongside `kinnoo.yaml` if agent project) or `~/.kinnoo/kinnoo-lock.yaml` for global installs

**Format:**
```yaml
# kinnoo-lock.yaml
lock_version: 1
locked_at: "2026-03-28T10:00:00Z"
platform:
  python: "3.12.4"
  os: "darwin-arm64"
agents:
  earthquake-predictor:
    version: "2.0.0"
    source: "registry.kinnoo.dev"
    archive_sha256: "a1b2c3d4..."
    signature_fingerprint: "e5f6g7h8..."
    installed_at: "2026-03-28T10:00:00Z"
```

**Dependencies:** None

#### feature73: `kinnoo diff`

**What changes:** New CLI command to compare two `.kno` archives and show meaningful differences.

**Why:** AgentPK has `agent diff`. It's obvious in retrospect — if agents are versioned packages, you need to see what changed between versions. Useful for security review before upgrading.

**Scope:**
- `kinnoo diff <a.kno> <b.kno>` — compare two archive files
- Extract both to temp directories, diff file trees
- Output sections: manifest changes (field-by-field), files added/removed, dependency changes, permission changes, env var changes
- Colorized terminal output (green for additions, red for removals)
- `--json` flag for machine-readable output
- Exit code 0 if identical, 1 if different

**Example output:**
```
$ kinnoo diff my-agent-1.0.0.kno my-agent-2.0.0.kno

Manifest changes:
  version: 1.0.0 → 2.0.0
  + env_vars: REDIS_URL (required)
  dependencies:
    + redis>=4.0

Files changed:
  M run.py (23 lines changed)
  A utils/cache.py (new file, 45 lines)
  D old_helper.py (removed)

Permissions:
  + network (new)
```

**Dependencies:** None

#### feature74: `kinnoo uninstall`

**What changes:** New CLI command to cleanly remove an installed agent.

**Why:** Table-stakes. Currently users must manually `rm -rf ~/.kinnoo/agents/<name>/` to remove agents. Every package manager has an uninstall command.

**Scope:**
- `kinnoo uninstall <name>` — remove installed agent by name
- Remove agent directory from `~/.kinnoo/agents/<name>/`
- Remove associated venv if one was created during install
- Update lockfile (feature72) if present
- Remove install trace entry
- Mandatory interactive confirmation before deletion (no bypass flag in Phase 6)
- Error message if agent not found

**Dependencies:** None (but coordinates with feature72 lockfile updates if both are implemented)

#### feature75: Framework Import Adapters

**What changes:** Add `--from <framework>` flag to `kinnoo import` that applies framework-specific knowledge for higher-quality manifest generation.

**Why:** The existing generic analyzer (`analyzer.py`) works but has limited accuracy for framework-specific patterns (user confirmed: "not that great"). GitAgent's `import --from` command demonstrates the value of framework-aware import. This is the fastest path to adoption — meeting developers where they already are.

**How it differs from existing `kinnoo import`:**
- Existing: Generic static analysis via `analyze_project()` — AST-based entrypoint detection, regex env var scanning, import-based framework inference with ~0.5 confidence
- With `--from langgraph`: Framework adapter skips inference, applies known LangGraph project structure and graph entrypoint conventions, maps default env vars, and generates a graph-friendly wrapper entrypoint, confidence → 0.9+

**Scope:**
- Add `--from` argument to import CLI parser (choices: `langchain`, `langgraph`, `openai`)
- Implement 3 framework adapters as pluggable modules in `src/kinnoo/framework_adapters/`:
  - `langchain_adapter.py`: Detects chain/agent patterns, sets up LangChain-specific runtime, maps OPENAI_API_KEY etc.
  - `langgraph_adapter.py`: Detects graph/workflow patterns, infers graph entrypoint and state-model dependencies
  - `openai_adapter.py`: Detects OpenAI Agents SDK patterns, maps function tool schemas, generates runner wrapper
- Each adapter returns an enhanced `AnalysisReport` that is fed into the existing import wizard
- Adapter enhances confidence scores so the wizard skips fields that would have been prompted
- Framework adapters are optional — generic import still works without `--from`
- Unknown frameworks: `--from custom` → falls back to generic analyzer with a message

**On manifest auto-generation without LLM (addressing skepticism):**
- Framework adapters handle *structural* fields well (entrypoint, runtime, dependencies, env vars, permissions)
- *Description* fields remain the gap — static analysis can't describe what an agent does
- Practical approach: leave descriptions as `"TODO: Describe what this agent does"` placeholders
- Future option: `kinnoo import --ai` could optionally call user's own LLM API key to enrich descriptions (not in Phase 6 scope)

**Dependencies:** None

### Phase 6 Execution Strategy

The Phase 6 features fall into two independent tracks that can be worked in parallel:

**Track A — OpenClaw (features 61-67, 70):** Sequential, dependency-ordered. Must be done in order.

**Track B — Competitive Response (features 68-69, 71-75):** Largely independent of each other and of Track A. Can be parallelized.

```
Track A (sequential):        Track B (parallel):
  feature61 (login)            feature68 (CI story)
  feature62 (schema)           feature69 (kinnoo test)
  feature63 (mirror)           feature71 (strict CI mode)
  feature64 (import bridge)    feature72 (lockfile)
  feature65 (install bridge)   feature73 (kinnoo diff)
  feature66 (run adapter)      feature74 (kinnoo uninstall)
  feature67 (sync)             feature75 (framework adapters)
  feature70 (docs)
```

---

## 3. Phase 7 — Focused Pressure Testing + Battle Hardening

**Theme:** "Validate the full lifecycle with 8 diverse agents, fix what breaks"

**Goal:** Confirm kinnoo handles real-world agents across frameworks and runtimes. Fix discovered bugs. Sharpen error messages. This is a focused validation pass, not exhaustive coverage.

### Changes from Planning-5

- **Agent count**: 20 → 8 (the 12 remaining agents move to a post-launch validation backlog)
- **Lifecycle steps**: 9 → 5 (skip publish → remote-install → inspect, which are already well-covered by the 450+ test suite)
- **Duration**: Estimated 1-1.5 weeks instead of 3-4 weeks
- **OpenClaw skills**: 5 → 2

### Selected Agents (8)

| # | Description | Framework | Why Selected |
|---|-------------|-----------|-------------|
| 1 | RAG agent with Chroma vector DB | LangChain | Heavy deps (~200MB), vector DB service, API key — max complexity Python agent |
| 2 | Structured output agent | PydanticAI | Typed I/O, async execution — tests type-safe agent patterns |
| 3 | Simple CLI chatbot | Vanilla Python | Minimal framework — baseline sanity test |
| 4 | CLI chatbot with OpenAI SDK | Node.js | Cross-language — validates Node.js packaging pipeline |
| 5 | TypeScript MCP server | MCP (TS) | Daemon runtime + TypeScript compilation — tests daemon lifecycle |
| 6 | Multi-file agent with src/ layout | Python | Subdirectory entrypoint, relative imports — tests real project structures |
| 7 | Weather skill (simple) | OpenClaw | Simplest possible skill — tests Phase 6 import bridge baseline |
| 8 | GitHub skill (binary dep) | OpenClaw | Requires `gh` CLI binary — tests dependency edge case |

### Shortened Lifecycle Protocol (5 steps)

```
1. kinnoo import <agent-dir> [--from <framework>]  → check detection accuracy
2. kinnoo check <agent-dir>                         → check false alarms
3. kinnoo pack <agent-dir>                          → check archive creation
4. kinnoo install <archive.kno>                     → check install + deps
5. kinnoo run <installed> "<input>"                 → check runtime execution
```

For OpenClaw skills (agents 7-8), use the Phase 6 bridge protocol:
```
1. kinnoo import --source clawhub <slug>  → test ClawHub import
2. kinnoo check <skill-dir>               → security sweep
3. kinnoo install <skill-package>          → delegated install
4. kinnoo run <skill> -- "<input>"         → run adapter test
```

### Features

| Feature | Title | Key Deliverables | Dependencies |
|---------|-------|------------------|--------------|
| feature76 | Pressure testing — 8 agents | Test agents 1-8 through shortened lifecycle; per-agent report in `notes/pressure-testing/`; bug list | Phase 6 features (for OpenClaw bridge + framework adapters) |
| feature77 | Bug fixes and battle hardening | Fix all bugs from feature76; improve error messages; CLI UX polish | feature76 |
| feature78 | Analyzer enhancements from findings | `.env.example` scanning, framework-to-env-var mapping, JS/TS env var regex, import-to-permission inference | feature76 |
| feature79 | Pressure testing summary | Aggregate summary report; top improvements list; known limitations doc | feature77, feature78 |

### Post-Launch Validation Backlog (from planning-5's 20 agents)

These agents are still valuable validation targets but don't block launch:
- OpenAI Agents SDK tool-calling agent
- LangGraph multi-step reasoning
- CrewAI/AutoGen multi-tool
- Python MCP server (filesystem)
- Streamlit agent dashboard
- FastAPI agent endpoint
- Express.js agent API
- Agent with 10+ env vars and 3 service deps
- Docker-dependent agent (Redis + Postgres)
- OpenClaw: ontology, gog, browser automation skills

---

## 4. Phase 8 — Agent Composition (Trimmed)

**Theme:** "Make agents composable building blocks (subprocess + tool invocation)"

**Goal:** An agent's `kinnoo.yaml` can declare dependencies on other agents. `kinnoo install` recursively installs the dependency tree. Agents can invoke sub-agents as subprocesses or Python-callable tools.

### Changes from Planning-5

- **Removed mcp-server runtime helper from this phase:** Deferred to post-launch. Subprocess and tool invocation cover the primary composition use cases. MCP server composition adds significant complexity (lifecycle management, health checks, port allocation) without user demand signal.
- **Removed full E2E cross-framework validation from this phase:** Replaced with a lighter validation step within the tool-invocation feature. A real composed agent is still tested, but the scope is 1 composed agent (Python parent → Python tool sub-agent), not the cross-framework Python+Node.js scenario from planning-5.

### Features

| Feature | Title | Key Deliverables | Dependencies |
|---------|-------|------------------|--------------|
| feature80 | Agent dependency schema and resolution | `agent_dependencies` field in `kinnoo.yaml`; version constraint parser; dependency resolver; circular dependency detection | None |
| feature81 | Recursive agent dependency installation | `kinnoo install` detects and resolves agent_dependencies from registry; installs sub-agents into `~/.kinnoo/agents/`; aggregated permission summary | feature80 |
| feature82 | Runtime helper — `invoke_as: subprocess` | Sub-agent invocation via subprocess; env var sandboxing; stdout capture; exit code propagation; timeout | feature81 |
| feature83 | Runtime helper — `invoke_as: tool` + light E2E validation | `kinnoo.runtime.load_agent_tool(name)` Python helper; wraps subprocess invocation as a callable; test with 1 real composed agent (Python parent → Python sub-agent) | feature82 |

### Deferred to Post-Launch

| Feature | Title | Reason |
|---------|-------|--------|
| (planning-5 feature81) | `invoke_as: mcp-server` runtime helper | Complexity (lifecycle, health checks, port allocation) without user demand signal |
| (planning-5 feature82) | Full cross-framework E2E | Covered by lighter validation in feature83 |

### Manifest example (unchanged from planning-5)

```yaml
name: earthquake-predictor
version: 2.0.0
runtime:
  language: python
  version: ">=3.11"
  type: one-shot
entrypoint: run.py
dependencies:
  - langchain
agent_dependencies:
  - name: seismic-data-fetcher
    version: ">=1.0,<2.0"
    invoke_as: tool
  - name: geological-model
    version: ">=3.0"
    invoke_as: subprocess
```

---

## 5. Phase 9 — Trust Ecosystem and Open Source Launch

**Theme:** "Trust signals for strangers, then open the doors"

### Changes from Planning-5

- **No structural changes.** Features 84-92 (renumbered from 83-91) remain the same.
- **Timeline acceleration**: Phase 9 prep work (open source repo setup, CONTRIBUTING.md) begins during Phase 8 to reduce calendar time.
- **Production deployment** (feature89 equivalent) can be done in parallel with Phase 8 since it's infrastructure, not code.

### Features

| Feature | Title | Dependencies |
|---------|-------|--------------|
| feature84 | GitHub OAuth and identity linking | None |
| feature85 | Verified publisher badges | feature84 |
| feature86 | Security and signing badges in registry | None |
| feature87 | `kinnoo update` command | feature61 |
| feature88 | CONTRIBUTING.md and community templates | None |
| feature89 | Open source preparation | feature88 |
| feature90 | Production deployment hardening | None |
| feature91 | Seed registry with 10-20 agents | feature89, feature90 |
| feature92 | Public launch and open source announcement | feature89, feature90, feature91 |

> Full design details remain the same as planning-5 features 83-91.

### Parallel Execution Strategy

```
Phase 8 (composition):          Phase 9 prep (parallel):
    feature80 (schema)              feature88 (CONTRIBUTING.md)
    feature81 (recursive install)   feature89 (open source prep)
    feature82 (subprocess)          feature90 (production hardening)
    feature83 (tool + E2E)
                                  ↓
                  feature84-87 (trust features)
                                  ↓
                  feature91 (seed registry)
                                  ↓
                  feature92 (launch)
```

---

## 6. Phase 10 — Agent Test and Eval Ecosystem

**Unchanged from planning-5.** Still shaped by post-launch user feedback.

| Feature | Title | Dependencies |
|---------|-------|--------------|
| feature93 | Test results in publish metadata | feature69 |
| feature94 | Test result badges in registry | feature93 |
| feature95 | `kinnoo test --mock` mode for CI | feature69 |
| feature96 | Eval framework — structured evaluations | feature69 |
| feature97 | Eval scores in registry | feature96 |
| feature98 | Test/eval documentation and best practices | feature93, feature96 |

---

## 7. Feature ID Traceability

### Planning-5 → Planning-6 mapping

| Planning-5 ID | Planning-6 ID | Status |
|---------------|---------------|--------|
| feature61-70 | feature61-70 | Unchanged |
| (new) | feature71 | NEW — Strict CI signed-package mode |
| (new) | feature72 | NEW — Lockfile |
| (new) | feature73 | NEW — kinnoo diff |
| (new) | feature74 | NEW — kinnoo uninstall |
| (new) | feature75 | NEW — Framework import adapters |
| (moved) | POST-LAUNCH | Sigstore signing migration deferred |
| feature71-73 | feature76 | MERGED — 20 agents → 8 agents in single feature |
| feature74 | feature77 | Renumbered — Bug fixes |
| feature75 | feature78 | Renumbered — Analyzer enhancements |
| feature76 | feature79 | Renumbered — Summary |
| feature77 | feature80 | Renumbered — Dependency schema |
| feature78 | feature81 | Renumbered — Recursive install |
| feature79 | feature82 | Renumbered — Subprocess helper |
| feature80 | feature83 | Renumbered — Tool helper (+ light E2E) |
| feature81 | DEFERRED | MCP server composition → post-launch |
| feature82 | DEFERRED | Full E2E validation → absorbed into feature83 |
| feature83-91 | feature84-92 | Renumbered |
| feature92-97 | feature93-98 | Renumbered |

---

## 8. Dependency Graph

```
Phase 6:
  Track A (OpenClaw, sequential):
    feature61 (login) → feature62 (schema) → feature63 (mirror) → feature64 (import bridge)
                                            → feature65 (install bridge) → feature66 (run adapter)
                                            → feature67 (sync)
    feature68 (CI) ← feature61

  Track B (Competitive Response, parallelizable):
    feature69 (kinnoo test)     — standalone
    feature70 (docs)            — standalone
    feature71 (strict CI mode)  — standalone
    feature72 (lockfile)        — standalone
    feature73 (kinnoo diff)     — standalone
    feature74 (uninstall)       — standalone
    feature75 (fw adapters)     — standalone

Phase 7:
  feature76 (pressure test) ← Phase 6
  feature77 (bug fixes) ← feature76
  feature78 (analyzer) ← feature76
  feature79 (summary) ← feature77, feature78

Phase 8:
  feature80 (dep schema) — standalone
  feature81 (recursive install) ← feature80
  feature82 (subprocess) ← feature81
  feature83 (tool + E2E) ← feature82

Phase 9 (overlaps with Phase 8):
  feature84 (OAuth) — standalone
  feature85 (verified badges) ← feature84
  feature86 (security badges) — standalone
  feature87 (update) ← feature61
  feature88 (CONTRIBUTING) — standalone
  feature89 (open source) ← feature88
  feature90 (production) — standalone
  feature91 (seed) ← feature89, feature90
  feature92 (launch) ← feature89, feature90, feature91

Phase 10:
  feature93 (test publish) ← feature69
  feature94 (test badges) ← feature93
  feature95 (mock mode) ← feature69
  feature96 (eval framework) ← feature69
  feature97 (eval scores) ← feature96
  feature98 (test/eval docs) ← feature93, feature96
```

---

## 9. Risks and Mitigations

Carried forward from planning-5, plus new entries:

| Risk | Impact | Mitigation |
|------|--------|------------|
| Strict mode can block existing CI pipelines | Teams using unsigned artifacts may see immediate failures | Start in warning/audit mode in docs first, then enforce `--strict` in CI templates |
| Framework adapters are incomplete | `--from langgraph` only handles common patterns, misses exotic setups | Adapters are best-effort + framework-specific TODO guidance; generic analyzer is always the fallback |
| Reduced pressure testing misses bugs | 8 agents vs 20 might miss edge cases | Post-launch validation backlog catches remaining cases; 450+ automated tests provide safety net |
| Phase 8/9 parallel execution causes conflicts | SWE agent working on composition while infrastructure changes for open-source prep | Strict file ownership: composition features have no overlap with CI/deployment files |
| Market window closes before launch | A major player (Docker, LangChain, OpenAI) launches competing tool | Focus on DX quality over feature quantity; a polished 80% product beats a rough 100% product |
| Lockfile format needs revision post-launch | Initial schema may not handle agent composition dependencies | Start with `lock_version: 1` field for forward compatibility; add `agent_dependencies` section when feature80 lands |
| Sigstore migration slips due to identity/provenance complexity | Post-launch trust roadmap might delay keyless signing | Keep Ed25519 path robust; treat Sigstore as a dedicated post-launch project with staged rollout |
