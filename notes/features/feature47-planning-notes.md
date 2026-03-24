# Feature 47 — Agent Supportability Assessment & Kinnoo Compatibility Roadmap

## Table of Contents
1. [Overview](#1-overview)
2. [Agent Pattern Classification](#2-agent-pattern-classification)
3. [Malformed / Excluded Agents](#3-malformed--excluded-agents)
4. [Per-Agent Analysis](#4-per-agent-analysis)
5. [Roadmaps for Supportable Patterns](#5-roadmaps-for-supportable-patterns)
6. [Task Plan](#6-task-plan)

---

## 1. Overview

114 agents in `example-scratch/agents/` were analyzed. Each agent was classified by:
- **Code pattern**: How the agent is organized (single script, class-only library, notebook, plugin, etc.)
- **Pattern commonality**: How frequently this pattern appears in open-source agent repos across GitHub/HuggingFace
- **Kinnoo supportability**: How much kinnoo code needs to change to support import/install/run

### Key Findings
- **21 agents are malformed** (SDK internals, docs hooks, monorepo fragments — not real agents). Excluded.
- **93 agents are real agents** with identifiable patterns.
- **~45 agents are HIGH supportability** (already work or need minimal changes).
- **~30 agents are MEDIUM supportability** (need specific kinnoo improvements).
- **~18 agents are LOW supportability** (need major features or have heavy external deps).

---

## 2. Agent Pattern Classification

| Pattern | Count | Commonality | Supportability | Example Agents |
|---------|-------|-------------|----------------|----------------|
| Python script + `__main__` guard | ~35 | Very Common | HIGH | pydanticai-weather-agent, openai-agents-hello-world |
| Python multi-file + main.py entrypoint | ~15 | Very Common | HIGH | openai-agents-sdk-customer-service, vanilla-python-octoagent |
| Python class-only / library (no entrypoint) | 7 | Very Common | LOW -> MEDIUM with wrapper | langchain-mrkl-agent-base, openai-agents-basic-tools |
| Jupyter notebook only | 5 | Common | LOW -> MEDIUM with converter | langgraph-customer-support-graph |
| MCP server (Python) | 6 | Common | HIGH | mcp-server-time-server, mcp-servers-minesweeper-example |
| MCP server (TypeScript) | 6 | Common | MEDIUM | mcp-server-memory-server, mcp-servers-tavily-search |
| MCP client (Python) | 8 | Common | MEDIUM-HIGH | mcp-client-stdio-client, basic-client-demo |
| OpenClaw plugin (TS) | 6 | Moderate | HIGH (daemon) | openclaw-ollama-extension-agent |
| Node.js/TS agent (non-OpenClaw) | ~12 | Common | MEDIUM | vanilla-typescript-easy-agent, vanilla-javascript-avr-llm-assistant |
| Python daemon/server (FastAPI, uvicorn) | 3 | Common | HIGH (daemon) | vanilla-python-reze-agent |
| Serverless/Lambda handler | 1 | Common | LOW | pydantic-ai-serverless-agents |
| Hardware/firmware | 1 | Rare | LOW (exclude) | openclaw-zeroclaw |
| Shell-based setup | 2 | Rare | LOW | openclaw-openclaw-agents-kit |

---

## 3. Malformed / Excluded Agents

These 21 agents are **not real agents** — they are SDK internals, documentation scaffolding, monorepo fragments, or otherwise non-functional. They are excluded from supportability analysis.

| Agent | Reason |
|-------|--------|
| pydantic-ai-chess-agent | Only docs/.hooks/ (deploy hooks, not agent code) |
| pydantic-ai-mcp-tool-agent | Only docs/.hooks/ |
| pydantic-ai-streaming-agent | Only docs/.hooks/ |
| langgraph-adaptive-rag-agent | LangGraph CLI libs/ (SDK internals, not agent) |
| langgraph-langgraph-quickstart | LangGraph CLI libs/ (SDK internals) |
| langgraph-plan-and-execute | LangGraph CLI libs/ (SDK internals) |
| langgraph-self-correction-agent | LangGraph CLI libs/ (SDK internals) |
| langgraph-storm-agent | LangGraph CLI libs/ (SDK internals) |
| openai-agents-sdk-guardrails-demo | SDK source code (src/agents/), not an agent |
| openai-agents-sdk-official-python-sdk | SDK source code, not an agent |
| openai-agents-sdk-workflow-lab | Duplicate of SDK source code |
| openclaw-easyclaw-ui | UI toolkit (packages/), not an agent |
| openclaw-openclaw-core | OpenClaw framework source, not an agent |
| mcp-servers-official-mcp-servers | Monorepo root (src/ with many servers) |
| mcp-servers-playwright-mcp | Monorepo (packages/) |
| mcp-servers-context7-docs | Monorepo (packages/) |
| agents-with-mcp-client-code-mcp-for-beginners | Files missing — incomplete download |
| agents-with-mcp-client-code-openai-mcp-client | SDK source, not client agent |
| vanilla-javascript-openai-cookbook-js | Cookbook recipe fragments, not agent |
| vanilla-typescript-vercel-ai-sdk-examples | SDK source packages |
| vanilla-typescript-agentica-framework | Test scaffolding only |

---

## 4. Per-Agent Analysis

### 4.1 LangChain Classic (6 agents)

Ported from feature46-notes.md Section 1.

All 6 agents are single `base.py` class definitions extracted from `langchain_classic/agents/`. None have a `__main__` guard or `main()`. This is **the** most common LangChain pattern — the official LangChain library distributes agents as importable classes, and 90%+ of LangChain tutorials follow this pattern.

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| langchain-mrkl-agent-base | Class-only (ZeroShotAgent) | Very Common | LOW | Needs wrapper: instantiate with tools + LLM |
| langchain-self-ask-search-agent | Class-only (SelfAskWithSearchAgent) | Very Common | LOW | Also needs search tool (SerpAPI) |
| langchain-structured-chat-agent | Class-only | Very Common | LOW | Good wrapper candidate -- standard tool-calling |
| langchain-tool-calling-agent | Class-only | Very Common | LOW | Simplest to wrap -- modern tool-calling API |
| langchain-openai-functions-multi-agent | Class-only (parallel functions) | Common | LOW | Complex parallel orchestration |
| langchain-openai-assistant-agent | Class-only (stateful threads) | Common | LOW | Stateful/async -- needs daemon-like wrapper |

**Roadmap**: See Section 5.1 (Auto-Wrapper Generation)

### 4.2 LangGraph Notebooks (5 agents) — SKIPPED

> **SKIPPED per human review (2025-03-23):** Notebook conversion burden is on the agent developer. These 5 agents are excluded from feature47 scope. task270 deprecated.

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| langgraph-customer-support-graph | .ipynb only | Very Common | LOW | Standard tutorial notebook |
| langgraph-hierarchical-agent-teams | .ipynb only | Very Common | LOW | Multi-agent teams pattern |
| langgraph-react-from-scratch | .ipynb only | Very Common | LOW | Minimal ReAct loop |
| langgraph-tool-calling-graph | .ipynb only | Very Common | LOW | Tool-calling via StateGraph |
| langgraph-web-voyager | .ipynb only | Very Common | LOW | Browser automation agent |

**Roadmap**: ~~See Section 5.2 (Notebook Conversion)~~ SKIPPED — task270 deprecated.

### 4.3 LangGraph with Python Entrypoints (3 agents) — SKIPPED

> **SKIPPED per human review (2025-03-23):** All LangGraph agents (7-14) excluded from feature47 scope, including these 3 agents with Python entrypoints. They could be supported via task271/task272 but were explicitly excluded.

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| langgraph-20-real-world-projects | main.py + StateGraph | Common | MEDIUM | Hardcoded API keys in code! Requires env var substitution |
| langgraph-multi-agent-router | main.py + StateGraph + crewai_tools | Common | MEDIUM | Multi-framework deps (langgraph + crewai) |
| langgraph-deep-agents-harness | examples/nvidia_deep_agent/src/agent.py | Common | MEDIUM | Deep nested entrypoint |

**Roadmap**: These need subdirectory entrypoint detection (Section 5.3) and requirements auto-inference (Section 5.4).

### 4.4 PydanticAI Legacy (6 agents)

Ported from feature46-notes.md Section 3. **Best framework fit for kinnoo.**

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| pydanticai-weather-agent | Single script + run_sync() | Very Common | HIGH | Tool chaining, parameterizable |
| pydanticai-roulette-wheel-agent | Single script + run_sync() | Very Common | HIGH (Excellent) | Minimal deps, simplest pattern |
| pydanticai-bank-support-agent | Single script + deps injection | Very Common | MEDIUM | Needs --json-input for deps |
| pydanticai-flight-booking-agent | Single script + stateful | Common | MEDIUM | Needs --json-input for booking data |
| pydanticai-rag-agent | Single script + vector DB | Common | LOW | Requires external vector DB |
| pydanticai-data-analyst-agent | Single script + data libs | Common | MEDIUM | If data is local, HIGH; if external DB, LOW |

**Roadmap**: weather + roulette already work. bank/flight need JSON input validation (Section 5.7). rag needs service declarations.

### 4.5 PydanticAI from Rebuild (3 real agents out of 9)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| pydantic-ai-official-bank-example | examples/ dir with multiple agents | Common | HIGH | Contains bank_support.py, roulette_wheel.py, etc. with __main__ |
| pydantic-ai-pydantic-ai-agent | Multi-file src/run_agent.py | Common | HIGH | Well-structured with deps pattern |
| pydantic-ai-rag-with-pydantic | examples/ dir with multiple agents | Common | HIGH | Same as official-bank-example (many PydanticAI examples) |
| pydantic-ai-github-agent | examples/ with evals | Common | MEDIUM | Contains agent + eval examples |
| pydantic-ai-pydantic-ai-history | Library module (no entrypoint) | Moderate | LOW | History processor library, not agent |
| pydantic-ai-serverless-agents | Lambda handler | Common | LOW | AWS Lambda handler(event, context) pattern |

### 4.6 OpenAI Agents Legacy (6 agents)

Ported from feature46-notes.md Section 2.

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| openai-agents-hello-world | Script + __main__ + asyncio.run() | Very Common | HIGH | Hardcoded input |
| openai-agents-customer-service | Multi-file + main.py + __main__ | Very Common | HIGH | Well-structured |
| openai-agents-message-filter-handoff | Script + __main__ | Common | HIGH | Handoff patterns internal to SDK |
| openai-agents-research-bot | Multi-file + source/main.py | Common | HIGH | Complex but single entrypoint |
| openai-agents-financial-research-agent | Multi-file + source/main.py | Common | HIGH | Pipeline stages, single entry |
| openai-agents-basic-tools | Library module (tools.py only) | Common | LOW | No __main__, defines tools only |

### 4.7 OpenAI Agents SDK from Rebuild (6 real agents out of 10)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| openai-agents-sdk-agent-search-tools | examples/ with async main | Common | HIGH | Has __main__ and asyncio.run() |
| openai-agents-sdk-customer-service | python-backend/main.py + requirements.txt | Common | HIGH | Full backend with deps |
| openai-agents-sdk-function-tool-demo | examples/customer_service/main.py | Common | HIGH | Standard example pattern |
| openai-agents-sdk-streaming-agent | examples/voice/streamed/main.py | Common | MEDIUM | Voice streaming -- needs audio stack |
| openai-agents-sdk-temporal-demos | Temporal workflows + run_*.py | Moderate | LOW | Requires Temporal server infrastructure |
| openai-agents-sdk-openai-sdk-knowledge | TS (src/index.ts) | Common | MEDIUM | TypeScript knowledge org tool |
| openai-agents-sdk-realtime-agents | TS (src/) | Common | MEDIUM | Real-time voice, TS/Next.js |

### 4.8 OpenClaw Plugins -- Legacy (6 agents)

Ported from feature46-notes.md Section 4. All JS/TS plugins running in the OpenClaw runtime.

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| openclaw-diffs-extension-agent | TS plugin (source/index.ts) | Moderate | HIGH | Standard OpenClaw extension |
| openclaw-ollama-extension-agent | TS plugin (source/index.ts) | Moderate | HIGH | Needs Ollama service |
| openclaw-llm-task-extension-agent | TS plugin (source/index.ts) | Moderate | HIGH | Standard extension |
| openclaw-lobster-extension-agent | TS plugin (source/index.ts) | Moderate | MEDIUM | External Lobster service |
| openclaw-open-prose-extension-agent | TS plugin (source/index.ts) | Moderate | HIGH | Skills directory pattern |
| openclaw-voice-call-extension-agent | TS plugin (source/index.ts) | Moderate | LOW | Heavy telephony deps (Twilio) |

### 4.9 OpenClaw from Rebuild (4 real agents out of 8)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| openclaw-build-your-own | Python CLI (11-multi-agent-routing/src/mybot/cli/main.py) | Common | MEDIUM | Tutorial multi-agent, deeply nested entrypoint |
| openclaw-nanobot-assistant | TS bridge (bridge/src/index.ts) | Moderate | MEDIUM | WhatsApp bridge agent |
| openclaw-openclaw-agents-kit | Shell-based (setup.sh) | Rare | LOW | Multi-agent setup script, not standard pattern |
| openclaw-openclaw-termux | Node.js (lib/index.js) | Rare | LOW | Android/Termux-specific platform |
| openclaw-selfclaw-identity | TS server (server/index.ts) | Rare | LOW | Identity/governance server |
| openclaw-zeroclaw | Python firmware (firmware/pico/main.py) | Rare | LOW | Pico microcontroller firmware |

### 4.10 MCP Clients -- Legacy (6 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| mcp-client-stdio-client | Python script, MCP SDK | Common | MEDIUM | Needs MCP server to connect to |
| mcp-client-completion-client | Python script + __main__ | Common | HIGH | Has proper entrypoint |
| mcp-client-streamable-basic-client | Python script + __main__ | Common | HIGH | Has proper entrypoint |
| mcp-client-pagination-client | Python script + __main__ | Common | HIGH | Has proper entrypoint |
| mcp-client-oauth-client | Python script, MCP SDK | Common | MEDIUM | Needs OAuth setup |
| mcp-client-url-elicitation-client | Python script, MCP SDK | Common | MEDIUM | URL elicitation pattern |

### 4.11 MCP Clients from Rebuild (4 real agents out of 9)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| agents-with-mcp-client-code-basic-client-demo | Python client + __main__ | Common | HIGH | Cleanest MCP client example |
| agents-with-mcp-client-code-simple-scraping-agent | Python main.py + pyproject.toml | Common | HIGH | Well-structured agent |
| agents-with-mcp-client-code-enrichmcp-orm | Python + LangChain + MCP | Common | MEDIUM | Multi-framework |
| agents-with-mcp-client-code-mcp-agent-loop | Python multi-file agent_loop/ | Common | MEDIUM | Complex agent loop |
| agents-with-mcp-client-code-langchainjs-burger | TS (packages/) | Common | MEDIUM | TypeScript MCP client |
| agents-with-mcp-client-code-mcp-browser-agent | TS (src/index.ts) | Common | MEDIUM | Browser automation |
| agents-with-mcp-client-code-opencode | TS (packages/) | Common | MEDIUM | Editor integration |

### 4.12 MCP Servers -- Legacy (6 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| mcp-server-fetch-server | Python MCP server | Very Common | HIGH | runtime.type: mcp-server |
| mcp-server-git-server | Python MCP server | Very Common | HIGH | runtime.type: mcp-server |
| mcp-server-time-server | Python MCP server + __main__ | Very Common | HIGH | Has proper entrypoint |
| mcp-server-filesystem-server | TS MCP server (source/index.ts) | Very Common | MEDIUM | Node.js runtime needed |
| mcp-server-memory-server | TS MCP server (source/index.ts) | Very Common | MEDIUM | Node.js runtime needed |
| mcp-server-sequentialthinking-server | TS MCP server (source/index.ts) | Very Common | MEDIUM | Node.js runtime needed |

### 4.13 MCP Servers from Rebuild (2 real agents out of 6)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| mcp-servers-minesweeper-example | Python servers with __main__ | Common | HIGH | Multiple server examples |
| mcp-servers-tavily-search | TS (src/index.ts) | Common | MEDIUM | Tavily API key needed |
| mcp-servers-notion-mcp | TS (src/openapi-mcp-server/index.ts) | Common | MEDIUM | Notion API key needed |

### 4.14 Vanilla JavaScript (5 real agents out of 6)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| vanilla-javascript-avr-llm-assistant | Node.js (index.js + package.json) | Common | MEDIUM | Voice/telephony agent |
| vanilla-javascript-multis-chat-agent | Node.js (src/index.js) | Common | MEDIUM | Multi-platform chat |
| vanilla-javascript-ntfy-mcp-server | Node.js MCP server (build/index.js) | Common | HIGH | Pre-built MCP server |
| vanilla-javascript-influxdb-mcp | TS MCP server (src/index.ts) | Common | MEDIUM | InfluxDB dep |
| vanilla-javascript-openai-proxy-shim | Node.js (example-app/index.js) | Common | MEDIUM | OpenAI proxy |

### 4.15 Vanilla Python (9 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| vanilla-python-minimal-research | main.py + multi-file | Very Common | HIGH | GPT Researcher -- well-structured |
| vanilla-python-octoagent | src/octoagent/main.py + CLI | Very Common | HIGH | GitHub agent with OpenAI SDK |
| vanilla-python-simple-ai-agents | examples/ with __main__ | Common | HIGH | Multiple standalone examples |
| vanilla-python-openai-patterns | examples/ with __main__ | Common | HIGH | Agent pattern demos |
| vanilla-python-verimap | verimap/main.py + argparse | Common | MEDIUM | Simulation engine, needs config |
| vanilla-python-reze-agent | main.py + FastAPI | Common | MEDIUM | Daemon (uvicorn), needs DB |
| vanilla-python-vanilla-ai-agents | samples/ dir | Common | MEDIUM | Azure samples |
| vanilla-python-agent-loop | agent_loop/main.py (no __main__) | Common | MEDIUM | Library module pattern |
| vanilla-python-pc-agent-loop | agentmain.py (spaghetti) | Rare | LOW | Heavy OS-level deps, messy code |

### 4.16 Vanilla TypeScript (6 real agents out of 8)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| vanilla-typescript-building-an-agent | index.ts (React/hooks pattern) | Common | MEDIUM | Frontend-oriented agent |
| vanilla-typescript-easy-agent | src/index.ts + CLI modes | Common | HIGH | CLI + Express modes |
| vanilla-typescript-ts-agents-framework | example/multiagent/index.ts | Common | HIGH | Clean multi-agent example |
| vanilla-typescript-social-media-agent | src/Agent/index.ts | Common | MEDIUM | Social media automation |
| vanilla-typescript-manifest-bun-ts | index.ts (Bun runtime) | Moderate | LOW | Requires Bun, not Node.js |
| vanilla-typescript-openai-realtime-ts | src/ (Next.js app) | Common | LOW | Full web app, not CLI agent |

---

## 5. Roadmaps for Supportable Patterns

### 5.1 Roadmap: Auto-Wrapper Generation for Class-Only Agents

**Agents supported**: langchain-mrkl-agent-base, langchain-self-ask-search-agent, langchain-structured-chat-agent, langchain-tool-calling-agent, langchain-openai-functions-multi-agent, langchain-openai-assistant-agent, openai-agents-basic-tools

**Pattern commonality**: VERY COMMON -- LangChain is the most popular agent framework. Most LangChain agents in the wild are importable classes, not standalone scripts.

**Current gap**: kinnoo's analyzer returns confidence 0.0 when no `__main__` guard or `main()` function is found. These agents are un-importable.

**Changes needed in kinnoo codebase**:

1. **`src/kinnoo/analyzer.py`** -- Add class-based agent detection:
   - After existing `_detect_entrypoint()` fails (confidence < 0.35), scan for agent base class patterns:
     - `class *Agent(*AgentMixin)` or `class *(BaseSingleActionAgent)`
     - `from langchain_core.agents import` patterns
     - `from agents import Agent` (OpenAI SDK)
   - Return a new detection result with `entrypoint_type: "class"` and `agent_class: "ClassName"`
   - Confidence: 0.60 for single clear agent class, 0.40 for multiple candidates

2. **`src/kinnoo/import_command.py`** -- Add wrapper generation step:
   - When analyzer returns `entrypoint_type: "class"`, offer to auto-generate `run.py`
   - Generated wrapper imports the class and runs it with sys.argv input
   - Framework-specific templates: LangChain (AgentExecutor wrapping), OpenAI SDK (Runner.run)

3. **`src/kinnoo/wrapper_templates/`** -- New directory with wrapper templates:
   - `langchain_wrapper.py.j2` -- LangChain class -> runnable script
   - `openai_agents_wrapper.py.j2` -- OpenAI Agents SDK class -> runnable script

**Estimated effort**: Medium. ~200 lines of new code + templates.

### 5.2 Roadmap: Jupyter Notebook to Python Conversion — DEPRECATED

> **DEPRECATED per human review (2025-03-23):** Notebook conversion is the agent developer’s burden. task270 deprecated. Agents 7-11 marked NO.

**Agents supported**: ~~langgraph-customer-support-graph, langgraph-hierarchical-agent-teams, langgraph-react-from-scratch, langgraph-tool-calling-graph, langgraph-web-voyager~~ None (skipped)

**Pattern commonality**: VERY COMMON -- most LangGraph tutorials and >50% of ML/AI notebooks in the wild are .ipynb format.

**Current gap**: kinnoo's analyzer ignores .ipynb files entirely. `_detect_entrypoint()` only looks for .py/.js/.ts files.

**Changes needed in kinnoo codebase**:

1. **`src/kinnoo/analyzer.py`** -- Add .ipynb detection:
   - In `_detect_entrypoint()`, after scanning for .py files, check for .ipynb files
   - Parse notebook JSON, extract code cells, check for agent patterns (StateGraph, Agent, etc.)
   - If found, set `entrypoint_type: "notebook"` with `notebook_path: "file.ipynb"`

2. **`src/kinnoo/import_command.py`** -- Add notebook conversion step:
   - When analyzer returns `entrypoint_type: "notebook"`, offer to convert to .py
   - Extract code cells (skip markdown cells)
   - Filter out IPython magic commands (%, !)
   - Add `if __name__ == "__main__":` guard wrapping the final execution cells
   - Write converted script alongside the .ipynb

3. **No new dependencies needed** -- .ipynb files are just JSON; json.load() is sufficient.

**Estimated effort**: Medium. ~150 lines of conversion logic.

### 5.3 Roadmap: Subdirectory Entrypoint Detection

**Agents supported**: langgraph-20-real-world-projects (project-23-coding-agent/main.py), openai-agents-sdk-customer-service (python-backend/main.py), openai-agents-financial-research-agent (source/main.py), openai-agents-research-bot (source/main.py), vanilla-python-octoagent (src/octoagent/main.py), openclaw-build-your-own (11-multi-agent-routing/src/mybot/cli/main.py), pydantic-ai-pydantic-ai-agent (src/run_agent.py)

**Pattern commonality**: VERY COMMON -- most production agents have main.py inside src/, source/, backend/, app/, etc.

**Current gap**: kinnoo's analyzer searches the top-level directory first. It finds main.py in subdirectories but may not rank them correctly or may miss them if maxdepth is limited.

**Changes needed in kinnoo codebase**:

1. **`src/kinnoo/analyzer.py`** -- Improve `_detect_entrypoint()` subdirectory search:
   - Increase search depth from 2 to 4 levels
   - Prioritize conventional subdirectory names: `src/`, `source/`, `app/`, `backend/`, `python-backend/`, `lambda/`
   - When multiple candidates exist in different subdirectories, prefer the shallowest one with a `__main__` guard
   - Return the relative path from the agent root (e.g., `source/main.py`)

2. **`src/kinnoo/run_command.py`** -- Ensure subdirectory entrypoints work:
   - When entrypoint is a relative path like `source/main.py`, set cwd to agent root and run `python source/main.py`
   - Alternatively, set PYTHONPATH to include the subdirectory

**Estimated effort**: Small. ~50 lines of changes to existing code.

### 5.4 Roadmap: Requirements Auto-Inference from Imports

**Agents supported**: Any Python agent lacking requirements.txt (many downloaded examples)

**Pattern commonality**: VERY COMMON -- most GitHub agent examples omit requirements.txt or have incomplete ones.

**Current gap**: kinnoo import reads requirements.txt if present but does nothing if it is missing. Many agents have imports (e.g., `from langchain_core import ...`) without a requirements.txt.

**Changes needed in kinnoo codebase**:

1. **`src/kinnoo/analyzer.py`** -- Add dependency inference:
   - Scan all .py files for import statements
   - Map common imports to PyPI package names (e.g., `langchain_core` -> `langchain-core`, `pydantic_ai` -> `pydantic-ai`, `agents` -> `openai-agents`)
   - Maintain a mapping dict of ~50 common AI/ML packages
   - Return `inferred_requirements: ["langchain-core>=0.1.0", ...]`

2. **`src/kinnoo/import_command.py`** -- Offer to generate requirements.txt:
   - When no requirements.txt exists and inferred deps are found, offer to write one
   - Show user the inferred packages for confirmation

**Estimated effort**: Medium. ~100 lines for import scanning + mapping dict.

### 5.5 Roadmap: Node.js/TypeScript Agent Import & Run Improvements

**Agents supported**: All TS/JS agents (vanilla-typescript-*, vanilla-javascript-*, MCP servers in TS, OpenClaw plugins, some MCP clients)

**Pattern commonality**: VERY COMMON -- ~25-30% of all agents in the wild are Node.js/TypeScript.

**Current gap**: kinnoo has basic Node.js runtime support (`runtime.language: nodejs`) but the import/analyzer does not detect TS agents well, and npm install during kinnoo install may not handle all package managers.

**Changes needed in kinnoo codebase**:

1. **`src/kinnoo/analyzer.py`** -- Improve Node.js/TS detection:
   - Detect package.json -> set `runtime.language: nodejs`
   - Check for tsconfig.json -> set compilation needed flag
   - Detect `start` or `main` script in package.json for entrypoint
   - Detect bun.lockb for Bun runtime (mark as LOW supportability)

2. **`src/kinnoo/run_command.py`** -- TypeScript compilation support:
   - If entrypoint is `.ts`, check for ts-node or tsx in devDependencies
   - Fall back to `npx tsx <entrypoint>` if tsx available
   - Add `runtime.typescript: true` option in manifest

3. **`src/kinnoo/install_command.py`** -- Ensure npm/yarn/pnpm install works:
   - Detect lockfile type (package-lock.json -> npm, yarn.lock -> yarn, pnpm-lock.yaml -> pnpm)
   - Run appropriate install command

**Estimated effort**: Medium-Large. ~200 lines across analyzer + run + install.

### 5.6 Roadmap: Async + Hardcoded Input Detection

**Agents supported**: All OpenAI Agents SDK agents (all use asyncio.run()), some MCP clients, PydanticAI agents using run_sync() vs run()

**Pattern commonality**: VERY COMMON -- async is the default for modern Python agent frameworks.

**Current gap**: kinnoo already handles async fine (subprocess execution), but the analyzer does not flag async patterns, and hardcoded vs parameterized input is not detected.

**Changes needed in kinnoo codebase**:

1. **`src/kinnoo/analyzer.py`** -- Detect async + input patterns:
   - Scan for `asyncio.run()`, `async def main()`, `agent.run_sync()` patterns
   - Detect if the agent reads `sys.argv` or `argparse` (parameterized input) vs hardcoded prompts
   - Set `inputs.required: false` when input is hardcoded

**Estimated effort**: Small. ~40 lines in analyzer.

### 5.7 Roadmap: PydanticAI Dependency Injection Support

**Agents supported**: pydanticai-bank-support-agent, pydanticai-flight-booking-agent, pydantic-ai-pydantic-ai-agent

**Pattern commonality**: COMMON -- PydanticAI's deps parameter is the recommended pattern for production agents.

**Current gap**: kinnoo run passes input as a string argument. PydanticAI agents with `deps_type` need structured input (customer_id, db connection, etc.) that must be injected separately from the prompt.

**Changes needed in kinnoo codebase**:

1. **`src/kinnoo/analyzer.py`** -- Detect deps pattern:
   - Scan for `Agent(... deps_type=...)` pattern
   - Extract the deps class fields from the Pydantic model
   - Set `inputs.type: json` with inferred schema

2. **Validation**: Verify that existing `--json-input` works correctly for deps injection. The agent's `run.py` wrapper would need to unpack JSON input into the deps class. This may require the auto-wrapper (from 5.1) to handle deps injection.

**Estimated effort**: Small. ~30 lines in analyzer + validation.

### 5.8 Roadmap: Service Dependency Auto-Detection

**Agents supported**: pydanticai-rag-agent (vector DB), vanilla-python-reze-agent (PostgreSQL), openclaw-ollama-extension-agent (Ollama), and others needing external services.

**Pattern commonality**: COMMON -- many production agents connect to databases, vector stores, or LLM endpoints.

**Current gap**: kinnoo supports `services:` in the manifest for health checks, but the analyzer does not auto-detect them from code.

**Changes needed in kinnoo codebase**:

1. **`src/kinnoo/analyzer.py`** -- Add service pattern scanning:
   - Detect known service patterns in imports and string literals:
     - `ollama` / `localhost:11434` -> Ollama
     - `chromadb` / `chroma` -> ChromaDB
     - `pinecone` -> Pinecone
     - `redis` -> Redis
     - `psycopg2` / `asyncpg` / `sqlalchemy` -> PostgreSQL
     - `pymongo` -> MongoDB
   - Return `detected_services: [{name: "ollama", url: "http://localhost:11434", ...}]`

2. **`src/kinnoo/import_command.py`** -- Populate services in generated kinnoo.yaml

**Estimated effort**: Small-Medium. ~80 lines.

---

## 6. Task Plan

Tasks are grouped by roadmap section. Each task targets one or more specific kinnoo code changes needed to support the agent pattern, with references to which agents become supportable.

| Task | Roadmap | Agents Supported | Priority |
|------|---------|-----------------|----------|
| task269 | 5.1 Auto-Wrapper Generation | 7 LangChain/library agents | HIGH |
| ~~task270~~ | ~~5.2 Notebook Conversion~~ | ~~5 LangGraph notebook agents~~ | ~~DEPRECATED~~ |
| task271 | 5.3 Subdirectory Entrypoint | ~7 multi-dir agents | HIGH |
| task272 | 5.4 Requirements Auto-Inference | All Python agents missing requirements.txt | MEDIUM |
| task273 | 5.5 Node.js/TS Import & Run | ~25 JS/TS agents | HIGH |
| task274 | 5.6 Async + Input Detection | ~15 async agents | MEDIUM |
| task275 | 5.8 Service Auto-Detection | ~8 agents with external services | LOW |
| task276 | 5.7 Deps Injection Support | 3 PydanticAI agents | LOW |
| task277 | E2E Validation | Representative from each pattern | HIGH |

See TASKS.txt for full task definitions and notes/features/feature47-handoff-notes.md for SWE implementation briefs.


---

# ADDENDUM: example-scratch-2 Agent Analysis

## A1. Overview (scratch-2)

132 agents in `example-scratch-2/agents/` were analyzed. Each agent was classified by:
- **Code pattern**: How the agent is organized
- **Pattern commonality**: How frequently this pattern appears in the wild
- **Kinnoo supportability**: How much kinnoo code needs to change

### Key Findings (scratch-2)
- **23 agents are monolithic** (>50 code files — excluded per project constraint).
- **109 agents are non-monolithic** and were fully classified.

- **5 agents are HIGH supportability** (already work or need minimal changes).
- **86 agents are MEDIUM supportability** (need targeted kinnoo improvements).
- **18 agents are LOW supportability** (need major features or are excluded).

### New Patterns Not Seen in scratch-1
1. **Streamlit/Gradio UI agents** (9 agents) — Use `streamlit run app.py` or Gradio `.launch()` as entrypoint. Kinnoo needs to detect these and set daemon-like run commands.
2. **CrewAI orchestration** (3 agents) — Class-based crew pattern with `Crew(...).kickoff()`. Needs framework-specific auto-wrapper template.
3. **OpenAI Swarm** (1 agent + 2 related swarm libs) — Multi-agent handoff via `swarm.repl.run_demo_loop()`.
4. **Agno/Phi** (2 agents) — Phidata/Agno framework with cookbook examples, deeply nested entrypoints.
5. **SmolAgents** (1 agent) — HuggingFace SmolAgents with web server pattern.
6. **AutoGen** (1 agent sample) — Microsoft AutoGen multi-agent chess game.
7. **Semantic Kernel** (1 agent) — Microsoft Semantic Kernel telemetry demos.
8. **MetaGPT** (1 agent) — MetaGPT with Streamlit UI component.
9. **LlamaIndex** (2 agents) — LlamaIndex/LlamaAgents SDK fragments.
10. **Anthropic client** (2 agents) — Direct Anthropic SDK usage for agent building.

### New Tasks Created for scratch-2
- **task278**: Streamlit/Gradio UI Agent Support — detect UI framework imports, set appropriate daemon run commands
- **task279**: Extended Framework Detection — CrewAI, Swarm, Agno, SmolAgents, AutoGen, Semantic Kernel, MetaGPT, LlamaIndex, Anthropic

---

## A2. Agent Pattern Classification (scratch-2)

| Pattern | Count | Commonality | Supportability | Example Agents |
|---------|-------|-------------|----------------|----------------|

| Python script + __main__ | 24 | Very Common | HIGH | legalai, optiguide, recai |
| Node.js/TypeScript | 18 | Common | MEDIUM | botpress, mastra, agentdock |
| Python multi-file | 14 | Common | MEDIUM | mirrorgpt, rasa, hive |
| Library/SDK | 13 | Moderate | LOW | diagnostics, langgraph, ui |
| FastAPI daemon | 13 | Very Common | MEDIUM | assistant, flow, blockagi |
| Flask daemon | 6 | Common | MEDIUM | shoppinggpt, bot, game |
| Streamlit webapp | 5 | Common | MEDIUM | hia, agent, autogroq |
| Gradio webapp | 4 | Common | MEDIUM | edugpt, microagents, ailoy |
| LlamaIndex SDK | 3 | Common | LOW | index, index, agentic |
| Agno/Phi | 2 | Common | MEDIUM | agno, phidata |
| Anthropic client | 2 | Common | MEDIUM | engineer, genomas |
| CrewAI orchestration | 1 | Common | MEDIUM | examples |
| AutoGen | 1 | Common | MEDIUM | autogen |
| SmolAgents | 1 | Moderate | MEDIUM | smolagents |
| Semantic Kernel | 1 | Common | MEDIUM | kernel |
| OpenAI Swarm | 1 | Common | MEDIUM | swarm |

---

## A3. Excluded (SDK/Library) (9 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| ashishpatel26-500-ai-agents-projects-ahmadvh-ai-agents-fo... | Library/SDK | Moderate | LOW | SDK/library fragment, no entrypoint |
| awesomelistsio-awesome-ai-agents-agno-agi-agent-ui | Library/SDK | Moderate | LOW | SDK/library fragment, no entrypoint |
| awesomelistsio-awesome-ai-agents-crewai-inc-crewai | Library/SDK | Moderate | LOW | SDK/library fragment, no entrypoint |
| awesomelistsio-awesome-ai-agents-langchain-ai-langchain | Library/SDK | Moderate | LOW | SDK/library fragment, no entrypoint |
| kyrolabs-awesome-agents-hwchase17-langchain | Library/SDK | Moderate | LOW | SDK/library fragment, no entrypoint |
| kyrolabs-awesome-agents-joaomdmoura-crewai | Library/SDK | Moderate | LOW | SDK/library fragment, no entrypoint |
| kyrolabs-awesome-agents-l33tdawg-sage | Library/SDK | Moderate | LOW | SDK/library fragment, no entrypoint |
| kyrolabs-awesome-agents-litanlitudan-skyagi | Library/SDK | Moderate | LOW | SDK/library fragment, no entrypoint |
| kyrolabs-awesome-agents-reworkd-agentgpt | Library/SDK | Moderate | LOW | SDK/library fragment, no entrypoint |

---

## A4. FastAPI/Flask Server Agents (19 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| ashishpatel26-500-ai-agents-projects-aleksnestu-ai-real-e... | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: apps/api/api/main.py |
| ashishpatel26-500-ai-agents-projects-hoanganhvu123-shoppi... | Flask daemon | Common | MEDIUM | Flask server, entry: app.py, deps: requirements.txt |
| ashishpatel26-500-ai-agents-projects-mohammed97ashraf-llm... | Flask daemon | Common | MEDIUM | Flask server, entry: app.py, deps: requirements.txt |
| ashishpatel26-500-ai-agents-projects-onjas-buidl-llm-agen... | Flask daemon | Common | MEDIUM | Flask server, entry: backend/app.py, deps: backend/requirements.txt |
| awesomelistsio-awesome-ai-agents-bytedance-deer-flow | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: docker/provisioner/app.py |
| kyrolabs-awesome-agents-blockpipe-blockagi | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: main.py, deps: pyproject.toml; ui/package.json |
| kyrolabs-awesome-agents-csunny-db-gpt | FastAPI daemon | Very Common | LOW | FastAPI server, no clear entrypoint |
| kyrolabs-awesome-agents-doriandarko-maestro | Flask daemon | Common | MEDIUM | Flask server, entry: flask_app/app.py, deps: flask_app/requirements.txt |
| kyrolabs-awesome-agents-evoagentx-evoagentx | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: evoagentx/app/main.py, deps: evoagentx/app/requirements.txt |
| kyrolabs-awesome-agents-internlm-lagent | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: lagent/distributed/http_serve/app.py |
| kyrolabs-awesome-agents-jonathan-adly-agentrun | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: agentrun-api/src/api/main.py |
| kyrolabs-awesome-agents-landing-ai-vision-agent | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: examples/chat/run.py, deps: examples/chat/requirements.txt |
| kyrolabs-awesome-agents-openbmb-xagent | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: XAgentServer/application/main.py |
| kyrolabs-awesome-agents-paulpierre-rasagpt | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: app/api/main.py, deps: app/api/requirements.txt |
| kyrolabs-awesome-agents-pipecat-ai-pipecat | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: src/pipecat/runner/run.py |
| kyrolabs-awesome-agents-ruc-datalab-deepanalyze | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: API/main.py |
| kyrolabs-awesome-agents-upsonic-upsonic | FastAPI daemon | Very Common | MEDIUM | FastAPI server, entry: src/upsonic/cli/main.py |
| kyrolabs-awesome-agents-vectara-open-rag-eval | Flask daemon | Common | LOW | Flask server, no clear entrypoint |
| kyrolabs-awesome-agents-xlang-ai-openagents | Flask daemon | Common | MEDIUM | Flask server, entry: backend/app.py, deps: backend/requirements.txt |

---

## A5. LangChain/LangGraph Agents (5 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| ashishpatel26-500-ai-agents-projects-crosleythomas-mirrorgpt | Python multi-file | Very Common | MEDIUM | LangChain/LangGraph agent, entry: mirror/mirror_agent/agent.py, no __main__ |
| ashishpatel26-500-ai-agents-projects-firica-legalai | Python script + __main__ | Very Common | HIGH | LangChain/LangGraph agent, entry: agent.py, has __main__ |
| kyrolabs-awesome-agents-jarrycyx-openlens-ai | Python script + __main__ | Very Common | MEDIUM | LangChain/LangGraph agent, entry: openlens_ai/main.py, has __main__ |
| kyrolabs-awesome-agents-kirill89-reviewcerberus | Python script + __main__ | Very Common | MEDIUM | LangChain/LangGraph agent, entry: src/main.py, has __main__ |
| kyrolabs-awesome-agents-yifan-song793-restgpt | Python script + __main__ | Very Common | HIGH | LangChain/LangGraph agent, entry: run.py, has __main__ |

---

## A6. Library Agents (4 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| ashishpatel26-500-ai-agents-projects-awesomelistsio-aweso... | Library/SDK | Common | LOW | Large library (22 code files), needs auto-wrapper |
| kyrolabs-awesome-agents-e2b-dev-e2b | Library/SDK | Common | LOW | Large library (16 code files), needs auto-wrapper |
| kyrolabs-awesome-agents-homanp-superagent | Library/SDK | Common | LOW | Large library (22 code files), needs auto-wrapper |
| kyrolabs-awesome-agents-minedojo-voyager | Library/SDK | Common | LOW | Large library (8 code files), needs auto-wrapper |

---

## A7. New Framework Agents (12 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| ashishpatel26-500-ai-agents-projects-awesomelistsio-aweso... | Agno/Phi | Common | MEDIUM | Agno/Phi framework, 46 code files, entry: cookbook/01_demo/run.py |
| ashishpatel26-500-ai-agents-projects-crewaiinc-crewai-exa... | CrewAI orchestration | Common | MEDIUM | CrewAI crew pattern with __main__, entry: crews/trip_planner/main.py |
| ashishpatel26-500-ai-agents-projects-kyrolabs-awesome-age... | AutoGen | Common | MEDIUM | Microsoft AutoGen, entry: python/samples/core_chess_game/main.py |
| awesomelistsio-awesome-ai-agents-huggingface-smolagents | SmolAgents | Moderate | MEDIUM | HuggingFace SmolAgents, entry: examples/server/main.py |
| awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-... | Semantic Kernel | Common | MEDIUM | Microsoft Semantic Kernel, samples only, no clear entrypoint |
| awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-... | OpenAI Swarm | Common | MEDIUM | OpenAI Swarm multi-agent, entry: examples/airline/main.py |
| awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-... | Agno/Phi | Common | MEDIUM | Agno/Phi framework, 46 code files, entry: cookbook/01_demo/run.py |
| awesomelistsio-awesome-ai-agents-run-llama-llama-index | LlamaIndex SDK | Common | LOW | LlamaIndex SDK, no clear entrypoint |
| kyrolabs-awesome-agents-doriandarko-claude-engineer | Anthropic client | Common | MEDIUM | Anthropic client agent, entry: Claude-Eng-v2/main.py |
| kyrolabs-awesome-agents-jerryjliu-llama-index | LlamaIndex SDK | Common | LOW | LlamaIndex SDK, no clear entrypoint |
| kyrolabs-awesome-agents-liu-hy-genomas | Anthropic client | Common | MEDIUM | Anthropic client agent, entry: main.py |
| kyrolabs-awesome-agents-vectara-py-vectara-agentic | LlamaIndex SDK | Common | LOW | LlamaIndex SDK, no clear entrypoint |

---

## A8. Node.js/TypeScript Agents (18 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-... | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: bots/clog/src/index.ts |
| awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-... | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: stores/pg/src/index.ts |
| kyrolabs-awesome-agents-agentdock-agentdock | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: src/lib/index.ts |
| kyrolabs-awesome-agents-agentset-ai-agentset | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: packages/db/src/index.ts |
| kyrolabs-awesome-agents-charlie85270-dorothy | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: mcp-x/src/index.ts |
| kyrolabs-awesome-agents-dust-tt-dust | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: sdks/js/src/index.ts |
| kyrolabs-awesome-agents-giselles-ai-giselle | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: packages/rag/src/index.ts |
| kyrolabs-awesome-agents-hkuds-nanobot | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: bridge/src/index.ts |
| kyrolabs-awesome-agents-hypermodeinc-modus | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: cli/src/index.ts |
| kyrolabs-awesome-agents-jcanizalez-vibegrid | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: src/main/index.ts |
| kyrolabs-awesome-agents-juspay-neurolink | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: src/cli/index.ts |
| kyrolabs-awesome-agents-miurla-babyagi-ui | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: src/hooks/index.ts |
| kyrolabs-awesome-agents-mnfst-manifest | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: packages/openclaw-plugin/src/index.ts |
| kyrolabs-awesome-agents-nilsherzig-llocalsearch | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: src/lib/index.ts |
| kyrolabs-awesome-agents-samuraigpt-camel-autogpt | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: client/src/index.js |
| kyrolabs-awesome-agents-sopaco-cortex-mem | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: examples/@memclaw/plugin/index.ts |
| kyrolabs-awesome-agents-sst-opencode | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: github/index.ts |
| kyrolabs-awesome-agents-voltagent-voltagent | Node.js/TypeScript | Common | MEDIUM | Node.js/TS agent (vanilla), entry: tools/core/src/index.ts |

---

## A9. OpenAI Agents (6 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| ashishpatel26-500-ai-agents-projects-microsoft-optiguide | Python script + __main__ | Very Common | MEDIUM | OpenAI SDK agent, entry: milp-evolve/src/milp_evolve_llm/main.py, has __main__ |
| ashishpatel26-500-ai-agents-projects-microsoft-recai | Python script + __main__ | Very Common | MEDIUM | OpenAI SDK agent, entry: RecLM-gen/main.py, has __main__ |
| ashishpatel26-500-ai-agents-projects-mingyuj666-stockagent | Python script + __main__ | Very Common | HIGH | OpenAI SDK agent, entry: agent.py, has __main__ |
| kyrolabs-awesome-agents-mpaepper-llm-agents | Python script + __main__ | Very Common | MEDIUM | OpenAI SDK agent, entry: llm_agents/agent.py, has __main__ |
| kyrolabs-awesome-agents-saharmor-voice-lab | Python script + __main__ | Very Common | HIGH | OpenAI SDK agent, entry: main.py, has __main__ |
| kyrolabs-awesome-agents-simonmesmith-agentflow | Python script + __main__ | Very Common | HIGH | OpenAI SDK agent, entry: run.py, has __main__ |

---

## A10. Streamlit/Gradio UI Agents (9 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| ashishpatel26-500-ai-agents-projects-harshhh28-hia | Streamlit webapp | Common | MEDIUM | Streamlit UI app, has __main__, no deps file |
| ashishpatel26-500-ai-agents-projects-hqanhh-edugpt | Gradio webapp | Common | MEDIUM | Gradio UI app, no deps file |
| ashishpatel26-500-ai-agents-projects-nirbar1985-ai-travel... | Streamlit webapp | Common | MEDIUM | Streamlit UI app, has __main__, deps: pyproject.toml |
| awesomelistsio-awesome-ai-agents-jgravelle-autogroq | Streamlit webapp | Common | MEDIUM | Streamlit UI app, has __main__, no deps file |
| awesomelistsio-awesome-ai-agents-josefdc-imageagent | Streamlit webapp | Common | MEDIUM | Streamlit UI app, has __main__, deps: requirements.txt |
| kyrolabs-awesome-agents-aymenfurter-microagents | Gradio webapp | Common | MEDIUM | Gradio UI app, has __main__, deps: requirements.txt |
| kyrolabs-awesome-agents-brekkylab-ailoy | Gradio webapp | Common | MEDIUM | Gradio UI app, deps: examples/gradio_chatbot/pyproject.toml |
| kyrolabs-awesome-agents-geekan-metagpt | Streamlit webapp | Common | MEDIUM | Streamlit UI app, has __main__, no deps file |
| kyrolabs-awesome-agents-openbmb-repoagent | Gradio webapp | Common | MEDIUM | Gradio UI app, has __main__, no deps file |

---

## A11. Vanilla Python Agents (27 agents)

| Agent | Pattern | Commonality | Supportability | Notes |
|-------|---------|-------------|----------------|-------|
| awesomelistsio-awesome-ai-agents-pydantic-pydantic-ai | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: docs/.hooks/main.py |
| awesomelistsio-awesome-ai-agents-rasahq-rasa | Python multi-file | Common | MEDIUM | Python multi-file, entry: rasa/cli/run.py, no __main__ |
| kyrolabs-awesome-agents-aden-hive-hive | Python multi-file | Common | MEDIUM | Python multi-file, entry: core/framework/schemas/run.py, no __main__ |
| kyrolabs-awesome-agents-agent-field-agentfield | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: examples/python_agent_nodes/agentic_rag/main.py |
| kyrolabs-awesome-agents-all-hands-ai-openhands | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: openhands/core/main.py |
| kyrolabs-awesome-agents-baidu-baige-loongflow | Python multi-file | Common | MEDIUM | Python multi-file, entry: tests/ccsdk/agent.py, no __main__ |
| kyrolabs-awesome-agents-cline-cline | Python multi-file | Common | MEDIUM | Has __main__ guards but no standard entrypoint found, needs investigation |
| kyrolabs-awesome-agents-deepset-ai-haystack | Python multi-file | Common | MEDIUM | Python multi-file, entry: haystack/components/agents/agent.py, no __main__ |
| kyrolabs-awesome-agents-fetchai-uagents | Python multi-file | Common | MEDIUM | Python multi-file, entry: python/src/uagents/agent.py, no __main__ |
| kyrolabs-awesome-agents-gobii-ai-gobii-platform | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: scripts/prototype/agent.py |
| kyrolabs-awesome-agents-kayba-ai-agentic-context-engine | Python multi-file | Common | MEDIUM | Python multi-file, entry: ace_next/steps/agent.py, no __main__ |
| kyrolabs-awesome-agents-kyegomez-swarms | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: swarms/cli/main.py |
| kyrolabs-awesome-agents-littlebearapps-untether | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: src/untether/cli/run.py |
| kyrolabs-awesome-agents-maximilian-winter-llama-cpp-agent | Python multi-file | Common | MEDIUM | Python multi-file, entry: examples/07_Memory/MemoryAssistant/main.py, no __main__ |
| kyrolabs-awesome-agents-meta-llama-llama-agentic-system | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: examples/DocQA/app.py |
| kyrolabs-awesome-agents-microsoft-taskweaver | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: playground/UI/app.py |
| kyrolabs-awesome-agents-modelscope-agentscope | Python multi-file | Common | MEDIUM | Python multi-file, entry: examples/agent/a2a_agent/main.py, no __main__ |
| kyrolabs-awesome-agents-princeton-nlp-swe-agent | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: sweagent/run/run.py |
| kyrolabs-awesome-agents-promtengineer-localgpt | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: rag_system/main.py |
| kyrolabs-awesome-agents-reddotrocket-agentup | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: src/agent/cli/main.py |
| kyrolabs-awesome-agents-run-llama-llama-agents | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: llama_deploy/cli/run.py |
| kyrolabs-awesome-agents-stitionai-devika | Python multi-file | Common | MEDIUM | Python multi-file, entry: src/agents/agent.py, no __main__ |
| kyrolabs-awesome-agents-strands-agents-sdk-python | Python multi-file | Common | MEDIUM | Python multi-file, entry: src/strands/agent/agent.py, no __main__ |
| kyrolabs-awesome-agents-technion-kishony-lab-data-to-paper | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: src/data_to_paper/scripts/run.py |
| kyrolabs-awesome-agents-teoslayer-pilotprotocol | Python multi-file | Common | MEDIUM | Python multi-file, entry: sdk/python/pilotprotocol/cli.py, no __main__ |
| kyrolabs-awesome-agents-voicetestdev-voicetest | Python multi-file | Common | MEDIUM | Python multi-file, entry: voicetest/tui/app.py, no __main__ |
| kyrolabs-awesome-agents-vrsen-agency-swarm | Python script + __main__ | Very Common | MEDIUM | Python script + __main__, entry: src/agency_swarm/cli/main.py |

---

## A12. Monolithic Agents Excluded (23 agents)

These agents have >50 code files and are excluded per project constraint (focus on low-to-medium complexity agents).

| Agent | Reason |
|-------|--------|
| awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-ag2ai-ag2 | Monolithic (>50 code files) |
| awesomelistsio-awesome-ai-agents-langflow-ai-langflow | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-aider-ai-aider | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-arize-ai-phoenix | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-assafelovic-gpt-researcher | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-cpacker-memgpt | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-fim-ai-fim-agent | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-hpcaitech-colossalai | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-iflytek-astron-agent | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-imartinez-privategpt | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-joinly-ai-joinly | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-josh-xt-agent-llm | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-kreneskyp-ix | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-melih-unsal-demogpt | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-mervinpraison-praisonai | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-openbmb-agentverse | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-openclaw-openclaw | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-openonion-connectonion | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-pythagora-io-gpt-pilot | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-sbusso-claudeclaw | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-steel-dev-steel-browser | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-trafficguard-nous | Monolithic (>50 code files) |
| kyrolabs-awesome-agents-transformeroptimus-superagi | Monolithic (>50 code files) |

---

## A13. New Roadmaps (scratch-2 Specific)

### A13.1 Roadmap: Streamlit/Gradio UI Agent Support (task278)

**Agents supported**: 
ashishpatel26-500-ai-agents-projects-harshhh28-hia, ashishpatel26-500-ai-agents-projects-hqanhh-edugpt, ashishpatel26-500-ai-agents-projects-nirbar1985-ai-travel-agent, awesomelistsio-awesome-ai-agents-jgravelle-autogroq, awesomelistsio-awesome-ai-agents-josefdc-imageagent, kyrolabs-awesome-agents-aymenfurter-microagents, kyrolabs-awesome-agents-brekkylab-ailoy, kyrolabs-awesome-agents-geekan-metagpt, kyrolabs-awesome-agents-openbmb-repoagent

**Pattern commonality**: COMMON — Streamlit is the most popular way to build LLM agent demos. Gradio is the #2 choice (especially in HuggingFace ecosystem). Together they account for ~30-40% of demo-grade agent UIs in the wild.

**Current gap**: kinnoo treats all Python agents as `python <entrypoint>` execution. Streamlit agents need `streamlit run <app.py>` and Gradio agents use `python <app.py>` but launch a web server (daemon pattern). Neither is detected today.

**Changes needed in kinnoo codebase**:

1. **`src/kinnoo/analyzer.py`** — Add UI framework detection:
   - Scan Python files for `import streamlit` or `from streamlit` → set `ui_framework: streamlit`
   - Scan for `import gradio` or `from gradio` → set `ui_framework: gradio`
   - Detect `st.chat_input`, `st.text_input` → confirm Streamlit app pattern
   - Detect `gr.Interface`, `gr.Blocks`, `.launch()` → confirm Gradio app pattern

2. **`src/kinnoo/import_command.py`** — Set runtime type for UI agents:
   - When `ui_framework: streamlit`, set `runtime.type: daemon` and `runtime.run_command: streamlit run <entrypoint>`
   - When `ui_framework: gradio`, set `runtime.type: daemon` (Gradio auto-launches web server)

3. **`src/kinnoo/run_command.py`** — Handle streamlit run command:
   - If runtime.run_command starts with "streamlit", execute it directly instead of `python <entrypoint>`

**Estimated effort**: Small-Medium. ~80 lines of new code.

### A13.2 Roadmap: Extended Framework Detection (task279) -- DEPRECATED

> **DEPRECATED per human review (2025-03-23):** All 9 extended framework detections deferred to a future feature.

**Agents supported**: All agents using CrewAI, OpenAI Swarm, Agno/Phi, SmolAgents, AutoGen, Semantic Kernel, MetaGPT, LlamaIndex, Anthropic -- DEFERRED

**Pattern commonality**: COMMON to VERY COMMON — These 9 frameworks represent the second tier of popular agent frameworks after LangChain/OpenAI SDK. CrewAI alone has 40K+ GitHub stars.

**Current gap**: kinnoo's analyzer only detects LangChain, OpenAI SDK, PydanticAI, and MCP patterns. These newer/niche frameworks are not detected, meaning kinnoo can't apply framework-specific wrapper templates or run configurations.

**Changes needed in kinnoo codebase**:

1. **`src/kinnoo/analyzer.py`** — Extend framework detection:
   - Add import patterns for 9 new frameworks:
     - `from crewai import` → CrewAI
     - `from swarm import` → OpenAI Swarm
     - `from agno import` or `from phi import` → Agno/Phi
     - `from smolagents import` → SmolAgents
     - `from autogen import` or `import autogen` → AutoGen
     - `from semantic_kernel import` → Semantic Kernel
     - `from metagpt import` → MetaGPT
     - `from llama_index import` or `from llama_deploy import` → LlamaIndex
     - `from anthropic import` → Anthropic (direct client)
   - For each, set `framework: <name>` in analysis result

2. **`src/kinnoo/wrapper_templates/`** — Add CrewAI wrapper template:
   - CrewAI agents use `Crew(...).kickoff()` pattern
   - Template: import crew class, call `.kickoff()` with sys.argv[1] as input

3. **`src/kinnoo/import_command.py`** — Framework-specific import hints:
   - When framework is detected, add framework name to kinnoo.yaml metadata
   - Add `requirements_hint` with known package names for each framework

**Estimated effort**: Medium. ~150 lines of detection + templates.


---

## A14. Task Plan (scratch-2 Additions)

| Task | Roadmap | Agents Supported | Priority |
|------|---------|-----------------|----------|
| task278 | A13.1 Streamlit/Gradio UI Support | 9 UI agents | MEDIUM |
| ~~task279~~ | ~~A13.2 Extended Framework Detection~~ | ~~15 new framework agents~~ | ~~DEPRECATED~~ |

Existing tasks from scratch-1 also apply to many scratch-2 agents:
- task269 (Auto-Wrapper): 8+ library/SDK agents in scratch-2
- task271 (Subdirectory Entrypoint): 30+ agents with nested main.py
- task272 (Requirements Inference): 60+ agents missing requirements.txt
- task273 (Node.js/TS): 15+ TS/JS agents in scratch-2
- task274 (Async/Input Detection): Many agents with no __main__ guard
- task275 (Service Detection): FastAPI/Flask server agents
- task277 (E2E Validation): All agents

# Revision: Human Review (2025-03-23)

## Decisions Applied

### scratch-1 Decisions
1. **LangChain class-only (1-6)**: YES -- support running via auto-wrapper (task269). Tool calling is best-effort.
2. **LangGraph notebooks (7-11)**: NO -- notebook conversion burden is on the developer. task270 deprecated.
3. **LangGraph Python entrypoints (12-14)**: NO -- explicitly excluded per human review despite having Python entrypoints.
4. **PydanticAI (15-24)**: ALL YES -- goal is to make sure they run, not necessarily produce correct output.
5. **Agent 19 (rag-agent)**: YES (task275, task277) -- even if it crashes on DB setup, that is the developer's problem.
6. **OpenAI SDK (27-36, 38-39)**: YES -- agents 36 (streaming) and 39 (realtime/Next.js) promoted from FUTURE.
7. **OpenClaw (40-44, 46)**: YES -- agent 43 (lobster) promoted from FUTURE. User will install deps.
8. **MCP clients (52-64)**: ALL YES -- agents 56/57/60/61 promoted from FUTURE.
9. **MCP servers (65-71, 73)**: YES. Agent 72 (tavily-search) was already YES.
10. **Vanilla JS (74-78)**: YES (unchanged).
11. **Vanilla Python (79-84, 86, 88-91)**: YES. Agent 85 stays FUTURE (Azure samples). Agent 87 stays NO.

### scratch-2 Decisions
1. **LangChain/LangGraph agents**: keep supporting (low-to-medium complexity)
2. **Streamlit UI agents**: YES (task278)
3. **Gradio UI agents**: YES (task278)
4. **LlamaIndex agents**: DEFER to FUTURE
5. **SmolAgents**: DEFER to FUTURE
6. **AutoGen agents**: DEFER to FUTURE
7. **Agno agents**: DEFER to FUTURE
8. **Anthropic agents**: DEFER to FUTURE
9. **CrewAI, MetaGPT, Swarm**: DO NOT SUPPORT -- all deferred to future feature

### Key Principle
> "Import should not throw errors unless the agent itself has issues. And kinnoo run should run the agent, but, depending on if the agent code itself has bugs, may or may not get to a successful output."

### Manifest Changes Applied
- **AC2** (notebook conversion): Removed from feature47
- **AC11**: DEPRECATED -- all 9 extended framework detections deferred to future feature
- **task270**: Deprecated (notebook conversion)
- **task279**: DEPRECATED -- all extended framework detection deferred to future feature
- **test386, test387**: Deprecated (notebook tests, AC2 removed)
- **test406, test407, test408, test409**: Deprecated (extended framework detection deferred)

### Statistics After Revision
- **scratch-1**: YES=74, FUTURE=1, NO=18 (was 72/11/10)
- **scratch-2**: YES=82, FUTURE=16, NO=11 (was 90/10/9)
- **Combined**: YES=156, FUTURE=17, NO=29
