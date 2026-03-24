# Task257 Notes - runtime.path Override for kinnoo run

Date: 2026-03-22

## Implementation Summary

Implemented support for an optional runtime executable override at `runtime.path` in `kinnoo.yaml`.

Behavior implemented:
1. Parse `runtime.path` from the runtime section.
2. If `runtime.path` resolves to an existing executable file, use it as the runtime executable.
3. If `runtime.path` is invalid (missing, non-file, or non-executable), print a warning and fall back to default runtime behavior.
4. Preserve existing behavior when `runtime.path` is not set.

Files updated:
- `src/kinnoo/run_command.py`
  - Added `runtime.path` resolution and validation.
  - Python runtime:
    - Uses `runtime.path` directly when valid.
    - Skips `.venv` creation and requirements install in this override mode.
    - Falls back to prior `.venv`/host-Python logic when override is absent or invalid.
  - Node runtime:
    - Uses `runtime.path` as the Node executable when valid.
    - Falls back to `node` when override is absent or invalid.
- `src/kinnoo/schema.py`
  - Added `runtime.path` to optional fields and type map (`str`).
- `src/kinnoo/validator.py`
  - Added semantic validation that `runtime.path` cannot be an empty string.
  - Error text: `Field 'runtime.path' must be a non-empty string.`

## Tests Added

Added targeted regression tests in `tests/test_cli.py`:
- `test_run_uses_runtime_path_python_override`
  - Verifies a valid alternate Python interpreter path in `runtime.path` is actually used.
  - Verifies reported runtime version matches the chosen interpreter and differs from the launcher interpreter.
- `test_run_uses_runtime_path_node_override`
  - Verifies a valid executable path in `runtime.path` is used for Node runtime.
  - Verifies invalid path fallback uses `node` and emits warning.

Test implementation notes:
- The Python override test uses `capfd` (not `capsys`) to avoid subprocess capture `fileno` issues.
- Alternate interpreter discovery filters out versions below the manifest constraint (`>=3.8`).

## Targeted Regression Run

Command:
```bash
python3 -m pytest --testmon tests/test_cli.py -k "test_run_uses_runtime_path_python_override or test_run_uses_runtime_path_node_override"
```

Result:
```text
2 passed, 50 deselected
```

## Previous Explanation: How kinnoo run Works Under the Hood

Your understanding is very close. Two details are slightly different in practice.

You run kinnoo run <my-agent>.
Correct. CLI dispatch for run is in cli.py:477.
kinnoo creates my-agent/.venv if missing, using python -m venv .venv with “global Python”.
Mostly correct, with an important nuance:
It creates .venv only when needed, via Python’s venv module at run_command.py:1228.
The interpreter used is the one executing kinnoo right now (sys.executable), not necessarily your machine default/global Python.
If .venv already exists, kinnoo reuses it; it does not auto-rebuild for a different Python version.
It only installs dependencies when requirements.txt exists and is non-empty at run_command.py:1221 and run_command.py:1236.
It runs base.py inside that venv using that venv’s Python.
Correct for normal Python runtime:
It resolves venv python at run_command.py:1266 and executes entrypoint with it at run_command.py:1468.
Special case: mcp-server runtime with no deps and no existing .venv may use host Python directly at run_command.py:1224 and run_command.py:1264.
On your setup/config idea:

Today: there is no dedicated kinnoo setup or kinnoo config command in CLI.
Yes, this is a good feature to add. A clean design is:
Add runtime.python_path in kinnoo.yaml (agent-level override).
Add global default in a user config file (for example ~/.config/kinnoo/config.yaml).
Resolution order: runtime.python_path -> global config python_path -> current sys.executable.
If chosen Python version differs from existing .venv, print a clear warning and offer recreate.
Practical way right now:

Run kinnoo with the exact interpreter you want.
Delete my-agent/.venv when switching Python versions so it is recreated with that interpreter.
Prefer per-version wrappers (like k312, k313) to avoid accidental interpreter drift.
