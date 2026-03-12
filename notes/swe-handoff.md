# Feature15 SWE Handoff — Trust Baseline

## Scope
Implement feature15 through tasks `task98` to `task104` in order. The goal is to add transparency and trust features to kinnoo: install-time summary with consent gate, unverified source warning, run trace logging, code-level security invariant comments, and a heuristic env var exposure sweep in inspect/pack.

**Critical security rule:** No env var or secret VALUES may ever appear in output, logs, or code paths — ONLY names. This is the single most important invariant in this feature.

## Task execution order and dependencies

### Group 1 — Install trust (can be done first)
1. `task98` — Install summary display + yes/no prompt + `--yes`/`-y` flag (AC1)
2. `task99` — Unverified source confirmation prompt (AC2, depends on task98)

### Group 2 — Run trace logging (independent of Group 1)
3. `task100` — Run trace logging to `~/.kinnoo/logs/` (AC3)
4. `task101` — Log file secret-safety enforcement (AC4, depends on task100)

### Group 3 — Code quality + sweep (depends on Groups 1 and 2)
5. `task102` — Inline no-secret-values comments on all trust code (AC5, depends on task98 + task100)
6. `task103` — Env var exposure heuristic sweep in inspect + pack (AC6)

### Group 4 — Documentation (depends on all above)
7. `task104` — Docs for all trust baseline features (depends on task98, task99, task100, task103)

A single SWE agent can implement all seven tasks in one pass. Groups 1 and 2 are independent and can be done in parallel or either-first. Group 3 depends on both. Group 4 is last.

## Tests to implement (already declared in TESTS.txt)
- `task98` -> `test126`, `test127`
- `task99` -> `test128`
- `task100` -> `test129`, `test130`
- `task101` -> `test130`
- `task102` -> `test131`
- `task103` -> `test132`, `test133`
- `task104` -> `test134`

## Feature15 AC coverage mapping
- `AC1`: `test126` (summary + prompt), `test127` (--yes bypass), `test134` (docs)
- `AC2`: `test128` (unverified source), `test134` (docs)
- `AC3`: `test129` (trace log safe fields), `test134` (docs)
- `AC4`: `test130` (no secret values in log)
- `AC5`: `test131` (inline comments audit), `test134` (docs)
- `AC6`: `test132` (inspect sweep), `test133` (pack sweep), `test134` (docs)

## Design constraints (must follow)

### Install summary (task98, task99)
- Extract manifest from .kno archive using existing `read_manifest_from_kno_archive()` in `inspect_command.py`.
- Display env_var NAMES (use `normalize_env_vars()` from `schema.py`), dependency names (from `requirements.txt` inside archive), and runtime type.
- Prompt format: `"Continue with install? [y/N]:"` — default is No.
- `--yes`/`-y` flag: show summary but skip prompt.
- Unverified source check: look for `<archive_path>.sha256` file on filesystem. If missing → warn + prompt. If present → skip warning (don't verify hash — that's feature16).

### Run trace logging (task100, task101)
- Log file location: `~/.kinnoo/logs/run.<TIMESTAMP>.log`
  - Filename timestamp must be UTC only.
  - Example: `~/.kinnoo/logs/run.2026-03-11T18-42-13Z.log`
- Log format: single JSON object with exact safe fields:
  ```json
  {
    "timestamp": "2026-03-11T18:42:13Z",
    "agent_name": "my-agent",
    "agent-version": "1.2.0",
    "runtime_type": "one-shot",
    "exit_code": 0
  }
  ```
- JSON `timestamp` must be UTC only.
- **Never log:** input content, env var values, secrets, stdout, stderr.
- Create `~/.kinnoo/logs/` if it does not exist. If creation fails, print a warning to stderr but do not crash — logging is best-effort.
- Write the log after `run_agent()` completes (or fails), not before.

### Security invariant comments (task102)
- Pattern: `# [agent] SECURITY INVARIANT: only env var NAMES, never values`
- Place on or near every line that displays, logs, or formats env var or secret-related data.
- Applies to: install summary display, run trace log write, inspect env var output, preflight env var output, code sweep output.

### Env var exposure sweep (task103)
- New file: `src/kinnoo/code_sweep.py`
- Function: `sweep_env_var_exposure(agent_dir: Path, declared_env_vars: list[str]) -> list[str]`
- Scans all `.py` files under `agent_dir`, excluding `.venv/` directories.
- Regex patterns to match:
  ```python
  EXPOSURE_PATTERNS = [
      (r'print\s*\(.*os\.environ',   "print() with os.environ access"),
      (r'print\s*\(.*os\.getenv',     "print() with os.getenv() access"),
      (r'log\w*\.\w+\(.*os\.environ', "logging with os.environ access"),
      (r'log\w*\.\w+\(.*os\.getenv',  "logging with os.getenv() access"),
      (r'\.write\s*\(.*os\.environ',  "file write with os.environ access"),
      (r'\.write\s*\(.*os\.getenv',   "file write with os.getenv() access"),
  ]
  ```
- Returns warnings as `["<file>:<line>: <description>", ...]`
- Integration points:
  - `kinnoo inspect`: add "Security sweep:" section at bottom of output. Clean → `"Security sweep: no env var exposure patterns detected (heuristic)"`. Dirty → print each warning.
  - `kinnoo pack`: run sweep before archiving. Print warnings to stderr. Do NOT abort pack.
- Always print disclaimer: `"(heuristic scan — may produce false positives; not a substitute for code review)"`

## Files expected to change
- New file: `src/kinnoo/code_sweep.py`
- Modify: `src/kinnoo/cli.py` (--yes flag on install subparser)
- Modify: `src/kinnoo/install_command.py` (summary display, prompts)
- Modify: `src/kinnoo/run_command.py` (trace logging after execution)
- Modify: `src/kinnoo/inspect_command.py` (security sweep section)
- Modify: `src/kinnoo/pack_command.py` (security sweep warning)
- New test file: `tests/test_trust_baseline.py`
- Modify: `tests/test_docs.py` (add feature15 docs test)
- Modify: `README.md`, `docs/manifest-schema-reference.md` (documentation)

## SWE completion checklist
- [ ] Implement tasks `task98`..`task104` in order (following group dependencies).
- [ ] Implement tests `test126`..`test134` and ensure they pass.
- [ ] Run `python3 -m pytest tests/test_trust_baseline.py tests/test_docs.py -q` first, then full suite.
- [ ] Verify no env var values, secrets, or input content appear in ANY output or log path.
- [ ] Run `python3 src/validate_project_manifests.py` before handoff.
- [ ] Update task statuses to `needs-review` when complete.
- [ ] Write task notes in `notes/tasks/task98-notes.md` .. `notes/tasks/task104-notes.md`.
