# Phase 6+ Planning (Revised): Follow-Up Analysis

_Date: March 27, 2026_

This document captures follow-up analysis on the Phase 6-8 plan, informed by deep research into ClawHub, OpenClaw's architecture, open-source licensing strategies, and the revised pressure-testing scope of 20 agents.

---

## Table of Contents

1. [ClawHub Assessment and Competitive Analysis](#1-clawhub-assessment-and-competitive-analysis)
2. [OpenClaw Memory and State — How It Actually Works](#2-openclaw-memory-and-state)
3. [OpenClaw Skill Bundles in Kinnoo — The `kinnoo attach` + `kinnoo run` Workflow](#3-openclaw-skill-bundles-in-kinnoo)
4. [Am I Competing with OpenClaw Itself?](#4-am-i-competing-with-openclaw-itself)
5. [20-Agent Pressure Test Plan](#5-20-agent-pressure-test-plan)
6. [Open Source Strategy: What to Make Public](#6-open-source-strategy)
7. [Test/Eval Framework Timing](#7-test-eval-framework-timing)
8. [Revised Phase 6+ Plan](#8-revised-phase-6-plan)

---

## 1. ClawHub Assessment and Competitive Analysis

### What ClawHub Is

ClawHub (clawhub.ai) is the public skill registry for OpenClaw. After deep analysis:

**Scale:** 38,545 skills, 7,000 GitHub stars, 82 contributors, 1,100 forks.

**Tech stack:** TanStack Start (React + Vite/Nitro) frontend, Convex (serverless DB + file storage + HTTP actions) backend, Convex Auth with GitHub OAuth, OpenAI embeddings (`text-embedding-3-small`) for vector search, deployed on Vercel.

**Security:** VirusTotal partnership (announced February 2026). Every published skill is:
1. Deterministically packaged into a ZIP
2. SHA-256 hashed
3. Checked against VirusTotal's database
4. Uploaded for fresh scanning if not found
5. Analyzed by VirusTotal's Code Insight (Gemini-powered LLM analysis) that reads the SKILL.md and all referenced scripts/resources
6. Auto-approved if "benign," auto-warned if "suspicious," instantly blocked if "malicious"
7. Re-scanned daily

They also have an OpenClaw-internal scan that produces its own confidence assessment (separate from VirusTotal). Example: the `gog` skill (created by the OpenClaw creator himself, Peter Steinberger) was flagged "Suspicious MEDIUM CONFIDENCE" by OpenClaw's own scanner due to OAuth credential requirements — a false positive on the creator's own skill.

**CLI:** Two interfaces:
- `openclaw skills install/search/update` — native OpenClaw commands
- `clawhub login/publish/sync/install/search` — separate ClawHub CLI for registry auth

**Content model:** Skills are directories containing a `SKILL.md` with YAML frontmatter + optional supporting files (scripts, configs, references). Versioned with semver + tags + changelogs. Downloadable as ZIPs.

**Additional registries:** ClawHub also hosts `onlycrabs.ai` (SOUL.md registry — personality/persona files) and a package catalog for native code plugins.

**Moderation:** GitHub account must be 1+ week old to publish. User reporting (max 20 active reports per user). 3+ unique reports auto-hides a skill. Moderators can hide/unhide/delete/ban. Clear acceptable use policy (no malware, bypass tools, fraud, surveillance, impersonation, NSFW, obfuscated execution).

### Assessment: What ClawHub Does Well

1. **Massive scale** — 38K skills in ~2 months is impressive adoption. Shows the OpenClaw community is highly engaged.
2. **VirusTotal integration** — A real partnership with a world-class security vendor. This is enterprise-grade security signaling.
3. **Vector search** — Semantic discovery via embeddings, not just keyword matching.
4. **Open source** — MIT license, fully transparent. Community can audit, contribute, fork.
5. **Low friction publishing** — `clawhub sync --all` scans local skills and publishes. Minimal ceremony.
6. **Clear moderation policy** — Well-written acceptable use policy with specific examples.

### Assessment: What ClawHub Does NOT Do

1. **Skills are NOT standalone agents.** A ClawHub skill is a set of instructions (SKILL.md) that teaches the OpenClaw agent how to use a tool. It's a prompt extension, not a packaged application. The skill doesn't bundle dependencies, doesn't have its own runtime, doesn't declare env vars in a structured manifest, and doesn't run independently. It requires a running OpenClaw gateway.

2. **No multi-framework support.** ClawHub serves ONE platform: OpenClaw. There's no concept of packaging a LangChain agent, a PydanticAI agent, or an MCP server that isn't OpenClaw.

3. **No dependency bundling.** Skills that need a binary (like `gog` needing the `gog` CLI) declare it in metadata, but don't include it. The user manually installs the binary via brew/npm/go. There's no `kinnoo install` equivalent that sets up a venv and installs pip packages.

4. **No archive signing.** Skills are ZIP files with SHA-256 hashes. No Ed25519 signature from the publisher. No cryptographic identity verification — just GitHub OAuth proving you have a GitHub account.

5. **No permissions model.** Skills can request env vars and binaries, but there's no structured permissions declaration ("this skill needs network access, filesystem read, shell execution"). The security scan is post-hoc analysis, not a declared contract.

6. **No agent composition / dependency resolution.** A skill can USE other skills (via the OpenClaw agent's skill loading), but there's no declared dependency graph, no version constraints, no resolution algorithm.

7. **No CI/CD integration story.** No `clawhub ci` command, no reference GitHub Actions workflows, no automated publish-on-merge flow.

8. **No structured test framework.** No concept of "this skill was tested with these inputs and produced these outputs."

9. **No sandbox execution.** The OpenClaw gateway has sandboxing, but ClawHub itself doesn't enforce sandbox execution for skills.

### Question (2): Am I Copying ClawHub?

**Partially, in concept. Not at all in implementation.**

The overlap is:
- Both are registries with versioning, search, and discovery
- Both have security scanning
- Both have CLI tools for publish/install

The differences are fundamental:
| Dimension | ClawHub | Kinnoo |
|-----------|---------|--------|
| **What's packaged** | SKILL.md instruction files (prompt extensions) | Full agents (entrypoint + deps + runtime + config) |
| **Platform scope** | OpenClaw only | LangChain, PydanticAI, OpenAI Agents, MCP, OpenClaw, vanilla Python/Node.js |
| **Runtime model** | Requires running OpenClaw gateway | Self-contained: `kinnoo run` handles venv, deps, execution |
| **Dependency handling** | "You install the binary yourself" | `kinnoo install` creates venv, installs pip/npm deps, bundles wheels |
| **Security model** | VirusTotal scan + OpenClaw scan (post-hoc) | Heuristic sweep + dep audit + Ed25519 signing + permissions + sandbox + runtime monitoring + kill switch |
| **Archive format** | ZIP of SKILL.md + supporting files | .kno archive (ZIP with manifest, code, wheels, assets, signature) |
| **Identity** | GitHub OAuth | Email + password, JWT, tenant management (GitHub OAuth planned) |
| **Tech stack** | TanStack Start + Convex + Vercel | FastAPI + S3 + Next.js (or Jinja2) |

**You're not copying ClawHub.** You're building something in a different category. ClawHub is a skill/prompt registry for one agent platform. Kinnoo is a full agent packaging and distribution system across all agent frameworks.

### Question (3): Am I Competing with ClawHub?

**Only in the narrow overlap of OpenClaw skill bundles.**

If you implement `type: skill` packaging for OpenClaw skills in kinnoo, then yes, a developer could choose to publish their OpenClaw skill to ClawHub OR to kinnoo. That's competition.

But here's the key insight: **ClawHub is entrenched.** 38K skills, integrated into the OpenClaw CLI natively, backed by the OpenClaw creator, VirusTotal partnership. You will not out-ClawHub ClawHub for OpenClaw skills.

**Don't compete — complement.** The right strategy is:

1. **Don't package raw OpenClaw skills.** ClawHub does this. Let them.
2. **Package OpenClaw agents as full deployable units.** An OpenClaw "agent" is more than a set of skills — it's a configured gateway + skills + memory + SOUL.md + integrations. Kinnoo should package the WHOLE THING, not individual skills.
3. **Position kinnoo as the cross-framework layer.** "ClawHub is for OpenClaw skills. Kinnoo is for any agent, including OpenClaw agents."

### Question (4): How to Go Beyond What ClawHub Offers

Here's where kinnoo can provide value that ClawHub structurally cannot:

**1. Full agent packaging (not just skills)**
ClawHub packages SKILL.md files. Kinnoo packages complete, runnable agents. An OpenClaw agent packaged with kinnoo includes:
- The OpenClaw configuration (`openclaw.json`)
- All custom skills (the entire `skills/` directory)
- The SOUL.md and MEMORY.md
- Declared env vars, services, permissions
- Security sweep results, signature, checksums

A consumer runs `kinnoo install jerry/my-openclaw-agent && kinnoo run my-openclaw-agent` and gets a fully configured OpenClaw instance with all skills pre-installed. ClawHub can't do that.

**2. Cross-framework agent composition**
ClawHub skills can use other ClawHub skills, but only within OpenClaw. Kinnoo's agent composition (Phase 7) would let an OpenClaw agent depend on a PydanticAI agent, which depends on an MCP server. That's cross-framework composition. ClawHub can't even represent this.

**3. Defense-in-depth security stack**
VirusTotal is impressive, but it's a single-layer scan. Kinnoo has:
- Heuristic code sweep (built-in, no external dependency)
- Dependency CVE audit (pip-audit/npm audit)
- Ed25519 archive signing (cryptographic publisher identity)
- Permissions model + sandbox execution (runtime enforcement)
- Runtime behavior monitoring + kill switch
- Input safety guard (6 threat categories)

This is defense-in-depth vs. a single scan. For enterprise/team use, kinnoo's security model is stronger.

**4. True CI/CD integration**
ClawHub has no CI story. Kinnoo can provide `kinnoo pack --preflight && kinnoo publish` in GitHub Actions, with signing, with test results attached to the version.

**5. Structured test results**
ClawHub has no concept of test results. Kinnoo (Phase 8+) can attach "2/2 tests passed on Python 3.12, macOS arm64" to every published version.

**Bottom line:** Don't compete with ClawHub on OpenClaw skills. Compete by being the thing ClawHub can't be: a full agent packaging system that works across all frameworks, with defense-in-depth security, agent composition, and CI integration.

---

## 2. OpenClaw Memory and State

Understanding OpenClaw's memory and state system is essential for kinnoo to handle OpenClaw agents properly.

### How OpenClaw Memory Works

OpenClaw memory is **plain Markdown files** in the agent workspace. There is no database — files are the source of truth. The model only "remembers" what gets written to disk.

**Two memory layers:**

1. **Daily logs:** `memory/YYYY-MM-DD.md` — append-only daily notes. OpenClaw reads today's + yesterday's at session start.

2. **Long-term memory:** `MEMORY.md` at workspace root — curated durable facts, preferences, decisions. Only loaded in the main private session (never in group contexts).

Both live under the workspace directory (`agents.defaults.workspace`, default `~/.openclaw/workspace`).

**Memory tools (agent-facing):**
- `memory_search` — semantic recall over indexed snippets (vector search using OpenAI, Gemini, Voyage, Mistral, Ollama, or local GGUF embeddings)
- `memory_get` — targeted read of a specific Markdown file/line range

**Pre-compaction memory flush:** When a session nears auto-compaction (context window filling up), OpenClaw triggers a silent turn that reminds the model to write durable notes to disk before context is compacted. This ensures important information isn't lost.

### How OpenClaw Session State Works

**Session store:** `~/.openclaw/agents/<agentId>/sessions/sessions.json` (per agent)

**Transcripts:** `~/.openclaw/agents/<agentId>/sessions/<SessionId>.jsonl`

**Session lifecycle:** Sessions reset daily (default 4:00 AM local time) or on idle timeout. `/new` or `/reset` commands start fresh sessions.

**Session maintenance:** Configurable pruning (prune stale entries, cap entry count, rotate session files, enforce disk budgets). Default: warn mode with 30-day prune, 500 max entries, 10MB rotate.

### How Kinnoo Should Handle OpenClaw Memory and State

Given this architecture, kinnoo needs to handle three things:

**1. The `memory/` directory is mutable state that must persist across versions.**
This is already supported via `state_dirs` in kinnoo.yaml:
```yaml
state_dirs:
  - memory/
```
When `kinnoo install` upgrades an agent, `state_dirs` contents are preserved. This is critical — an OpenClaw agent's memory IS its identity. Wiping `memory/` on upgrade would destroy all learned context.

**2. The `sessions/` directory is runtime state, not package content.**
Sessions are created at runtime by the OpenClaw gateway. They should NOT be packed into .kno archives. They should be in a kinnoo-level `.kinnoo-ignore` or excluded by default (similar to how `__pycache__/` is excluded).

**3. MEMORY.md and SOUL.md are part of the agent identity.**
These should be included in the .kno archive as part of the agent's "personality." When someone installs an OpenClaw agent, they get the SOUL.md and baseline MEMORY.md. But the daily `memory/YYYY-MM-DD.md` logs are per-user runtime state.

**Recommendation for kinnoo.yaml OpenClaw template:**
```yaml
name: my-openclaw-agent
framework: openclaw
runtime:
  language: nodejs
  type: daemon
entrypoint: index.mjs
state_dirs:
  - memory/
  - .openclaw/          # gateway runtime state
assets:
  - SOUL.md
  - MEMORY.md           # baseline long-term memory (if provided)
  - skills/             # bundled custom skills
exclude:
  - sessions/           # runtime-only, per-user
  - .openclaw/agents/   # runtime session data
```

---

## 3. OpenClaw Skill Bundles in Kinnoo — The `kinnoo attach` + `kinnoo run` Workflow

You proposed:
1. `kinnoo attach` → sets up OpenClaw and starts the OpenClaw daemon
2. `kinnoo run <skill-bundle>` → runs a particular skill bundle

Let me think through this carefully, because this is a different model from what kinnoo currently does.

### The Problem

An OpenClaw skill bundle (from ClawHub) is NOT a standalone executable. It's a SKILL.md file (+ optional scripts) that teaches an already-running OpenClaw agent how to do something. You can't "run" a skill in isolation — you need the OpenClaw gateway running to interpret and execute it.

This is fundamentally different from a LangChain agent, which has its own entrypoint and runs independently.

### The Design: `kinnoo attach` + `kinnoo run`

**`kinnoo attach`** is a new command concept. It means: "I'm about to work with agents that need an environment/daemon running. Set it up."

For OpenClaw:
```
$ kinnoo attach openclaw

[kinnoo attach] Checking for OpenClaw installation...
[kinnoo attach] OpenClaw v2.x found at /usr/local/bin/openclaw
[kinnoo attach] Starting OpenClaw gateway...
  ✓ Gateway started (PID 12345)
  ✓ Control UI: http://127.0.0.1:18789/
[kinnoo attach] Ready. Use `kinnoo run <skill>` to execute skills.
```

If OpenClaw is not installed:
```
$ kinnoo attach openclaw

[kinnoo attach] OpenClaw not found.
[kinnoo attach] Install with: curl -fsSL https://openclaw.ai/install.sh | bash
[kinnoo attach] Then run: kinnoo attach openclaw
```

**`kinnoo run <skill-bundle>`** when attached to OpenClaw:
```
$ kinnoo run weather "What's the weather in San Francisco?"

[kinnoo run] Running skill 'weather' via OpenClaw gateway...
[kinnoo run] Invoking: openclaw run --skill weather "What's the weather in San Francisco?"
San Francisco: ☀️ +18°C 55% ↗8km/h
```

Under the hood, `kinnoo run` delegates to the OpenClaw gateway for skill execution.

### Important Design Decision: Don't Compete with `openclaw skills install`

The OpenClaw CLI already has `openclaw skills install <slug>`. If kinnoo tries to replicate this, you're fighting ClawHub on their home turf.

Instead, kinnoo's value for OpenClaw skills should be:
1. **Security wrapping** — `kinnoo inspect <skill>` shows kinnoo's security analysis (permissions, code sweep, signing) on top of whatever ClawHub/VirusTotal already provides
2. **Cross-framework discovery** — a PydanticAI developer can `kinnoo search calendar` and find both a PydanticAI calendar agent AND an OpenClaw calendar skill
3. **Bundled agents** — `kinnoo pack` can package an OpenClaw agent WITH all its skills pre-installed, creating a deployable unit

### Alternative Approach: Bridge, Don't Replace

Rather than `kinnoo attach`, consider a simpler integration:

```yaml
# kinnoo.yaml for an OpenClaw agent
name: my-assistant
framework: openclaw
runtime:
  language: nodejs
  type: daemon
  requires: openclaw    # kinnoo checks that OpenClaw is installed
entrypoint: index.mjs
skills:                 # NEW: declare which ClawHub skills this agent uses
  - weather
  - gog
  - github
  - ontology
state_dirs:
  - memory/
```

Then `kinnoo install my-assistant`:
1. Installs the agent code
2. Checks that OpenClaw is installed (or prompts to install)
3. Installs the declared ClawHub skills via `openclaw skills install`
4. Sets up the workspace

And `kinnoo run my-assistant` starts the OpenClaw gateway with this agent's configuration.

This approach treats OpenClaw skills as declared dependencies, similar to how `agent_dependencies` works in the composition design. Kinnoo doesn't need to replicate ClawHub — it just orchestrates.

**Recommendation:** Start with the "bridge" approach. Kinnoo declares which ClawHub skills are needed and delegates installation to the OpenClaw CLI. Don't build `kinnoo attach` yet — it's a large surface area for one framework. If pressure testing reveals that the bridge approach is insufficient, then consider `kinnoo attach`.

---

## 4. Am I Competing with OpenClaw Itself?

**No. OpenClaw and kinnoo are different layers.**

| | OpenClaw | Kinnoo |
|---|---|---|
| **What it is** | A runtime/gateway for AI agents (the "operating system") | A packaging/distribution tool for AI agents (the "package manager") |
| **What it does** | Runs an agent 24/7, connects to chat apps, manages sessions, memory, skills | Packages agents for distribution, manages installation, enforces trust |
| **Analogy** | The web browser that runs web apps | The app store that distributes web apps |
| **Competition** | Competes with other agent runtimes (ChatGPT, custom bots) | Competes with "just clone the repo" and ClawHub (for OpenClaw skills only) |

Kinnoo doesn't run the agent — it packages and distributes it. OpenClaw doesn't package agents for distribution — it runs them.

**The risk of perceived competition:**
If kinnoo tries to replicate ClawHub's skill registry for OpenClaw skills, the OpenClaw community might see kinnoo as a competitor/fragmenter. This would be counterproductive.

**The strategy to avoid this:**
1. **Position kinnoo as complementary.** "Kinnoo packages your OpenClaw agent so others can install it. ClawHub distributes individual skills."
2. **Don't replicate ClawHub's skill registry.** Use the bridge approach: declare ClawHub skill dependencies in kinnoo.yaml, delegate installation to `openclaw skills install`.
3. **Focus on what ClawHub can't do.** Full agent packaging (gateway + skills + config + memory baseline), cross-framework discovery, signed deployable units, CI/CD integration.
4. **Consider contributing upstream.** If kinnoo's security scanning finds something VirusTotal misses, that's a contribution to the OpenClaw ecosystem, not competition.

---

## 5. 20-Agent Pressure Test Plan

### Agent Selection

Divided into 5 categories to cover different frameworks, runtimes, modalities, and edge cases:

#### Category 1: Python One-Shot Agents (6)

| # | Agent Description | Framework | Key Stress Points |
|---|---|---|---|
| 1 | RAG agent with Chroma vector DB | LangChain | Heavy transitive deps (~200MB), vector DB service, embedding model API key |
| 2 | Structured output agent with typed responses | PydanticAI | JSON output type, typed tool definitions, async execution |
| 3 | Tool-calling agent with function definitions | OpenAI Agents SDK | Multiple API keys possible, function tool schema, handoff patterns |
| 4 | Multi-step reasoning workflow (plan-and-execute) | LangGraph | Graph-based execution, intermediate state, complex dependency chain |
| 5 | Simple CLI chatbot (minimal deps) | Vanilla Python (openai + requests) | Minimal framework, tests baseline kinnoo functionality without framework complexity |
| 6 | Multi-tool research agent | CrewAI or AutoGen | Tests a framework kinnoo doesn't have a template for — how well does `kinnoo import` handle the unknown? |

#### Category 2: Python Daemon / Server Agents (3)

| # | Agent Description | Framework | Key Stress Points |
|---|---|---|---|
| 7 | Filesystem MCP server | MCP (Python) | Daemon runtime, MCP protocol, permission enforcement for filesystem access |
| 8 | Streamlit agent dashboard | Streamlit | Web UI agent, unusual entrypoint (`streamlit run`), port binding, assets |
| 9 | FastAPI agent endpoint with WebSocket | FastAPI | HTTP server, WebSocket support, health check endpoint, multiple routes |

#### Category 3: Node.js / TypeScript Agents (3)

| # | Agent Description | Framework | Key Stress Points |
|---|---|---|---|
| 10 | CLI chatbot with OpenAI SDK | Node.js (vanilla) | node_modules size, npm install, package.json parsing |
| 11 | TypeScript MCP server | MCP (TypeScript) | tsx execution, compile step, type declarations, daemon mode |
| 12 | Express.js agent API | Node.js + Express | npm deps, daemon runtime, port binding, middleware stack |

#### Category 4: Edge Cases and Stress Tests (3)

| # | Agent Description | Framework | Key Stress Points |
|---|---|---|---|
| 13 | Multi-file agent with src/ layout and package imports | Python | Subdirectory entrypoint, relative imports, `src/` layout convention |
| 14 | Agent with 10+ env vars and 3 service dependencies | Any | Tests env var detection exhaustively, service declaration, `.env.example` parsing |
| 15 | Docker-dependent agent (requires Redis + Postgres) | Any | Tests the boundary of what kinnoo CAN'T do — documents limitations |

#### Category 5: OpenClaw Skill Bundles (5)

For these, the workflow is NOT `kinnoo pack/install/run` in the traditional sense. Instead, we're testing kinnoo's ability to understand, inspect, and package OpenClaw skill bundles.

| # | Skill Bundle | Source (ClawHub) | Key Stress Points |
|---|---|---|---|
| 16 | Weather (simple, SKILL.md only) | steipete/weather | Zero deps, zero API keys, SKILL.md only — simplest possible skill |
| 17 | Ontology (knowledge graph, has Python scripts) | oswalpalash/ontology | SKILL.md + scripts + references, state persistence in `memory/ontology/`, Python execution |
| 18 | GitHub (instruction-only, requires `gh` CLI) | steipete/github | Binary dependency (`gh`), no supporting files — just SKILL.md instructions |
| 19 | Gog (Gmail/Calendar, needs OAuth + CLI binary) | steipete/gog | OAuth credential requirements, external CLI binary install, flagged "suspicious" by scanner (false positive) |
| 20 | Browser automation (headless browser binary) | matrixy/agent-browser-clawdbot | Large binary dep, system-level requirements, cross-platform install |

### Test Protocol for Each Agent

For agents 1-15 (full agents), use the 9-step lifecycle from the original plan:
```
1. kinnoo import <agent-dir>     → record auto-detection accuracy
2. kinnoo check <agent-dir>      → record false alarms, missing checks
3. kinnoo run <agent-dir> "input" → record runtime success/failure
4. kinnoo pack <agent-dir>       → record archive size, warnings
5. kinnoo install <archive.kno>  → record install time, dep failures
6. kinnoo run <installed> "input" → record post-install behavior
7. kinnoo publish <name>         → record upload success
8. kinnoo install <name> --remote → record remote install success
9. kinnoo inspect <name>         → record metadata accuracy
```

For agents 16-20 (OpenClaw skill bundles), adapted protocol:
```
1. Download skill from ClawHub     → verify download and extraction
2. kinnoo import <skill-dir>       → can the analyzer detect the skill format?
3. kinnoo inspect <skill-dir>      → is the manifest metadata useful?
4. kinnoo check <skill-dir>        → does the security sweep work on SKILL.md + scripts?
5. Manual install into OpenClaw     → does `openclaw skills install` work?
6. Manual test via OpenClaw gateway → does the skill work when invoked?
7. Document: what kinnoo SHOULD do  → identify gaps in kinnoo's OpenClaw support
```

### Finding and Downloading Test Agents

For agents 1-15, source from:
- **GitHub:** Search for well-starred repos with clear README and requirements.txt/package.json
- **Official framework examples:** LangChain docs examples, PydanticAI docs examples, OpenAI Agents SDK examples
- **Personal creation:** Build minimal but realistic agents that stress specific kinnoo features

For agents 16-20, download directly from ClawHub:
```
# Download skill ZIPs from ClawHub
mkdir -p scratch/example-scratch-3/agents/openclaw-skills
cd scratch/example-scratch-3/agents/openclaw-skills

# Each can be downloaded via ClawHub API
clawhub install weather
clawhub install ontology
clawhub install github
clawhub install gog
clawhub install agent-browser-clawdbot
```

Or download the ZIPs directly from the ClawHub download API.

### Output Artifacts

For each agent, produce a report file in `notes/pressure-testing/`:
```
notes/pressure-testing/
  agent-01-langchain-rag.md
  agent-02-pydanticai-structured.md
  ...
  agent-20-openclaw-browser.md
  summary.md                    → aggregate findings, kinnoo bugs, improvements needed
```

Each report includes:
- Agent description and source
- Step-by-step results (pass/fail with details)
- Kinnoo bugs discovered
- Suggested kinnoo improvements
- Updated/corrected kinnoo.yaml (if applicable)

### Schedule

20 agents at ~2 per day = 10 working days for the full pressure test. Recommend batching:
- Days 1-3: Python one-shot agents (agents 1-6)
- Days 4-5: Python daemon/server agents (agents 7-9)
- Days 6-7: Node.js/TypeScript agents (agents 10-12)
- Days 8-9: Edge cases (agents 13-15)
- Day 10: OpenClaw skill bundles (agents 16-20) — faster since they're smaller artifacts

---

## 6. Open Source Strategy: What to Make Public

### The Advice You Received Is Correct

You were told not to make the entire codebase public. This is sound advice, and it follows the pattern of the most successful open-source-adjacent developer tools.

### The Pattern: Open Core / Open CLI

Here's how the most successful projects in a similar category handle this:

| Project | What's Open | What's Closed |
|---------|------------|---------------|
| **npm** | npm CLI (open source, MIT) | npmjs.com registry (proprietary service) |
| **Cargo/crates.io** | Cargo CLI (open source), crates.io source (open) | crates.io hosting/infra (Rust Foundation operated) |
| **Docker** | Docker Engine + CLI (Apache 2.0) | Docker Hub (proprietary service), Docker Desktop (proprietary) |
| **GitLab** | GitLab CE (MIT) | GitLab EE (proprietary premium features) |
| **Supabase** | Client libraries, Postgres extensions (Apache 2.0) | Supabase Cloud (proprietary hosting + dashboard) |
| **Sentry** | Sentry SDK + server (BSL → open) | Sentry SaaS (hosted service) |
| **Terraform/OpenTofu** | Terraform CLI (BSL/fork: MPL-2.0) | Terraform Cloud (proprietary) |

The common pattern: **the CLI/client is open, the server/registry/hosted service is proprietary or separately licensed.**

### Recommendation for Kinnoo

**Open source (public repo `kinnoo`):**
- `src/kinnoo/` — the entire CLI tool
- `tests/` — all tests
- `pyproject.toml`, `requirements.txt` — build config
- `README.md`, `LICENSE` (Apache 2.0 or MIT recommended)
- `docs/` — documentation, schema reference, framework guides

**Keep private (private repo or not published):**
- `server/` — the FastAPI registry server
- `web/` — the Next.js web frontend
- Deployment configs, infrastructure
- `notes/`, `scratch/` — internal development notes
- Registration/auth system implementation details

### Why This Split Works

1. **The CLI is the developer interface.** Making it open source lets developers trust it, audit it, contribute to it. An agent developer needs to trust `kinnoo pack` and `kinnoo install` — open source gives that trust.

2. **The registry is your moat.** The server + web frontend is what makes kinnoo a platform. Keeping it proprietary lets you operate it as a service, monetize it later, and prevent competitors from running a clone.

3. **Security by transparency.** The scanning, signing, and permission enforcement logic in the CLI is visible to everyone. This builds trust. The server-side auth, storage, and moderation logic stays private.

4. **Community contributions flow naturally.** Framework templates, analyzer detectors, documentation — these are contributions to the CLI, which is open. Community members don't need to touch the server.

### Is It a Significant Refactor?

**No.** Your codebase is already naturally separated:

```
src/kinnoo/         → CLI (open source this)
server/             → Registry server (keep private)
web/                → Web frontend (keep private)
tests/              → Tests for CLI (open source this)
```

The CLI communicates with the server via HTTP API. They're already loosely coupled. The steps would be:

1. **Create a public GitHub repo** called `kinnoo` (or `kinnoo-cli`).
2. **Copy the CLI code** (src/kinnoo/, tests/, pyproject.toml, requirements.txt, README.md, docs/) to the public repo.
3. **Add a LICENSE** file (Apache 2.0 recommended — it includes a patent grant, which is important for developer tools).
4. **Keep the current repo private** with everything (or rename it to `kinnoo-platform`).
5. **Set up CI** on the public repo to run tests independently.
6. **Publish to PyPI** from the public repo: `pip install kinnoo`.

Alternatively, you can use a **monorepo with a `.gitignore` approach** — but that's messier. The cleanest approach is two repos: `kinnoo` (public, CLI) and `kinnoo-platform` (private, server + web + deploy).

### Timing

Don't open source until:
1. The pressure testing (Phase 6) is complete — don't expose rough edges
2. There are 10-20 agents in the registry — don't open an empty store
3. The README and CONTRIBUTING.md are written — first impressions matter
4. The CLI is stable (no breaking changes in the near-term plan)

This aligns with Phase 8 (feature80/81) in the revised plan.

---

## 7. Test/Eval Framework Timing

### Your Instinct Is Right: Defer to Post-Launch

The `kinnoo test` command and eval framework (from Section 9 of phase6-planning.md) should come **after** the public launch, for these reasons:

1. **Eval design is hard and evolving.** The AI eval landscape is changing rapidly (EvalGen, Braintrust, Langfuse, etc.). Building a test framework now risks building the wrong thing. Wait until you have real users who can tell you what they need.

2. **Non-deterministic outputs are the core challenge.** Agent tests that call real LLM APIs produce different outputs every time. Substring matching (`expected_output_contains`) is a start, but it's fragile. The community needs to converge on agent testing patterns before you codify them.

3. **Test results become stale.** A test that passed on GPT-4o in March 2026 may fail on GPT-4o in April 2026 due to model updates. The test badge needs to convey what it means — and that requires careful UX design.

4. **Launch pressure > feature completeness.** Getting kinnoo in front of real users is more valuable than building a test framework that no one has asked for yet.

### When to Build It

**Phase 9 or post-launch sprint.** After kinnoo is public and you have:
- Real users publishing agents
- Feedback on what "trust signals" they want to see
- A clearer picture of the agent eval landscape

### What to Build When You Do

When the time comes, the design from phase6-planning.md Section 9c is solid:
- `tests` section in kinnoo.yaml
- `kinnoo test <agent-dir>` command
- Test results attached to published versions
- Test badge in registry

But add these refinements:
- **`--mock` mode** for CI (mocked LLM responses, deterministic)
- **Platform-specific results** ("passed on Python 3.12, macOS arm64")
- **Cost tracking** ("running these tests costs ~$0.05 in API calls")
- **Test result expiry** ("tested 7 days ago" vs "tested 90 days ago")

---

## 8. Revised Phase 6+ Plan

Based on all of the above, here's the revised plan:

### Phase 6: Pressure Testing and Battle-Hardening

**Theme:** "Test 20 real agents, fix everything that breaks, ship what we have"

**Rationale:** Before adding new features, validate that the existing 60-feature pipeline works reliably with diverse real-world agents. This phase is primarily testing and bug-fixing, with targeted improvements to the analyzer.

| Feature | Title | Key Deliverables |
|---------|-------|-----------------|
| feature61 | Pressure testing — Python one-shot agents (batch 1) | Test agents 1-6 (LangChain RAG, PydanticAI, OpenAI Agents, LangGraph, vanilla Python, CrewAI/AutoGen) through full lifecycle; file report per agent |
| feature62 | Pressure testing — Python daemon/server + Node.js agents (batch 2) | Test agents 7-12 (MCP server, Streamlit, FastAPI, Node.js chatbot, TS MCP server, Express agent) through full lifecycle; file report per agent |
| feature63 | Pressure testing — edge cases + OpenClaw skills (batch 3) | Test agents 13-20 (multi-file layout, heavy env vars, Docker-dependent, 5 OpenClaw skill bundles); file report per agent |
| feature64 | Pressure test bug fixes and polish | Fix all bugs discovered in features 61-63; improve error messages, handle edge cases discovered |
| feature65 | Analyzer enhancements from pressure test findings | .env.example scanning, framework-to-env-var mapping, JS/TS env var regex, constructor-to-env-var mapping — guided by actual findings from pressure tests |
| feature66 | GitHub Actions reference workflow and CI story | Reference workflow YAML, verify/implement `KINNOO_REGISTRY_TOKEN` env var support, document signing in CI, verify exit codes |
| feature67 | Landing page and messaging update | Update tagline ("Ship any AI agent"), sub-line, feature section copy and cards per revised positioning |

### Phase 7: Agent Composition and Cross-Framework

**Theme:** "Make agents composable building blocks"

**Rationale:** This is kinnoo's killer differentiator vs. ClawHub and "just clone the repo." Once agents can depend on other agents across frameworks, kinnoo creates a real ecosystem effect.

| Feature | Title | Key Deliverables |
|---------|-------|------------------|
| feature68 | Agent dependency schema and resolution | `agent_dependencies` manifest field, version constraint parsing, dependency resolver, circular dependency detection |
| feature69 | Agent dependency installation | `kinnoo install` recursively installs agent dependencies, aggregated permission summary, skip already-installed |
| feature70 | Agent runtime helpers (`invoke_as: subprocess`) | Sub-agent invocation via subprocess mode, env var sandboxing per sub-agent |
| feature71 | Agent runtime helpers (`invoke_as: tool`) | `kinnoo.runtime.load_agent_tool()` Python helper, callable wrapper |
| feature72 | Agent runtime helpers (`invoke_as: mcp-server`) | `kinnoo.runtime.start_agent_server()` for MCP server sub-agents |
| feature73 | OpenClaw agent packaging (full agents, not skills) | Package complete OpenClaw agents (gateway config + skills + SOUL.md + MEMORY.md), ClawHub skill dependencies in kinnoo.yaml, `openclaw skills install` delegation |
| feature74 | Composition end-to-end validation | Build and test a real composed agent (parent + 2 sub-agents, cross-framework), validate full lifecycle |

### Phase 8: Trust Ecosystem and Open Source Launch

**Theme:** "Build the trust layer, then open the doors"

| Feature | Title | Key Deliverables |
|---------|-------|------------------|
| feature75 | GitHub OAuth and identity linking | GitHub OAuth flow for registry accounts, link GitHub identity to registry publisher |
| feature76 | Verified publisher badges | Verify publisher owns declared repository, display "Verified" badge |
| feature77 | Security and signing badges in registry | Record scan/sign/audit results at publish, display badges in web UI and CLI |
| feature78 | CONTRIBUTING.md and community template system | Framework contribution guide, community template directory, GitHub Discussions setup |
| feature79 | Open source preparation | Extract CLI to public repo, add LICENSE (Apache 2.0), README for open source, 3-5 framework guide docs |
| feature80 | Seed registry with 10-20 agents | Package and publish agents from pressure testing + new examples, ensure registry has content before launch |
| feature81 | Public launch | Public access to registry, open source announcement, first external users |

### Post-Launch (Phase 9+)

**Deferred features (revisit after user feedback):**
- `kinnoo test` and eval framework (Section 7 above)
- OpenClaw memory migration / `kinnoo upgrade` (wait for real OpenClaw user feedback)
- `kinnoo attach` for framework-specific runtimes (wait for demand signal)
- Third-party security audit badges
- `kinnoo ci` convenience command

---

## Summary of Key Strategic Decisions

1. **Don't compete with ClawHub on OpenClaw skills.** Package full OpenClaw agents (gateway + skills + config), not individual skills. Use the bridge approach: declare ClawHub skill dependencies in kinnoo.yaml, delegate to `openclaw skills install`.

2. **Open source the CLI, keep the server/web private.** This is the npm/Docker/GitLab model. The CLI builds trust; the registry is your moat. Apache 2.0 license recommended.

3. **Defer test/eval to post-launch.** The landscape is moving fast. Ship first, then build evals based on real user needs.

4. **Phase 6 is 100% pressure testing + battle-hardening.** 20 agents, 5 categories, detailed reports. Fix everything before adding new features.

5. **Agent composition (Phase 7) is the wedge.** Cross-framework agent dependencies are what ClawHub can't do and "just clone the repo" can't do. This is kinnoo's unique value.

6. **Kinnoo and OpenClaw are complementary layers.** OpenClaw = runtime (runs the agent). Kinnoo = packaging (distributes the agent). Position accordingly in messaging and community interactions.
