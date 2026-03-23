# Feature 47 — Agent Supportability Summary

## Overview

114 agents in `example-scratch/agents/` were assessed for kinnoo compatibility. This table shows each agent, its supportability level, the commonality of its code pattern, and whether kinnoo will attempt to support it.

### Legend
- **Supportability**: HIGH = already works or minimal changes; MEDIUM = doable with targeted kinnoo improvements; LOW = major work or heavy external deps
- **Commonality**: How many agents in the wild follow this pattern (Very Common > Common > Moderate > Rare)
- **Will Support?**: YES = targeted by a feature47 task; FUTURE = may address later; NO = excluded (malformed, rare, or out of scope)

---

## Agent Supportability Table

| # | Agent Slug | Framework | Supportability | Commonality | Will Support? | Enabling Task | Notes |
|---|-----------|-----------|----------------|-------------|---------------|---------------|-------|
| 1 | langchain-mrkl-agent-base | LangChain | LOW | Very Common | YES | task269 | Class-only, needs auto-wrapper |
| 2 | langchain-self-ask-search-agent | LangChain | LOW | Very Common | YES | task269 | Class-only + search tool |
| 3 | langchain-structured-chat-agent | LangChain | LOW | Very Common | YES | task269 | Class-only, tool-calling |
| 4 | langchain-tool-calling-agent | LangChain | LOW | Very Common | YES | task269 | Simplest LangChain to wrap |
| 5 | langchain-openai-functions-multi-agent | LangChain | LOW | Common | YES | task269 | Parallel functions |
| 6 | langchain-openai-assistant-agent | LangChain | LOW | Common | YES | task269 | Stateful/async |
| 7 | langgraph-customer-support-graph | LangGraph | LOW | Very Common | YES | task270 | Notebook only |
| 8 | langgraph-hierarchical-agent-teams | LangGraph | LOW | Very Common | YES | task270 | Notebook only |
| 9 | langgraph-react-from-scratch | LangGraph | LOW | Very Common | YES | task270 | Notebook only |
| 10 | langgraph-tool-calling-graph | LangGraph | LOW | Very Common | YES | task270 | Notebook only |
| 11 | langgraph-web-voyager | LangGraph | LOW | Very Common | YES | task270 | Notebook only |
| 12 | langgraph-20-real-world-projects | LangGraph | MEDIUM | Common | YES | task271, task272 | Nested main.py |
| 13 | langgraph-multi-agent-router | LangGraph | MEDIUM | Common | YES | task271, task272 | Multi-framework deps |
| 14 | langgraph-deep-agents-harness | LangGraph | MEDIUM | Common | YES | task271 | Deeply nested entrypoint |
| 15 | pydanticai-weather-agent | PydanticAI | HIGH | Very Common | YES | task277 | Already works |
| 16 | pydanticai-roulette-wheel-agent | PydanticAI | HIGH | Very Common | YES | task277 | Already works |
| 17 | pydanticai-bank-support-agent | PydanticAI | MEDIUM | Very Common | YES | task276 | Needs JSON input for deps |
| 18 | pydanticai-flight-booking-agent | PydanticAI | MEDIUM | Common | YES | task276 | Needs JSON input |
| 19 | pydanticai-rag-agent | PydanticAI | LOW | Common | FUTURE | -- | Requires vector DB |
| 20 | pydanticai-data-analyst-agent | PydanticAI | MEDIUM | Common | FUTURE | -- | External data sources |
| 21 | pydantic-ai-official-bank-example | PydanticAI | HIGH | Common | YES | task277 | Multiple examples with __main__ |
| 22 | pydantic-ai-pydantic-ai-agent | PydanticAI | HIGH | Common | YES | task277 | Well-structured multi-file |
| 23 | pydantic-ai-rag-with-pydantic | PydanticAI | HIGH | Common | YES | task277 | Multiple examples |
| 24 | pydantic-ai-github-agent | PydanticAI | MEDIUM | Common | FUTURE | -- | Eval examples |
| 25 | pydantic-ai-pydantic-ai-history | PydanticAI | LOW | Moderate | NO | -- | Library, not agent |
| 26 | pydantic-ai-serverless-agents | PydanticAI | LOW | Common | NO | -- | Lambda pattern |
| 27 | openai-agents-hello-world | OpenAI SDK | HIGH | Very Common | YES | task274, task277 | Hardcoded input |
| 28 | openai-agents-customer-service | OpenAI SDK | HIGH | Very Common | YES | task277 | Well-structured |
| 29 | openai-agents-message-filter-handoff | OpenAI SDK | HIGH | Common | YES | task277 | Handoff pattern |
| 30 | openai-agents-research-bot | OpenAI SDK | HIGH | Common | YES | task271, task277 | source/main.py |
| 31 | openai-agents-financial-research-agent | OpenAI SDK | HIGH | Common | YES | task271, task277 | source/main.py |
| 32 | openai-agents-basic-tools | OpenAI SDK | LOW | Common | YES | task269 | Library, needs wrapper |
| 33 | openai-agents-sdk-agent-search-tools | OpenAI SDK | HIGH | Common | YES | task274, task277 | Async examples |
| 34 | openai-agents-sdk-customer-service | OpenAI SDK | HIGH | Common | YES | task271, task277 | python-backend/main.py |
| 35 | openai-agents-sdk-function-tool-demo | OpenAI SDK | HIGH | Common | YES | task277 | Standard example |
| 36 | openai-agents-sdk-streaming-agent | OpenAI SDK | MEDIUM | Common | FUTURE | -- | Voice streaming |
| 37 | openai-agents-sdk-temporal-demos | OpenAI SDK | LOW | Moderate | NO | -- | Needs Temporal server |
| 38 | openai-agents-sdk-openai-sdk-knowledge | OpenAI SDK | MEDIUM | Common | YES | task273 | TypeScript agent |
| 39 | openai-agents-sdk-realtime-agents | OpenAI SDK | MEDIUM | Common | FUTURE | -- | Next.js app |
| 40 | openclaw-diffs-extension-agent | OpenClaw | HIGH | Moderate | YES | task277 | Already supported via daemon |
| 41 | openclaw-ollama-extension-agent | OpenClaw | HIGH | Moderate | YES | task275, task277 | Needs Ollama service decl |
| 42 | openclaw-llm-task-extension-agent | OpenClaw | HIGH | Moderate | YES | task277 | Standard extension |
| 43 | openclaw-lobster-extension-agent | OpenClaw | MEDIUM | Moderate | FUTURE | -- | External Lobster dep |
| 44 | openclaw-open-prose-extension-agent | OpenClaw | HIGH | Moderate | YES | task277 | Skills pattern |
| 45 | openclaw-voice-call-extension-agent | OpenClaw | LOW | Moderate | NO | -- | Heavy telephony deps |
| 46 | openclaw-build-your-own | OpenClaw | MEDIUM | Common | YES | task271 | Deeply nested Python CLI |
| 47 | openclaw-nanobot-assistant | OpenClaw | MEDIUM | Moderate | YES | task273 | TS bridge agent |
| 48 | openclaw-openclaw-agents-kit | OpenClaw | LOW | Rare | NO | -- | Shell-based setup |
| 49 | openclaw-openclaw-termux | OpenClaw | LOW | Rare | NO | -- | Termux-specific |
| 50 | openclaw-selfclaw-identity | OpenClaw | LOW | Rare | NO | -- | Identity server |
| 51 | openclaw-zeroclaw | OpenClaw | LOW | Rare | NO | -- | Pico firmware |
| 52 | mcp-client-stdio-client | MCP Client | MEDIUM | Common | YES | task277 | Needs MCP server |
| 53 | mcp-client-completion-client | MCP Client | HIGH | Common | YES | task277 | Has __main__ |
| 54 | mcp-client-streamable-basic-client | MCP Client | HIGH | Common | YES | task277 | Has __main__ |
| 55 | mcp-client-pagination-client | MCP Client | HIGH | Common | YES | task277 | Has __main__ |
| 56 | mcp-client-oauth-client | MCP Client | MEDIUM | Common | FUTURE | -- | OAuth setup |
| 57 | mcp-client-url-elicitation-client | MCP Client | MEDIUM | Common | FUTURE | -- | URL elicitation |
| 58 | agents-with-mcp-client-code-basic-client-demo | MCP Client | HIGH | Common | YES | task277 | Clean example |
| 59 | agents-with-mcp-client-code-simple-scraping-agent | MCP Client | HIGH | Common | YES | task277 | Well-structured |
| 60 | agents-with-mcp-client-code-enrichmcp-orm | MCP Client | MEDIUM | Common | FUTURE | -- | Multi-framework |
| 61 | agents-with-mcp-client-code-mcp-agent-loop | MCP Client | MEDIUM | Common | FUTURE | -- | Complex loop |
| 62 | agents-with-mcp-client-code-langchainjs-burger | MCP Client | MEDIUM | Common | YES | task273 | TS MCP client |
| 63 | agents-with-mcp-client-code-mcp-browser-agent | MCP Client | MEDIUM | Common | YES | task273 | TS browser agent |
| 64 | agents-with-mcp-client-code-opencode | MCP Client | MEDIUM | Common | YES | task273 | TS editor |
| 65 | mcp-server-fetch-server | MCP Server | HIGH | Very Common | YES | task277 | Already supported |
| 66 | mcp-server-git-server | MCP Server | HIGH | Very Common | YES | task277 | Already supported |
| 67 | mcp-server-time-server | MCP Server | HIGH | Very Common | YES | task277 | Has __main__ |
| 68 | mcp-server-filesystem-server | MCP Server | MEDIUM | Very Common | YES | task273 | TS MCP server |
| 69 | mcp-server-memory-server | MCP Server | MEDIUM | Very Common | YES | task273 | TS MCP server |
| 70 | mcp-server-sequentialthinking-server | MCP Server | MEDIUM | Very Common | YES | task273 | TS MCP server |
| 71 | mcp-servers-minesweeper-example | MCP Server | HIGH | Common | YES | task277 | Python servers with __main__ |
| 72 | mcp-servers-tavily-search | MCP Server | MEDIUM | Common | YES | task273 | TS, Tavily API key |
| 73 | mcp-servers-notion-mcp | MCP Server | MEDIUM | Common | YES | task273 | TS, Notion API key |
| 74 | vanilla-javascript-avr-llm-assistant | Vanilla JS | MEDIUM | Common | YES | task273 | Node.js voice agent |
| 75 | vanilla-javascript-multis-chat-agent | Vanilla JS | MEDIUM | Common | YES | task273 | Multi-platform chat |
| 76 | vanilla-javascript-ntfy-mcp-server | Vanilla JS | HIGH | Common | YES | task273, task277 | Pre-built MCP server |
| 77 | vanilla-javascript-influxdb-mcp | Vanilla JS | MEDIUM | Common | YES | task273 | TS MCP server |
| 78 | vanilla-javascript-openai-proxy-shim | Vanilla JS | MEDIUM | Common | YES | task273 | OpenAI proxy |
| 79 | vanilla-python-minimal-research | Vanilla Python | HIGH | Very Common | YES | task277 | GPT Researcher |
| 80 | vanilla-python-octoagent | Vanilla Python | HIGH | Very Common | YES | task271, task277 | CLI in src/ |
| 81 | vanilla-python-simple-ai-agents | Vanilla Python | HIGH | Common | YES | task277 | Multiple examples |
| 82 | vanilla-python-openai-patterns | Vanilla Python | HIGH | Common | YES | task277 | Pattern demos |
| 83 | vanilla-python-verimap | Vanilla Python | MEDIUM | Common | YES | task271, task272 | Config-driven engine |
| 84 | vanilla-python-reze-agent | Vanilla Python | MEDIUM | Common | YES | task275 | FastAPI + DB |
| 85 | vanilla-python-vanilla-ai-agents | Vanilla Python | MEDIUM | Common | FUTURE | -- | Azure samples |
| 86 | vanilla-python-agent-loop | Vanilla Python | MEDIUM | Common | YES | task272 | No __main__ in main.py |
| 87 | vanilla-python-pc-agent-loop | Vanilla Python | LOW | Rare | NO | -- | Spaghetti code, OS deps |
| 88 | vanilla-typescript-building-an-agent | Vanilla TS | MEDIUM | Common | YES | task273 | React/hooks pattern |
| 89 | vanilla-typescript-easy-agent | Vanilla TS | HIGH | Common | YES | task273, task277 | CLI + Express |
| 90 | vanilla-typescript-ts-agents-framework | Vanilla TS | HIGH | Common | YES | task273, task277 | Multi-agent |
| 91 | vanilla-typescript-social-media-agent | Vanilla TS | MEDIUM | Common | YES | task273 | Social media |
| 92 | vanilla-typescript-manifest-bun-ts | Vanilla TS | LOW | Moderate | NO | -- | Requires Bun |
| 93 | vanilla-typescript-openai-realtime-ts | Vanilla TS | LOW | Common | NO | -- | Full web app |

### Excluded (Malformed) -- 21 agents

| # | Agent Slug | Reason |
|---|-----------|--------|
| 94 | pydantic-ai-chess-agent | Docs hooks only |
| 95 | pydantic-ai-mcp-tool-agent | Docs hooks only |
| 96 | pydantic-ai-streaming-agent | Docs hooks only |
| 97 | langgraph-adaptive-rag-agent | SDK CLI internals |
| 98 | langgraph-langgraph-quickstart | SDK CLI internals |
| 99 | langgraph-plan-and-execute | SDK CLI internals |
| 100 | langgraph-self-correction-agent | SDK CLI internals |
| 101 | langgraph-storm-agent | SDK CLI internals |
| 102 | openai-agents-sdk-guardrails-demo | SDK source code |
| 103 | openai-agents-sdk-official-python-sdk | SDK source code |
| 104 | openai-agents-sdk-workflow-lab | SDK source duplicate |
| 105 | openclaw-easyclaw-ui | UI toolkit |
| 106 | openclaw-openclaw-core | Framework source |
| 107 | mcp-servers-official-mcp-servers | Monorepo root |
| 108 | mcp-servers-playwright-mcp | Monorepo |
| 109 | mcp-servers-context7-docs | Monorepo |
| 110 | agents-with-mcp-client-code-mcp-for-beginners | Incomplete download |
| 111 | agents-with-mcp-client-code-openai-mcp-client | SDK source |
| 112 | vanilla-javascript-openai-cookbook-js | Cookbook fragments |
| 113 | vanilla-typescript-vercel-ai-sdk-examples | SDK source packages |
| 114 | vanilla-typescript-agentica-framework | Test scaffolding |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total agents analyzed | 114 |
| Real agents (not malformed) | 93 |
| Malformed / excluded | 21 |
| HIGH supportability | 45 |
| MEDIUM supportability | 33 |
| LOW supportability | 15 |
| Will support (YES) | 72 |
| Future support (FUTURE) | 11 |
| Will not support (NO) | 10 |
| Enabling tasks created | 9 (task269-task277) |


---

# ADDENDUM: example-scratch-2 Agent Supportability

## scratch-2 Agent Supportability Table

| # | Agent Slug | Framework | Supportability | Commonality | Will Support? | Enabling Task | Notes |
|---|-----------|-----------|----------------|-------------|---------------|---------------|-------|
| 115 | ashishpatel26-500-ai-agents-projects-ahmadvh-ai-agents-for-medical-diagnostics | langchain | LOW | Moderate | NO | -- | SDK/library fragment, no entrypoint |
| 116 | ashishpatel26-500-ai-agents-projects-aleksnestu-ai-real-estate-assistant | fastapi, langchain | MEDIUM | Very Common | YES | task271, task275, task272 | FastAPI server, entry: apps/api/api/main.py |
| 117 | ashishpatel26-500-ai-agents-projects-awesomelistsio-awesome-ai-agents-agno-agi-agno | agno_phi | MEDIUM | Common | YES | task279, task271 | Agno/Phi framework, 46 code files, entry: cookbook/01_demo/run.py |
| 118 | ashishpatel26-500-ai-agents-projects-awesomelistsio-awesome-ai-agents-langchain-ai-langgraph | langchain, langgraph | LOW | Common | FUTURE | task269 | Large library (22 code files), needs auto-wrapper |
| 119 | ashishpatel26-500-ai-agents-projects-crewaiinc-crewai-examples | crewai, langchain | MEDIUM | Common | YES | task279, task272 | CrewAI crew pattern with __main__, entry: crews/trip_planner/main.py |
| 120 | ashishpatel26-500-ai-agents-projects-crosleythomas-mirrorgpt | langchain | MEDIUM | Very Common | YES | task271, task272 | LangChain/LangGraph agent, entry: mirror/mirror_agent/agent.py, no __main__ |
| 121 | ashishpatel26-500-ai-agents-projects-firica-legalai | langchain, streamlit | HIGH | Very Common | YES | task277 | LangChain/LangGraph agent, entry: agent.py, has __main__ |
| 122 | ashishpatel26-500-ai-agents-projects-harshhh28-hia | langchain, streamlit | MEDIUM | Common | YES | task278 | Streamlit UI app, has __main__, no deps file |
| 123 | ashishpatel26-500-ai-agents-projects-hoanganhvu123-shoppinggpt | flask, langchain | MEDIUM | Common | YES | task275 | Flask server, entry: app.py, deps: requirements.txt |
| 124 | ashishpatel26-500-ai-agents-projects-hqanhh-edugpt | gradio, langchain | MEDIUM | Common | YES | task278 | Gradio UI app, no deps file |
| 125 | ashishpatel26-500-ai-agents-projects-kyrolabs-awesome-agents-microsoft-autogen | autogen | MEDIUM | Common | YES | task279, task271 | Microsoft AutoGen, entry: python/samples/core_chess_game/main.py |
| 126 | ashishpatel26-500-ai-agents-projects-microsoft-optiguide | openai | MEDIUM | Very Common | YES | task271, task277, task272 | OpenAI SDK agent, entry: milp-evolve/src/milp_evolve_llm/main.py, has __main__ |
| 127 | ashishpatel26-500-ai-agents-projects-microsoft-recai | openai | MEDIUM | Very Common | YES | task271, task277 | OpenAI SDK agent, entry: RecLM-gen/main.py, has __main__ |
| 128 | ashishpatel26-500-ai-agents-projects-mingyuj666-stockagent | openai | HIGH | Very Common | YES | task277 | OpenAI SDK agent, entry: agent.py, has __main__ |
| 129 | ashishpatel26-500-ai-agents-projects-mohammed97ashraf-llm-agri-bot | flask, openai | MEDIUM | Common | YES | task275 | Flask server, entry: app.py, deps: requirements.txt |
| 130 | ashishpatel26-500-ai-agents-projects-nirbar1985-ai-travel-agent | langchain, langgraph, streamlit | MEDIUM | Common | YES | task278 | Streamlit UI app, has __main__, deps: pyproject.toml |
| 131 | ashishpatel26-500-ai-agents-projects-onjas-buidl-llm-agent-game | flask, langchain | MEDIUM | Common | YES | task271, task275 | Flask server, entry: backend/app.py, deps: backend/requirements.txt |
| 132 | awesomelistsio-awesome-ai-agents-agno-agi-agent-ui | vanilla | LOW | Moderate | NO | -- | SDK/library fragment, no entrypoint |
| 133 | awesomelistsio-awesome-ai-agents-bytedance-deer-flow | fastapi | MEDIUM | Very Common | YES | task271, task275, task272 | FastAPI server, entry: docker/provisioner/app.py |
| 134 | awesomelistsio-awesome-ai-agents-crewai-inc-crewai | crewai | LOW | Moderate | NO | -- | SDK/library fragment, no entrypoint |
| 135 | awesomelistsio-awesome-ai-agents-huggingface-smolagents | smolagents | MEDIUM | Moderate | YES | task279, task275 | HuggingFace SmolAgents, entry: examples/server/main.py |
| 136 | awesomelistsio-awesome-ai-agents-jgravelle-autogroq | anthropic, streamlit | MEDIUM | Common | YES | task278 | Streamlit UI app, has __main__, no deps file |
| 137 | awesomelistsio-awesome-ai-agents-josefdc-imageagent | langchain, langgraph, streamlit | MEDIUM | Common | YES | task278 | Streamlit UI app, has __main__, deps: requirements.txt |
| 138 | awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-botpress-botpress | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: bots/clog/src/index.ts |
| 139 | awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-mastra-ai-mastra | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: stores/pg/src/index.ts |
| 140 | awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-microsoft-semantic-kernel | semantic_kernel | MEDIUM | Common | FUTURE | task279 | Microsoft Semantic Kernel, samples only, no clear entrypoint |
| 141 | awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-openai-swarm | swarm | MEDIUM | Common | YES | task279, task271 | OpenAI Swarm multi-agent, entry: examples/airline/main.py |
| 142 | awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-phidatahq-phidata | agno_phi | MEDIUM | Common | YES | task279, task271 | Agno/Phi framework, 46 code files, entry: cookbook/01_demo/run.py |
| 143 | awesomelistsio-awesome-ai-agents-langchain-ai-langchain | langchain | LOW | Moderate | NO | -- | SDK/library fragment, no entrypoint |
| 144 | awesomelistsio-awesome-ai-agents-pydantic-pydantic-ai | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: docs/.hooks/main.py |
| 145 | awesomelistsio-awesome-ai-agents-rasahq-rasa | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: rasa/cli/run.py, no __main__ |
| 146 | awesomelistsio-awesome-ai-agents-run-llama-llama-index | llama_index | LOW | Common | FUTURE | task269, task279 | LlamaIndex SDK, no clear entrypoint |
| 147 | kyrolabs-awesome-agents-aden-hive-hive | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: core/framework/schemas/run.py, no __main__ |
| 148 | kyrolabs-awesome-agents-agent-field-agentfield | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: examples/python_agent_nodes/agentic_rag/main.py |
| 149 | kyrolabs-awesome-agents-agentdock-agentdock | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: src/lib/index.ts |
| 150 | kyrolabs-awesome-agents-agentset-ai-agentset | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: packages/db/src/index.ts |
| 151 | kyrolabs-awesome-agents-all-hands-ai-openhands | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: openhands/core/main.py |
| 152 | kyrolabs-awesome-agents-aymenfurter-microagents | gradio, openai | MEDIUM | Common | YES | task278 | Gradio UI app, has __main__, deps: requirements.txt |
| 153 | kyrolabs-awesome-agents-baidu-baige-loongflow | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: tests/ccsdk/agent.py, no __main__ |
| 154 | kyrolabs-awesome-agents-blockpipe-blockagi | fastapi, langchain | MEDIUM | Very Common | YES | task275 | FastAPI server, entry: main.py, deps: pyproject.toml; ui/package.json |
| 155 | kyrolabs-awesome-agents-brekkylab-ailoy | gradio | MEDIUM | Common | YES | task278 | Gradio UI app, deps: examples/gradio_chatbot/pyproject.toml |
| 156 | kyrolabs-awesome-agents-charlie85270-dorothy | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: mcp-x/src/index.ts |
| 157 | kyrolabs-awesome-agents-cline-cline | streamlit | MEDIUM | Common | YES | task271, task274 | Has __main__ guards but no standard entrypoint found, needs investigation |
| 158 | kyrolabs-awesome-agents-csunny-db-gpt | fastapi | LOW | Very Common | FUTURE | task275, task272 | FastAPI server, no clear entrypoint |
| 159 | kyrolabs-awesome-agents-deepset-ai-haystack | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: haystack/components/agents/agent.py, no __main__ |
| 160 | kyrolabs-awesome-agents-doriandarko-claude-engineer | anthropic | MEDIUM | Common | YES | task279, task272 | Anthropic client agent, entry: Claude-Eng-v2/main.py |
| 161 | kyrolabs-awesome-agents-doriandarko-maestro | flask | MEDIUM | Common | YES | task271, task275 | Flask server, entry: flask_app/app.py, deps: flask_app/requirements.txt |
| 162 | kyrolabs-awesome-agents-dust-tt-dust | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: sdks/js/src/index.ts |
| 163 | kyrolabs-awesome-agents-e2b-dev-e2b | vanilla | LOW | Common | FUTURE | task269 | Large library (16 code files), needs auto-wrapper |
| 164 | kyrolabs-awesome-agents-evoagentx-evoagentx | fastapi | MEDIUM | Very Common | YES | task271, task275 | FastAPI server, entry: evoagentx/app/main.py, deps: evoagentx/app/requirements.txt |
| 165 | kyrolabs-awesome-agents-fetchai-uagents | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: python/src/uagents/agent.py, no __main__ |
| 166 | kyrolabs-awesome-agents-geekan-metagpt | metagpt, streamlit | MEDIUM | Common | YES | task278 | Streamlit UI app, has __main__, no deps file |
| 167 | kyrolabs-awesome-agents-giselles-ai-giselle | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: packages/rag/src/index.ts |
| 168 | kyrolabs-awesome-agents-gobii-ai-gobii-platform | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: scripts/prototype/agent.py |
| 169 | kyrolabs-awesome-agents-hkuds-nanobot | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: bridge/src/index.ts |
| 170 | kyrolabs-awesome-agents-homanp-superagent | anthropic, openai | LOW | Common | FUTURE | task269 | Large library (22 code files), needs auto-wrapper |
| 171 | kyrolabs-awesome-agents-hwchase17-langchain | langchain | LOW | Moderate | NO | -- | SDK/library fragment, no entrypoint |
| 172 | kyrolabs-awesome-agents-hypermodeinc-modus | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: cli/src/index.ts |
| 173 | kyrolabs-awesome-agents-internlm-lagent | fastapi | MEDIUM | Very Common | YES | task271, task275, task272 | FastAPI server, entry: lagent/distributed/http_serve/app.py |
| 174 | kyrolabs-awesome-agents-jarrycyx-openlens-ai | langchain, langgraph | MEDIUM | Very Common | YES | task271, task277, task272 | LangChain/LangGraph agent, entry: openlens_ai/main.py, has __main__ |
| 175 | kyrolabs-awesome-agents-jcanizalez-vibegrid | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: src/main/index.ts |
| 176 | kyrolabs-awesome-agents-jerryjliu-llama-index | llama_index | LOW | Common | FUTURE | task269, task279 | LlamaIndex SDK, no clear entrypoint |
| 177 | kyrolabs-awesome-agents-joaomdmoura-crewai | crewai | LOW | Moderate | NO | -- | SDK/library fragment, no entrypoint |
| 178 | kyrolabs-awesome-agents-jonathan-adly-agentrun | fastapi | MEDIUM | Very Common | YES | task271, task275, task272 | FastAPI server, entry: agentrun-api/src/api/main.py |
| 179 | kyrolabs-awesome-agents-juspay-neurolink | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: src/cli/index.ts |
| 180 | kyrolabs-awesome-agents-kayba-ai-agentic-context-engine | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: ace_next/steps/agent.py, no __main__ |
| 181 | kyrolabs-awesome-agents-kirill89-reviewcerberus | langchain, langgraph | MEDIUM | Very Common | YES | task271, task277, task272 | LangChain/LangGraph agent, entry: src/main.py, has __main__ |
| 182 | kyrolabs-awesome-agents-kyegomez-swarms | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: swarms/cli/main.py |
| 183 | kyrolabs-awesome-agents-l33tdawg-sage | vanilla | LOW | Moderate | NO | -- | SDK/library fragment, no entrypoint |
| 184 | kyrolabs-awesome-agents-landing-ai-vision-agent | fastapi | MEDIUM | Very Common | YES | task271, task275 | FastAPI server, entry: examples/chat/run.py, deps: examples/chat/requirements.txt |
| 185 | kyrolabs-awesome-agents-litanlitudan-skyagi | langchain | LOW | Moderate | NO | -- | SDK/library fragment, no entrypoint |
| 186 | kyrolabs-awesome-agents-littlebearapps-untether | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: src/untether/cli/run.py |
| 187 | kyrolabs-awesome-agents-liu-hy-genomas | anthropic, openai | MEDIUM | Common | YES | task279, task272 | Anthropic client agent, entry: main.py |
| 188 | kyrolabs-awesome-agents-maximilian-winter-llama-cpp-agent | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: examples/07_Memory/MemoryAssistant/main.py, no __main__ |
| 189 | kyrolabs-awesome-agents-meta-llama-llama-agentic-system | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: examples/DocQA/app.py |
| 190 | kyrolabs-awesome-agents-microsoft-taskweaver | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: playground/UI/app.py |
| 191 | kyrolabs-awesome-agents-minedojo-voyager | vanilla | LOW | Common | FUTURE | task269 | Large library (8 code files), needs auto-wrapper |
| 192 | kyrolabs-awesome-agents-miurla-babyagi-ui | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: src/hooks/index.ts |
| 193 | kyrolabs-awesome-agents-mnfst-manifest | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: packages/openclaw-plugin/src/index.ts |
| 194 | kyrolabs-awesome-agents-modelscope-agentscope | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: examples/agent/a2a_agent/main.py, no __main__ |
| 195 | kyrolabs-awesome-agents-mpaepper-llm-agents | openai | MEDIUM | Very Common | YES | task271, task277, task272 | OpenAI SDK agent, entry: llm_agents/agent.py, has __main__ |
| 196 | kyrolabs-awesome-agents-nilsherzig-llocalsearch | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: src/lib/index.ts |
| 197 | kyrolabs-awesome-agents-openbmb-repoagent | gradio, llama_index | MEDIUM | Common | YES | task278 | Gradio UI app, has __main__, no deps file |
| 198 | kyrolabs-awesome-agents-openbmb-xagent | fastapi | MEDIUM | Very Common | YES | task271, task275, task272 | FastAPI server, entry: XAgentServer/application/main.py |
| 199 | kyrolabs-awesome-agents-paulpierre-rasagpt | fastapi, langchain, openai | MEDIUM | Very Common | YES | task271, task275 | FastAPI server, entry: app/api/main.py, deps: app/api/requirements.txt |
| 200 | kyrolabs-awesome-agents-pipecat-ai-pipecat | fastapi | MEDIUM | Very Common | YES | task271, task275, task272 | FastAPI server, entry: src/pipecat/runner/run.py |
| 201 | kyrolabs-awesome-agents-princeton-nlp-swe-agent | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: sweagent/run/run.py |
| 202 | kyrolabs-awesome-agents-promtengineer-localgpt | vanilla | MEDIUM | Very Common | YES | task271, task277 | Python script + __main__, entry: rag_system/main.py |
| 203 | kyrolabs-awesome-agents-reddotrocket-agentup | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: src/agent/cli/main.py |
| 204 | kyrolabs-awesome-agents-reworkd-agentgpt | fastapi | LOW | Moderate | NO | -- | SDK/library fragment, no entrypoint |
| 205 | kyrolabs-awesome-agents-ruc-datalab-deepanalyze | fastapi, openai | MEDIUM | Very Common | YES | task271, task275, task272 | FastAPI server, entry: API/main.py |
| 206 | kyrolabs-awesome-agents-run-llama-llama-agents | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: llama_deploy/cli/run.py |
| 207 | kyrolabs-awesome-agents-saharmor-voice-lab | openai | HIGH | Very Common | YES | task277 | OpenAI SDK agent, entry: main.py, has __main__ |
| 208 | kyrolabs-awesome-agents-samuraigpt-camel-autogpt | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: client/src/index.js |
| 209 | kyrolabs-awesome-agents-simonmesmith-agentflow | openai | HIGH | Very Common | YES | task277 | OpenAI SDK agent, entry: run.py, has __main__ |
| 210 | kyrolabs-awesome-agents-sopaco-cortex-mem | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: examples/@memclaw/plugin/index.ts |
| 211 | kyrolabs-awesome-agents-sst-opencode | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: github/index.ts |
| 212 | kyrolabs-awesome-agents-stitionai-devika | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: src/agents/agent.py, no __main__ |
| 213 | kyrolabs-awesome-agents-strands-agents-sdk-python | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: src/strands/agent/agent.py, no __main__ |
| 214 | kyrolabs-awesome-agents-technion-kishony-lab-data-to-paper | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: src/data_to_paper/scripts/run.py |
| 215 | kyrolabs-awesome-agents-teoslayer-pilotprotocol | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: sdk/python/pilotprotocol/cli.py, no __main__ |
| 216 | kyrolabs-awesome-agents-upsonic-upsonic | fastapi | MEDIUM | Very Common | YES | task271, task275, task272 | FastAPI server, entry: src/upsonic/cli/main.py |
| 217 | kyrolabs-awesome-agents-vectara-open-rag-eval | flask | LOW | Common | FUTURE | task275, task272 | Flask server, no clear entrypoint |
| 218 | kyrolabs-awesome-agents-vectara-py-vectara-agentic | fastapi, llama_index | LOW | Common | FUTURE | task269, task279 | LlamaIndex SDK, no clear entrypoint |
| 219 | kyrolabs-awesome-agents-voicetestdev-voicetest | vanilla | MEDIUM | Common | YES | task271, task274, task272 | Python multi-file, entry: voicetest/tui/app.py, no __main__ |
| 220 | kyrolabs-awesome-agents-voltagent-voltagent | vanilla | MEDIUM | Common | YES | task273 | Node.js/TS agent (vanilla), entry: tools/core/src/index.ts |
| 221 | kyrolabs-awesome-agents-vrsen-agency-swarm | vanilla | MEDIUM | Very Common | YES | task271, task277, task272 | Python script + __main__, entry: src/agency_swarm/cli/main.py |
| 222 | kyrolabs-awesome-agents-xlang-ai-openagents | flask, langchain | MEDIUM | Common | YES | task271, task275 | Flask server, entry: backend/app.py, deps: backend/requirements.txt |
| 223 | kyrolabs-awesome-agents-yifan-song793-restgpt | langchain | HIGH | Very Common | YES | task277, task272 | LangChain/LangGraph agent, entry: run.py, has __main__ |

### Excluded (Monolithic) — 23 agents

| # | Agent Slug | Reason |
|---|-----------|--------|
| 224 | awesomelistsio-awesome-ai-agents-kyrolabs-awesome-agents-ag2ai-ag2 | Monolithic (>50 code files, excluded) |
| 225 | awesomelistsio-awesome-ai-agents-langflow-ai-langflow | Monolithic (>50 code files, excluded) |
| 226 | kyrolabs-awesome-agents-aider-ai-aider | Monolithic (>50 code files, excluded) |
| 227 | kyrolabs-awesome-agents-arize-ai-phoenix | Monolithic (>50 code files, excluded) |
| 228 | kyrolabs-awesome-agents-assafelovic-gpt-researcher | Monolithic (>50 code files, excluded) |
| 229 | kyrolabs-awesome-agents-cpacker-memgpt | Monolithic (>50 code files, excluded) |
| 230 | kyrolabs-awesome-agents-fim-ai-fim-agent | Monolithic (>50 code files, excluded) |
| 231 | kyrolabs-awesome-agents-hpcaitech-colossalai | Monolithic (>50 code files, excluded) |
| 232 | kyrolabs-awesome-agents-iflytek-astron-agent | Monolithic (>50 code files, excluded) |
| 233 | kyrolabs-awesome-agents-imartinez-privategpt | Monolithic (>50 code files, excluded) |
| 234 | kyrolabs-awesome-agents-joinly-ai-joinly | Monolithic (>50 code files, excluded) |
| 235 | kyrolabs-awesome-agents-josh-xt-agent-llm | Monolithic (>50 code files, excluded) |
| 236 | kyrolabs-awesome-agents-kreneskyp-ix | Monolithic (>50 code files, excluded) |
| 237 | kyrolabs-awesome-agents-melih-unsal-demogpt | Monolithic (>50 code files, excluded) |
| 238 | kyrolabs-awesome-agents-mervinpraison-praisonai | Monolithic (>50 code files, excluded) |
| 239 | kyrolabs-awesome-agents-openbmb-agentverse | Monolithic (>50 code files, excluded) |
| 240 | kyrolabs-awesome-agents-openclaw-openclaw | Monolithic (>50 code files, excluded) |
| 241 | kyrolabs-awesome-agents-openonion-connectonion | Monolithic (>50 code files, excluded) |
| 242 | kyrolabs-awesome-agents-pythagora-io-gpt-pilot | Monolithic (>50 code files, excluded) |
| 243 | kyrolabs-awesome-agents-sbusso-claudeclaw | Monolithic (>50 code files, excluded) |
| 244 | kyrolabs-awesome-agents-steel-dev-steel-browser | Monolithic (>50 code files, excluded) |
| 245 | kyrolabs-awesome-agents-trafficguard-nous | Monolithic (>50 code files, excluded) |
| 246 | kyrolabs-awesome-agents-transformeroptimus-superagi | Monolithic (>50 code files, excluded) |

---

## scratch-2 Summary Statistics

| Metric | Count |
|--------|-------|
| Total agents analyzed | 132 |
| Non-monolithic (classified) | 109 |
| Monolithic (excluded) | 23 |
| HIGH supportability | 5 |
| MEDIUM supportability | 86 |
| LOW supportability | 18 |
| Will support (YES) | 90 |
| Future support (FUTURE) | 10 |
| Will not support (NO) | 9 |
| New tasks created | 2 (task278-task279) |

## Combined Statistics (scratch-1 + scratch-2)

| Metric | scratch-1 | scratch-2 | Total |
|--------|-----------|-----------|-------|
| Agents analyzed | 114 | 132 | 246 |
| Real/non-mono agents | 93 | 109 | 202 |
| Excluded | 21 | 23 | 44 |
| HIGH supportability | 45 | 5 | 50 |
| MEDIUM supportability | 33 | 86 | 119 |
| LOW supportability | 15 | 18 | 33 |
| Enabling tasks | 9 | 2 new | 11 (task269-task279) |
