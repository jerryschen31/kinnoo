I now have deep context from the codebase, the Gemini conversations, and the documented V2 ideas. Here's my TechLead assessment:

---

## Phase 1 MVP Assessment

**What was delivered:** A working end-to-end agent packaging lifecycle — `init → run → pack → install → run`. Six features, 38 tasks, 60 tests. Three LLM framework templates (Gemini, ChatGPT, Claude). ZIP-based `.kno` archives with bundled wheels.

**What works well:**
- The black-box execution model (`python run.py "<input>"`) is exactly right for MVP — framework-agnostic by design
- The manifest schema is clean and extensible (required fields are minimal; optional fields accepted silently)
- Wheel bundling in `.kno` archives solves the reproducibility problem

**Technical debt to address (before or early in V2):**
- **Monolithic CLI:** All command logic (~280 lines) lives in [src/kinnoo/cli.py](src/kinnoo/cli.py). Install is inline rather than in `install_command.py`
- **Archive format inconsistency:** Docs/notes reference tar.gz; code implements zip. Needs canonical decision
- **`--no-deps` wheel building:** Transitive dependencies are NOT included (only direct deps). This can break installs
- **`--force` flag hack:** Parsed from `sys.argv` rather than argparse
- **Missing `--version` flag**
- **Duplicate test function** in [tests/test_pack.py](tests/test_pack.py)

---

## Strategic Assessment: Where to Go from Here

The Gemini conversations surfaced several strategic directions. Here's my critical evaluation as TechLead with the 2026 landscape in mind:

### The Competitive Landscape (Feb 2026)

| Layer | Players | Kinnoo's Position |
|-------|---------|-------------------|
| Agent Frameworks | LangGraph, PydanticAI, CrewAI, Agno, Smolagents | **Agnostic wrapper** — strength, not weakness |
| Agent Protocols | MCP (Anthropic/Linux Foundation), A2A (Google) | **Must support MCP** as pass-through |
| Agent "Hubs" | HuggingFace Agents, Agno Hub, ClawHub | **Direct competitors** — differentiate on packaging standard |
| Walled Gardens | OpenAI GPT Store, Microsoft Copilot Studio, Salesforce Agentforce | **Counter-position:** open, local-first |

### The 5 Risks (from your Gemini discussion) and How V2 Addresses Them

1. **Thin Wrapper Moat** — Solved by being "VLC for Agents": framework-neutral, so no single framework's cloud runner replaces Kinnoo
2. **Security Paradox** — Addressed in V2 via env_vars manifest section + preflight warnings (governance/sandboxing deferred to V3)
3. **Fragmentation Trap** — MCP as the universal tool interface; black-box execution means we don't chase framework internals
4. **Discovery Fallacy** — Registry starts local and curated; avoids "Hello World graveyard"
5. **Big Tech Steamroller** — Local-first privacy story; open standard beats walled garden for developers

### The Key Strategic Insight

From the Gemini conversation you landed on the right answer: **Kinnoo should be the "Host" (infrastructure/environment manager), not the "Client" (MCP/tool integrator).** The pass-through model is correct for V2. The agent framework (PydanticAI, LangGraph, etc.) already has MCP client logic built in. Kinnoo provides: secrets injection, dependency management, venv isolation, and subprocess permissions.

---

## Proposed Phase 2 (V2) Plan

I recommend organizing V2 into **3 tiers** based on strategic value and dependency ordering:

### Tier 1: Foundation (fix debt + unlock V2 features)

These are enablers — they make everything else cleaner.

**1. CLI Refactor & Modular Architecture**
- Extract install logic from [cli.py](src/kinnoo/cli.py) into [install_command.py](src/kinnoo/init_command.py) (like `init_command.py` and `pack_command.py` already are)
- Add proper `--version` flag
- Fix `--force` argparse integration
- Add `kinnoo inspect <archive-or-dir>` command (EPICS E4) — reads manifest and displays metadata. Low effort, high utility

**2. Packaging Robustness**
- Fix `pip wheel --no-deps` to include transitive dependencies (`pip wheel` without `--no-deps`)
- Canonical archive format decision (recommend sticking with zip since that's what's implemented; update all docs)
- Implement the V2 fallback for missing wheels (warn, not error; attempt PyPI install on `kinnoo install`)

**3. Manifest Schema V2 Extensions (additive, non-breaking)**
- `description` field (string) — needed for registry/inspect
- `author` field (string) — needed for registry
- `license` field (string) — needed for distribution
- `env_vars` field (list[string]) — declares required environment variables (the "pass-through" secret injection). This is the single most important V2 manifest addition
- `runtime.type: mcp-server` support — enables long-running agent processes

### Tier 2: Core V2 Features (the value propositions)

**4. Environment Variable / Secret Management (`env_vars`)**
- When running an agent, if `kinnoo.yaml` declares `env_vars`, the runtime:
  - Checks if each var is set in the current environment
  - If missing, checks for `.env` file in agent directory
  - If still missing, prompts the user interactively
  - Injects all vars into the subprocess environment
- This is the "pass-through" MCP strategy in action — developer's agent code handles MCP connections; Kinnoo ensures the tokens are available

**5. `runtime.type: mcp-server` Support**
- New execution mode: instead of one-shot `python run.py "<input>"`, the runtime launches `python run.py` as a long-running process
- `kinnoo run` keeps the process alive, pipes stdin/stdout
- Enables packaging MCP servers themselves as `.kno` archives (huge ecosystem play — anyone can `kinnoo install` an MCP server)

**6. `kinnoo inspect` Command**
- Reads manifest from a `.kno` archive or agent directory
- Displays: name, version, author, description, dependencies, env_vars, runtime type
- Foundation for registry browsing

**7. Local Registry (`kinnoo publish` + `kinnoo install <name>`)**
- `kinnoo publish` copies `.kno` archive to `~/.kinnoo/registry/<name>/<version>/`
- `kinnoo install <name>` resolves from local registry (no network needed)
- `kinnoo list` shows all locally published agents
- This is EPICS E7 + E9. Keep it dead simple — a local directory with version folders

**8. Interactive Mode Flag**
- `kinnoo run <dir> --interactive` — starts agent in REPL mode
- Instead of passing a single input via CLI arg, pipes stdin to the agent process
- Enables conversational agents (the line between a "tool" and an "agent")
- Manifest field: `capabilities.interactive: true/false` (metadata only, does not change behavior unless flag is used)

### Tier 3: Differentiation (what makes Kinnoo special)

**9. Preflight Checks**
- `kinnoo run <dir> --preflight` (or automatic before first run)
- Checks: Python version matches manifest, declared env_vars are set, entrypoint file exists, declared binary tools (npx, etc.) are available
- This is a huge UX win — instead of cryptic runtime errors, users get actionable guidance

**10. Additional Framework Templates**
- `kinnoo init --framework=pydantic-ai` — PydanticAI boilerplate with tool examples
- `kinnoo init --framework=langgraph` — LangGraph stateful agent template
- `kinnoo init --framework=agno` — Agno agent template
- Each template demonstrates a real tool-calling pattern, not just "Hello World"

**11. `kinnoo run` from Archive Directly**
- `kinnoo run my-agent.kno "input"` — extract to temp dir, install, run in one step
- Completing EPICS E6. Maximum developer convenience

---

### What V2 Deliberately Does NOT Include (Deferred to V3+)

| Deferred Item | Why |
|---|---|
| Remote registry (HTTP) | Need proven local registry first (EPICS E10/E11) |
| Docker/container generation | Venv isolation is sufficient for now |
| Security sandboxing (filesystem/network jailing) | Complex; pass-through model means agent controls MCP, not Kinnoo |
| Agent composition / multi-agent | Too early; single-agent packaging not yet proven at scale |
| Model compatibility spec (`intelligence` section) | Useful but not blocking adoption |
| Evaluation/testing harness | Defer until registry has real agents to test |
| Tool permission system (MCP proxy/interceptor) | Level 3 strategy — needs V3 engineering |
| Paid features / cloud compute | Focus on open-source adoption first |

---

### V2 Feature Dependency Graph

```
Tier 1 (Foundation)
  ├── [1] CLI Refactor ──────────────────────────┐
  ├── [2] Packaging Robustness                   │
  └── [3] Manifest Schema V2 ───────────────┐    │
                                             │    │
Tier 2 (Core)                                │    │
  ├── [4] Env Var Management ←───────────────┤    │
  ├── [5] MCP Server Runtime ←───────────────┤    │
  ├── [6] kinnoo inspect ←──────────────────────┘
  ├── [7] Local Registry ←── [6]             │
  └── [8] Interactive Mode ←─────────────────┘
                                             
Tier 3 (Differentiation)                     
  ├── [9] Preflight Checks ←── [4]
  ├── [10] Framework Templates
  └── [11] Run from Archive ←── [7]
```

---

### Estimated Effort

| Item | Tasks | Tests | Effort |
|------|-------|-------|--------|
| [1] CLI Refactor | 3-4 | 3-4 | Small |
| [2] Packaging Robustness | 2-3 | 3-4 | Small |
| [3] Manifest Schema V2 | 2-3 | 4-5 | Small |
| [4] Env Var Management | 3-4 | 5-6 | Medium |
| [5] MCP Server Runtime | 3-4 | 4-5 | Medium |
| [6] kinnoo inspect | 2-3 | 3-4 | Small |
| [7] Local Registry | 4-5 | 5-6 | Medium |
| [8] Interactive Mode | 2-3 | 3-4 | Small |
| [9] Preflight Checks | 3-4 | 4-5 | Medium |
| [10] Framework Templates | 3-4 | 6-8 | Medium |
| [11] Run from Archive | 2-3 | 3-4 | Small |

**Total: ~30-40 tasks, ~45-55 tests**

---

### The V2 Tagline (Evolution of MVP)

> **V1:** "Package any agent. Run it anywhere."
> **V2:** "Package any agent. Share it. Run it — with its tools, keys, and connections ready."

---

### Key Concepts You Should Understand for AI Engineering Interviews

Several concepts surfacing in V2 are directly relevant to AI engineering interviews:

1. **MCP (Model Context Protocol):** The 2026 industry standard for agent-to-tool communication. Three-layer architecture: Host (Kinnoo) → Client (PydanticAI) → Server (GitHub MCP). Understand stdio vs SSE transport, tool discovery, and why it solves the N×M integration problem.

2. **Agent Runtime vs. Agent Framework:** A runtime (Kinnoo) provides infrastructure — venv, secrets, process management. A framework (PydanticAI, LangGraph) provides logic — prompts, tool calling, state machines. These are different layers. Docker was the runtime; Rails was the framework.

3. **Pass-through vs. Proxy Architecture:** Pass-through = Kinnoo sets up environment, agent handles connections. Proxy = Kinnoo intercepts and mediates all tool calls. Pass-through is lower effort and more universal; Proxy enables security governance. Real systems often start pass-through and evolve to proxy.

4. **Dependency Isolation (venv + wheels):** Why "it works on my machine" fails for agents — implicit deps on Python versions, system libraries, API key assumptions. Wheel bundling solves offline reproducibility.

---

Would you like me to refine any section of this plan, or shall I break a specific tier into concrete FEATURES.txt / TASKS.txt / TESTS.txt entries for SWE agent handoff?
