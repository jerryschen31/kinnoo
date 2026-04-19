# Import Hardening — Planning & Spec

Date: 2026-04-18
Scope: Planning only. Captures the operator prompt and response before SWE agent handoff.

---

## Operator Prompt

**PRE-RELEASE FEATURE 6**
[todo]
kinnoo import hardening - kinnoo import support and testing is currently weak
have AI agents harden kinnoo import and make it minimally but robustly functional for production release - simple and robust is the goal

[definition of done]
- `kinnoo import <path>` works for Python projects (detects entrypoint, runtime, dependencies)
- `kinnoo import <path>` works for Node.js/TypeScript projects (detects package.json, entrypoint, runtime)
- Analyzer correctly infers manifest fields and generated kinnoo.yaml passes validation
- Clear error messages when import fails (missing entrypoint, ambiguous project structure, unsupported language)
- User is prompted to review and confirm generated manifest before writing
- Integration tests cover: Python project happy path, Node.js project happy path, missing entrypoint, empty project, project with existing kinnoo.yaml
- No crash or traceback on any reasonable input — all error paths produce user-friendly messages

**Operator follow-up questions:**

1. Is this enough information for a Copilot agent to do the kinnoo import hardening? Outline comprehensively what else an agent would need to harden kinnoo import so that it is robust for a subset of frameworks.
2. Consider what is currently built out in the codebase - I think we have limited support for langchain, langgraph and openai.
3. We need to adjust kinnoo import of openclaw since now we are using the recent "agent" (openclaw agent) functionality of openclaw. `kinnoo import --from openclaw [target] [import path]` should point to an existing openclaw agent workspace (usually in `~/.openclaw/workspace-<agent>/`) and successfully copy the relevant files (SOUL.md, IDENTITY.md, memory/, skills/ ... and DO NOT COPY .git/, .openclaw/ or .clawhub/) to relative or absolute path [target], essentially adding kinnoo.yaml.
4. Make sure that we focus on hardening import of a limited set of frameworks (but we make those imports robust to a variety of agents built with those frameworks). Suggest JUST focusing on langchain, langgraph, openai agents SDK, and openclaw, as well as basic Python or JS/TS LLM- or LLM+ReAct- based agents that just have prompts and memory / context md files, but make these imports ROBUST, STRAIGHTFORWARD and as ERROR-FREE as possible.

---

## Response

### Question 1: Is the DoD enough for an SWE agent? What's missing?

**Short answer: No.** The DoD is a reasonable acceptance checklist for a human reviewer but it's too vague for an SWE agent to execute without guessing. Here's what's missing and what the agent needs.

#### A. Current state is more built-out than the DoD implies

The DoD reads like the import feature doesn't exist yet, but it does. There's a substantial implementation already:

| Component | File | Lines | Status |
|---|---|---|---|
| Import command orchestration | `src/kinnoo/import_command.py` | ~1,340 | Works for basic cases |
| Project analyzer (detectors) | `src/kinnoo/analyzer.py` | ~2,286 | Covers entrypoint, runtime, deps, framework, env vars, assets, services |
| LangChain adapter | `src/kinnoo/framework_adapters/langchain_adapter.py` | ~65 | Functional but minimal |
| LangGraph adapter | `src/kinnoo/framework_adapters/langgraph_adapter.py` | ~92 | Functional but minimal |
| OpenAI adapter | `src/kinnoo/framework_adapters/openai_adapter.py` | ~91 | Functional but minimal |
| Framework adapter infra | `src/kinnoo/framework_adapters/__init__.py` | ~85 | Clean merge/override system |
| Class-wrapper generation | `src/kinnoo/wrapper_templates/*.j2` | 2 files | LangChain + OpenAI templates |
| OpenClaw workspace detection | In import_command.py + analyzer.py | scattered | Partial — detects workspace, registers with openclaw CLI, generates manifest |
| Import CLI tests | `tests/test_cli_import.py` | ~1,113 | ~14 tests covering core flows |
| Analyzer unit tests | `tests/test_analyzer.py` | ~599 | ~12 tests |

**The SWE agent needs to know:** this is a HARDENING task, not a greenfield build. The goal is to make what exists robust, not rewrite it. The agent should read the existing code first and work incrementally.

#### B. What the SWE agent specifically needs beyond the DoD

##### B1. A concrete "robustness matrix" — what inputs to handle gracefully

The DoD says "no crash on reasonable input" but doesn't enumerate what "reasonable" means. Here is the matrix the agent should use:

**Python project variations:**

| Scenario | Expected behavior | Currently works? |
|---|---|---|
| Single `main.py` with `if __name__` guard | Detect entrypoint, infer Python runtime | ✅ Yes |
| Single `run.py` without main guard | Detect entrypoint (lower confidence) | ✅ Yes |
| Multiple `.py` files, one with main guard | Pick the one with main guard | ✅ Yes |
| Multiple `.py` files, several with main guards | Pick best by scoring, warn ambiguous | ✅ Yes |
| `requirements.txt` present | Parse deps | ✅ Yes |
| `pyproject.toml` with `[project].dependencies` | Parse deps | ✅ Yes |
| Both `requirements.txt` and `pyproject.toml` | Merge + dedup deps | ✅ Yes |
| Neither requirements file (bare .py files) | Infer from import statements | ✅ Yes (task256) |
| `setup.py` only (legacy) | **Not handled** — should fall back to import inference | ❌ Gap |
| Poetry `pyproject.toml` (`[tool.poetry].dependencies`) | **Not handled** — should extract deps from poetry section | ❌ Gap |
| LangChain project: `from langchain_core import ...` | Detect framework, set runtime | ✅ Yes |
| LangGraph project: `from langgraph import StateGraph` | Detect framework, set runtime | ✅ Yes |
| OpenAI Agents SDK: `from agents import Agent` | Detect framework, set runtime | ✅ Yes |
| Class-only agent (no entrypoint script) | Detect class, offer wrapper generation | ✅ Yes (task269) |
| Virtual env `.venv/` present | Analyzer ignores venv dir | ✅ Yes |
| Huge project with >500 .py files | Analyzer uses max_depth limit | ✅ Yes |
| Project with `Dockerfile` but no Python entrypoint | Fail gracefully with clear message | ❓ Untested |
| Empty directory | Fail gracefully with clear message | ❓ Untested |

**Node.js/TypeScript project variations:**

| Scenario | Expected behavior | Currently works? |
|---|---|---|
| `package.json` with `main` field | Detect entrypoint | ✅ Yes |
| `package.json` with `scripts.start` | Extract entrypoint from start script | ✅ Yes |
| No `package.json` but `index.ts` at root | Detect conventional entrypoint | ✅ Yes |
| `src/index.ts` nested entrypoint | Detect from conventional dirs | ✅ Yes |
| TypeScript agent with `@langchain/langgraph` | LangGraph adapter detects TS markers | ✅ Yes |
| OpenAI SDK for TS: `from "openai"` | OpenAI adapter detects TS markers | ✅ Yes |
| `pnpm-lock.yaml` / `yarn.lock` present | Detect package manager | ✅ Yes |
| `node_modules/` present | Analyzer skips it | ✅ Yes |
| Monorepo with multiple package.json | **Not handled** — should warn and import the root | ❌ Gap |
| Pure `.mjs` files, no package.json | Detect entrypoint by name convention | ✅ Yes |

**OpenClaw agent workspace import:**

| Scenario | Expected behavior | Currently works? |
|---|---|---|
| Standard workspace in `~/.openclaw/workspace-<agent>/` | Detect, register, generate kinnoo.yaml | Partially (see Gap section below) |
| External workspace dir (not in `~/.openclaw/`) | Copy to `~/.openclaw/` and register | ✅ Yes (with prompt) |
| Workspace with `.git/`, `.openclaw/`, `.clawhub/` | Exclude from kinnoo archive | ❌ Gap (see operator request) |
| `kinnoo import --from openclaw` new flow | **Not implemented** — this is a new operator requirement | ❌ New feature |

**Generic LLM agent (no framework):**

| Scenario | Expected behavior | Currently works? |
|---|---|---|
| Python script using `openai` library directly (not Agents SDK) | Detect as generic Python, not framework-specific | ✅ Yes |
| Prompt-based agent: `prompts/`, `context/`, `.md` files | Detect entrypoint normally, include prompts as assets | ❓ Partial |
| ReAct-pattern agent with tools folder | Detect entrypoint normally | ✅ Yes |

##### B2. The specific openclaw import changes needed

The operator's request introduces a NEW import flow that doesn't exist today:

**Current behavior:** `kinnoo import <openclaw-workspace-dir>` auto-detects an openclaw workspace by looking for `openclaw.json`, `AGENTS.md`, `SOUL.md`, `skills/`, `memory/`. If found, it registers with `openclaw agents add`, generates kinnoo.yaml with `framework: openclaw` and `type: openclaw-skill`.

**New behavior requested:** `kinnoo import --from openclaw [target] [import-path]`

This needs a completely different flow from the auto-detection path:

```
kinnoo import --from openclaw ./my-kinnoo-agent ~/.openclaw/workspace-mybot/
                               ^                ^
                               target           source (openclaw workspace)
```

1. **Source** (`import-path`): An existing openclaw agent workspace (typically `~/.openclaw/workspace-<agent>/`)
2. **Target** (`target`): Where the imported kinnoo agent project will be created (can be relative or absolute)
3. **What gets copied from source → target:**
   - `SOUL.md`
   - `IDENTITY.md`
   - `memory/` directory
   - `skills/` directory
   - `AGENTS.md`
   - `TOOLS.md`, `USER.md`, `MEMORY.md`, `BOOTSTRAP.md`, `HEARTBEAT.md` (if they exist)
   - `openclaw.json` (metadata — useful for manifest generation)
   - Any other user-created `.md` files at root
   - Any `*.py`, `*.js`, `*.ts` files (agent code)
4. **What gets EXCLUDED:**
   - `.git/`
   - `.openclaw/`
   - `.clawhub/`
   - `node_modules/`
   - `.venv/`
5. **After copy:** Generate `kinnoo.yaml` in the target directory with:
   - `framework: openclaw`
   - `type: openclaw-skill`
   - Runtime inferred from workspace contents (Node.js if `package.json`, Python if `.py` files)
   - Dependencies from `package.json` or `requirements.txt` if present

**The flag syntax decision:** Currently `--from` accepts `langchain`, `langgraph`, `openai` — these are framework *hint* flags that tell the adapter system which framework to bias toward. The operator confirmed that `--from openclaw` is the correct design, even though it semantically overloads the flag. The rationale: kinnoo no longer treats individual ClawHub skills as the fundamental OpenClaw unit — it now supports OpenClaw workspace-based agents. The `--source clawhub` flow is deprecated. Adding `openclaw` to `--from` keeps the user-facing syntax simple and consistent with the "import from a framework ecosystem" mental model.

**Confirmed syntax:** `kinnoo import --from openclaw [target] [import-path]`

```
kinnoo import --from openclaw ./my-kinnoo-agent ~/.openclaw/workspace-mybot/
```

Or if the user just wants to import the current directory and the source workspace is the second arg:

```
kinnoo import --from openclaw . ~/.openclaw/workspace-mybot/
```

##### B3. Framework adapter hardening specifics

The current adapters detect framework markers but don't do much beyond setting `framework` and `runtime`. For hardening, each adapter should also:

1. **Validate the detected framework's project structure is minimally viable** — e.g., a LangChain project should have at least one file with a chain/agent definition, not just an import
2. **Detect the specific entry pattern** — e.g., LangGraph agents typically have a `compile()` call on the graph; LangChain agents typically have a `create_agent()` or `AgentExecutor()` call
3. **Infer correct dependencies with versions** — e.g., if `from langchain_openai import ChatOpenAI` is found, add both `langchain-openai` and `openai` to deps
4. **Detect common env vars for that framework** — e.g., LangGraph almost always needs `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`; OpenAI SDK needs `OPENAI_API_KEY`
5. **Produce framework-specific warnings** — e.g., "LangGraph agent detected but no `compile()` call found — verify graph construction"

Here are the specific improvements per adapter:

**LangChain adapter (`langchain_adapter.py`):**

| Current | Hardened |
|---|---|
| Detects `import langchain` / `from langchain` | Also detect `langchain_openai`, `langchain_anthropic`, `langchain_community`, `langchain_google_genai` |
| Sets `framework: langchain` | Also detect chain type: RAG, conversational, agent with tools |
| No dependency help | Infer deps from langchain sub-package imports (`langchain-openai`, `langchain-anthropic`, etc.) |
| No env var help | Detect env vars from code (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, etc.) |
| No structural validation | Warn if no chain/agent construction found |

**LangGraph adapter (`langgraph_adapter.py`):**

| Current | Hardened |
|---|---|
| Detects `import langgraph` / `StateGraph` | Also detect `MessageGraph`, `create_react_agent` |
| Sets `framework: langgraph` | Same |
| No dependency help | Infer deps: `langgraph` + any `langchain-*` sub-packages used |
| No env var help | Detect env vars from code |
| No structural validation | Warn if no `compile()` call found |

**OpenAI Agents SDK adapter (`openai_adapter.py`):**

| Current | Hardened |
|---|---|
| Detects `from agents import` / `import agents` / `from openai import` | Distinguish between OpenAI base SDK (`openai`) and OpenAI Agents SDK (`agents`) |
| Sets `framework: openai-agents` | Set `framework: openai-agents` for Agents SDK, `framework: openai` for base SDK |
| No dependency help | Infer deps: `openai` and/or `openai-agents` based on which imports found |
| No env var help | Add `OPENAI_API_KEY` to inferred env vars |
| No structural validation | Warn if no `Agent()` instantiation found (for Agents SDK) |

##### B4. Error message catalog

The DoD says "clear error messages" but the SWE agent won't know what's clear enough. Here's the catalog of error scenarios and exact messages:

| Scenario | Message |
|---|---|
| Empty directory | `Error: No source files found in {path}. kinnoo import requires a project with at least one code file (.py, .js, .ts).` |
| No detectable entrypoint | `Error: Could not detect an entrypoint. Create a main script (e.g., run.py or index.ts) or specify one manually.` |
| `kinnoo.yaml` already exists | `Error: kinnoo.yaml already exists in {path}. Use --force to overwrite.` |
| Target path doesn't exist | `Error: Import target does not exist: {path}` |
| Target path is a file, not a directory | `Error: Import target must be a directory: {path}` |
| Unsupported language only (e.g., only `.rs` files) | `Error: No supported language detected. kinnoo import currently supports Python and Node.js/TypeScript projects.` |
| OpenClaw source workspace not found | `Error: OpenClaw workspace not found at {path}. Expected a directory with SOUL.md, AGENTS.md, or openclaw.json.` |
| OpenClaw source has no copyable content | `Error: OpenClaw workspace at {path} contains no agent files to import.` |
| GitHub clone failed | `Error: Failed to clone repository: {git_error}` |
| Validation failed on generated manifest | `Warning: Generated kinnoo.yaml has validation issues: {errors}. Review and fix before packing.` |

##### B5. Test plan for the SWE agent

The DoD says "integration tests cover X" but the agent needs a concrete test list.

**New tests to add to `tests/test_cli_import.py`:**

| Test name | What it verifies |
|---|---|
| `test_import_empty_directory_fails_gracefully` | Empty dir → clear error, no crash, no kinnoo.yaml written |
| `test_import_unsupported_language_only` | Dir with only .rs files → clear "unsupported language" error |
| `test_import_python_with_poetry_deps` | `pyproject.toml` with `[tool.poetry].dependencies` → deps parsed |
| `test_import_python_with_setup_py_fallback` | `setup.py` only → falls back to import inference for deps |
| `test_import_node_monorepo_warns` | Multiple `package.json` files → warns about monorepo, imports root |
| `test_import_langchain_infers_sub_package_deps` | `from langchain_openai import ChatOpenAI` → `langchain-openai` in deps |
| `test_import_langgraph_warns_no_compile` | LangGraph imports but no `compile()` → warning in output |
| `test_import_openai_agents_sdk_detected` | `from agents import Agent` → `framework: openai-agents` |
| `test_import_openai_base_sdk_detected` | `from openai import OpenAI` (no agents import) → `framework: openai` |
| `test_import_openclaw_from_copies_files` | `--from openclaw` copies SOUL.md, skills/, memory/ but excludes .git/, .openclaw/ |
| `test_import_openclaw_from_missing_workspace_error` | `--from openclaw` with invalid path → clear error |
| `test_import_openclaw_source_generates_manifest` | After copy, kinnoo.yaml exists with `framework: openclaw` |
| `test_import_generic_llm_agent_with_prompts` | Dir with `run.py` + `prompts/` folder → prompts detected as assets |
| `test_import_generated_manifest_passes_validation` | For every framework fixture, generated manifest passes `validate()` |
| `test_import_all_framework_adapters_no_crash_on_empty` | Each adapter called on empty project → returns `detected=False`, no crash |

**New tests to add to `tests/test_analyzer.py`:**

| Test name | What it verifies |
|---|---|
| `test_poetry_deps_extraction` | Poetry `pyproject.toml` deps parsed |
| `test_setup_py_fallback_to_import_inference` | `setup.py` present but deps from import inference |
| `test_langchain_sub_package_dep_inference` | `langchain_openai` import → `langchain-openai` dep |
| `test_langgraph_compile_detection` | `StateGraph(...).compile()` → structural validation passes |
| `test_openai_agents_vs_base_sdk_distinction` | `from agents import Agent` vs `from openai import OpenAI` correctly distinguished |
| `test_node_monorepo_detection` | Multiple `package.json` → warning emitted |

---

### Question 2: What's currently built? (Detailed audit)

Already covered in the table in B1 above. Summary:

**What works well:**
- Basic Python import with entrypoint detection, main guard analysis, scoring for ambiguous cases
- Basic Node.js/TS import with `package.json` parsing, conventional entrypoint detection
- Dependency parsing from `requirements.txt` and standard `pyproject.toml`
- Import-from-inference for deps when no requirements file exists (task256)
- Class-only agent detection with wrapper generation (task269)
- LangChain, LangGraph, and OpenAI framework adapters (detection + runtime inference)
- OpenClaw workspace detection and registration
- Manifest rollback on failure
- `--force` override for existing kinnoo.yaml
- GitHub URL import with shallow clone
- `--from langchain|langgraph|openai` adapter hints
- `--source clawhub` import path (DEPRECATED — kinnoo now supports OpenClaw workspace-based agents, not individual ClawHub skills)

**What's weak or missing:**
- Poetry dependency extraction
- `setup.py` dependency handling
- Node.js monorepo handling
- Framework adapters are thin (detect markers only, don't validate project structure or infer framework-specific deps)
- OpenClaw `--from openclaw` copy flow doesn't exist yet
- OpenClaw file exclusion list (.git, .openclaw, .clawhub) not enforced during kinnoo pack
- Empty directory handling may crash rather than error gracefully
- No systematic "generated manifest must pass validation" assertion in tests
- Error messages are inconsistent in formatting

---

### Question 3: OpenClaw import — `--from openclaw` design

See section B2 above for the full design. Summary:

**Confirmed syntax:** `kinnoo import --from openclaw [target] [source-workspace]`

**Implementation steps for SWE agent:**

1. Add `"openclaw"` to the `--source` choices in `cli.py` (currently only `["clawhub"]`)

2. Create a new function `_import_from_openclaw_workspace()` in `import_command.py` that:
   a. Validates source workspace path exists and looks like an openclaw workspace
   b. Creates target directory if it doesn't exist
   c. Copies files from source to target using an explicit allowlist + blocklist:
      ```python
      OPENCLAW_EXCLUDE_DIRS = {".git", ".openclaw", ".clawhub", "node_modules", ".venv", "__pycache__"}
      OPENCLAW_EXCLUDE_FILES = {".DS_Store"}
      ```
      Everything else gets copied (identity .md files, skills/, memory/, code files, config files).
   d. Runs the analyzer on the target directory
   e. Generates kinnoo.yaml with `framework: openclaw`, `type: openclaw-skill`
   f. Prints success with next-step guidance

3. Wire it up in `import_agent()` — when `framework_from == "openclaw"`, intercept early and route to the new flow:
   ```python
   if framework_from == "openclaw":
       return _import_from_openclaw_workspace(
           target_path_arg=target_path_arg,
           source_workspace_arg=import_path_arg,
           force=force,
       )
   ```

4. If no `import_path_arg` is provided, default to discovering the workspace:
   - If `target` matches `~/.openclaw/workspace-*` pattern → use it as both source and target (in-place import, same as today's auto-detect)
   - Otherwise → error: "Usage: kinnoo import --from openclaw <target> <openclaw-workspace-path>"

---

### Question 4: Focused framework scope and robustness strategy

Agreed. The hardening scope is:

**Tier 1 — Full adapter hardening (robust to many project shapes):**
1. LangChain (Python only)
2. LangGraph (Python + Node.js/TS)
3. OpenAI Agents SDK (Python + Node.js/TS)
4. OpenClaw (Node.js primarily, but detect Python openclaw projects too)

**Tier 2 — Generic detection (no framework adapter, just solid basics):**
5. Generic Python LLM agent (uses `openai`/`anthropic`/`google-generativeai` libraries directly)
6. Generic JS/TS LLM agent (uses npm `openai`/`@anthropic-ai/sdk`/`@google/generative-ai` packages)
7. Prompt-and-memory agents (agent is mostly `.md` files + a thin runner script)

**Robustness strategy for each tier:**

**Tier 1 adapters — what "robust" means specifically:**

For each Tier 1 framework, the adapter should handle these project shapes without crashing:

| Shape | Description | Example repos |
|---|---|---|
| Tutorial/example | Single file, minimal code | `langchain-quickstart.py` |
| Multi-file with clear entrypoint | `main.py` imports from modules | Most production agents |
| Class-only (no script entrypoint) | Reusable agent class, no `__main__` | OSS langchain tool packages |
| Monorepo subfolder | Agent code in a subdirectory | Some enterprise layouts |
| Missing dependencies file | No `requirements.txt` or `pyproject.toml` | Quick-start repos, notebooks converted to scripts |

For each shape, the adapter should:
1. Not crash (return `detected=False` if it can't make sense of the project)
2. Produce a valid kinnoo.yaml that passes `validate()`
3. Produce at least one actionable warning if the project structure is unusual

**Tier 2 generic agents — what "robust" means specifically:**

The generic path (no adapter match) should:
1. Always find an entrypoint if one exists (using the scoring system already built)
2. Always produce a valid manifest even if some fields are guessed
3. Include any `.md` files in the project root as assets (these are prompts/context)
4. Detect `prompts/`, `context/`, `memory/`, `tools/` directories and include them as assets

**What we explicitly do NOT handle (out of scope for hardening):**

- Jupyter notebook agents (`.ipynb` entrypoints)
- Rust, Go, Java agents
- Multi-language polyglot projects
- Docker-only agents (no source code, just a Dockerfile)
- Remote API agents (agent is a hosted service, not local code)

---

## Implementation Task Breakdown for SWE Agent

### Task Group A: Error hardening and edge cases (no new features)

These tasks make existing code more robust without adding new functionality.

**A1. Graceful handling of degenerate inputs**
- Empty directory: return clear error, don't crash
- Directory with only unsupported files (.rs, .go, .java): return clear error
- Directory with only binary files: return clear error
- Validate that `analyze_project()` never raises on any directory input
- Add `try/except` around all file reads in analyzer detectors

**A2. Ensure generated manifests always pass validation**
- After `_build_manifest_from_analysis()`, call `validate_manifest_data()` on the result
- If validation fails, log warnings and fix auto-fixable issues (e.g., missing `dependencies: []` default)
- Add a post-generation validation step in the import flow

**A3. Standardize error message format**
- All error messages should follow the pattern: `Error: <one-line description>. <actionable next step>.`
- All warnings should follow: `Warning: <one-line description>.`
- Audit all `print(style_text(...))` calls in `import_command.py` for consistency

### Task Group B: Framework adapter hardening

**B1. LangChain adapter improvements**
- Add `langchain_openai`, `langchain_anthropic`, `langchain_community`, `langchain_google_genai` to marker list
- Infer sub-package deps from imports (e.g., `from langchain_openai import ...` → add `langchain-openai` to deps)
- Detect common LangChain env vars (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`)
- Warn if no chain/agent construction found (no `RunnableSequence`, `AgentExecutor`, `create_*_agent`)

**B2. LangGraph adapter improvements**
- Add `MessageGraph`, `create_react_agent`, `ToolNode` to marker list
- Detect `compile()` call as structural validation
- Infer deps from both `langgraph` and any `langchain-*` sub-packages
- Detect env vars from code

**B3. OpenAI adapter improvements**
- Distinguish `openai` base SDK from `agents` (OpenAI Agents SDK)
- Set `framework: openai` for base SDK, `framework: openai-agents` for Agents SDK
- Infer `OPENAI_API_KEY` env var
- For Agents SDK: detect `Agent()` instantiation as structural validation
- Infer `openai` and/or `openai-agents` deps correctly

**B4. Generic LLM agent detection (new, but simple)**
- If no framework adapter matches but the project uses LLM libraries directly:
  - Set `framework: null` (generic)
  - Detect env vars for the specific LLM provider used
  - Infer the correct library dep
- Detect `prompts/`, `context/`, `memory/` directories as assets
- Detect `.md` files at project root as potential prompt/context assets

### Task Group C: OpenClaw --from import (new feature)

**C1. Add `openclaw` to `--from` choices in CLI**
- Update `cli.py` to accept `--from openclaw` (add `"openclaw"` to the `--from` choices list)

**C2. Implement `_import_from_openclaw_workspace()` in import_command.py**
- Validate source workspace (must contain at least one of: SOUL.md, AGENTS.md, openclaw.json, skills/, memory/)
- Create target directory
- Copy files with exclude list: `.git/`, `.openclaw/`, `.clawhub/`, `node_modules/`, `.venv/`, `__pycache__/`
- Use `shutil.copytree` with `ignore` parameter for clean exclusion
- Run analyzer on target
- Generate kinnoo.yaml with `framework: openclaw`, `type: openclaw-skill`
- Print success + next-step guidance

**C3. Handle default workspace discovery**
- If only one positional arg given with `--from openclaw`, try to use it as the source workspace
- If it looks like an openclaw workspace (in `~/.openclaw/`), import in-place
- Otherwise, error with usage hint

### Task Group D: Dependency detection improvements

**D1. Poetry support**
- Detect `[tool.poetry].dependencies` in `pyproject.toml`
- Extract dep names + version constraints
- Merge with other dep sources (requirements.txt, standard pyproject.toml)

**D2. Sub-package dependency inference for frameworks**
- When `langchain_openai` is imported, add `langchain-openai` to deps
- Map common import-to-package translations for langchain ecosystem
- Map for openai ecosystem: `agents` → `openai-agents`, `openai` → `openai`

### Task Group E: Tests

**E1. Add missing edge-case tests (test_cli_import.py)**
- Empty directory, unsupported language, poetry deps, monorepo warning, openclaw source

**E2. Add adapter-specific tests (test_analyzer.py)**
- Sub-package dep inference, structural validation, agents SDK vs base SDK distinction

**E3. Add "manifest always valid" regression test**
- For every test fixture that generates a manifest, assert it passes `validate_manifest_data()`

---

## SWE Agent Execution Order

1. **Read existing code first:** `import_command.py`, `analyzer.py`, all three framework adapters, `cli.py` import parser section, existing tests. Do not modify anything until you understand the flow.

2. **Task Group A** (error hardening) — lowest risk, immediately testable. Run existing tests after each change to ensure no regressions.

3. **Task Group D** (dependency improvements) — small, contained changes to analyzer.

4. **Task Group B** (adapter hardening) — moderate changes, each adapter is independent.

5. **Task Group C** (openclaw --source) — new feature, slightly higher risk. Implement after the hardening is done.

6. **Task Group E** (tests) — write tests throughout, not just at the end. Each task group should have its tests written alongside the implementation.

**Estimated scope:** This is a medium-large hardening task, not a rewrite. The existing code is ~5,300 lines across the four main files. The hardening will touch perhaps 30-40% of that and add ~500 lines of new code + ~400 lines of new tests.

---

## PRE-RELEASE-CHECKLIST.md Updates Needed

> **APPLIED (2026-04-18 Round 2):** The Feature 6 todo and DoD in PRE-RELEASE-CHECKLIST.md have been updated to reflect this scoped plan. See the updated version in `notes/PRE-RELEASE-CHECKLIST.md`.

---

## Round 2 — Operator Review & Design Decisions (2026-04-18)

### Operator Prompt (Round 2)

**Q1 reply:** Yes, fix the todo descriptions and definition-of-done for Feature 6 in PRE-RELEASE-CHECKLIST to emphasize this is import HARDENING, not implementation from nothing. Also adjust the todo and DoD with what was said in Q1-Q4 — high-level todo and DoD that an outside dev can understand without knowing internals of kinnoo.

**Q3 reply — DISAGREES with `--source openclaw` recommendation:** This is NOT importing from ClawHub anymore. Agents were confused because the original approach with openclaw was skills-based. UPDATE ALL relevant documentation to EMPHASIZE that kinnoo supports openclaw "agents" (workspace-based), NOT individual skills from ClawHub. Make sure that any notes in notes/ that reference openclaw skills as a fundamental agentic unit that kinnoo supports should be noted as DEPRECATED. Keep `--from openclaw` as the import design. The new flow is correct.

**Q4 reply:** Correct. Tier 1 then Tier 2. Make sure the SWE agent works on hardening ONE framework at a time. The SWE agent should also use REAL open-source public agents on GitHub as examples, and needs to MAKE SURE that the framework matches (i.e., that detected LangGraph agent is truly a LangGraph agent). If it is too hard for the SWE agent or Tech Lead to find good example agents from GitHub, then SWE agent should intelligently create an example agent in the given framework that adequately tests import — perhaps using the framework's documentation to help construct a good example agent that has the structure of a "real-world" agent (not a shallow mock agent that just passes tests).

---

### Response (Round 2)

#### Actions Taken

**1. PRE-RELEASE-CHECKLIST.md Feature 6 updated**

The todo and DoD in `notes/PRE-RELEASE-CHECKLIST.md` have been rewritten to:
- Explicitly state this is a HARDENING pass on an existing feature, not a greenfield build
- Describe work items at a level an outside dev can understand without knowing kinnoo internals
- Incorporate all Q1–Q4 decisions: framework-specific adapter hardening, `--from openclaw` workspace import, dependency detection improvements, generic LLM agent support, test strategy with real or realistic agents
- Include DoD criteria around framework detection accuracy (detected LangGraph is truly LangGraph)

**2. OpenClaw paradigm shift: workspace-based agents, NOT ClawHub skills**

The operator confirmed a fundamental shift: **kinnoo now supports OpenClaw workspace-based agents, NOT individual skills from ClawHub.** This affects the entire OpenClaw integration model.

**What changed:**
- The `--from openclaw` flag is confirmed as the correct design (NOT `--source openclaw`)
- All references to `--source openclaw` in import-hardening.md have been corrected to `--from openclaw`
- The Option A/B design discussion has been replaced with the confirmed decision

**Deprecation notices added to the following files:**

| File | What was deprecated |
|---|---|
| `notes/manifest-schema-reference.md` — Feature62 section | `openclaw-skill` type and ClawHub-based provenance model |
| `notes/manifest-schema-reference.md` — Feature64 section | `--source clawhub` import flow |
| `notes/tasks/task378-notes.md` | `--openclaw-skill` search mode (already removed by task477) |
| `notes/tasks/task379-notes.md` | OpenClaw skill search preflight |
| `notes/features/feature83-swe-handoff.md` | `kinnoo install --openclaw-skill` |
| `notes/features/feature84-swe-handoff.md` | `kinnoo search --openclaw-skill` |
| `notes/features/feature66-swe-handoff.md` | Skill-specific routing in run adapter (partially deprecated) |
| `notes/phases/phase6-planning-6.md` | OpenClaw skill-based features (feature62/63/64/83/84) |

Each deprecation notice:
- Uses the `> ⚠️ DEPRECATED` callout format for high visibility
- Explains what the old paradigm was (individual skills from ClawHub)
- States what replaced it (OpenClaw workspace-based agents via `--from openclaw`)
- Notes the file is retained for historical context only

**What this means for the codebase (future cleanup, NOT part of this hardening task):**
- `type: openclaw-skill` in schema.py and validator.py may eventually be renamed or aliased to `type: openclaw-agent`
- `--source clawhub` in cli.py may eventually be removed or hidden behind a legacy flag
- ClawHub mirror index features (feature63) are likely unnecessary in the new paradigm
- The `openclaw_preflight.py` commands list includes `openclaw-skill-install` and `openclaw-skill-search` — these may need cleanup

**3. Confirmed `--from openclaw` design**

The design uses `--from openclaw` (adding `openclaw` to the existing `--from` choices: `langchain`, `langgraph`, `openai`).

When `--from openclaw` is set, the import flow is fundamentally different from the other `--from` values:
- LangChain/LangGraph/OpenAI: `--from` is a **hint** that biases the analyzer toward that framework
- OpenClaw: `--from openclaw` is a **source directive** that triggers a workspace-copy-and-import flow

This semantic overloading is acceptable because:
1. The user experience is simple: "I'm importing from an openclaw agent workspace"
2. The `--source clawhub` flow is being deprecated, so there's no confusion with that flag
3. All `--from` values share the meaning "this project comes from framework X" — the fact that openclaw also requires a copy step is an implementation detail

**Implementation note for SWE agent:** When `framework_from == "openclaw"`, intercept BEFORE the normal import flow (before `analyze_project()` etc.) and route to `_import_from_openclaw_workspace()`. The `import_path_arg` positional serves as the source workspace path. The `target_path_arg` is where the copied files + kinnoo.yaml will go.

**CLI change needed:** In `cli.py`, the `--from` argument currently has `choices=["langchain", "langgraph", "openai"]`. Add `"openclaw"` to this list. Also, the current guard `if import_path_arg is not None and not is_github_url(target_arg)` rejects import-path for non-GitHub imports — this needs to be relaxed when `--from openclaw` is set, since import-path is the source workspace.

#### 4. Testing strategy — one framework at a time, real agents

**Confirmed approach:** The SWE agent should harden one framework at a time, in this order:
1. LangChain
2. LangGraph
3. OpenAI Agents SDK
4. OpenClaw agent workspaces
5. Generic Python/JS LLM agents

**For each framework, the SWE agent should:**

1. **Find 2–3 real open-source agents on GitHub** that are built with that framework. These serve as ground-truth test cases. The agent should verify the repo actually uses the framework (check imports, not just the repo description).

2. **If real agents are hard to find or are too complex for a test fixture:** Create a realistic synthetic agent that matches the structure of real-world projects. NOT a shallow mock. The synthetic agent should:
   - Have the same file layout as real agents (e.g., LangGraph agents typically have a `graph.py` with `StateGraph`, a `state.py` with typed state, a `tools.py`, and a `main.py`)
   - Use real import statements from the framework
   - Have a `requirements.txt` or `pyproject.toml` with real dependency names
   - Include env var references (`os.getenv("OPENAI_API_KEY")`)
   - Be complex enough that the analyzer has to work (not just a single `hello.py`)

3. **Verify framework detection accuracy:** After importing, assert that the detected framework is exactly what it should be. A LangGraph agent must not be detected as LangChain. An OpenAI Agents SDK agent must not be detected as generic OpenAI.

**Example GitHub repos to start from (SWE agent should verify these):**

| Framework | Repo (verify before using) | Notes |
|---|---|---|
| LangChain | `langchain-ai/langchain/templates/*` | Official templates with real chain construction |
| LangGraph | `langchain-ai/langgraph/examples/*` | Official examples with StateGraph + compile() |
| OpenAI Agents SDK | `openai/openai-agents-python/examples/*` | Official examples with Agent() |
| OpenClaw | `~/.openclaw/workspace-*` on the dev machine | Real agent workspaces |
| Generic Python | Any simple `openai` library script | Not framework-specific |

**The SWE agent should create test fixtures in `tests/fixtures/import/` organized by framework:**

```
tests/fixtures/import/
  langchain/
    simple-rag/        # minimal LangChain RAG agent
    multi-file/        # multi-module LangChain agent
  langgraph/
    react-agent/       # LangGraph ReAct agent with StateGraph
    multi-node/        # multi-node graph with tools
  openai-agents/
    simple-agent/      # minimal OpenAI Agents SDK agent
    multi-agent/       # multi-agent handoff
  openai-base/
    simple-completion/ # just uses openai library directly
  openclaw/
    minimal-workspace/ # SOUL.md + IDENTITY.md + skills/ + memory/
    full-workspace/    # all identity files + code + config
  generic/
    python-llm/        # Python script with direct LLM calls
    nodejs-llm/        # Node.js with openai package
    prompt-agent/      # mostly .md files + thin runner
  edge-cases/
    empty/             # empty directory
    unsupported/       # only .rs files
    no-entrypoint/     # Python files but no main guard
```

Each fixture should have a companion comment or `_expected.yaml` file documenting what the import should produce, so test assertions are clear.

---

## Round 3 — Subagent Sufficiency Addendum (2026-04-19)

This section captures a two-subagent review (SWE-focused + test-focused) of this note and adds missing implementation/testing details to minimize hallucination and guessing.

### Sufficiency verdict

- Current note is strong but **not yet fully deterministic** for execution by an SWE agent and test agent without ambiguity.
- The main remaining risk is inconsistent interpretation of CLI contract, framework precedence, and fixture quality for realistic imports.

### Canonical CLI contract (normative)

- OpenClaw copy import syntax is:
  - `kinnoo import --from openclaw <target> <source-workspace>`
- `<target>`:
  - Create if missing.
  - Error if it exists and is a file.
  - In-place import is allowed only when `<target> == <source-workspace>` and source is a valid OpenClaw workspace.
- `<source-workspace>`:
  - Must be an existing workspace-like directory containing at least one of `SOUL.md`, `AGENTS.md`, `openclaw.json`, `skills/`, `memory/`.
- `--source clawhub` is deprecated and out of scope for hardening changes in this feature.
- Non-interactive behavior:
  - No confirmation prompts on import path handling.
  - Use actionable errors unless `--force` is provided for overwrite scenarios.

### Framework resolution and anti-misclassification rules (normative)

- Detection precedence for hardening:
  1. explicit `--from openclaw`
  2. `openai-agents`
  3. `langgraph`
  4. `langchain`
  5. `openai` (base SDK)
  6. generic (`framework: null`)
- If multiple framework signals are present, apply precedence and emit:
  - `Warning: Multiple frameworks detected; selected <framework> by precedence.`
- Must distinguish:
  - OpenAI Agents SDK (`agents` imports / `Agent(...)`) vs OpenAI base SDK (`openai` only)
  - LangGraph vs LangChain when both langchain-family imports appear

### Required output contract per fixture

Each import fixture must define `_expected.yaml` with:

- `detected.framework`
- `detected.runtime`
- `detected.type`
- `entrypoint` (path or null)
- `dependencies` (set; order-insensitive)
- `env_vars` (set)
- `assets` (set)
- `warnings_contains` (required warning substrings)
- `errors_exact` (for failure fixtures)
- `manifest_valid` (boolean)

Normalization requirements for assertions:

- Sort and compare `dependencies`, `env_vars`, and `assets` as sets.
- Normalize paths to `/`.
- Keep warning/error assertions deterministic (exact string or explicit regex list).

### Production-ready fixture policy (mandatory)

- Do not rely on toy one-file fixtures as primary coverage for any framework.
- For each framework family (`langchain`, `langgraph`, `openai-agents`, `openclaw`, generic):
  - Include at least **2 realistic fixtures** with multi-file structure and realistic config/dependency/env usage.
- A production-ready synthetic fixture must include:
  - At least 4 files across modules
  - Real framework imports
  - At least one structural marker (for example `compile()`, `Agent()`, `AgentExecutor`)
  - Prompt/context assets and at least one env var reference
- Tests must be fully offline and deterministic:
  - Fixtures live under `tests/fixtures/import/**`
  - No network access or live GitHub clone during test execution

### Real-agent sourcing requirement for SWE and test agents

- For each framework hardening pass, SWE/test agents should first identify 2–3 production-quality public agents.
- If suitable public agents are not available or too heavy for fixtures:
  - Build a high-fidelity synthetic agent from official framework docs and production project structure conventions.
- In task notes, the implementing agent must include either:
  - Public reference(s): repo URL + pinned commit/tag + why it is production-representative, or
  - Synthetic fixture rationale: framework doc references + structure decisions used to mimic production agents.
- The implementing agent should include the resulting fixture code (or a direct reference to public agent code) in task notes so follow-on reviewers can verify realism and framework correctness.

### File-level implementation map (required touchpoints)

- `src/kinnoo/cli.py`: `--from openclaw` parsing and positional-arg validation updates.
- `src/kinnoo/import_command.py`: `_import_from_openclaw_workspace` routing/copy/exclusions/manifest flow.
- `src/kinnoo/analyzer.py`: poetry dependency extraction, setup.py fallback, monorepo warnings.
- `src/kinnoo/framework_adapters/{langchain,langgraph,openai}_adapter.py`:
  - stronger structural checks, dependency inference, env var inference, warnings.
- `tests/test_cli_import.py`, `tests/test_analyzer.py`:
  - matrix coverage, anti-misclassification assertions, manifest validity assertions.
