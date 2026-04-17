## Feature12 Review (Jerry)

- feature12 implements kinnoo publish as publishing to a local registry at ~/.kinnoo/
- this feature will largely be deprecated
- instead, kinnoo publish will publish to a remote registry. For now, we will mock a registry on the local filesystem as registry-scratch/...
- kinnoo pack will be refactored into a command that packs an agent to a local archive ~/.kinnoo/archive/
- these refactors will be implemented as feature13

# Feature12 deprecation notes

## Short deprecation summary
- Feature12 local-registry semantics were superseded by Feature13.
- Deprecated scope:
  - Tasks: `task69` to `task77`
  - Tests: `test96` to `test104`
- Deprecated tests are historical references and should not be re-enabled.

## Detailed implementation notes (deprecation pass)

### What was changed
- Marked `task69` to `task77` as `status: deprecated` in `TASKS.txt`.
- Marked `test96` to `test104` as `type: deprecated` in `TESTS.txt`.
- Added explicit `[agent] test deprecated` notes in `TESTS.txt` for each deprecated test, including replacement pointers to active Feature13 tests.
- Commented out deprecated pytest functions with `[agent] test deprecated` headers in:
  - `tests/test_registry.py`
  - `tests/test_cli_registry.py`
  - `tests/test_docs.py`

### Coupling and safety checks
- Verified no active test coupling to deprecated Feature12 pytest functions (definition-only legacy references before comment-out).
- Ensured deprecated tests are not executed by the targeted test run after comment-out.

### Replacement coverage mapping
- `test96` -> `test107`
- `test97` -> `test109`, `test111`, `test118`
- `test98` -> `test109`, `test110`
- `test99` -> `test112`, `test113`, `test116`, `test118`
- `test100` -> `test112`, `test113`
- `test101` -> `test112`, `test113`, `test116`
- `test102` -> `test114`
- `test103` -> `test115`
- `test104` -> `test117`

### Validation performed
- `python3 scripts/validate_project_manifests.py` -> passed.
- Targeted tests after deprecation edits:
  - `pytest -q tests/test_registry.py tests/test_cli_registry.py tests/test_docs.py` -> passed.

### Agent guidance for future edits
- Do not re-activate Feature12 deprecated tests unless explicitly requested by TechLead in a tracked task.
- For behavior changes in this area, update Feature13 tasks/tests instead.
- Preserve deprecation notes in `TESTS.txt` so migration rationale remains discoverable.
