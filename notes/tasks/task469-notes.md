# Task469 - install default openclaw install path

## Summary
- Added OpenClaw-aware install default target path resolution.
- When no target dir is provided and the manifest is OpenClaw (`framework: openclaw`), install now defaults to `~/.openclaw/workspace-<agent-name>`.
- Preserved explicit target-dir override behavior.

## Files changed
- src/kinnoo/install_command.py
- tests/test_cli_install.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli_install.py --testmon -k "test_install_openclaw_default_path"
- Result:
  - 1 passed, 23 deselected

## Teaching notes
- Feature detection should use manifest semantics (framework/type) instead of filename or path heuristics.
- For default path behavior, tests should validate both default and explicit-override flows to lock in user intent and backward compatibility.
