# Task202 - feature36 manifest validity and unresolved TODO guidance

## Summary
- Updated [src/kinnoo/import_command.py](src/kinnoo/import_command.py) to validate generated `kinnoo.yaml` after import write using the existing validator contract.
- Added deterministic validation output in import flow:
  - `Generated manifest validation: PASS` when schema validation succeeds.
  - `Generated manifest validation: WARNING` with explicit validator errors when it does not.
- Added unresolved guidance support for warning-first onboarding:
  - emits `TODO guidance:` section when unresolved confidence conditions exist,
  - includes explicit entrypoint/runtime/framework follow-up instructions,
  - includes entrypoint compatibility warning details when present.
- Added task-linked test300 in [tests/test_cli_import.py](tests/test_cli_import.py):
  - `test_feature36_manifest_valid_or_todo_guidance`
  - validates both complete valid path and unresolved warning/TODO path.
- Updated [TASKS.txt](TASKS.txt):
  - `task202` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_import.py::test_feature36_manifest_valid_or_todo_guidance` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Post-generation validation is a practical guardrail for inference-driven tooling: it catches contract issues at the point operators need actionable feedback.
- Distinguish schema validity from operational readiness. A manifest can be schema-valid yet still need TODO guidance (for example uncertain entrypoint compatibility).
- Deterministic warning text is crucial for both UX trust and regression testing stability.
