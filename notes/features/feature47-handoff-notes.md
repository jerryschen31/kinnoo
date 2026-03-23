# Feature 47 — SWE Handoff Notes

## Overview

These notes provide implementation guidance for each task in feature47. The SWE agent should work through these tasks in the order listed, as some later tasks depend on earlier ones.

**Critical instruction**: For each task, continue making code changes and tweaks until the target agent(s) can be successfully imported, installed, and run with kinnoo. Install external dependencies or mock them as needed. If a dependency is too complex to install (specific databases, cloud credentials, etc.), document what's blocking and move on. "Run successfully" means kinnoo's pass-through to the agent entrypoint works -- if the agent itself errors due to its own bugs, that's not kinnoo's responsibility.

---

## task269: Auto-Wrapper Generation for Class-Only Python Agents

### Target agents
- langchain-mrkl-agent-base
- langchain-self-ask-search-agent
- langchain-structured-chat-agent
- langchain-tool-calling-agent
- langchain-openai-functions-multi-agent
- langchain-openai-assistant-agent
- openai-agents-basic-tools

### Implementation plan

1. **Modify `src/kinnoo/analyzer.py`**:
   - In `_detect_entrypoint()`, after all existing checks, add a fallback that scans Python files for agent class definitions
   - Look for patterns: `class \w+Agent\(`, `class \w+\(BaseSingleActionAgent\)`, `class \w+\(BaseMultiActionAgent\)`, `from langchain` imports combined with class definitions, `from agents import Agent`
   - If a single clear agent class is found, return `{"entrypoint": None, "entrypoint_type": "class", "agent_class": class_name, "agent_module": module_file, "confidence": 0.60}`
   - If multiple candidates, return confidence 0.40 with all candidates listed

2. **Modify `src/kinnoo/import_command.py`**:
   - After analyzer returns results, check for `entrypoint_type == "class"`
   - Offer the user (with y/N prompt) to auto-generate a `run.py` wrapper
   - Use framework-specific templates based on detected imports

3. **Create `src/kinnoo/wrapper_templates/` directory** with:
   - `langchain_wrapper.py.j2`: Template that imports the agent class, creates an AgentExecutor with a dummy LLM placeholder, and runs it with sys.argv[1] as input
   - `openai_agents_wrapper.py.j2`: Template that imports the Agent class and uses Runner.run_sync() with sys.argv[1]
   - These are simple string templates (Python f-strings or str.format), no need for Jinja2

4. **Test with agents**: After implementation, run `kinnoo import` on `langchain-tool-calling-agent` and `openai-agents-basic-tools` to verify wrapper generation works. Then `kinnoo run` to verify the generated wrapper is functional (it will likely fail due to missing LLM API keys, which is expected -- the wrapper itself should be syntactically correct).

### Tests
- test384: Verify analyzer detects class-only agent pattern and returns entrypoint_type "class"
- test385: Verify import command generates a valid run.py wrapper for detected class agent

---

## task270: Jupyter Notebook to Python Script Conversion

### Target agents
- langgraph-customer-support-graph
- langgraph-hierarchical-agent-teams
- langgraph-react-from-scratch
- langgraph-tool-calling-graph
- langgraph-web-voyager

### Implementation plan

1. **Modify `src/kinnoo/analyzer.py`**:
   - In `_detect_entrypoint()`, after scanning for .py/.js/.ts files, scan for .ipynb files
   - Parse notebook JSON: `json.load(f)["cells"]` -- filter for `cell_type == "code"`
   - Check if code cells contain agent patterns (import langgraph, import langchain, StateGraph, etc.)
   - Return `{"entrypoint": None, "entrypoint_type": "notebook", "notebook_path": "file.ipynb", "confidence": 0.55}`

2. **Modify `src/kinnoo/import_command.py`**:
   - When `entrypoint_type == "notebook"`, offer to convert to .py
   - Extract all code cells in order
   - Strip IPython magic lines (lines starting with `%` or `!`)
   - Strip `display()` and `HTML()` calls that are Jupyter-specific
   - Write to `<notebook_name>.py` with a `if __name__ == "__main__":` guard wrapping the main execution code
   - Set the converted .py as the entrypoint in kinnoo.yaml

3. **Test with agents**: Try converting `langgraph-react-from-scratch` (simplest notebook) first. The converted script should be syntactically valid Python. Running it will require langgraph + LLM API keys.

### Tests
- test386: Verify analyzer detects .ipynb files and returns entrypoint_type "notebook"
- test387: Verify notebook conversion produces valid Python script with __main__ guard

---

## task271: Subdirectory Entrypoint Detection Improvement

### Target agents
- langgraph-20-real-world-projects (project-23-coding-agent/main.py)
- openai-agents-sdk-customer-service (python-backend/main.py)
- openai-agents-financial-research-agent (source/main.py)
- openai-agents-research-bot (source/main.py)
- vanilla-python-octoagent (src/octoagent/main.py)
- openclaw-build-your-own (11-multi-agent-routing/src/mybot/cli/main.py)
- pydantic-ai-pydantic-ai-agent (src/run_agent.py)

### Implementation plan

1. **Modify `src/kinnoo/analyzer.py`** -- `_detect_entrypoint()`:
   - Increase `os.walk()` max depth from 2 to 4
   - Add priority weighting for conventional subdirectory names: `src/`, `source/`, `app/`, `backend/`, `python-backend/`, `lambda/`, `lib/`
   - When multiple main.py candidates found at different depths, prefer: (a) shallowest depth, (b) in a priority subdirectory, (c) with a `__main__` guard
   - Return relative path from agent root: `"entrypoint": "source/main.py"`

2. **Verify `src/kinnoo/run_command.py`** handles relative entrypoints:
   - Ensure `subprocess.run(["python", entrypoint], cwd=agent_dir)` works when entrypoint is `source/main.py`
   - May need to set `PYTHONPATH` to include subdirectories so relative imports inside the agent work

3. **Test**: Import `openai-agents-sdk-customer-service` and verify `python-backend/main.py` is detected. Import `vanilla-python-octoagent` and verify `src/octoagent/main.py` is detected.

### Tests
- test388: Verify analyzer finds main.py in subdirectories (src/, source/, python-backend/)
- test389: Verify kinnoo run executes a subdirectory entrypoint correctly

---

## task272: Requirements Auto-Inference from Python Imports

### Target agents
- Any Python agent without requirements.txt
- Particularly: langgraph-20-real-world-projects, langgraph-multi-agent-router, vanilla-python-agent-loop

### Implementation plan

1. **Modify `src/kinnoo/analyzer.py`** -- Add new function `_infer_requirements(agent_dir)`:
   - Walk all .py files, parse `import X` and `from X import Y` statements
   - Strip stdlib modules using `sys.stdlib_module_names` (Python 3.10+) or a hardcoded set
   - Map top-level import names to PyPI package names using a dict:
     ```python
     IMPORT_TO_PYPI = {
         "langchain": "langchain",
         "langchain_core": "langchain-core",
         "langchain_openai": "langchain-openai",
         "langchain_google_genai": "langchain-google-genai",
         "langgraph": "langgraph",
         "pydantic_ai": "pydantic-ai",
         "agents": "openai-agents",
         "openai": "openai",
         "anthropic": "anthropic",
         "crewai": "crewai",
         "crewai_tools": "crewai-tools",
         "httpx": "httpx",
         "fastapi": "fastapi",
         "uvicorn": "uvicorn",
         "chromadb": "chromadb",
         "pinecone": "pinecone-client",
         "redis": "redis",
         "mcp": "mcp",
         "dotenv": "python-dotenv",
         "loguru": "loguru",
         "pydantic": "pydantic",
         # ... extend as needed
     }
     ```
   - Return list of inferred package names

2. **Modify `src/kinnoo/import_command.py`**:
   - If no requirements.txt found, call `_infer_requirements()`
   - Display inferred packages to user and offer to generate requirements.txt
   - Write minimal requirements.txt with package names (no version pins)

3. **Test**: Import `langgraph-multi-agent-router` (has requirements.txt so compare inferred vs actual). Import an agent without requirements.txt and verify inference works.

### Tests
- test390: Verify import-to-PyPI mapping correctly maps common agent imports
- test391: Verify requirements.txt generation from inferred imports

---

## task273: Node.js/TypeScript Agent Import & Run Improvements

### Target agents
All TS/JS agents including:
- vanilla-typescript-easy-agent, vanilla-typescript-ts-agents-framework
- vanilla-javascript-avr-llm-assistant, vanilla-javascript-ntfy-mcp-server
- mcp-server-filesystem-server, mcp-server-memory-server, mcp-server-sequentialthinking-server
- mcp-servers-tavily-search, mcp-servers-notion-mcp
- openclaw-nanobot-assistant
- agents-with-mcp-client-code-langchainjs-burger, agents-with-mcp-client-code-mcp-browser-agent

### Implementation plan

1. **Modify `src/kinnoo/analyzer.py`**:
   - Detect package.json: parse it to find `main` field or `scripts.start` for entrypoint
   - Detect tsconfig.json: flag that TypeScript compilation is needed
   - Check for lockfiles: package-lock.json (npm), yarn.lock (yarn), pnpm-lock.yaml (pnpm)
   - Set `runtime.language: nodejs` and `runtime.package_manager` accordingly

2. **Modify `src/kinnoo/run_command.py`**:
   - If entrypoint is `.ts` and no compiled `.js` exists:
     - Check if `tsx` or `ts-node` is available (via `npx tsx --version`)
     - Run `npx tsx <entrypoint>` for TypeScript files
   - If entrypoint is `.js`, run `node <entrypoint>`

3. **Modify `src/kinnoo/install_command.py`**:
   - Detect package manager from lockfile and run appropriate install command
   - Support `npm install`, `yarn install`, `pnpm install`

4. **Test**: Import `vanilla-typescript-easy-agent` (has package.json + src/index.ts). Verify it gets runtime.language: nodejs and can be run with npx tsx.

### Tests
- test392: Verify analyzer detects package.json and sets runtime.language to nodejs
- test393: Verify kinnoo run handles TypeScript entrypoints via tsx/ts-node

---

## task274: Async Entrypoint + Hardcoded Input Detection

### Target agents
- openai-agents-hello-world (hardcoded input)
- openai-agents-sdk-agent-search-tools (async)
- All OpenAI Agents SDK agents with asyncio.run()
- MCP clients

### Implementation plan

1. **Modify `src/kinnoo/analyzer.py`**:
   - Scan Python entrypoint for `asyncio.run(main())` or `asyncio.run(` patterns
   - Set `async_entrypoint: true` in analysis result (informational, kinnoo already handles via subprocess)
   - Scan for `sys.argv` or `argparse` usage -- if absent and hardcoded strings found in agent.run() calls, set `inputs.required: false`
   - Look for patterns like `agent.run("hardcoded string")` or `Runner.run(agent, "hardcoded")`

2. **Modify `src/kinnoo/import_command.py`**:
   - When generating kinnoo.yaml, use `inputs.required: false` if hardcoded input detected
   - Add a comment in generated kinnoo.yaml noting "input is hardcoded in agent code"

3. **Test**: Import `openai-agents-hello-world` and verify `inputs.required` is set to false. Import an agent with argparse and verify `inputs.required` is true.

### Tests
- test394: Verify analyzer detects hardcoded vs parameterized input patterns
- test395: Verify kinnoo.yaml generation sets inputs.required correctly

---

## task275: Service Dependency Auto-Detection

### Target agents
- openclaw-ollama-extension-agent (Ollama)
- vanilla-python-reze-agent (PostgreSQL/SQLAlchemy)
- pydanticai-rag-agent (vector DB -- chromadb/pinecone)

### Implementation plan

1. **Modify `src/kinnoo/analyzer.py`** -- Add `_detect_services(agent_dir)`:
   - Scan imports and string literals for known service patterns:
     - `import ollama` or `localhost:11434` -> `{name: "ollama", url: "http://localhost:11434"}`
     - `import chromadb` -> `{name: "chromadb", url: "http://localhost:8000"}`
     - `import pinecone` -> `{name: "pinecone", config_required: true}`
     - `import redis` or `localhost:6379` -> `{name: "redis", url: "redis://localhost:6379"}`
     - `import psycopg2` or `asyncpg` or `sqlalchemy` -> `{name: "postgresql"}`
     - `import pymongo` -> `{name: "mongodb"}`
   - Return list of detected services

2. **Modify `src/kinnoo/import_command.py`**:
   - Include detected services in generated kinnoo.yaml under `services:` field
   - Preflight checks will then verify these services are reachable

3. **Test**: Scan `vanilla-python-reze-agent` code and verify PostgreSQL dependency is detected. Scan `openclaw-ollama-extension-agent` and verify Ollama is detected.

### Tests
- test396: Verify service pattern detection finds Ollama/PostgreSQL/Redis imports
- test397: Verify detected services are included in generated kinnoo.yaml

---

## task276: PydanticAI Dependency Injection (deps) Support

### Target agents
- pydanticai-bank-support-agent
- pydanticai-flight-booking-agent
- pydantic-ai-pydantic-ai-agent

### Implementation plan

1. **Modify `src/kinnoo/analyzer.py`**:
   - Scan for `Agent(... deps_type=...)` pattern in PydanticAI agents
   - Try to extract the deps class name and its fields (Pydantic model)
   - Set `inputs.type: json` when deps injection is detected
   - Add `deps_type: ClassName` to analysis metadata

2. **Validate existing --json-input flow**:
   - Ensure `kinnoo run <agent> --json-input '{"customer_id": 123}'` passes through correctly
   - The agent's entrypoint must unpack JSON to construct the deps object
   - If the agent lacks this unpacking logic, the auto-wrapper (task269) should handle it

3. **Test**: Run `pydanticai-bank-support-agent` with `--json-input '{"customer_id": 123}'` and verify the JSON reaches the agent correctly (even if the agent itself errors due to missing DB -- kinnoo's job is pass-through).

### Tests
- test398: Verify analyzer detects PydanticAI deps_type pattern
- test399: Verify --json-input correctly passes structured data to PydanticAI agent

---

## task277: End-to-End Validation with Representative Agents

### Target agents (pick 1-2 from each supported pattern)
- Python script: pydanticai-roulette-wheel-agent, openai-agents-hello-world
- Multi-file: openai-agents-customer-service or openai-agents-sdk-customer-service
- MCP server: mcp-server-time-server or mcp-servers-minesweeper-example  
- MCP client: mcp-client-streamable-basic-client or agents-with-mcp-client-code-basic-client-demo
- OpenClaw plugin: openclaw-diffs-extension-agent
- Node.js/TS: vanilla-typescript-easy-agent (if task273 is done)
- PydanticAI multi-file: pydantic-ai-pydantic-ai-agent

### Implementation plan

1. For each representative agent:
   - Run `kinnoo import <agent-dir>`
   - Verify kinnoo.yaml is generated with correct fields
   - Run `kinnoo pack <agent-dir>`
   - Run `kinnoo install <archive>.kno`
   - Run `kinnoo run <installed-agent> "test input"`
   - Document results: PASS (agent runs), PARTIAL (kinnoo works but agent errors), or FAIL (kinnoo error)

2. Fix any kinnoo-side issues discovered during E2E testing.

3. Write results into a test report section in this file.

### Tests
- test400: E2E import-pack-install-run for a simple Python script agent (one-shot)
- test401: E2E import-pack-install-run for an MCP server agent


---

# ADDENDUM: scratch-2 New Task Handoff Notes

## task278: Streamlit/Gradio UI Agent Support

### Target agents (from scratch-2)
- ashishpatel26-500-ai-agents-projects-harshhh28-hia (streamlit-app)
- ashishpatel26-500-ai-agents-projects-hqanhh-edugpt (gradio-app)
- ashishpatel26-500-ai-agents-projects-nirbar1985-ai-travel-agent (streamlit-app)
- awesomelistsio-awesome-ai-agents-jgravelle-autogroq (streamlit-app)
- awesomelistsio-awesome-ai-agents-josefdc-imageagent (streamlit-app)
- kyrolabs-awesome-agents-aymenfurter-microagents (gradio-app)
- kyrolabs-awesome-agents-brekkylab-ailoy (gradio-app)
- kyrolabs-awesome-agents-geekan-metagpt (streamlit-app)
- kyrolabs-awesome-agents-openbmb-repoagent (gradio-app)

### Implementation plan

1. **Modify `src/kinnoo/analyzer.py`** — Add UI framework detection:
   - After existing framework detection, scan Python files for Streamlit/Gradio imports
   - Look for `import streamlit as st` or `from streamlit` → set `ui_framework: streamlit`
   - Look for `import gradio as gr` or `from gradio` → set `ui_framework: gradio`
   - Confirm app pattern:
     - Streamlit: `st.chat_input(`, `st.text_input(`, `st.title(`, `st.write(`
     - Gradio: `gr.Interface(`, `gr.Blocks(`, `gr.ChatInterface(`, `.launch(`
   - Set `entrypoint_type: "ui-app"` with `ui_framework` and `ui_entrypoint` fields

2. **Modify `src/kinnoo/import_command.py`** — Generate kinnoo.yaml for UI agents:
   - When `entrypoint_type == "ui-app"`:
     - If Streamlit: set `runtime.type: daemon`, `runtime.run_command: "streamlit run <app.py> --server.port ${PORT:-8501}"`
     - If Gradio: set `runtime.type: daemon` (Gradio scripts auto-launch on port 7860)
   - Add `runtime.ports: [8501]` for Streamlit or `runtime.ports: [7860]` for Gradio

3. **Modify `src/kinnoo/run_command.py`** — Handle UI run commands:
   - If `runtime.run_command` is set, use it instead of `python <entrypoint>`
   - Support environment variable substitution in run_command (e.g., `${PORT:-8501}`)
   - Set health check to `http://localhost:<port>` for daemon verification

4. **Test with agents**: 
   - Import `nirbar1985-ai-travel-agent` (Streamlit + LangGraph)
   - Verify kinnoo.yaml has `runtime.type: daemon` and correct run_command
   - Import `aymenfurter-microagents` (Gradio + OpenAI)
   - Verify Gradio daemon detection

### Tests
- test402: Verify analyzer detects Streamlit import and sets ui_framework
- test403: Verify analyzer detects Gradio import and sets ui_framework
- test404: Verify kinnoo.yaml generation sets daemon type for Streamlit agents
- test405: Verify kinnoo run uses 'streamlit run' command for Streamlit agents

---

## task279: Extended Framework Detection (CrewAI, Swarm, Agno, etc.)

### Target agents (from scratch-2)
- ashishpatel26-500-ai-agents-projects-awesomelistsio-awesome-ai-agents-agno-agi-agno (Agno/Phi)
- ashishpatel26-500-ai-agents-projects-crewaiinc-crewai-examples (CrewAI orchestration)
- ashishpatel26-500-ai-agents-projects-kyrolabs-awesome-agents-microsoft-autogen (AutoGen)
- awesomelistsio-awesome-ai-agents-huggingface-smolagents (SmolAgents)
- awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-microsoft-semantic-kernel (Semantic Kernel)
- awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-openai-swarm (OpenAI Swarm)
- awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-phidatahq-phidata (Agno/Phi)
- awesomelistsio-awesome-ai-agents-run-llama-llama-index (LlamaIndex SDK)
- kyrolabs-awesome-agents-doriandarko-claude-engineer (Anthropic client)
- kyrolabs-awesome-agents-jerryjliu-llama-index (LlamaIndex SDK)
- kyrolabs-awesome-agents-liu-hy-genomas (Anthropic client)
- kyrolabs-awesome-agents-vectara-py-vectara-agentic (LlamaIndex SDK)

### Implementation plan

1. **Modify `src/kinnoo/analyzer.py`** — Extend `_detect_framework()`:
   - Add detection patterns for 9 new frameworks. For each, scan imports:
     ```python
     FRAMEWORK_IMPORTS = {
         "crewai": ["from crewai import", "import crewai"],
         "swarm": ["from swarm import", "import swarm"],
         "agno": ["from agno import", "from phi import", "from phidata import"],
         "smolagents": ["from smolagents import", "import smolagents"],
         "autogen": ["from autogen import", "import autogen", "from ag2 import"],
         "semantic_kernel": ["from semantic_kernel import", "import semantic_kernel"],
         "metagpt": ["from metagpt import", "import metagpt"],
         "llama_index": ["from llama_index import", "from llama_deploy import"],
         "anthropic": ["from anthropic import", "import anthropic"],
     }
     ```
   - Return `framework: <name>` in analysis result
   - For multi-framework agents (e.g., langchain+crewai), return primary framework + secondary list

2. **Modify `src/kinnoo/import_command.py`** — Framework-aware import:
   - When framework is detected, add to kinnoo.yaml: `metadata.framework: crewai`
   - For CrewAI: detect `Crew(` class and suggest `.kickoff()` as run invocation
   - For Swarm: detect `run_demo_loop(` and suggest CLI wrapper
   - For Agno/Phi: detect cookbook pattern with `run.py` convention

3. **Create `src/kinnoo/wrapper_templates/crewai_wrapper.py.j2`**:
   ```python
   #!/usr/bin/env python3
   import sys
   from {{module}} import {{crew_class}}
   
   if __name__ == "__main__":
       input_text = sys.argv[1] if len(sys.argv) > 1 else ""
       crew = {{crew_class}}(input_text)
       result = crew.run()
       print(result)
   ```

4. **Update `IMPORT_TO_PYPI` mapping** in requirements inference (task272):
   ```python
   "crewai": "crewai",
   "crewai_tools": "crewai-tools",
   "swarm": "openai-swarm",
   "agno": "agno",
   "phi": "phidata",
   "smolagents": "smolagents",
   "autogen": "autogen-agentchat",
   "semantic_kernel": "semantic-kernel",
   "metagpt": "metagpt",
   "llama_index": "llama-index",
   "llama_deploy": "llama-deploy",
   "anthropic": "anthropic",
   ```

5. **Test with agents**:
   - Import `crewaiinc-crewai-examples` — verify CrewAI framework detected
   - Import `openai-swarm` — verify Swarm framework detected
   - Import `agno-agi-agno` — verify Agno framework detected

### Tests
- test406: Verify analyzer detects CrewAI framework from imports
- test407: Verify analyzer detects OpenAI Swarm framework from imports
- test408: Verify analyzer detects Agno/Phi framework from imports
- test409: Verify IMPORT_TO_PYPI mapping includes all new frameworks
