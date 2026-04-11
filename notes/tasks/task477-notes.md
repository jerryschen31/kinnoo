# Task477 - search remove openclaw-skills and generalize JSON output

## Summary
- Removed `--openclaw-skill(s)` handling from search parser/dispatch.
- Removed OpenClaw skill delegation path from search command implementation.
- Refactored search `--json` into a general structured output mode for local and remote search results.

## Files changed
- src/kinnoo/cli.py
- src/kinnoo/search_command.py
- tests/test_cli_registry.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli_registry.py --testmon -k "test_search_openclaw_skills_removed or test_search_json_output"
- Result:
  - 2 passed, 10 deselected

## Teaching notes
- When deprecating an option, remove both parser exposure and backend execution paths to avoid zombie code and accidental partial behavior.
- General JSON search output should preserve filtering semantics while returning a stable envelope (`query`, `source`, `results`) for downstream tooling.
