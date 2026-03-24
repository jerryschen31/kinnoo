# Task277 Notes - E2E Validation with Representative Agents

## What was implemented
- Added `tests/test_cli.py::test_e2e_python_oneshot` (test400):
  - Builds a representative one-shot Python agent fixture.
  - Executes full `import -> pack -> install -> run` flow.
  - Verifies command success and expected runtime output.
- Added `tests/test_cli.py::test_e2e_mcp_server` (test401):
  - Builds a representative MCP-server runtime fixture.
  - Executes full `import -> pack -> install -> run` flow.
  - Verifies startup signal appears in output.
- Updated both E2E tests to pass `--allow-unverified-publisher` during install for non-interactive unsigned local test archives.

## Targeted regression run
Command:
```bash
python3 -m pytest tests --testmon -k "test_e2e_python_oneshot or test_e2e_mcp_server"
```
Result:
```text
2 passed, 388 deselected
```

## Validation matrix (representative subset)
- one-shot Python script: PASS
- MCP server runtime: PASS

## Teaching notes
- Why these tests are valuable:
  - They assert real workflow seams (artifact creation, install policy, runtime invocation), not just isolated unit behavior.
- Why the unverified publisher flag was needed:
  - Local test artifacts are unsigned, and current install policy blocks non-interactive installation without explicit override.
- Interview angle (platform reliability):
  - E2E tests should model production constraints (security flags, packaging conventions) to catch policy regressions that unit tests miss.
