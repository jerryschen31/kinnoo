I now have full context. Here's my thinking process and the proposed feature breakdown:

**Current state:**
- Features: feature1–feature6 (all completed, V1/MVP)
- Tasks: task0–task38 (all completed)
- Tests: test0–test60 (all completed)
- Next IDs: feature7, task39, test61

**My approach:** I'm mapping the V2 plan items directly to features, incorporating your decisions from the followup:
- Keep `--preflight` on `kinnoo run` (not standalone `kinnoo doctor`)
- Include Trust Baseline
- Interactive Mode = Medium effort
- `kinnoo search` as part of Local Registry
- `kinnoo test` pushed to V3
- Keep original slogan
- CrewAI as lowest-priority framework template in V2 (REMOVED per your latest instruction)
- `--mcp` flag on `kinnoo init`

---

## Plan: V2 Feature Breakdown

**TL;DR:** 13 features (feature7–feature19) organized in 3 tiers matching the V2 plan. Tier 1 addresses V1 tech debt first (the user's explicit priority). Each feature has concrete, unit-testable acceptance criteria. Tasks will be created separately after feature approval.

**Features Overview**

| ID | Title | Tier | Depends On | Effort |
|----|-------|------|------------|--------|
| feature7 | CLI Refactor & Modular Architecture | 1 (Foundation) | — | Small |
| feature8 | Packaging Robustness | 1 (Foundation) | — | Small |
| feature9 | Manifest Schema V2 Extensions | 1 (Foundation) | — | Small |
| feature10 | Environment Variable / Secret Management | 2 (Core) | feature9 | Medium |
| feature11 | MCP Server Runtime Support | 2 (Core) | feature9 | Medium |
| feature12 | `kinnoo inspect` Command | 2 (Core) | feature7 | Small |
| feature13 | Local Registry | 2 (Core) | feature12 | Medium |
| feature14 | Interactive Mode | 2 (Core) | feature9 | Medium |
| feature15 | Preflight Checks (`--preflight`) | 3 (Differentiation) | feature10 | Medium |
| feature16 | Additional Framework Templates | 3 (Differentiation) | — | Medium |
| feature17 | Run from Archive Directly | 3 (Differentiation) | feature13 | Small |
| feature18 | Trust Baseline | 3 (Differentiation) | feature10 | Small |
| feature19 | `--mcp` flag on `kinnoo init` | 3 (Differentiation) | feature16 | Medium |

**Detailed Feature Definitions**

### feature7 — CLI Refactor & Modular Architecture

Extract install logic from monolithic [cli.py](src/kinnoo/cli.py) into a dedicated `install_command.py` module (matching `init_command.py` and `pack_command.py` pattern). Fix `--force` argparse integration. Add `--version` flag. Clean up duplicate test in [test_pack.py](tests/test_pack.py).

**ACs:**
1. Install logic lives in `src/kinnoo/install_command.py`, not inline in `cli.py`
2. `cli.py` imports and delegates to `install_command.py` for install operations
3. `--force` flag is handled via argparse (not raw `sys.argv` parsing)
4. `kinnoo --version` prints the package version and exits
5. No duplicate test functions exist in the test suite
6. All existing V1 tests continue to pass after refactor

### feature8 — Packaging Robustness

Fix transitive dependency bundling in `kinnoo pack`. Make canonical archive format decision (zip). Implement fallback behavior for missing/failed wheel builds.

**ACs:**
1. `kinnoo pack` includes transitive dependencies (not just direct), so `pip install` in an offline venv succeeds
2. Archive format is zip with `.kno` extension; all docs/code/notes reference zip consistently
3. If a wheel build fails for a dependency, `kinnoo pack` warns but continues (does not abort)
4. `kinnoo install` falls back to PyPI install for any missing wheels (with a warning)
5. A packed agent with transitive deps installs and runs correctly in a fresh venv

### feature9 — Manifest Schema V2 Extensions

Add optional fields to kinnoo.yaml schema: `description`, `author`, `license`, `env_vars` (list[string]), and `runtime.type: mcp-server` as a valid runtime type. All additions are non-breaking — existing V1 manifests remain valid.

**ACs:**
1. `description` (string), `author` (string), `license` (string) are accepted as optional fields
2. `env_vars` (list[string]) is accepted as an optional field; validator ensures it is a list of strings when present
3. `runtime.type: mcp-server` passes validation (in addition to existing `one-shot`)
4. A V1 manifest (without any new fields) still passes validation with no errors
5. Invalid types for new fields (e.g., `env_vars` as a string, `description` as a number) produce specific error messages
6. `kinnoo init` templates include `description` and `author` fields with placeholder values

### feature10 — Environment Variable / Secret Management (`env_vars`)

When running an agent whose `kinnoo.yaml` declares `env_vars`, the runtime checks, resolves, and injects the required variables into the subprocess environment. Resolution order: current environment → `.env` file in agent directory → interactive prompt.

**ACs:**
1. If `env_vars` declares variables and all are set in the current environment, agent runs normally with those vars injected
2. If a declared env var is missing from environment, kinnoo checks for a `.env` file in the agent directory and loads it
3. If a declared env var is still missing after `.env` check, kinnoo prompts the user interactively
4. All resolved env vars are injected into the subprocess environment when executing the agent
5. If the user declines to provide a missing env var (e.g., Ctrl+C), execution aborts with a clear message
6. Agents without `env_vars` in manifest are unaffected — no prompting, no `.env` loading

### feature11 — MCP Server Runtime Support (`runtime.type: mcp-server`)

New execution mode for `kinnoo run`: when manifest declares `runtime.type: mcp-server`, the runtime launches the entrypoint as a long-running process and keeps it alive, piping stdin/stdout. This enables packaging MCP servers as `.kno` archives.

**ACs:**
1. `kinnoo run <mcp-server-dir>` with `runtime.type: mcp-server` starts the entrypoint as a persistent process (does not exit after one response)
2. stdin/stdout are piped between the terminal and the agent process
3. The process stays alive until the user sends SIGINT (Ctrl+C) or the process exits on its own
4. `kinnoo run` with `runtime.type: mcp-server` does NOT require an input argument (unlike one-shot mode)
5. Environment variables from `env_vars` are injected before starting the MCP server process
6. An MCP server agent can be packed, installed, and run through the full lifecycle (`pack → install → run`)

### feature12 — `kinnoo inspect` Command

New CLI command that reads and displays manifest metadata from a `.kno` archive or agent directory. Foundation for registry browsing and agent discovery.

**ACs:**
1. `kinnoo inspect <agent-dir>` reads `kinnoo.yaml` and displays name, version, description, author, license, dependencies, env_vars, runtime type
2. `kinnoo inspect <archive.kno>` reads manifest from inside the archive without extracting the full archive
3. Output is human-readable formatted text (not raw YAML)
4. Missing optional fields are omitted from output (not shown as "None" or empty)
5. Invalid manifest produces a clear error (reuses feature1 validator)
6. `kinnoo inspect` without arguments prints usage help

### feature13 — Local Registry (`kinnoo publish`, `kinnoo install <name>`, `kinnoo list`, `kinnoo search`)

Implement a local registry at `~/.kinnoo/registry/` where agents can be published by name/version and installed by name. Includes listing and searching published agents.

**ACs:**
1. `kinnoo publish <archive.kno>` copies the archive to `~/.kinnoo/registry/<name>/<version>/`
2. `kinnoo install <name>` resolves the latest version from local registry and installs it (no network)
3. `kinnoo install <name>==<version>` installs a specific version from local registry
4. `kinnoo list` displays all locally published agents with name, version, and description
5. `kinnoo search <query>` filters the local registry by name/description substring match
6. Publishing the same name+version twice produces a clear error (no silent overwrite)
7. `kinnoo install <file.kno>` (file path) continues to work as before (V1 behavior preserved)

### feature14 — Interactive Mode

Add `--interactive` flag to `kinnoo run` that starts the agent in REPL mode, piping stdin to the agent process in a loop instead of passing a single CLI argument. Add `capabilities.interactive` manifest field.

**ACs:**
1. `kinnoo run <dir> --interactive` starts the agent and enters a REPL loop (prompts for input, displays output, repeats)
2. `/exit` command in the REPL terminates the session and the agent process
3. `/clear` command clears the terminal screen
4. `capabilities.interactive: true` is accepted as an optional manifest field
5. An agent started with `--interactive` receives each user input on stdin (one line per turn)
6. Agent stdout is displayed to the user after each input
7. Transcript of the session is saved to `outputs/` directory in the agent folder

### feature15 — Preflight Checks (`--preflight`)

Add `--preflight` flag to `kinnoo run` that validates the agent's environment before execution: Python version, env vars, entrypoint, and declared binary tools.

**ACs:**
1. `kinnoo run <dir> --preflight` runs all checks and reports results without executing the agent
2. Check: Python version matches `runtime.version` constraint in manifest
3. Check: All declared `env_vars` are set (or resolvable via `.env`)
4. Check: Entrypoint file exists at the declared path
5. Check: Dependencies in `requirements.txt` are installable (dry-run pip check)
6. Results are printed as a checklist with pass/fail status for each check
7. If all checks pass, prints "Ready to run" message; if any fail, prints actionable guidance

### feature16 — Additional Framework Templates

Add framework templates for `pydantic-ai`, `langgraph`, and `agno` to `kinnoo init --framework`. Each template demonstrates a real tool-calling pattern, not just "Hello World". (CrewAI template REMOVED for V2)

**ACs:**
1. `kinnoo init <name> --framework pydantic-ai` generates PydanticAI boilerplate with tool-calling example and correct `requirements.txt`
2. `kinnoo init <name> --framework langgraph` generates LangGraph stateful agent boilerplate and correct `requirements.txt`
3. `kinnoo init <name> --framework agno` generates Agno agent boilerplate and correct `requirements.txt`
4. Each generated agent passes `kinnoo.yaml` validation
5. Each generated `run.py` is syntactically valid Python
6. Each README.md includes framework-specific API key setup instructions

### feature17 — Run from Archive Directly

Enable `kinnoo run <archive.kno> "<input>"` to extract, install, and run an agent in one step from a `.kno` archive.

**ACs:**
1. `kinnoo run my-agent.kno "input"` extracts to a temporary directory, installs, and executes the agent
2. The temporary directory is cleaned up after execution completes
3. Exit code from the agent is propagated to the `kinnoo` process
4. Works with both one-shot and MCP server runtime types
5. If the archive is invalid, a clear error is shown before any extraction

### feature18 — Trust Baseline

Add transparency and trust features: display permission/dependency summary on install, warn on untrusted agents, and log run traces.

**ACs:**
1. `kinnoo install` displays a summary of what the agent requires (env_vars, dependencies, runtime type) before installing, and prompts for confirmation
2. If an agent is not from the local registry (installed from a raw `.kno` file), a warning is displayed: "This agent is from an unverified source"
3. `kinnoo run` logs a trace (timestamp, agent name, input summary, exit code) to `~/.kinnoo/logs/run.log`
4. `kinnoo run` displays the agent's declared `env_vars` and `dependencies` before first execution (first run only)
5. Log file does not contain the actual values of environment variables or secrets

### feature19 — `--mcp` flag on `kinnoo init`

Add `--mcp <server>` flag to `kinnoo init` that generates MCP client boilerplate alongside the framework template. Also add `--mcp-server` flag to scaffold an MCP server project.

**ACs:**
1. `kinnoo init <name> --framework pydantic-ai --mcp github` generates `run.py` with PydanticAI + GitHub MCP client boilerplate
2. `kinnoo init <name> --framework pydantic-ai --mcp filesystem` generates `run.py` with PydanticAI + Filesystem MCP client boilerplate
3. `--mcp` flag requires `--framework` to be specified; using `--mcp` without `--framework` prints a clear error
4. Generated `kinnoo.yaml` includes appropriate `env_vars` for the MCP server (e.g., `GITHUB_TOKEN` for github)
5. `kinnoo init <name> --mcp-server` generates an MCP server template with `runtime.type: mcp-server` in the manifest
6. Supported `--mcp` values for V2: `github`, `filesystem`, `sqlite`, `brave-search`
7. Using an unsupported `--mcp` value prints an error listing available options

**Verification**
- Run `python3 scripts/validate_project_manifests.py` after adding features to ensure FEATURES.txt is valid
- Each feature's ACs map directly to unit/integration tests that will be defined in TESTS.txt when tasks are created
- Dependency graph: verify no circular dependencies and Tier 1 features have no feature dependencies

**Decisions**
- feature7–9 (Tier 1) address tech debt first per user's explicit priority
- `--preflight` stays as a flag on `kinnoo run`, not a standalone `kinnoo doctor` (user's Q5 decision)
- `kinnoo test` excluded from V2 — pushed to V3 (user's Q5 decision)
- CrewAI REMOVED from V2 (per user instruction)
- `kinnoo search` folded into feature13 (Local Registry) as a sub-item (user's Q5 agreement)
- `--mcp` Pattern 1 only (self-contained embedded client) — Pattern 2 (composable) deferred to V3 (Q6 recommendation)
- Slogan remains: "Package any agent. Share it. Run it — with its tools, keys, and connections ready."
- All features have `tasks: []` initially — tasks and tests will be created in the next step per the Manifest Update Checklist

---

Does this feature breakdown look right? Any features you'd like to split, merge, reorder, or modify before I write them into FEATURES.txt?