# User Prompt (2026-02-26)

As you say, agents will get more complex (RAG pipelines, multi-tool setups, MCP server dependencies, vector stores, embedding models). So when say V2 should focus on packaging robustness, what does this mean? Elaborate on this. Would I be able to support packaging of the agent you described in your example (“a developer in 2027 who builds a RAG agent with LangGraph / LlamaIndex + ChromaDB + Pinecone + three MCP tools”) ? If not, what should be the minimum agent for which I should be able to support the entire cycle (pack -> install -> run)? In other words, V1 supports pack -> install -> run of a very simple one-shot LLM agent (Gemini, Claude or ChatGPT), so what agents should V2 support? What’s the “goal” of V2? And then in the same manner, what should be the goals for V3, V4, etc? I want to be clear on the goal, so that the features we decide on support the goal and we're not just implementing features because "oh, this is nice to have".

---

# Copilot Response (2026-02-26)

 This is the right question. Let me work through it systematically.

---

## What "Packaging Robustness" Actually Means

In V1, `kinnoo pack` works for the happy path: a simple agent with a few pure-Python dependencies. It breaks or produces unreliable archives in several real-world scenarios:

| Problem | What happens today | Impact |
|---------|-------------------|--------|
| **Transitive deps missing** | `pip wheel --no-deps` only bundles direct deps. If `langchain` requires `pydantic`, `pydantic` is NOT in the archive. | Agent fails on install if the machine doesn't have internet or has different versions |
| **Platform-specific wheels** | Wheels built on macOS ARM won't install on Linux x86. No cross-platform handling. | "Works on my machine" — the exact problem Kinnoo exists to solve |
| **No archive integrity** | No checksum or signature on `.kno` files | Can't verify the archive wasn't tampered with. Blocks trust story. |
| **No size awareness** | Pack doesn't warn or report archive size | A LangChain agent with all transitive deps could be 500MB+ of wheels. User has no visibility. |
| **Brittle archive structure** | Some edge cases in zip handling, no canonical layout validation | Install can fail silently on malformed archives |

"Packaging robustness" means fixing these so that `kinnoo pack` produces an archive that **reliably installs and runs on a different machine.** It's not glamorous work, but it's the foundation.

---

## The Version Goals: What Agent Tier Each Version Supports

Here's how I'd frame it — each version should have a clear **target agent archetype** that defines "done":

### V1 (Complete): The Hello World Agent

**Target archetype:** A one-shot LLM agent with a single API provider.

**Example:** "Ask ChatGPT a question and print the answer"
```
Code: run.py (20 lines)
Dependencies: openai
Secrets: OPENAI_API_KEY (manually set by user)
Data: none
External services: none
```

**What V1 proves:** The pack → install → run cycle works end-to-end for the simplest case. The manifest format is viable. The black-box model works.

**What V1 can't do:** Multiple secrets, dependency reliability across machines, discoverability, any agent complexity beyond "call one LLM."

---

### V2 Goal: The Multi-Tool Agent

**Target archetype:** An agent that uses one LLM provider + 2-3 Python-based tools/libraries, with multiple API keys, shareable via a local registry.

**Example:** "A LangChain agent that answers questions using OpenAI, searches the web with Tavily, and checks the weather with a REST API"
```
Code: run.py + tools/ (100-200 lines)
Dependencies: langchain, openai, tavily-python, requests (+ all transitive deps)
Secrets: OPENAI_API_KEY, TAVILY_API_KEY
Data: none
External services: none (all accessed via Python libraries + API keys)
```

**Why this archetype?** This is the most common "real" agent being built today. Tutorials on LangChain, PydanticAI, Agno — they all look like this. An LLM with a few tool integrations, all accessed through Python packages and API keys. No infrastructure to set up. No vector databases. No MCP servers. Just code, deps, and secrets.

**What V2 must solve to support this:**

1. **Reliable dependency bundling** — transitive deps included, cross-platform awareness (at minimum: warn if platform-specific wheels detected)
2. **Secret declaration + injection** — manifest declares `env_vars: [OPENAI_API_KEY, TAVILY_API_KEY]`, runtime resolves from env → .env file → interactive prompt
3. **Local registry** — `kinnoo publish` stores the archive locally, `kinnoo install agent-name` retrieves it. Version management. This is what turns Kinnoo from a build tool into a package manager.
4. **Inspect + preflight** — before running, show what the agent needs (deps, secrets, Python version). Validate everything is present before execution.
5. **Archive integrity** — checksums so you can verify what you installed is what was published

**What V2 explicitly does NOT need:**
- Vector stores or databases
- MCP server dependencies
- Data file bundling
- Interactive/REPL mode
- Remote registry
- Cross-platform wheel compilation (just detection + warning)
- Container/sandbox isolation

**V2 success test:** A developer on Machine A builds a LangChain+Tavily agent, runs `kinnoo pack && kinnoo publish`. A developer on Machine B (same OS) runs `kinnoo install my-agent && kinnoo run my-agent "What's the weather in NYC?"` — it prompts for API keys, installs deps, and runs successfully. Zero manual setup beyond providing secrets.

---

### V3 Goal: The Connected Agent

**Target archetype:** An agent with external service dependencies — vector stores, MCP tool servers, or databases that exist outside the Python process.

**Example:** "A RAG agent that uses LlamaIndex + Pinecone for retrieval, OpenAI for generation, and a GitHub MCP server for code search"
```
Code: run.py + tools/ + prompts/ (300+ lines)
Dependencies: llama-index, openai, pinecone-client (+ transitive)
Secrets: OPENAI_API_KEY, PINECONE_API_KEY, GITHUB_TOKEN
External services: 
  - Pinecone index at env.PINECONE_INDEX_URL
  - GitHub MCP server (stdio or HTTP)
Data: possibly bundled documents for local RAG, or remote-only
```

**What's new vs. V2:** The agent depends on things that aren't just Python packages and API keys. There are **services** that need to be running or reachable. This is a fundamentally harder problem.

**What V3 must solve:**

1. **Service declaration in manifest** — `services:` section that declares external dependencies (vector store type + connection, MCP server reference, database engine)
2. **Preflight service checks** — before running, verify services are reachable (HTTP health check on Pinecone endpoint, MCP server availability)
3. **Data/asset bundling** — optional `data:` section in manifest for bundling documents, embeddings, or pre-built indices in the archive
4. **Lifecycle hooks** — `post_install` script support (e.g., "build the ChromaDB index from bundled documents after install")
5. **MCP server packaging** — an agent that IS an MCP server (long-running process, `runtime.type: mcp-server`)
6. **Remote registry** — for real distribution beyond a single machine. This is where Kinnoo becomes a platform.
7. **Interactive mode** — RAG agents are inherently conversational. REPL support belongs here.

**V3 success test:** The killer scenario from before. Developer A builds a RAG agent with Pinecone + MCP tools, publishes to Kinnoo's remote registry. Developer B runs `kinnoo install rag-agent`, gets prompted for API keys, Kinnoo validates Pinecone is reachable and MCP server is available, and the agent runs a multi-turn conversation.

---

### V4 Goal: The Composable Agent

**Target archetype:** Multi-agent systems where agents depend on other agents, with governance, sandboxing, and enterprise-grade trust.

**Example:** "An orchestrator agent that delegates to a research agent (RAG), a code agent (MCP tools), and a writing agent, all packaged separately and composed via A2A or direct invocation"
```
Agent dependencies: research-agent@1.2.0, code-agent@2.0.0, writer-agent@1.0.0
Orchestration: workflow graph or A2A protocol
Trust: sandboxed execution, permission scoping, audit trail
```

**What V4 must solve:**

1. **Agent-as-dependency** — manifest declares dependencies on other Kinnoo agents, with version constraints
2. **Agent composition** — an agent can invoke another installed agent (sub-process, API, or A2A)
3. **Sandboxed execution** — container-based isolation for untrusted agents
4. **Permission model** — declare and enforce what an agent can access (network, filesystem, other agents)
5. **Audit/governance** — execution traces, cost tracking, approval workflows for sensitive actions
6. **Multi-language support** — agents in Node.js, Go, etc. (not just Python)

**V4 success test:** An enterprise team deploys a multi-agent system where each agent is independently versioned, published, and sandboxed. Updating one agent doesn't break the others. Permissions are enforced at the Kinnoo level.

---

## The Progression at a Glance

| Version | Target Agent | Key Capability Added | Tagline |
|---------|-------------|---------------------|---------|
| **V1** ✅ | One-shot, single LLM | Pack → Install → Run | "Package any agent. Run it anywhere." |
| **V2** | Multi-tool, multi-secret | Reliable deps + secrets + local registry | "Install any agent. It just works." |
| **V3** | Connected (RAG, MCP, services) | Service deps + data + remote registry | "Share any agent. Run it with its full stack." |
| **V4** | Composable multi-agent | Agent-as-dependency + sandboxing | "Compose agents. Trust them. Scale them." |

---

## Answering Your Direct Question

> Would I be able to support the RAG+ChromaDB+Pinecone+MCP agent in V2?

**No, and you shouldn't try.** That agent has external service dependencies (Pinecone, MCP servers) that require service declaration, health checks, and possibly data bundling. That's V3 territory.

> What's the minimum agent V2 should fully support?

**A multi-tool agent with multiple Python dependencies and multiple API keys, discoverable via a local registry.** This is the 80% case for agents being built today. It's a meaningful step up from V1, it's achievable, and it forces you to solve the hard packaging problems (transitive deps, secrets, registry) without the complexity of external services.

> What's the "goal" of V2?

**Make `kinnoo install <agent> && kinnoo run <agent>` reliable and trustworthy for any Python-based agent whose dependencies are pip-installable packages and API keys.** Every V2 feature should serve that goal. If a feature doesn't make install+run more reliable for this class of agent, it's not V2.
