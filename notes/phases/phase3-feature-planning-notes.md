## Thinking Through Feature Decomposition

Here's my analysis of each of the 6 phase3 notes items:

### 1. Remote Registry (3-4 weeks) — **NEEDS SPLITTING**
This is massive. It covers: server-side FastAPI app, S3 storage, auth, web UI, CLI `publish` to remote, CLI `install` from remote, CLI `search`/`list` from remote. Breaking into:
- **feature20**: Registry Backend Abstraction & Remote Client — Extract `RegistryBackend` protocol, implement HTTP client for CLI commands (`publish`, `install`, `search`, `list` with `--remote` pointing at a real remote server instead of mock)
- **feature21**: Remote Registry Server — FastAPI server with S3 storage, JSON metadata, token-based auth, presigned URLs
- **feature22**: Registry Web UI — Jinja2 templates for login, agent listing, agent profile pages

### 2. Flexible Runtime Inputs (3-5 days) — **Single feature OK**
- **feature23**: Allow no-input `kinnoo run`, pass-through args with `--` separator, manifest `inputs.required: false`, input guard on pass-through args
- **⚠ REGRESSION RISK**: Changes `kinnoo run` argparse — currently `input` is a required positional arg. Needs careful backward compat.

### 3. Service Declarations & Health Checks (1.5-2.5 weeks) — **NEEDS SPLITTING**
Benefits from MCP, but schema can be standalone. Breaking into:
- **feature24**: Service Declarations Schema — Manifest `services` section with validation
- **feature25**: Service Health Checks Runtime — Preflight health checks for declared services during `kinnoo run`

### 4. Data & Asset Bundling (4-7 days) — **Single feature OK**
- **feature26**: Manifest `data` section, pack includes data, install extracts data, size warnings
- **⚠ REGRESSION RISK**: Changes pack/install archive format (now includes data directories)

### 5. MCP Server Packaging & Client Templates (2-3 weeks) — **NEEDS SPLITTING**
New runtime type, lifecycle management, templates. Breaking into:
- **feature27**: MCP Server Runtime Type — `runtime.type: mcp-server` in schema, lifecycle supervisor for `kinnoo run`
- **feature28**: MCP Server Packages & Client Templates — Packaged MCP servers (GitHub, Filesystem with permissions), MCP client agent templates
- **⚠ REGRESSION RISK**: Adding `mcp-server` to SUPPORTED_RUNTIME_TYPES changes schema validation

### 6. Framework & Template Expansion (1-1.5 weeks) — **Single feature OK**
- **feature29**: PydanticAI, LangGraph, OpenAI Agent SDK templates for `kinnoo init --framework`

### Implementation Order:
1. **feature23** (Flexible Runtime Inputs) — small, quick win, independent
2. **feature29** (Framework Templates) — self-contained, parallel
3. **feature26** (Data Bundling) — small, self-contained
4. **feature27** (MCP Server Runtime Type) — establishes new runtime type
5. **feature24** (Service Declarations Schema) — schema-only, independent
6. **feature28** (MCP Packages & Client Templates) — depends on feature27
7. **feature25** (Service Health Checks) — depends on feature24, benefits from feature27/28
8. **feature20** (Registry Client Abstraction) — independent, can start anytime
9. **feature21** (Registry Server) — depends on feature20
10. **feature22** (Registry Web UI) — depends on feature21

Phase 3 features are defined. Here's the summary of what was created and the reasoning behind the decisions:

### Decomposition: 6 High-Level → 10 Features
Three of the six phase3 items were too large for a single feature and were split:

### Phase3 Item	Scope Issue	Split Into
Remote Registry (3-4 weeks)	Server + client + web UI are distinct deliverables	feature27 (client abstraction), feature28 (server), feature29 (web UI)
MCP Server Packaging (2-3 weeks)	Runtime type is a schema/lifecycle concern; templates are a packaging concern	feature23 (runtime type + supervisor), feature26 (packages + client templates)
Service Declarations (1.5-2.5 weeks)	Schema validation and runtime health checks are different layers	feature24 (schema only), feature25 (runtime health checks)
The other three (Flexible Runtime Inputs, Data Bundling, Framework Templates) stayed as single features.

### Feature IDs and Ordering
Wave	Feature	Title	Dependencies
1 (parallel)	feature20	Flexible Runtime Inputs	feature3, feature18
1 (parallel)	feature21	Framework Templates (PydanticAI, LangGraph, OpenAI Agents)	feature4
1 (parallel)	feature22	Data & Asset Bundling	feature5, feature8
2	feature23	MCP Server Runtime Type — Schema & Lifecycle	feature3, feature9
3	feature24	Service Declarations — Manifest Schema	feature9
4	feature25	Service Health Checks — Runtime Preflight	feature24, feature14
4	feature26	MCP Server Packages & Client Templates	feature23, feature21
5+	feature27	Registry Backend Abstraction & Remote Client	feature13
5+	feature28	Remote Registry Server	feature27
5+	feature29	Registry Web UI	feature28

### Regression Risk
Every feature that modifies existing code has explicit notes in the YAML calling out which test files the SWE agent must regression-test. The highest-risk features are feature20 (changes kinnoo run argparse), feature23 (adds mcp-server to SUPPORTED_RUNTIME_TYPES), and feature27 (refactors registry command internals).

### What each AC targets
All ACs are designed to be testable with simple, fast unit tests — no live network calls, no real S3, no real MCP servers. Server features (feature28/29) use FastAPI's TestClient; MCP lifecycle tests use mock subprocesses; health checks test against localhost sockets.