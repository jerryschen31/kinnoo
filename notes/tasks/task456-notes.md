# task456 Notes

## Summary
- Changed Python entrypoint defaults from `run.py` to `main.py` in init scaffolding.
- Updated template manifest defaults so Python entrypoints are written as `main.py`.
- Updated Python framework scaffold generation logic to write `main.py` for framework templates and vanilla Python templates.
- Updated Python README template references from `run.py` to `main.py`.
- Added regression test:
  - `tests/test_init.py::test_init_python_entrypoint_main_py`

## Files changed
- `src/kinnoo/init_command.py`
- `src/kinnoo/templates.py`
- `tests/test_init.py`
- `TASKS.txt`

## Test run
- Command:
  - `python3 -m pytest tests/test_init.py --testmon -k test_init_python_entrypoint_main_py`
- Result:
  - `1 passed, 54 deselected`

## Teaching notes
- Rename migrations are safest when done in three synchronized layers: emitted file names, manifest metadata defaults, and generated docs/examples.
- Keep regression tests focused on both filesystem output and manifest contract fields; this catches partial migrations where only one side updates.
