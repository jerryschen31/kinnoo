# Task169 - feature31 run path for Node.js entrypoints

## Summary
- Implemented runtime-language branching in [src/kinnoo/run_command.py](src/kinnoo/run_command.py):
  - Added `runtime.language` resolution from manifest runtime section.
  - Preserved Python behavior by keeping existing `.venv` bootstrap and `requirements.txt` install path under `runtime.language: python`.
  - Added Node.js run path for `runtime.language: nodejs` using `node <entrypoint> <input>` plus passthrough args.
  - Preserved stdout/stderr streaming and exit-code propagation by reusing existing subprocess execution flow.
  - Added explicit error for unsupported runtime.language values.
- Added task169 scoped regression test in [tests/test_cli.py](tests/test_cli.py):
  - `test_feature31_run_nodejs_entrypoint_streams_and_propagates_exit` (test265)
  - Verifies node command argument contract, output surfacing on stdout/stderr, propagated exit code, and no Python venv creation for node runtime.
- Updated `task169` status to `needs-review` in [TASKS.txt](TASKS.txt).

## Tests and results
- `python3 -m pytest tests/test_cli.py::test_feature31_run_nodejs_entrypoint_streams_and_propagates_exit` -> `1 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Runtime polymorphism in CLIs is safest when language-specific setup is isolated behind an early manifest-derived branch. This avoids leaking Python assumptions (like `.venv`) into non-Python runtimes.
- Behavior parity does not mean identical internals. For feature31 AC2, parity means preserving externally visible contracts: input arg forwarding, streamed output, and exit-code propagation.
- For cross-runtime tests, deterministic subprocess fakes are often better than shelling out to real language runtimes in unit/integration boundaries. They keep the test reliable while still validating command construction and observable I/O semantics.
