# Task189 - feature34 OpenClaw scaffold file and directory generation

## Summary
- Added OpenClaw scaffold templates in [src/kinnoo/templates.py](src/kinnoo/templates.py):
  - `OPENCLAW_PACKAGE_JSON_TEMPLATE`
  - `OPENCLAW_JSON_TEMPLATE`
  - `OPENCLAW_INDEX_MJS_TEMPLATE`
  - `OPENCLAW_DEFAULT_SKILL_TEMPLATE`
  - `OPENCLAW_AGENTS_MD_TEMPLATE`
  - `OPENCLAW_SOUL_MD_TEMPLATE`
- Updated OpenClaw framework routing in [src/kinnoo/init_command.py](src/kinnoo/init_command.py):
  - added `openclaw` to `SUPPORTED_FRAMEWORKS`,
  - normalized `--framework` to lowercase before passing through generation,
  - added scaffold generation branch for OpenClaw-specific files/directories.
- OpenClaw scaffold generation now creates required artifacts for AC1:
  - files: `package.json`, `openclaw.json`, `index.mjs`, `AGENTS.md`, `SOUL.md`, `skills/default/SKILL.md`
  - directories: `memory/`, `skills/`, `skills/default/`
- Added task-linked integration coverage in [tests/test_init.py](tests/test_init.py):
  - `test_feature34_openclaw_scaffold_structure` (test287),
  - validates required file and directory structure for deterministic paths.
- Updated [TASKS.txt](TASKS.txt):
  - `task189` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_init.py::test_feature34_openclaw_scaffold_structure` -> `1 passed`

## Bug/error notes
- Encountered one bug class during implementation:
  - `KeyError` from `.format(...)` against JSON template braces.
- Resolution:
  - escaped literal JSON braces in OpenClaw template strings using doubled braces (`{{` and `}}`).
- Same bug/error class fix attempts: `1`.

## Teaching notes
- When using Python string formatting with JSON templates, always escape non-placeholder braces (`{{` and `}}`) to avoid accidental placeholder parsing.
- For scaffold features, split generated outputs into:
  - baseline cross-framework files,
  - framework-specific overlays.
  This keeps template logic composable and reduces regression risk.
- Determinism in scaffolding is easiest to enforce with tests that assert exact relative paths for both files and directories, not just existence of top-level artifacts.
