## Plan: Phase 2 (V2) Roadmap & Strategic Assessment

**TL;DR:**  
With MVP (Phase 1) complete, Kinnoo now offers reproducible agent packaging, framework-agnostic CLI, and a clean manifest schema. The next phase should focus on expanding agent portability, developer experience, and ecosystem integration. This means supporting advanced agent types (e.g., MCP servers), richer manifest fields, preflight checks, and registry integration. The goal: make Kinnoo the universal standard for agent packaging, sharing, and execution—across frameworks and platforms.

---

### Strategic Assessment

**Current Strengths:**
- Portable, reproducible agent packaging (manifest + entrypoint + dependencies)
- Framework-agnostic execution (black-box philosophy)
- CLI covers init, pack, install, run
- Manifest schema is extensible for future features

**AI Landscape Trends (2026):**
- MCP (Model Context Protocol) is emerging as the universal agent/tool interface (adopted by Copilot, Claude, Cursor, etc.)
- LLM agent frameworks (LangChain, CrewAI, AutoGen) are converging on async, tool-centric, and composable designs
- Developers want easier sharing, installation, and registry-driven discovery
- Security, permissioning, and reproducibility are increasingly important

**Opportunities:**
- Support MCP server agents (long-running, tool-exposing processes)
- Richer manifest fields: tools, services, memory, permissions, resources
- Preflight checks for environment, dependencies, and required services/tools
- Registry integration for publishing, discovery, and versioning
- Framework-aware scaffolding and adapters (opt-in, not forced)
- Evaluation/test harness for agent validation

---

### Concrete Phase 2 (V2) Plan

**Steps**

1. **Manifest Schema Expansion**
   - Add fields for runtime type (`one-shot`, `mcp-server`, `server`), tools, services, memory, storage, permissions, resources, evaluation/tests.
   - Update `src/kinnoo/schema.py` and `src/kinnoo/validator.py` to support new fields.
   - Ensure backward compatibility (MVP manifests remain valid).

2. **MCP Server Support**
   - Implement support for agents with `runtime.type: mcp-server` (long-running, JSON-RPC over stdin/stdout or HTTP).
   - Update CLI (`kinnoo run`) to handle server lifecycle, handshake, and tool exposure.
   - Document contract differences vs. one-shot agents.

3. **Preflight Checks & Environment Validation**
   - Add CLI preflight checks for required tools, services, GPU, environment variables.
   - Fail-fast or warn if requirements are unmet.
   - Extend manifest validator to check for declared resources/services.

4. **Registry Integration**
   - Design and implement a simple registry for agent packages (local or remote).
   - Add CLI commands: `kinnoo publish`, `kinnoo search`, `kinnoo install <from registry>`.
   - Support versioning, metadata, and discoverability.

5. **Framework-Aware Scaffolding (Opt-In)**
   - Extend `kinnoo init` with `--framework` flag for LangChain, CrewAI, AutoGen, etc.
   - Generate framework-specific templates, config files, and README instructions.
   - Keep default behavior framework-agnostic.

6. **Evaluation/Test Harness**
   - Add manifest fields for test datasets, expected behaviors, benchmarks.
   - Implement CLI command: `kinnoo test` to run agent against declared tests.
   - Integrate with pytest or custom runner.

7. **Security & Permission Model**
   - Add manifest fields for permissions (network, data, tools).
   - Implement CLI warnings and enforcement (sandboxing deferred to V3).

8. **Documentation & Developer Experience**
   - Update docs/ with new manifest schema, CLI usage, MCP support, registry workflow.
   - Improve error messages, UX, and onboarding.

---

**Verification**
- Run `python3 src/validate_project_manifests.py` on new manifest examples.
- Test CLI commands for MCP agents, registry operations, preflight checks.
- Validate framework templates with real-world agents.
- Run evaluation harness on sample agents.
- Review docs for clarity and completeness.

---

**Decisions**
- Adopt MCP server support as a core V2 feature (future-proof, ecosystem alignment).
- Manifest schema expansions are additive—no breaking changes.
- Registry is simple, metadata-driven, and versioned.
- Framework adapters are opt-in, not forced.
- Security model starts with declarative permissions and warnings.

---

**Summary:**  
Phase 2 will transform Kinnoo from a packaging tool into a universal agent platform, supporting advanced agent types, richer metadata, registry-driven sharing, and developer-centric features. This aligns with the AI landscape and positions Kinnoo as the standard for agent portability and composability.
