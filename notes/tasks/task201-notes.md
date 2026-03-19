# Task201 - feature36 identity artifact signals for OpenClaw inference

## Summary
- Updated [src/kinnoo/analyzer.py](src/kinnoo/analyzer.py) to recognize OpenClaw identity files as explicit weighted signals:
  - required identity anchors: SOUL.md and AGENTS.md
  - optional identity anchor: USER.md
- Added identity evidence labels into framework confidence evidence so import diagnostics show why OpenClaw was inferred.
- Kept USER.md optional by making it additive-only; missing USER.md does not invalidate otherwise strong OpenClaw detection.
- Added task-linked test299 in [tests/test_analyzer.py](tests/test_analyzer.py):
  - test_feature36_identity_signal_detection

## Tests and results
- python3 -m pytest tests/test_analyzer.py::test_feature36_identity_signal_detection -> 1 passed

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: 0.

## Teaching notes
- Weighted-signal detection is more robust than binary checks because it can encode optional evidence without making it mandatory.
- Optional signals should be additive, not subtractive. This preserves stable behavior when optional files are absent.
- Evidence strings are part of operator UX. Keep them deterministic so users can trust and debug inference decisions quickly.
