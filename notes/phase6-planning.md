# Phase 6-8 Planning: Kinnoo Strategic Direction

_Date: March 26, 2026_

This document captures the strategic discussion and concrete planning for Phases 6-8 of kinnoo, informed by a thorough review of all 60 completed features and the project's value proposition analysis.

---

## Table of Contents

1. [Features Already Implemented (Summary)](#1-features-already-implemented)
2. [Kinnoo's Value to Developer Teams](#2-kinnoos-value-to-developer-teams)
3. [Tagline and Messaging Recommendations](#3-tagline-and-messaging-recommendations)
4. [Feature Section Recommendations](#4-feature-section-recommendations)
5. [GitHub Actions Integration](#5-github-actions-integration)
6. [Agent Composition — Detailed Design](#6-agent-composition--detailed-design)
7. [Real-World Agent Pressure Testing Plan](#7-real-world-agent-pressure-testing-plan)
8. [OpenClaw Deep Support Strategy](#8-openclaw-deep-support-strategy)
9. [Verified Publishers, Badges, and Agent Testing](#9-verified-publishers-badges-and-agent-testing)
10. [Improving Auto-Detection in the Analyzer](#10-improving-auto-detection-in-the-analyzer)
11. [Open Source Community Strategy](#11-open-source-community-strategy)
12. [Revised Phase 6, 7, 8 Plans](#12-revised-phase-6-7-8-plans)

---

## 1. Features Already Implemented

Having reviewed all of FEATURES.txt, here is what kinnoo already has across 60 features in 5 phases:

**Phase 1 (V1) — MVP (features 1-6):** Manifest schema, `kinnoo init`, `kinnoo run`, `--framework` templates (gemini, chatgpt, claude-chat), `kinnoo pack`, `kinnoo install` from .kno archive.

**Phase 2 (V2) — Expanded CLI (features 7-19):** CLI refactor, packaging robustness (transitive deps, zip format, fallback), schema V2 (description, author, license, env_vars), env var management (.env fallback, masked prompt), `kinnoo inspect`, local registry (publish/install/list/search), pack/publish refactor, preflight checks, trust baseline (install summary, run traces, heuristic code sweep), checksums (SHA256), pack size reporting, input safety guard (6 threat categories, Protocol-based), `kinnoo import` (analyzer-backed onboarding wizard).

**Phase 3 (V3) — Share Any Agent (features 20-30, 42-44):** Flexible runtime inputs (no-input, pass-through args), framework expansion (pydantic-ai, langgraph, openai-agents), asset bundling, MCP server runtime type, service declarations, service health checks, MCP server packages + client templates, project analyzer module, **remote registry backend abstraction + client**, **remote registry FastAPI server** (S3 storage, JWT auth, presigned URLs, pagination), **registry web UI** (Jinja2, session cookies, CSRF), JSON input/output types, auth/user/tenant management (argon2 hashing, bootstrap CLI, JWT, key rotation), UAT improvements.

**Phase 4 (V4) — OpenClaw + JS/TS (features 31-41, 45-48):** Node.js runtime support, daemon runtime type + process controls, OpenClaw schema extensions, OpenClaw scaffold template, mutable state directories, OpenClaw import detection, Node.js dependency audit + CVE gating, JS/TS static security sweep, manifest permissions model + sandbox execution, archive signing (Ed25519), runtime behavior monitoring + kill switch, agent supportability assessment (246 agents analyzed), `kinnoo inspect --full/--raw/--update`, `kinnoo check`, `kinnoo import` from URL.

**Phase 5 (V5) — Web Frontend (features 49-60):** Next.js App Router project, MainLayout + design system, landing page + terminal preview + feature grid, secure login UI, registry dashboard (my agents + search), agent cards + manifest modal, BFF proxy + CSRF + auth guard, admin bootstrap, security headers + production hardening, signup + email verification + tenant provisioning, forgot password + session revocation, relational auth foundation (SQLite dev, PostgreSQL-ready).

**Bottom line:** Kinnoo is genuinely feature-rich. The remote registry, web UI, auth system, multi-runtime support (Python + Node.js), signing, sandboxing, monitoring — these are all implemented. The "distribution" gap identified in the previous conversation (features 28-30) has been closed.

---

## 2. Kinnoo's Value to Developer Teams

You asked: "Wouldn't kinnoo still help a team of agent developers?"

**Yes, absolutely.** Here's how to think about it:

Kinnoo is NOT a replacement for Git in the development workflow. But it is a powerful complement in the **release and consumption** workflow. The analogy:

- **Git** = how the team collaborates on the code (branching, PRs, code review)
- **kinnoo** = how the team releases the agent and how consumers use it

For a team of 3 developers working on an earthquake-prediction agent:

| Workflow Step | Tool |
|---|---|
| Write code, branch, PR, merge | Git + GitHub |
| CI runs tests → `kinnoo pack && kinnoo publish` on merge to main | GitHub Actions + kinnoo |
| Agent appears in registry with version, signature, scan results | kinnoo registry |
| A researcher runs `kinnoo install earthquake-predictor && kinnoo run earthquake-predictor "analyze CA"` | kinnoo CLI |
| The researcher wants to contribute → sees `repository: github.com/team/earthquake-predictor` in `kinnoo inspect` | kinnoo → Git |

Kinnoo provides value to the team in these specific ways:

1. **Versioned registry stamps** — Each `kinnoo publish` creates a versioned, signed, security-scanned snapshot in the registry. The team has a clear audit trail: "v1.3.0 was published by jerry, signed with key X, passed security sweep, checksum Y."

2. **Simplified onboarding** — New team members (or testers, or stakeholders) don't need to clone the repo and figure out setup. `kinnoo install` handles it.

3. **CI/CD integration** — `kinnoo pack --preflight && kinnoo pack && kinnoo publish` in GitHub Actions means every merge to main produces a tested, signed, publishable artifact. The team's release process is automated.

4. **Cross-project agent reuse** — If team A builds a data-fetcher agent and team B builds an analysis agent, the analysis agent can declare `kinnoo install data-fetcher` as part of its setup. Eventually (with composition), it can declare the data-fetcher as an agent dependency.

5. **Trust verification** — Even within a team, `kinnoo inspect` and the security sweep catch things code review might miss (hardcoded secrets, unsafe patterns, excessive permissions).

Your instinct is right. The tagline should acknowledge this team value. More on that next.

---

## 3. Tagline and Messaging Recommendations

### Main Tagline Analysis

"Building AI agents together" is warm and collaborative, but you're right to question it — it implies kinnoo is primarily about the collaboration workflow (which is Git's territory). It doesn't convey what kinnoo actually does.

The tagline needs to communicate the core action: **packaging and distributing agents** with trust and simplicity.

**Suggested taglines** (ordered by my preference):

1. **"Ship any AI agent"**
   - Action-oriented, framework-agnostic, concise
   - Implies the full lifecycle: pack → publish → install → run
   - "Ship" resonates with developers (shipping code, shipping features)
   - Doesn't box you into just one use case

2. **"Package. Publish. Run."**
   - Three words, three core actions
   - Immediately communicates what kinnoo does
   - Memorable and scannable

3. **"Every agent, one install away"**
   - Consumer-facing: emphasizes the ease of getting agents
   - Creates desire ("I want that experience")
   - Implies the registry/discovery ecosystem

4. **"Trusted agent delivery"**
   - Emphasizes the security and trust differentiator
   - "Delivery" implies the full pipeline
   - More enterprise-flavored

5. **"The package manager for AI agents"**
   - Most literal, most searchable
   - You pushed back on "npm for agents" — this version is more professional
   - Developers immediately understand the category

My recommendation: **"Ship any AI agent"** as the main tagline. It's short, it's action-oriented, it's framework-agnostic, and it implies the full lifecycle. "Building AI agents together" can still appear elsewhere — in the community/contribution section, or on the GitHub README.

### Sub-line Analysis

Current: "The open, secure platform to package, publish and share any AI agent"

This is actually quite good. It hits the key points: open source, security, the three core actions, framework-agnostic ("any AI agent"). Minor suggestions:

**Option A (keep close to current):**
> "The open-source platform to package, publish, and run AI agents — securely"

Rationale: replaced "share" with "run" (more concrete action), moved "securely" to the end for emphasis, added hyphen to "open-source" for grammatical precision.

**Option B (more punchy):**
> "Package, publish, and run AI agents with built-in trust"

Rationale: shorter, action-first, "built-in trust" is more compelling than "secure" (implies proactive, not just defensive).

**Option C (ecosystem-forward):**
> "The open platform where developers package, discover, and run AI agents"

Rationale: adds "discover" (implies registry), positions as a platform/ecosystem play.

My recommendation: **Option B** if you want to be concise, **Option A** if you want to keep the current tone.

---

## 4. Feature Section Recommendations

### Current feature section intro:

> "Take any AI agent — a LangGraph chatbot, a PydanticAI workflow, an OpenClaw daemon — and give it a portable, version-controlled, signed package that anyone can install and run"

### Suggested replacement:

> "Take any AI agent — LangGraph, PydanticAI, OpenAI Agents SDK, OpenClaw — and turn it into a signed, portable package that anyone can install and run in two commands"

Rationale: "two commands" is more concrete than "anyone can install and run." Dropped "version-controlled" (implies Git, which is confusing). Added "OpenAI Agents SDK" since it's a major supported framework. Changed "give it a package" to "turn it into a package" (more active).

### Suggested 6 features:

**1. Works with any agent framework**
> Initialize, import, or install agents built with LangChain, LangGraph, PydanticAI, OpenAI Agents SDK, OpenClaw, MCP servers, and more — Python and Node.js.

Rationale: Added "MCP servers" (big talking point) and "Python and Node.js" (multi-runtime is a differentiator). Changed from "Supports common" to "Works with any" (more inclusive, more confident).

**2. Two commands to install and run**
> `kinnoo install my-agent && kinnoo run my-agent "analyze this"` — no README hunting, no venv setup, no env var guessing. Dependencies, runtime, and configuration are handled by the manifest.

Rationale: Lead with the concrete developer experience instead of the packaging step. This is what makes someone try kinnoo. The current "One-command packaging" headline speaks to the publisher, not the consumer. Both matter, but the consumer experience is more compelling for adoption.

**3. Publish to a hosted registry**
> Package your agent into a signed .kno archive and publish it to the kinnoo registry. Others discover it with `kinnoo search`, inspect it with `kinnoo inspect`, and install it — all from the CLI or the web dashboard.

Rationale: Combines the publish + discover story into one card. Mentions both CLI and web UI. Uses "signed" to hint at trust.

**4. Inspect and trust before you run**
> Before running someone else's agent, see exactly what it needs: permissions, API keys, dependencies, services, and security scan results. Signed archives verify publisher identity. Permission declarations keep you in control.

Rationale: This is kinnoo's biggest differentiator vs. "just clone a repo." Leads with the trust story. Combines the current cards #5 and #6 into a stronger single card.

**5. Built for real-world agents**
> Python venvs, Node.js package managers, MCP servers, long-running daemons, assets, mutable state — kinnoo handles the full runtime spectrum. Preflight checks catch problems before execution, not after.

Rationale: Keeps the "real-world" messaging but tightens it. Mentioning specific things (venvs, MCP servers, daemons, assets) proves it's not vaporware.

**6. Secure by default**
> Input safety guards, heuristic code sweeps, dependency audits, Ed25519 archive signing, sandbox execution, runtime monitoring, and an automated kill switch. Defense in depth — from pack to run.

Rationale: The security feature list is genuinely impressive and differentiating. "Defense in depth — from pack to run" is a strong close.

---

## 5. GitHub Actions Integration

You asked: "Is there anything I need to do for GitHub Actions integration?"

The good news: **kinnoo's CLI is already CI-friendly.** You have `--yes` flags, non-interactive modes, JSON exit codes, and `kinnoo pack --preflight`. So a working GitHub Actions workflow can be written today with no new kinnoo features.

What you should create (no code changes to kinnoo required):

### A reference GitHub Actions workflow file

Create a file like `docs/github-actions-example.yml` or publish it in a separate `kinnoo-github-action` repo:

```yaml
# .github/workflows/kinnoo-publish.yml
name: Pack & Publish Agent
on:
  push:
    tags: ['v*']

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install kinnoo
        run: pip install kinnoo

      - name: Preflight check
        run: kinnoo run . --preflight

      - name: Pack agent
        run: kinnoo pack . --yes

      - name: Publish to registry
        run: kinnoo publish $(cat kinnoo.yaml | grep 'name:' | awk '{print $2}') --yes
        env:
          KINNOO_REGISTRY_URL: ${{ secrets.KINNOO_REGISTRY_URL }}
          KINNOO_REGISTRY_TOKEN: ${{ secrets.KINNOO_REGISTRY_TOKEN }}
```

### Things to verify / potentially implement:

1. **`KINNOO_REGISTRY_TOKEN` env var support** — The CLI already reads `KINNOO_REGISTRY_URL` from env. Verify that `kinnoo publish` can also read the auth token from an env var (not just `~/.kinnoo/config.yaml`). If not, add `KINNOO_REGISTRY_TOKEN` env var support — this is essential for CI where you can't write to a config file. Check the existing code in `src/kinnoo/registry.py` or the remote client.

2. **`kinnoo pack` outputting the archive path** — Verify `kinnoo pack` prints or returns the archive path so CI scripts can reference it. It already prints "Archive size" — confirm it also prints the full path.

3. **Sign in CI** — `kinnoo pack --sign` needs the private key available. Document how to inject signing keys via GitHub Secrets (e.g., `KINNOO_SIGNING_KEY` env var → write to temp file → pass to `--sign`).

4. **Exit codes** — Verify that `kinnoo pack` and `kinnoo publish` return non-zero on failure so CI pipelines fail properly. Should already be the case, but worth a quick verification.

5. **Consider a `kinnoo ci` convenience command** — A single command that runs `check + pack + publish` in sequence, designed for CI. Not essential for Phase 6, but nice for developer experience.

**The main point:** This is mostly documentation and verification work, not new feature development. The CI story is already 90% there.

---

## 6. Agent Composition — Detailed Design

You asked for concrete details on how agent composition would work in practice.

### The Problem

Today, if agent A needs to call agent B, the developer has to:
1. Manually install agent B
2. Write custom integration code in agent A to invoke agent B
3. Handle agent B's input/output format, env vars, and lifecycle manually
4. Hope the versions are compatible

### The Solution: `agent_dependencies` in kinnoo.yaml

```yaml
# kinnoo.yaml for earthquake-predictor (the "parent" agent)
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
    invoke_as: tool        # "tool" | "subprocess" | "mcp-server"
  - name: geological-model
    version: ">=3.0"
    invoke_as: subprocess
inputs:
  type: text
outputs:
  type: json
```

### How `kinnoo install` handles agent dependencies

```
$ kinnoo install earthquake-predictor

[kinnoo install] Resolving earthquake-predictor@2.0.0...
[kinnoo install] Agent dependencies detected:
  - seismic-data-fetcher >=1.0,<2.0 (resolving... 1.2.0)
  - geological-model >=3.0 (resolving... 3.1.0)

[kinnoo install] Installing seismic-data-fetcher@1.2.0...
  ✓ Archive verified (SHA256 + Ed25519 signature)
  ✓ Dependencies installed (3 packages)

[kinnoo install] Installing geological-model@3.1.0...
  ✓ Archive verified (SHA256 + Ed25519 signature)
  ✓ Dependencies installed (5 packages)

[kinnoo install] Installing earthquake-predictor@2.0.0...
  ✓ Archive verified (SHA256 + Ed25519 signature)
  ✓ Dependencies installed (8 packages)
  ✓ Agent dependencies wired

[kinnoo install] Permission summary:
  earthquake-predictor: network, filesystem (read-only)
  seismic-data-fetcher: network
  geological-model: filesystem (read-only)
  Approve? [y/N]: y

✓ earthquake-predictor@2.0.0 ready to run
```

### How `kinnoo run` invokes sub-agents (three modes)

#### Mode 1: `invoke_as: tool` (recommended for most cases)

Kinnoo generates a wrapper that the parent agent can call as a Python function or tool. This is the lightest integration:

```python
# run.py of earthquake-predictor
import sys
from kinnoo.runtime import load_agent_tool  # provided by kinnoo

# kinnoo provides a helper that wraps the sub-agent as a callable
fetch_data = load_agent_tool("seismic-data-fetcher")

def main(query: str):
    # Calling fetch_data invokes the sub-agent's entrypoint
    # under the hood: subprocess call to the installed agent
    raw_data = fetch_data("get seismic data for California last 30 days")
    
    # ... process raw_data with LangChain ...
    print(result)

if __name__ == "__main__":
    main(sys.argv[1])
```

What `load_agent_tool()` does internally:
1. Finds the installed sub-agent directory (e.g., `~/.kinnoo/agents/seismic-data-fetcher/`)
2. Returns a callable that, when invoked, runs the sub-agent's entrypoint as a subprocess
3. Captures stdout as the return value
4. Handles env var forwarding (only the vars declared in the sub-agent's manifest)
5. Enforces the sub-agent's permissions

#### Mode 2: `invoke_as: subprocess`

The parent agent calls the sub-agent explicitly via CLI. No helper needed — just shell out:

```python
import subprocess
result = subprocess.run(
    ["kinnoo", "run", "geological-model", "analyze california fault lines"],
    capture_output=True, text=True
)
model_output = result.stdout
```

This is the simplest mode — no kinnoo runtime library needed. But it requires kinnoo to be on PATH.

#### Mode 3: `invoke_as: mcp-server`

The sub-agent is started as a long-running MCP server, and the parent agent connects to it as an MCP client:

```python
from kinnoo.runtime import start_agent_server  # provided by kinnoo

# Starts the MCP server sub-agent and returns connection info
server = start_agent_server("seismic-data-fetcher")
# server.port, server.stdio_transport, etc.

# Parent agent connects via MCP protocol
# ... framework-specific MCP client code ...
```

### What needs to be implemented in kinnoo for composition

Here's the concrete implementation breakdown:

**A. Schema changes (in `src/kinnoo/schema.py`):**
- Add `agent_dependencies` as an optional list field in the manifest
- Each entry has: `name` (required), `version` (optional semver range), `invoke_as` (optional, default "tool", enum: tool/subprocess/mcp-server)
- Validate structure, version constraint format, invoke_as values

**B. Dependency resolution (new module: `src/kinnoo/agent_resolver.py`):**
- Given agent_dependencies, resolve each to a specific version from the registry
- Check for circular dependencies (A depends on B depends on A)
- Check for version conflicts (A needs data-fetcher@1.x, B needs data-fetcher@2.x)
- Produce a flat install plan

**C. Install changes (in `src/kinnoo/install_command.py`):**
- After installing the main agent, recursively install agent_dependencies
- Install sub-agents into a well-known location (e.g., `<agent-dir>/.kinnoo-deps/` or `~/.kinnoo/agents/`)
- Skip already-installed sub-agents at compatible versions
- Aggregate permission summaries across all agents in the tree

**D. Runtime helpers (new module: `src/kinnoo/runtime.py`):**
- `load_agent_tool(name)` → returns a callable that subprocess-invokes the installed sub-agent
- `start_agent_server(name)` → starts an MCP server sub-agent and returns connection info
- These are lightweight wrappers, not heavy frameworks

**E. Pack changes:**
- `kinnoo pack` should NOT bundle sub-agent archives (that would create huge nested archives)
- Instead, agent_dependencies are recorded in the manifest = resolved at install time from the registry
- This is the same model as npm: package.json lists dependencies, npm install fetches them

**Estimated implementation: 2-3 features (~8-12 tasks)**

**Important design decision:** Start with `invoke_as: subprocess` only. It's the simplest mode — no runtime library needed, works with any language, and proves the concept. Add `invoke_as: tool` (Python helper) and `invoke_as: mcp-server` as follow-up features.

---

## 7. Real-World Agent Pressure Testing Plan

Yes, there absolutely needs to be a phase of real-world pressure testing. Feature 47 analyzed 246 agent examples statically, but hasn't done full end-to-end lifecycle testing with diverse real agents. Here's a concrete plan:

### Agent Selection (10 representative agents)

Pick agents that stress different parts of the pipeline:

| # | Agent | Framework | Why it stresses kinnoo |
|---|---|---|---|
| 1 | LangChain RAG agent with Chroma vector DB | LangChain | Heavy deps (~200MB), external service dependency (Chroma) |
| 2 | PydanticAI multi-tool agent | PydanticAI | JSON input/output, typed tools, async |
| 3 | OpenAI Agents SDK with handoffs | OpenAI Agents | Agent handoffs, multiple API keys |
| 4 | OpenClaw personal assistant | OpenClaw | Node.js daemon, mutable state, memory dir |
| 5 | MCP server (filesystem or GitHub) | MCP | Long-running server, permission enforcement |
| 6 | Streamlit dashboard agent | Streamlit | UI agent, daemon runtime, unusual entrypoint |
| 7 | Multi-file Python agent with src/ layout | Vanilla Python | Subdirectory entrypoint, package imports |
| 8 | Node.js + TypeScript agent | Node.js/TS | tsx execution, node_modules exclusion |
| 9 | Large agent with ONNX model weight | Any | 500MB+ asset bundling, pack size warnings |
| 10 | Agent with Docker-dependent service | Any | Tests the boundary: what kinnoo CAN'T do |

### Test Protocol for Each Agent

For each agent, run through the full lifecycle:

```
1. kinnoo import <agent-dir>          # Can the analyzer detect everything?
   → Record: which fields were auto-detected, which needed manual input
   → Record: false positives, missed env vars, wrong framework detection

2. kinnoo check <agent-dir>           # Does check pass?
   → Record: any false alarms, missing checks, confusing messages

3. kinnoo run <agent-dir> "<input>"   # Does it actually run?
   → Record: runtime errors, missing deps, env var issues, permission problems

4. kinnoo pack <agent-dir>            # Does it pack cleanly?
   → Record: archive size, any warnings, packing time

5. kinnoo install <archive.kno>       # Does it install cleanly?
   → Record: install time, any dep failures, wheel issues

6. kinnoo run <installed-dir> "<input>"    # Does the installed version run?
   → Record: any differences from step 3

7. kinnoo publish <agent-name>        # Does it publish to the registry?
   → Record: any issues with metadata, upload size

8. kinnoo install <name> --remote     # Can someone else install from registry?
   → Record: download, integrity check, install success

9. kinnoo inspect <name>              # Is the inspect output useful?
   → Record: is the manifest metadata accurate and complete?
```

### Output Artifacts

For each agent, produce:
- A test report (pass/fail for each step, with details on failures)
- A list of kinnoo bugs or improvements needed
- An updated/verified kinnoo.yaml (contributed back to the agent's repo if open source)

### Schedule

This should be 1-2 weeks of focused work. Aim for 2 agents per day. Record findings in `notes/pressure-testing/` with one file per agent.

### When to Do This

**Before Phase 7 (agent composition) and before open-sourcing.** Real-world testing will reveal the rough edges that need smoothing before external developers try kinnoo. Do it as the first part of Phase 6 or as a standalone sprint between Phase 5 and Phase 6.

---

## 8. OpenClaw Deep Support Strategy

You asked: "Should I pursue deeper support for OpenClaw-based agents?"

**Yes, but surgically.** OpenClaw is popular in 2026, but "deeper support" doesn't mean building an OpenClaw gateway inside kinnoo. It means making kinnoo the best way to package and distribute OpenClaw agents.

### What kinnoo already has for OpenClaw:
- `kinnoo init --framework openclaw` scaffold template
- Analyzer detects OpenClaw projects (weighted signal system: openclaw.json, SOUL.md, AGENTS.md, skills/, memory/)
- `runtime.type: daemon` for long-running OpenClaw agents
- `state_dirs` for mutable memory directories
- Node.js runtime support (npm/pnpm)
- OpenClaw-specific schema validation (framework: openclaw → must be nodejs, daemon, etc.)

### What's missing for deeper OpenClaw support:

**1. Skill packaging as first-class artifacts**
OpenClaw agents are primarily composed of skills. Right now, kinnoo packages the whole agent. What if individual skills could be packaged separately?

```yaml
# kinnoo.yaml for a skill (not a full agent)
name: calendar-skill
version: 1.0.0
type: skill                    # new: artifact type
framework: openclaw
skill_path: skills/calendar/
```

This would let developers share individual OpenClaw skills via the registry: `kinnoo install calendar-skill` adds it to an existing agent's skills directory. This is a natural extension of agent composition.

**2. Memory state migration**
OpenClaw agents accumulate state in `memory/`. When upgrading an agent version, users need to preserve their memory state. Kinnoo could provide:
- `kinnoo upgrade earthquake-agent` — upgrades code but preserves `memory/` and `state_dirs`
- Conflict detection if the new version's state schema changed

**3. OpenClaw gateway bridge (deferred — risky scope)**
OpenClaw agents typically run via the OpenClaw gateway, not standalone. Building a gateway bridge inside kinnoo is scope creep. Instead, provide documentation and templates showing how a kinnoo-packaged OpenClaw agent connects to an existing gateway.

### Recommendation:
- Do skill packaging (#1) as part of Phase 7 (it's a natural extension of agent composition)
- Do memory migration (#2) as part of Phase 8 (it's a polish feature)
- Do NOT do gateway bridge (#3) — it's out of scope and drags kinnoo into framework-specific runtime concerns

---

## 9. Verified Publishers, Badges, and Agent Testing

### 9a. Verified Publishers (link GitHub identity)

**Current state:** Users create accounts via the kinnoo registry (email + password). There's no link to their GitHub identity.

**Implementation plan:**

1. **Add `repository` field to kinnoo.yaml** — Optional field where the publisher declares their source repo:
   ```yaml
   repository: https://github.com/jerry/earthquake-predictor
   ```
   Schema change in `src/kinnoo/schema.py`, displayed in `kinnoo inspect`.

2. **GitHub OAuth integration for registry accounts** — Feature 60 already has the identity schema ready for SSO (deferred Google/GitHub login). Implementing GitHub OAuth would let users link their registry account to their GitHub identity:
   - Add GitHub OAuth flow to the server (server/auth/)
   - When a user links GitHub, store their GitHub username in the identity table
   - Display a "Verified" badge on agents where the publisher's GitHub account owns the declared `repository`

3. **Verification logic:**
   - If agent manifest declares `repository: github.com/jerry/earthquake-predictor`
   - AND the publisher's linked GitHub identity is `jerry`
   - AND `jerry` is a collaborator on that repo (verified via GitHub API)
   - → Display "✓ Verified publisher" on the registry listing and in `kinnoo inspect`

**Estimated: 2 features (GitHub OAuth + verification badge logic)**

### 9b. Security Audit Badges

**Current state:** `kinnoo pack` runs a heuristic code sweep and `kinnoo inspect` shows results. But there's no persistent badge in the registry.

**Implementation plan:**

1. **Record scan results at publish time** — When `kinnoo publish` uploads an archive, the server runs (or the CLI provides) the scan results as metadata:
   ```json
   {
     "security_scan": {
       "heuristic_sweep": "clean",     // clean | warnings | flagged
       "dependency_audit": "clean",     // clean | vulnerabilities
       "archive_signed": true,
       "permissions_declared": true,
       "scan_timestamp": "2026-03-26T..."
     }
   }
   ```

2. **Display badges in registry UI and CLI** — The web dashboard shows badges:
   - 🟢 "Signed" — archive has Ed25519 signature
   - 🟢 "Sweep clean" — heuristic sweep found no issues
   - 🟢 "Deps audited" — dependency audit passed
   - 🟡 "Permissions declared" — manifest includes permissions section
   - `kinnoo inspect` and `kinnoo search` also show these badges in CLI output

3. **Future: third-party audits** — Allow registered security auditors to sign off on an agent version, adding an "Audited by X" badge. This is a much later feature.

**Estimated: 1 feature (scan metadata in publish + badge rendering)**

### 9c. Agent Testing Results

**Current state:** `kinnoo pack --preflight` runs preflight checks. But there's no concept of "this agent was tested with these inputs and produced expected outputs."

**Implementation plan:**

1. **Add `tests` section to kinnoo.yaml:**
   ```yaml
   tests:
     - name: basic-query
       input: "Is there earthquake risk in California?"
       expected_output_contains: ["seismic", "risk"]
       timeout_seconds: 30
     - name: empty-input
       input: ""
       expected_exit_code: 0
   ```

2. **`kinnoo test <agent-dir>` command** — Runs each declared test case:
   ```
   $ kinnoo test ./earthquake-predictor
   Running 2 test(s)...
   ✓ basic-query (2.3s) — output contains expected strings
   ✓ empty-input (0.5s) — exit code 0
   2/2 passed
   ```

3. **Record test results at publish time** — `kinnoo publish` optionally runs `kinnoo test` before publishing and attaches results to the version metadata:
   ```
   $ kinnoo publish earthquake-predictor --test
   Running tests before publish...
   ✓ 2/2 tests passed
   Publishing earthquake-predictor@1.3.0...
   ✓ Published with test results: 2/2 passed
   ```

4. **Display test badge in registry** — "✓ 2/2 tests passed" badge on registry listings.

**Design considerations:**
- Tests that call real LLM APIs cost money and have non-deterministic output. The `expected_output_contains` approach (substring matching) is pragmatic.
- Consider a `--mock` mode where tests run with mocked LLM responses for CI (the agent would need to support a test-safe mode, like OpenClaw's `KINNOO_TEST_SAFE_MODE`).
- Test results are per-version, per-platform. "Passed on Python 3.12, macOS arm64" is useful metadata.

**Estimated: 2 features (kinnoo test command + test results in publish metadata)**

---

## 10. Improving Auto-Detection in the Analyzer

### Current state of env var detection:

The analyzer's `_detect_env_vars` uses Python AST parsing to find:
- `os.getenv("VAR_NAME")`
- `os.environ.get("VAR_NAME")`
- `os.environ["VAR_NAME"]`

### What it misses:

1. **`dotenv` / `load_dotenv()` patterns** — Many agents use python-dotenv:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   api_key = os.getenv("OPENAI_API_KEY")  # this IS detected
   ```
   The `os.getenv` call is detected, but if the .env file has vars not referenced in code, they're missed.

2. **Framework-specific config patterns:**
   ```python
   # LangChain: often uses env vars implicitly
   llm = ChatOpenAI(model="gpt-4")  # implicitly needs OPENAI_API_KEY
   
   # PydanticAI: similar
   agent = Agent('openai:gpt-4o-mini')  # implicitly needs OPENAI_API_KEY
   ```

3. **JS/TS env var patterns:**
   ```javascript
   process.env.OPENAI_API_KEY    // not detected (Python AST only)
   ```

4. **Connection strings and URLs** embedded in code that imply service dependencies.

5. **Permissions and network access** — Static analysis can't fully determine what filesystem paths an agent accesses or what network calls it makes at runtime.

### Practical improvements to implement:

**Level 1: Quick wins (extend existing analyzer)**

1. **Scan .env and .env.example files** — If a `.env.example` file exists, parse it for var names:
   ```python
   def _detect_env_vars_from_dotenv(project_dir: Path) -> set[str]:
       for env_file in [".env.example", ".env.template", ".env.sample"]:
           path = project_dir / env_file
           if path.exists():
               for line in path.read_text().splitlines():
                   if "=" in line and not line.strip().startswith("#"):
                       var_name = line.split("=", 1)[0].strip()
                       yield var_name
   ```

2. **Framework-to-env-var mapping** — Maintain a known mapping:
   ```python
   FRAMEWORK_ENV_VARS = {
       "langchain": ["OPENAI_API_KEY", "LANGCHAIN_API_KEY", "LANGCHAIN_TRACING_V2"],
       "openai-agents": ["OPENAI_API_KEY"],
       "pydantic-ai": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"],
       "claude-chat": ["ANTHROPIC_API_KEY"],
       "gemini": ["GOOGLE_API_KEY"],
       "openclaw": ["OPENCLAW_API_KEY"],
   }
   ```
   After detecting the framework, suggest likely env vars with a lower confidence:
   ```
   Detected framework: langchain
   Suggested env vars (from framework defaults, verify manually):
     - OPENAI_API_KEY (common for langchain)
     - LANGCHAIN_API_KEY (optional, for tracing)
   ```

3. **JS/TS env var scanning** — Extend `_detect_env_vars` to also scan `.js`, `.mjs`, `.ts` files with a regex (since AST parsing is Python-only):
   ```python
   JS_ENV_PATTERN = re.compile(r"process\.env\.([A-Z_][A-Z0-9_]*)")
   ```

4. **Scan for well-known API client constructors** — AST-detect calls like:
   ```python
   # If we see `ChatOpenAI(...)` → suggest OPENAI_API_KEY
   # If we see `Anthropic(...)` → suggest ANTHROPIC_API_KEY
   # If we see `genai.GenerativeModel(...)` → suggest GOOGLE_API_KEY
   ```
   This is a heuristic constructor-to-env-var map.

**Level 2: Medium effort (new detection capabilities)**

5. **Permission inference from imports:**
   ```python
   IMPORT_PERMISSION_MAP = {
       "requests": {"network": True},
       "httpx": {"network": True},
       "urllib": {"network": True},
       "aiohttp": {"network": True},
       "subprocess": {"shell": True},
       "os.system": {"shell": True},
       "pathlib": {"filesystem": True},
       "open": {"filesystem": True},
       "sqlite3": {"filesystem": True},
       "selenium": {"browser": True},
       "playwright": {"browser": True},
   }
   ```
   After scanning imports, suggest a `permissions` section:
   ```
   Detected imports suggesting permissions:
     - requests, httpx → network: true
     - subprocess → shell: true
     - pathlib → filesystem: read (verify scope)
   ```

6. **Service detection from connection patterns** — The current `_detect_services` already does this for URLs. Extend it to detect:
   - Database connection strings in config files (not just Python source)
   - Docker Compose service names (parse `docker-compose.yml` if present)
   - Kubernetes service references

**Level 3: Aspirational (not for near-term)**

7. **LLM-assisted manifest inference** — Use a code LLM to read the agent source and generate a kinnoo.yaml. This is the "nuclear option" for auto-detection but introduces LLM API costs and non-determinism. Better as an optional `kinnoo import --ai` flag.

### Recommendation:
Implement Level 1 items (1-4) in Phase 6 as part of the "real-world pressure testing" work — the pressure tests will reveal exactly which detection gaps hurt the most. Level 2 items (5-6) can go in Phase 7. Level 3 is a future consideration.

---

## 11. Open Source Community Strategy

You asked: "Should I invite devs to suggest new CLI commands?"

### Tight core, open extensions

The best open source CLI tools follow a pattern: **tight core maintained by the creator, open extension points for the community.**

**Keep tight control of:**
- The core CLI commands (init, run, pack, install, publish, inspect, check, import, test)
- The manifest schema (kinnoo.yaml format)
- The archive format (.kno structure)
- The registry API contract
- Security primitives (signing, permissions, guard)

These are your API surface. Changing them breaks users. You need to control them.

**Open to community contribution:**
- Framework templates (`kinnoo init --framework <X>`) — This is the easiest contribution path. A community member who uses CrewAI can submit a `--framework crewai` template without touching core code. Templates are isolated, testable, and low-risk.
- Analyzer detectors — New detector functions for framework detection, env var patterns, service detection. These are additive and don't break existing functionality.
- Registry widgets/badges — Community-built badge integrations (e.g., "Works with GPT-4o" badge).
- Documentation — Framework guides, tutorials, blog posts, video walkthroughs.
- Agent packages — The most important community contribution is publishing agents to the registry. The registry IS the community play.

### Concrete open source strategy:

1. **Create a `CONTRIBUTING.md`** that clearly defines:
   - What contributions are welcome (templates, detectors, docs, agents)
   - What requires RFC/discussion first (new CLI commands, schema changes, security changes)
   - How to submit a framework template (step-by-step guide)

2. **Create a `templates/community/` directory** for community-contributed templates, separate from the core `templates.py`.

3. **Use GitHub Discussions for feature requests** — Not issues. Discussion threads for "I want kinnoo to support X" let the community vote and discuss before anyone writes code.

4. **Write 3-5 framework guide docs first** — Before asking for contributions, demonstrate the pattern. Write guides for LangChain, PydanticAI, OpenClaw. Then say "want to add CrewAI? Follow this pattern."

5. **Don't open source until the registry is publicly accessible** — Open sourcing a package manager without packages is like opening an empty store. Wait until there are 10-20 agents in the registry. Even if you publish them yourself, the registry needs content.

---

## 12. Revised Phase 6, 7, 8 Plans

Based on everything discussed above, here are the revised phase plans:

### Phase 6: Pressure Testing, CI Story, and Analyzer Upgrades

**Theme:** "Make what we have bulletproof before adding new capabilities"

**Rationale:** Kinnoo has 60 features but hasn't been pressure-tested with diverse real-world agents. Before adding composition or expanding the ecosystem, validate that the existing lifecycle works reliably end-to-end.

| Feature | Title | Key Deliverables |
|---------|-------|-----------------|
| feature61 | Real-world agent pressure testing (batch 1) | Test 5 agents (LangChain RAG, PydanticAI, OpenAI Agents, OpenClaw daemon, MCP server) through full lifecycle; file bug reports for each failure |
| feature62 | Real-world agent pressure testing (batch 2) | Test 5 more agents (Streamlit, multi-file Python, Node.js/TS, large asset, Docker-dependent); file bug reports |
| feature63 | Pressure test bug fixes and polish | Fix all bugs discovered in feature61-62; improve error messages, edge cases |
| feature64 | Analyzer enhancements — env var and permission detection | .env.example scanning, framework-to-env-var mapping, JS/TS env var regex, import-to-permission inference, constructor-to-env-var mapping |
| feature65 | GitHub Actions reference workflow and CI story | Reference workflow YAML, verify `KINNOO_REGISTRY_TOKEN` env var support, document signing in CI, verify exit codes, consider `kinnoo ci` convenience command |
| feature66 | Landing page and messaging update | Update tagline, sub-line, feature section copy and cards based on revised positioning |
| feature67 | Agent test framework (`kinnoo test`) | `tests` section in kinnoo.yaml, `kinnoo test` command, test result recording |

### Phase 7: Agent Composition and Skill Packaging

**Theme:** "Make agents composable building blocks"

**Rationale:** This is the killer differentiator. Once agents can depend on other agents, kinnoo creates a real ecosystem effect that Git alone cannot provide.

| Feature | Title | Key Deliverables |
|---------|-------|------------------|
| feature68 | Agent dependency schema and resolution | `agent_dependencies` manifest field, version constraint parsing, dependency resolver, circular dependency detection |
| feature69 | Agent dependency installation | `kinnoo install` recursively installs agent dependencies, aggregated permission summary, skip already-installed |
| feature70 | Agent runtime helpers (`invoke_as: subprocess`) | Sub-agent invocation via subprocess mode, env var sandboxing per sub-agent |
| feature71 | Agent runtime helpers (`invoke_as: tool`) | `kinnoo.runtime.load_agent_tool()` Python helper, callable wrapper for sub-agents |
| feature72 | Agent runtime helpers (`invoke_as: mcp-server`) | `kinnoo.runtime.start_agent_server()` for MCP server sub-agents |
| feature73 | OpenClaw skill packaging | `type: skill` manifest artifact, `kinnoo install <skill>` adds to agent's skills directory |
| feature74 | Composition end-to-end validation | Build and test a real composed agent (parent + 2 sub-agents), validate full lifecycle |

### Phase 8: Trust Ecosystem and Open Source Launch

**Theme:** "Build the trust layer that makes strangers comfortable running each other's agents"

**Rationale:** Composition creates the ecosystem; trust makes it safe. This phase adds verified publishers, badges, and test results — then opens the doors.

| Feature | Title | Key Deliverables |
|---------|-------|------------------|
| feature75 | GitHub OAuth and identity linking | GitHub OAuth flow for registry accounts, link GitHub identity to registry publisher |
| feature76 | Verified publisher badges | Verify publisher owns declared repository, display "✓ Verified" badge in registry and CLI |
| feature77 | Security and signing badges in registry | Record scan/sign/audit results at publish time, display badges in web UI and `kinnoo inspect/search` |
| feature78 | Test results in publish metadata | `kinnoo publish --test` runs tests before publish, attach results to version metadata, display test badge |
| feature79 | OpenClaw memory migration and upgrade flow | `kinnoo upgrade` command preserving state_dirs, conflict detection for state schema changes |
| feature80 | Open source preparation | CONTRIBUTING.md, community template system, GitHub Discussions setup, 3-5 framework guide docs |
| feature81 | Public launch | 10-20 seed agents in registry, public access to registry, announcement, open source |

---

## Final Thought: Kinnoo's Real Position

You said: "I still think kinnoo can provide value to a team of developers working on an agent."

You're right. And the key insight is that **kinnoo provides value at different levels to different people:**

| Persona | Value kinnoo provides |
|---------|----------------------|
| **Agent developer (solo)** | Convention (kinnoo.yaml), preflight checks, security sweep, one-command testing |
| **Agent team (2-5 devs)** | CI/CD publishing, versioned registry stamps, verified signatures, simplified onboarding for new team members |
| **Agent consumer (not on the team)** | `kinnoo install && kinnoo run` — two commands, no setup, trust verification before execution |
| **Agent ecosystem (many teams)** | Discovery via registry, composition via agent dependencies, trust via badges and verified publishers |

The tagline and messaging should speak to levels 3 and 4 (that's what differentiates kinnoo from "just use Git"), while the documentation and CI integration serve levels 1 and 2.

The composition play (Phase 7) is what transforms kinnoo from a "nice convenience tool" into something genuinely new. No one else in the AI agent ecosystem does dependency-resolved agent composition today. That's your wedge.
