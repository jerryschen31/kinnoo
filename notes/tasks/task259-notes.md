# Task259 Notes - Add --preflight to kinnoo pack

Date: 2026-03-22

## Scope Implemented

Implemented task259 by adding `--preflight` support to `kinnoo pack`, integrating preflight pass/fail flow control, persisting PASS metadata in `kinnoo.yaml`, and adding focused automated tests mapped to `test366` and `test367`.

## What Changed

### 1) CLI wiring for pack --preflight
Updated `src/kinnoo/cli.py`:
- Added `--preflight` flag to the `pack` subcommand parser.
- Passed `preflight` argument through to `pack_agent(...)`.

### 2) Preflight gate and metadata persistence in pack flow
Updated `src/kinnoo/pack_command.py`:
- Extended `pack_agent(...)` signature with `preflight: bool = False`.
- When `--preflight` is enabled:
  1. Calls `run_preflight(abs_agent_dir)`.
  2. If preflight PASS (`exit code == 0`):
     - writes `preflight_status: PASS`
     - writes `preflight_date: <UTC ISO8601>`
     - persists metadata to `kinnoo.yaml` before archive creation.
  3. If preflight FAIL:
     - prints warning to stderr,
     - prompts user: `Preflight failed. Continue packing anyway? [y/N]:`
     - aborts pack unless user explicitly confirms with `y`.

This preserves safety-by-default while still allowing operator override on failing readiness checks.

## Tests Added (Task259)

Updated `tests/test_pack.py`:
- `test_pack_preflight_pass_records_status` (test366)
  - Runs `kinnoo pack <agent> --preflight` on a fixture that passes preflight.
  - Verifies preflight PASS appears in output.
  - Verifies `kinnoo.yaml` contains `preflight_status: PASS` and `preflight_date`.

- `test_pack_preflight_fail_warns` (test367)
  - Uses fixture with non-empty `requirements.txt` and no `.venv` to force preflight FAIL.
  - Runs `kinnoo pack <agent> --preflight` with interactive confirmation `y`.
  - Verifies FAIL diagnostics + warning + continuation prompt are emitted.
  - Verifies pack still succeeds after explicit confirmation.

## Targeted Test Run

Command:
```bash
python3 -m pytest tests/test_pack.py -k "test_pack_preflight_pass_records_status or test_pack_preflight_fail_warns" -q
```

Result:
```text
2 passed, 22 deselected
```

## Teaching Notes

### Why this flow uses warning + explicit confirmation
In agent packaging pipelines, preflight checks are a quality gate, not always a hard validity gate. Some teams still need to produce artifacts for debugging, CI triage, or downstream environments.

This pattern balances both needs:
- default safety: FAIL warns loudly and blocks unless user confirms,
- operational flexibility: explicit override allows packaging when intentionally needed.

### Design pattern takeaway for agentic systems
This is a practical example of a "human-in-the-loop escalation" policy:
- automated evaluator (preflight) classifies state as PASS/FAIL,
- system surfaces actionable diagnostics,
- operator makes a deliberate continuation decision.

This pattern is broadly useful for AI/agent toolchains where strict hard-fail behavior can block useful workflows, but silent continuation would be risky.
