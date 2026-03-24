# Task266 Notes - Add kinnoo check Command

Date: 2026-03-22

## Scope Implemented

Added `kinnoo check <agent-dir | github-url>` to run import-compatibility analysis, inspect, and preflight in one command with step-level PASS/FAIL and guidance.

## What Changed

- Updated src/kinnoo/cli.py:
  - Added `check` subcommand and dispatch.
- Added src/kinnoo/check_command.py:
  - Prepares target from local path or GitHub URL.
  - For URL, clones to `/tmp/kinnoo-agent-check/<repo>`.
  - Runs step sequence:
    1. import compatibility (analyzer-based)
    2. inspect
    3. preflight
  - Emits PASS/FAIL per step and actionable guidance on failure.
  - Returns non-zero on any step failure.

## Tests Added

- tests/test_cli.py::test_check_command_local_pass (test378)
- tests/test_cli.py::test_check_command_intelligent_failure (test379)

## Targeted Test Run

```bash
python3 -m pytest tests/test_cli.py -k "test_check_command_local_pass or test_check_command_intelligent_failure" -q
```

Result:

```text
2 passed
```

## Teaching Notes

`kinnoo check` is a small pipeline orchestrator:
- Shared context: local working directory.
- Ordered evaluators: analyzer -> inspect -> preflight.
- Aggregated status with localized remediation tips.

This mirrors AI evaluation pipelines where each gate contributes structured pass/fail evidence before promotion.