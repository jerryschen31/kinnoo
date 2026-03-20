# Task193 - feature34 deterministic scaffold output without openclaw CLI dependency

## Summary
- Added task-linked test291 in [tests/test_init.py](tests/test_init.py):
  - `test_feature34_scaffold_deterministic_without_openclaw_cli`.
- Test291 enforces three guarantees for OpenClaw scaffold generation:
  - deterministic output by comparing full file-content snapshots across two independent `init_agent(...)` runs,
  - no external `openclaw` binary shell-out by guarding subprocess executable usage,
  - no `openclaw` CLI binary requirement by running `kinnoo init --framework openclaw` with an empty `PATH`.
- Added an implementation note in [src/kinnoo/init_command.py](src/kinnoo/init_command.py) documenting that OpenClaw scaffold generation is template-driven and does not shell out.
- Updated [TASKS.txt](TASKS.txt):
  - `task193` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_init.py::test_feature34_scaffold_deterministic_without_openclaw_cli` -> `1 passed`

## Bug/error notes
- One bug encountered and resolved:
  - initial subprocess guard incorrectly treated framework argument token `openclaw` as an executable invocation.
  - fixed by checking only the executable token (`argv[0]`) for `openclaw`.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- Determinism tests for scaffolders are strongest when they compare a complete normalized artifact snapshot (relative file paths + file contents), not only file existence.
- Shell-out guard tests should validate the command executable (`argv[0]`) instead of scanning all tokens; otherwise valid arguments can produce false positives.
- Testing with a constrained environment (for example `PATH=""`) is a practical way to prove a flow is independent from optional external binaries and remains CI/offline safe.
