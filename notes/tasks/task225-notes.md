# Task225 - feature41 permission violation enforcement and kill switch

## Summary
- Added deterministic violation enforcement policy resolution in src/kinnoo/runtime_monitor.py:
  - warn_continue for soft violations in warn mode,
  - kill_switch_terminate for hard/critical violations,
  - explicit reason codes for machine-consumable outcomes.
- Integrated policy enforcement into sandbox violation handling in src/kinnoo/run_command.py:
  - violation events now include enforcement_action and reason_code,
  - warn mode records violation and continues execution,
  - hard violations trigger deterministic kill-switch termination path.
- Added mapped test323 in tests/test_cli.py:
  - test_feature41_violation_enforcement_and_kill_switch,
  - validates warn-only continuation path and hard kill-switch path,
  - validates enforcement fields in persisted .kinnoo/violation-events.jsonl.
- Updated TASKS.txt: task225 -> needs-review.

## Tests and results
- python3 -m pytest tests/test_cli.py::test_feature41_violation_enforcement_and_kill_switch -> 1 passed

## Bug/error notes
- Bug class 1: assumption mismatch between expected stdout diagnostics and actual structured diagnostic format.
  - Fix attempts: 2
  - Resolution: assert deterministic enforcement semantics primarily through violation event payload fields, while keeping minimal user-facing output assertions.
- Bug class 2: misplaced assertions due test insertion boundary issue in tests/test_cli.py.
  - Fix attempts: 1
  - Resolution: restored prior test function boundaries and moved assertions back to the correct test.
- 5-attempt cap status: no bug/error class exceeded 5 attempts.

## Teaching notes
- For security-policy enforcement, separate policy decision (action/reason code) from rendering/output format. This makes tests robust and contracts stable for automation.
- Treat persisted event artifacts as primary audit truth for security controls; CLI text should remain operator-friendly but not be the only assertion surface.
- Hard-violation handling should be deterministic and capability-aware (for example shell execution as critical), while soft paths can support controlled warn-and-continue modes for progressive rollout.
