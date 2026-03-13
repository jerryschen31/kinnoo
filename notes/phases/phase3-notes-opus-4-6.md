## Revised V3 Feature Plan

Based on your responses, here's the revised V3 scope:

### Phase 3 (V3): "Share any agent. Run it with its full stack."

**Features (6 features, ordered by dependency):**

1. **Remote Registry** — HTTP-backed publish/install/search with S3 storage, auth, and simple web UI
   - FastAPI server with Jinja2 templates
   - S3 archive storage + JSON metadata index
   - Token-based auth for CLI, session auth for web
   - `kinnoo publish` uploads to remote; `kinnoo install/search/list` query remote
   - Web UI: login → agent table → profile
   - Tests: local TestClient + existing mock registry
   - Effort estimate: 3-4 weeks (1 engineer), or 2 weeks with scope tightly limited to publish/install/search + minimal UI.
   - Implementation notes: start by extracting a `RegistryBackend` HTTP client in CLI and keep current local backend unchanged for fallback/testing.
   - Implementation notes: use presigned upload/download URLs so the API server does not proxy large `.kno` files directly.
   - Implementation notes: keep metadata schema small (`name`, `version`, `description`, `author`, checksum, upload timestamp) and add pagination early.

2. **Flexible Runtime Inputs** — No-input run + parameterized pass-through arguments
   - `kinnoo run myagent` (no input) for self-contained agents
   - `kinnoo run myagent -- -e "text" -u "url" -p "path"` pass-through
   - Manifest `inputs.required: false` option
   - Input guard updated to scan typed pass-through args
   - `--` separator convention (standard Unix pattern)
   - Effort estimate: 3-5 days (1 engineer).
   - Implementation notes: update CLI parsing to capture args after `--` as `argparse.REMAINDER`, then forward verbatim to subprocess.
   - Implementation notes: preserve backward compatibility for current single positional input mode while introducing pass-through mode.
   - Implementation notes: extend input guard to evaluate each forwarded argument with type hints inferred from option names or manifest metadata.

3. **Service Declarations & Health Checks** — Manifest `services` section *(depends on #5 for MCP services)*
   - Declare external service dependencies in `kinnoo.yaml`
   - Health check protocol per service (HTTP endpoint, TCP port, process alive)
   - `kinnoo run` pre-flight checks service health before agent launch
   - Service types: mcp-server, vector-db, database, api, local-process
   - Effort estimate: 1.5-2.5 weeks (1 engineer).
   - Implementation notes: add schema validation first (`services[]` typed object), then implement runtime checks in `run_command` as a separate preflight stage.
   - Implementation notes: normalize checks to a small interface (`http`, `tcp`, `process`) and map service types onto one of those checks.
   - Implementation notes: default behavior should warn+prompt in interactive mode and fail-fast in non-interactive mode.

4. **Data & Asset Bundling** — Pack/install data alongside agent code *(parallel with #3)*
   - Manifest `data` section for declaring bundled assets
   - Included in `.kno` archive during pack, extracted during install
   - Size warnings (>100MB) and configurable size limits
   - Use cases: local vector DB, embeddings, reference documents
   - Effort estimate: 4-7 days (1 engineer).
   - Implementation notes: reuse existing `files` inclusion path logic where possible, but add explicit `data` semantics for validation and clearer UX.
   - Implementation notes: enforce deterministic archive paths for data directories to avoid install-time path mismatches.
   - Implementation notes: add warning thresholds and optional hard limits (`max_bundle_size_mb`) in manifest or config.

5. **MCP Server Packaging & Client Templates** — New archive type + templates *(parallel with #2, #6)*
   - `runtime.type: mcp-server` for long-running MCP server archives
   - `kinnoo run` lifecycle management (start server → start agent → cleanup)
   - GitHub MCP server + Filesystem MCP server as first packaged servers
   - Filesystem permissions: **read-only default**, opt-in write+create (no delete), `allowed_paths` sandboxing
   - MCP client agent templates (agents that connect to MCP servers)
   - Effort estimate: 2-3 weeks (1 engineer) for first stable slice.
   - Implementation notes: implement lifecycle as a supervisor module (spawn, readiness probe, signal handling, teardown) instead of embedding logic inline.
   - Implementation notes: represent filesystem permissions explicitly in manifest and enforce them in the packaged Filesystem MCP server wrapper.
   - Implementation notes: ship one end-to-end reference pair first (MCP server archive + MCP client template) before expanding server catalog.

6. **Framework & Template Expansion** — New framework templates *(parallel with #2)*
   - PydanticAI template (agent with typed tools, multi-model)
   - LangGraph template (stateful graph agent with nodes/edges)
   - OpenAI Agent SDK template (agents with handoffs, guardrails)
   - Each includes: `run.py` scaffold, `requirements.txt`, `kinnoo.yaml`, `README.md`
   - `kinnoo init myagent --framework pydantic-ai|langgraph|openai-agents`
   - Effort estimate: 1-1.5 weeks (1 engineer), assuming templates stay minimal and smoke-tested.
   - Implementation notes: define a common template contract (inputs, env vars, run behavior, docs sections) so all frameworks feel consistent.
   - Implementation notes: add one smoke test per template via `kinnoo init` + `kinnoo run` with mocked provider responses when possible.
   - Implementation notes: pin dependency major versions in template `requirements.txt` to reduce churn from upstream breaking changes.

**Deferred to V4+:**
- `kinnoo test` command
- `kinnoo doctor` standalone diagnostics
- Security/governance expansion (permission model, sandboxing, tool interception)
- Autogen template (pending ecosystem stabilization)

**Dependency graph:**
- **#1 (Remote Registry)** — independent, can start immediately; largest scope item
- **#2 (Flexible Runtime Inputs)** — independent, small scope; **parallel with #1**
- **#5 (MCP Server Packaging)** — independent of #1; **parallel with #1, #2**
- **#6 (Framework Templates)** — independent; **parallel with all**
- **#3 (Service Declarations)** — benefits from #5 (MCP server type definition) but can start with non-MCP services first
- **#4 (Data Bundling)** — independent, small scope; **parallel with #3**

**Suggested implementation order:**
1. First wave (parallel): **#2** (small, quick win) + **#6** (templates, self-contained) + **#4** (small, self-contained)
2. Second wave: **#5** (MCP packaging — establishes `mcp-server` runtime type)
3. Third wave: **#3** (service declarations — uses MCP server type from #5)
4. Throughout / largest: **#1** (remote registry — can be developed in parallel but has the longest tail)