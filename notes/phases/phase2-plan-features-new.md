## Plan: Revised V2 Feature List

**TL;DR:** 10 features (feature7–feature16), focused exclusively on making `kinnoo install <agent> && kinnoo run <agent>` reliable and trustworthy for multi-tool, multi-secret Python agents. All template, interactive, and MCP features moved to V3. Every feature passes the filter: "Does this make install+run more reliable?"

### Overview Table

| ID | Title | Tier | Depends On | Effort | V2 Goal Justification |
|----|-------|------|------------|--------|----------------------|
| **Tier 1: Foundation (tech debt)** | | | | | |
| feature7 | CLI Refactor & Modular Architecture | 1 | — | Small | Unlocks all V2 work; fixes V1 hacks |
| feature8 | Packaging Robustness | 1 | — | Medium | THE core V2 problem — transitive deps, reliable archives |
| feature9 | Manifest Schema V2 Extensions | 1 | — | Small | Enables env_vars, metadata for registry/inspect |
| **Tier 2: Core ("it just works")** | | | | | |
| feature10 | Environment Variable / Secret Management | 2 | feature9 | Medium | Multi-secret agents need automated resolution |
| feature11 | `kinnoo inspect` Command | 2 | feature7 | Small | Transparency — see what an agent needs before install/run |
| feature12 | Local Registry | 2 | feature11 | Medium | Core package manager: publish, install-by-name, versioning |
| **Tier 3: Trust & Reliability** | | | | | |
| feature13 | Preflight Checks (`--preflight`) | 3 | feature10 | Medium | Validate everything before execution — "it just works" |
| feature14 | Trust Baseline | 3 | feature10 | Small | Install transparency, unverified source warnings, run logging |
| feature15 | Archive Integrity (Checksums) | 3 | feature8 | Small | Verify archives haven't been tampered with |
| feature16 | Pack Size Reporting & Warnings | 3 | feature8 | Small | Visibility into archive size; warn on large packs |

### Feature Details

---

#### feature7 — CLI Refactor & Modular Architecture

Extract install logic from monolithic [cli.py](src/kinnoo/cli.py) into a dedicated `install_command.py` module (matching [init_command.py](src/kinnoo/init_command.py) and [pack_command.py](src/kinnoo/pack_command.py)). Add `--version` flag. Clean up duplicate test in test_pack.py.

**ACs:**
1. Install logic lives in `src/kinnoo/install_command.py`, not inline in `cli.py`
2. `cli.py` imports and delegates to `install_command.py` for install operations
3. `kinnoo --version` prints the package version and exits
4. No duplicate test functions exist in the test suite
5. All existing V1 tests continue to pass after refactor

---

#### feature8 — Packaging Robustness

Fix transitive dependency bundling in `kinnoo pack` (currently uses `--no-deps`). Canonicalize archive format as zip. Implement fallback behavior for missing/failed wheel builds. Add cross-platform wheel detection with warnings.

**ACs:**
1. `kinnoo pack` includes transitive dependencies (not just direct), so `pip install` in an offline venv succeeds
2. Archive format is zip with `.kno` extension; all docs/code/notes reference zip consistently
3. If a wheel build fails for a dependency, `kinnoo pack` warns but continues (does not abort the entire pack)
4. `kinnoo install` falls back to PyPI install for any missing wheels (with a warning message)
5. A packed agent with transitive deps installs and runs correctly in a fresh venv with no internet access (offline install test)
6. If platform-specific wheels are detected during packing, a warning is printed: "Archive contains platform-specific wheels that may not install on other operating systems"

---

#### feature9 — Manifest Schema V2 Extensions

Add optional fields to `kinnoo.yaml` schema: `description`, `author`, `license`, `env_vars` (list[string]). All additions are non-breaking — existing V1 manifests remain valid.

**ACs:**
1. `description` (string), `author` (string), `license` (string) are accepted as optional fields; absent is valid
2. `env_vars` (list[string]) is accepted as an optional field; validator ensures it is a list of strings when present
3. A V1 manifest (without any new fields) still passes validation with no errors
4. Invalid types for new fields (e.g., `env_vars` as a string, `description` as a number) produce specific error messages naming the field and expected type
5. `kinnoo init` templates include `description` and `author` fields with placeholder values
6. `env_vars` items are validated as non-empty strings (no empty string items in the list)

**Note:** `runtime.type` list support (for interactive, mcp-server) is deferred to V3 since those runtime modes are V3 features. V2 keeps `runtime.type` as a single string with only `one-shot` as a valid value.

---

#### feature10 — Environment Variable / Secret Management (`env_vars`)

When running an agent whose `kinnoo.yaml` declares `env_vars`, the runtime checks, resolves, and injects the required variables into the subprocess environment. Resolution order: current environment → `.env` file in agent directory → interactive prompt. **Secret values must NEVER be displayed, logged, or echoed anywhere in the codebase.**

**ACs:**
1. If `env_vars` declares variables and all are set in the current environment, agent runs normally with those vars injected into the subprocess
2. If a declared env var is missing from environment, kinnoo checks for a `.env` file in the agent directory and loads matching variables
3. If a declared env var is still missing after `.env` check, kinnoo prompts the user interactively with **masked input** (characters not echoed to terminal)
4. All resolved env vars are injected into the subprocess environment when executing the agent
5. If the user declines to provide a missing env var (e.g., Ctrl+C), execution aborts with a clear message listing which variable was not provided
6. Agents without `env_vars` in manifest are unaffected — no prompting, no `.env` loading, existing V1 behavior unchanged
7. **No code path in the entire codebase ever prints, logs, or displays the VALUE of any env var or secret** — only variable NAMES may appear in output or logs

---

#### feature11 — `kinnoo inspect` Command

New CLI command that reads and displays manifest metadata from a `.kno` archive or agent directory. Provides transparency into what an agent requires before install/run.

**ACs:**
1. `kinnoo inspect <agent-dir>` reads `kinnoo.yaml` and displays: name, version, description, author, license, dependencies, env_var NAMES (not values), runtime type
2. `kinnoo inspect <archive.kno>` reads manifest from inside the zip archive without extracting the full archive to disk
3. Output is human-readable formatted text (not raw YAML dump)
4. Missing optional fields are omitted from output (not shown as "None" or empty)
5. Invalid manifest produces a clear error (reuses feature1 validator)
6. `kinnoo inspect` without arguments prints usage help

---

#### feature12 — Local Registry (`kinnoo publish`, `kinnoo install <name>`, `kinnoo list`, `kinnoo search`)

Implement a local registry at `~/.kinnoo/registry/` where agents can be published by name/version and installed by name. Version is extracted from the archive's `kinnoo.yaml`. Code is structured behind an abstraction so swapping to a remote backend in V3 is straightforward.

**ACs:**
1. `kinnoo publish <archive.kno>` extracts name and version from the archive's `kinnoo.yaml` and copies the archive to `~/.kinnoo/registry/<name>/<version>/`
2. `kinnoo publish <archive.kno> --local` does the same (explicit local flag for forward-compatibility)
3. `kinnoo install <name>` resolves the latest version from local registry and installs it (no network required)
4. `kinnoo install <name>==<version>` installs a specific version from local registry
5. `kinnoo list` displays all locally published agents with name, latest version, and description
6. `kinnoo search <query>` filters the local registry by name/description substring match
7. Publishing the same name+version twice produces a clear error (no silent overwrite)
8. `kinnoo install <file.kno>` (file path) continues to work as before (V1 behavior preserved)
9. Publish/resolve logic is behind an abstraction (e.g., `RegistryBackend` interface) so swapping local for remote is a minimal change

---

#### feature13 — Preflight Checks (`--preflight`)

Add `--preflight` flag to `kinnoo run` that validates the agent's environment before execution. Catches missing deps, wrong Python version, missing secrets — gives actionable guidance instead of cryptic runtime errors.

**ACs:**
1. `kinnoo run <dir> --preflight` runs all checks and reports results **without executing the agent**
2. Check: Python version matches `runtime.version` constraint in manifest
3. Check: All declared `env_vars` NAMES are resolvable (set in env or in `.env` file) — **never displays values**
4. Check: Entrypoint file exists at the declared path
5. Check: All dependencies in `requirements.txt` are installed in the venv (or installable)
6. Results are printed as a checklist with pass/fail status for each check
7. If all checks pass, prints "Ready to run"; if any fail, prints actionable guidance per failed check

---

#### feature14 — Trust Baseline

Add transparency and trust features: display dependency/secret summary on install, warn on untrusted source agents, and log run traces. **Absolute rule: no env var or secret VALUES ever appear in output, logs, or code paths.**

**ACs:**
1. `kinnoo install` displays a summary of what the agent requires (env_var NAMES, dependency NAMES, runtime type) before installing, and prompts for yes/no confirmation
2. If an agent is installed from a raw `.kno` file (not from the local registry), a warning is displayed: "This agent is from an unverified source"
3. `kinnoo run` logs a trace to `~/.kinnoo/logs/run.log` containing ONLY: timestamp, agent name, runtime type, and exit code — **no input content, no env var values, no secrets**
4. `kinnoo run` displays the agent's declared env_var NAMES and dependency NAMES before first execution (first run only) — **never values**
5. Log file never contains actual values of environment variables, secrets, or user input
6. All trust-related display and logging code includes inline comments documenting the "no secret values" invariant

---

#### feature15 — Archive Integrity (Checksums)

Generate and verify SHA256 checksums for `.kno` archives. Enables detection of tampered or corrupted archives.

**ACs:**
1. `kinnoo pack` generates a `.kno.sha256` checksum file alongside the `.kno` archive
2. `kinnoo install <file.kno>` checks for a `.kno.sha256` file; if present, verifies the archive matches before extracting
3. If checksum verification fails, install aborts with a clear error: "Archive integrity check failed — the file may be corrupted or tampered with"
4. If no `.kno.sha256` file is present, install proceeds with a warning: "No checksum file found — archive integrity not verified"
5. `kinnoo publish` stores the checksum alongside the archive in the registry
6. `kinnoo inspect` displays the archive checksum if available

---

#### feature16 — Pack Size Reporting & Warnings

Report archive size after packing and warn when archives are unusually large (common with heavy dependency trees like LangChain).

**ACs:**
1. `kinnoo pack` prints the final archive size in human-readable format (e.g., "Archive size: 45.2 MB") after packing
2. If archive size exceeds 100MB, a warning is printed: "Warning: archive is large (X MB). Consider whether all dependencies are necessary."
3. `kinnoo inspect` displays the archive size when inspecting a `.kno` file
4. `kinnoo list` includes archive size in the registry listing

---

### What Moved to V3

These features from the previous 32-feature plan are deferred to V3 per the strategic alignment:

| Deferred Feature | Reason |
|-----------------|--------|
| All interactive mode features (18-24) | Runtime extension, not packaging. V3 target: "Connected Agent" |
| All MCP features (25-32) | Advanced runtime, not packaging. V3 target: "Connected Agent" |
| Per-framework one-shot templates (pydantic-ai, langgraph, agno) | Agent creation, not packaging. `kinnoo init` is convenience, not core |
| `runtime.type` list support | Not needed until interactive/mcp modes exist in V3 |
| Run from archive directly | Convenience, not reliability |

### V2 Success Test (restated)

A developer on Machine A builds a LangChain+Tavily agent (multi-tool, multi-secret), runs:
```bash
kinnoo pack ./my-agent && kinnoo publish ./my-agent-1.0.0.kno
```

A developer on Machine B (same OS) runs:
```bash
kinnoo install my-agent
# → displays deps + env_var names, prompts for confirmation
# → installs from local registry
kinnoo run ./my-agent "What's the weather in NYC?"
# → prompts for OPENAI_API_KEY, TAVILY_API_KEY (masked input)
# → runs agent successfully
```

Zero manual setup beyond providing secrets. Every feature in this list serves that scenario.

### Decisions Log

- **Reduced from 32 features to 10.** Applied the filter: "Does this make install+run more reliable?" ruthlessly.
- **All template features moved to V3.** `kinnoo init` is convenience, not core packaging. Existing V1 templates (gemini, chatgpt, claude-chat) are sufficient for V2.
- **All interactive/MCP features moved to V3.** These are runtime extensions for the "Connected Agent" archetype.
- **Added feature15 (Archive Integrity) and feature16 (Size Reporting).** These were identified in the packaging robustness analysis but weren't in the previous plan. They directly serve trust and reliability.
- **`runtime.type` stays single-string in V2.** List support deferred until V3 interactive/mcp modes need it.
- **Kept env_vars naming** — industry-appropriate for "list of variable names."
- **No `--force` flag** — safety first, consistent with V1 decision.
