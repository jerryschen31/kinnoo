# Task179 - feature32 daemon start path and persisted state

## Summary
- Implemented daemon runtime start behavior in `src/kinnoo/run_command.py`:
	- Added a `runtime.type == daemon` branch in `run_agent`.
	- Launches daemon processes detached (`start_new_session=True`) and returns terminal control immediately.
	- Writes daemon stdout/stderr to a deterministic agent-local log file.
	- Persists deterministic lifecycle state metadata for future control commands.
	- Emits clear operator hints after successful daemon start.
- Added daemon lifecycle helpers to `src/kinnoo/supervisor.py`:
	- `daemon_runtime_dir(...)`
	- `daemon_state_path(...)`
	- `daemon_log_path(...)`
	- `build_daemon_state_payload(...)`
	- `write_daemon_state(...)` with atomic replace semantics.
- Added task-linked integration coverage in `tests/test_cli.py`:
	- `test_feature32_run_daemon_start_persists_state` (test277)
	- Covers both Python and Node.js daemon fixtures.
	- Verifies run exits cleanly, daemon metadata is persisted, and operator-facing hints are printed.
- Updated `TASKS.txt`:
	- `task179` set to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli.py::test_feature32_run_daemon_start_persists_state` -> `2 passed`

## Bug/error notes
- Encountered one test-fixture issue:
	- Monkeypatched `subprocess.Popen` interfered with Python venv creation internals (`unexpected keyword argument 'executable'`).
- Fix:
	- Pre-created minimal `.venv/bin/python` in the Python daemon fixture to avoid invoking real `venv.create` during this focused test.
- Same bug/error class fix attempts: `1` (well below the 5-attempt cap).

## Teaching notes
- Control-plane-first daemon design:
	- A daemon feature becomes maintainable when lifecycle state is explicit and deterministic (state file + log path + pid + runtime metadata). This enables stop/attach/logs without brittle process discovery.
- Testability pattern for process-launch code:
	- For lifecycle flows, mock process launch at the boundary and assert persisted artifacts + operator output. This gives high confidence without flaky long-running subprocess behavior.
- Compatibility discipline:
	- Excluding daemon mode from one-shot JSON output enforcement avoids accidental behavior coupling and keeps runtime-type semantics clean for incremental rollout.
