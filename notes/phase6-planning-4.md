# Phase 6+ Planning (Revised #3): ClawHub Piggyback Strategy

_Date: March 27, 2026_

This update revises the prior recommendation and evaluates your idea directly:

- Use OpenClaw skills as a first-class packaging unit in kinnoo
- Piggyback on ClawHub instead of recreating a parallel OpenClaw ecosystem
- Mirror/sync ClawHub metadata into a clearly labeled open registry namespace: `kinnoo-clawhub`
- Let kinnoo add value with preflight, security overlays, trust signals, and later evals

Short conclusion: **Yes, this can work and is a strong strategy** if we treat it as a delegated integration layer (not a replacement runtime or replacement registry).

---

## 1. Direct Answer: Is Piggybacking Off ClawHub a Good Idea?

Yes. This is likely the best OpenClaw strategy for kinnoo.

It aligns with reality:
1. ClawHub already has scale and network effects.
2. OpenClaw CLI already supports native ClawHub search/install/update.
3. Kinnoo should avoid rebuilding ClawHub from scratch.
4. Kinnoo can still add clear value: normalized metadata, extra safety checks, cross-framework discoverability, and consistent trust UX.

So this becomes:
- **ClawHub = source of truth for OpenClaw skills**
- **Kinnoo = metadata mirror + security overlay + cross-framework discovery + lifecycle UX**

---

## 2. Key Reality Check: No Documented `openclaw skills run`

Your proposed flow used:

`openclaw skills run slack --action sendMessage --data '{...}'`

Current OpenClaw docs show these `skills` commands:
- `search`
- `install`
- `update`
- `list`
- `info`
- `check`

They do **not** document `skills run` right now.

That does not kill your idea. It just changes execution design:

### Practical execution options for kinnoo

Option A (preferred near-term):
- `kinnoo run` for OpenClaw skill units delegates to a supported OpenClaw invocation path (for example `openclaw agent --message ...` with skill-specific prompt/command conventions).

Option B (future):
- If/when OpenClaw exposes an official `skills run` command, kinnoo upgrades delegation to use it directly.

Design implication:
- Build kinnoo run delegation behind a small adapter interface so the command backend can change without breaking kinnoo UX.

---

## 3. Revised Product Model

The earlier "package full OpenClaw agent" model was too heavy. Your new "skills as packaging unit" model is cleaner.

### New unit type

Introduce a dedicated package unit in kinnoo:
- `type: openclaw-skill`
- `framework: openclaw`
- `source_registry: clawhub`
- `source_slug: owner/skill`
- `source_version: semver`

This is a thin package contract around a ClawHub skill, not a full daemon app.

### What gets stored in kinnoo

For each mirrored skill record in `kinnoo-clawhub`:
- ClawHub slug, owner, version, tags
- Description + install requirements metadata
- Source URL + attribution
- Last synced timestamp
- Kinnoo-added fields:
  - normalized manifest projection
  - preflight/security scan summary
  - compatibility and confidence flags
  - optional test/eval metadata later

### Clear labeling in UX

Every mirrored record should display:
- `Source: ClawHub (mirrored)`
- `Install delegated to OpenClaw CLI`
- `This listing is synced metadata, not an independently published kinnoo artifact`

This addresses confusion and avoids competing narrative.

---

## 4. Proposed Command UX

### 4.1 Import

Your suggested command:
- `kinnoo import <openclaw-skill>`

Recommended explicit forms:
- `kinnoo import openclaw:steipete/slack`
- `kinnoo import --source clawhub steipete/slack`

Behavior:
1. Resolve skill metadata from mirrored index (or live fallback).
2. Scaffold `kinnoo.yaml` with `type: openclaw-skill` + source fields.
3. Populate known requirements (bins/env/config gates) from skill metadata.
4. Save a local import report explaining what is inferred vs unresolved.

### 4.2 Install

- `kinnoo install <skill-package>` delegates to OpenClaw native install:
  - `openclaw skills install <slug> [--version]`

Then kinnoo runs its added checks on the local installed skill directory:
- static checks
- policy checks
- optional extra dependency/script heuristics

### 4.3 Run

Given current OpenClaw docs, define run as delegated invocation adapter:

- `kinnoo run <openclaw-skill> -- <skill args>`

Adapter behavior (phase-gated):
1. Detect available OpenClaw invocation backend.
2. If native skill execution command exists in installed OpenClaw version, use it.
3. Else fallback to supported agent invocation mode with generated skill-oriented command/prompt envelope.

Important:
- Keep this version-aware and transparent in logs:
  - `Delegating via openclaw backend: agent-message` (or `skills-run` when available)

### 4.4 Sync

Your sync concept is good here.

Add:
- `kinnoo sync clawhub`
- `kinnoo sync clawhub --since <timestamp>`
- `kinnoo sync clawhub --full`

Behavior:
- Pull skill metadata delta from ClawHub source
- Upsert into `kinnoo-clawhub`
- Preserve source attribution and mirrored status
- Never rewrite source ownership

This is where `sync` is justified (mirror ingest), distinct from package update semantics.

---

## 5. Architecture: `kinnoo-clawhub` Mirror

### Data flow

1. **Ingest**: pull ClawHub metadata (official API if available, otherwise supported CLI export flow)
2. **Normalize**: map to kinnoo schema extension (`openclaw-skill` unit)
3. **Enrich**: add kinnoo checks and trust fields
4. **Serve**: show in kinnoo search/list/inspect under `kinnoo-clawhub`
5. **Install/Run**: delegate to OpenClaw runtime CLI

### Separation of concerns

- Do not rehost source bundles unless explicitly needed for caching/compliance.
- Prefer metadata mirror + delegated install.
- If caching is added later, keep source integrity metadata (hash/version/source URL) and provenance labels.

### Failure modes to handle

- ClawHub unavailable
- OpenClaw CLI not installed
- OpenClaw CLI version mismatch
- Skill metadata field drift
- Skill removed or hidden on ClawHub

### Required guardrails

- Strong attribution in UI/CLI
- Rate limiting and polite sync policy
- Respect source terms and moderation signals
- Display mirrored suspicious flags from ClawHub and kinnoo-side flags distinctly

---

## 6. Value Added by Kinnoo Without Rebuilding ClawHub

This model gives kinnoo differentiated value while piggybacking:

1. Cross-framework discovery in one place.
2. Unified preflight and install diagnostics across frameworks.
3. Additional static safety checks and policy scoring.
4. Consistent manifest projection for teams.
5. Future eval/test overlays with comparable trust badges across OpenClaw, MCP, Python, Node.

So users get OpenClaw skill access plus kinnoo platform capabilities, with minimal duplication.

---

## 7. Feasibility Assessment

### Engineering complexity

Low to medium for the first useful version.

Low complexity:
- mirrored index model
- `kinnoo import --source clawhub`
- delegated install
- source labeling in search/inspect

Medium complexity:
- robust sync pipeline
- run delegation adapter across OpenClaw versions
- provenance and conflict handling

High complexity (defer):
- full execution abstraction over unstable OpenClaw skill invocation contracts
- deep compatibility testing over many skill command styles

### Recommended feasibility stance

- **Do this** as a scoped integration.
- Keep MVP to metadata mirror + delegated install + inspect/check.
- Phase run delegation behind compatibility flags until invocation backend is stable.

---

## 8. Revised Phase 6+ Plan

This updates phase6-planning-3.md to incorporate the piggyback strategy.

## Phase 6: Pressure Testing and ClawHub Bridge MVP

| Feature | Title | Key Deliverables |
|---------|-------|------------------|
| feature61 | Pressure testing batch 1 | Python one-shot agents (1-6), reports |
| feature62 | Pressure testing batch 2 | Python daemon + Node agents (7-12), reports |
| feature63 | Pressure testing batch 3 | Edge cases (13-15) + OpenClaw skills (16-20) via delegated install/inspect flows |
| feature64 | Bug fixes from pressure tests | Reliability, errors, UX fixes from 61-63 |
| feature65 | Analyzer enhancements | env var mapping, JS/TS detections, constructor hints |
| feature66 | Registry auth UX | `kinnoo login` + `kinnoo logout` |
| feature67 | ClawHub mirror index MVP | New mirrored registry namespace `kinnoo-clawhub`; metadata ingestion + attribution fields |
| feature68 | ClawHub import bridge | `kinnoo import --source clawhub <slug>` scaffolds `kinnoo.yaml` for `type: openclaw-skill` |
| feature69 | Delegated install bridge | `kinnoo install` for openclaw-skill delegates to `openclaw skills install` and runs kinnoo checks |
| feature70 | Landing page + docs update | Positioning: "Kinnoo integrates with ClawHub" and source-labeling UX |

## Phase 7: Execution Adapter + Composition Core

| Feature | Title | Key Deliverables |
|---------|-------|------------------|
| feature71 | OpenClaw run adapter v1 | `kinnoo run` delegation backend for openclaw-skill units, backend detection, transparent logs |
| feature72 | Agent dependency schema | `agent_dependencies` constraints + resolver |
| feature73 | Recursive dependency install | dependency install + permission aggregation |
| feature74 | Runtime helper: subprocess | sub-agent invocation helper |
| feature75 | Runtime helper: tool | callable wrapper helper |
| feature76 | Runtime helper: mcp-server | MCP server sub-agent helper |
| feature77 | Composition E2E validation | parent + sub-agents cross-framework validation |

## Phase 8: Trust, Sync Hardening, and Launch

| Feature | Title | Key Deliverables |
|---------|-------|------------------|
| feature78 | ClawHub sync command | `kinnoo sync clawhub` with delta/full modes, observability, retries |
| feature79 | Verified source badges | Distinct badge model: source-verified vs kinnoo-verified checks |
| feature80 | Security and trust badges | scan/sign/check indicators for mirrored and native packages |
| feature81 | Open source prep | CLI publicization + docs + contributor guides |
| feature82 | Seed registry content | curate top mirrored skills + native kinnoo agents |
| feature83 | Public launch | launch with explicit ClawHub integration narrative |

---

## 9. Implementation Rules (Critical)

To keep this strategy healthy:

1. Never pretend mirrored skills are first-party kinnoo packages.
2. Always show source provenance and sync timestamp.
3. Keep install/run delegated to OpenClaw where possible.
4. Do not fork ClawHub distribution logic unless strictly necessary.
5. Keep run delegation backend-compatible and version-aware.

---

## 10. Final Recommendation

Adopt your piggyback model.

Refined position:
- OpenClaw skills can be a packaging unit in kinnoo.
- But kinnoo should treat them as **source-mirrored delegated units**, not standalone runnable apps.
- Build the bridge first (mirror/import/install/check), then phase in run delegation safely.

This gives kinnoo the upside of OpenClaw ecosystem compatibility without rebuilding ClawHub or fighting OpenClaw’s native workflow.
