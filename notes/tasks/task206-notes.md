# Task206 - feature37 lifecycle script detection warnings and ignore-scripts

## Summary
- Updated [src/kinnoo/cli.py](src/kinnoo/cli.py) install parser and dispatch wiring to add `--ignore-scripts`.
- Updated [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
  - Detect lifecycle scripts declared in `package.json` (`preinstall`, `install`, `postinstall`, `prepublish`, `preprepare`, `prepare`, `postprepare`).
  - Emit warning-first lifecycle visibility when scripts are detected.
  - Emit deterministic script policy line (`allowed` or `ignored`).
  - Pass `--ignore-scripts` to Node package-manager install invocation when requested.
- Added task-linked integration coverage in [tests/test_cli_install.py](tests/test_cli_install.py):
  - `test_feature37_lifecycle_scripts_warning_and_ignore_scripts_mode` (test304),
  - validates lifecycle warning output,
  - validates deterministic policy output,
  - validates package-manager invocation includes `--ignore-scripts` only when requested.
- Updated [TASKS.txt](TASKS.txt):
  - `task206` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_install.py::test_feature37_lifecycle_scripts_warning_and_ignore_scripts_mode` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Lifecycle scripts are supply-chain risk multipliers because they execute code at install time; warning-first visibility helps operators make informed trust decisions.
- Security policy flags should be explicit and orthogonal: one flag for vulnerability override (`--allow-vulnerable`) and one for script execution policy (`--ignore-scripts`).
- Deterministic output strings are important for CI regression safety and downstream machine-readable trace generation in later tasks.
