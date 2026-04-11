# task459 Notes

## Summary
- Added language-specific `.gitignore` templates for complete scaffolds:
  - Python
  - JavaScript
  - TypeScript
  - OpenClaw
- Wired `.gitignore` selection by scaffold language/framework.
- Preserved task457 contract that `.gitignore` is emitted only for complete templates (not `--minimal`).
- Added task tests:
  - `tests/test_init.py::test_init_python_gitignore`
  - `tests/test_init.py::test_init_javascript_gitignore`
  - `tests/test_init.py::test_init_typescript_gitignore`
  - `tests/test_init.py::test_init_openclaw_gitignore`

## Files changed
- `src/kinnoo/init_command.py`
- `tests/test_init.py`
- `TASKS.txt`

## Test run
- Command:
  - `python3 -m pytest tests/test_init.py --testmon -k "test_init_python_gitignore or test_init_javascript_gitignore or test_init_typescript_gitignore or test_init_openclaw_gitignore"`
- Result:
  - `4 passed, 59 deselected`

## Teaching notes
- Treat scaffold templates as contracts: for each language variant, include both inclusion and exclusion assertions (for example, JS template should include `node_modules/` and exclude Python cache entries).
- Keep template emission deterministic and centralized so future UAT updates only touch one mapping point.
