# Task152 - feature25 interactive and non-interactive failure policy

## Summary
- Implemented task152 policy behavior in `src/kinnoo/run_command.py` for unhealthy service checks:
  - Non-interactive mode (`stdin` not TTY) now aborts immediately with explicit message.
  - Interactive mode prompts per unhealthy service with exact text:
    - `Service <name> is not healthy. Proceed anyway? [y/N]`
  - Proceed only when response is `y`; default/empty/non-yes aborts execution.
- Added task152 test coverage in `tests/test_cli.py`:
  - `test_feature25_non_interactive_aborts_on_unhealthy_service` (test233)
  - `test_feature25_interactive_prompt_allows_proceed_or_abort` (test234)
- Used a deterministic test strategy for interactive behavior by stubbing `_run_service_checks` in the interactive test, which isolates prompt-policy logic and avoids global subprocess side effects.

## Tests and results
- `python3 -m pytest tests/test_cli.py::test_feature25_non_interactive_aborts_on_unhealthy_service tests/test_cli.py::test_feature25_interactive_prompt_allows_proceed_or_abort` -> `2 passed`
- `python3 src/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Bug/error notes
- First approach to the interactive test patched `subprocess.Popen` globally via the module object and unintentionally affected other subprocess usage (`subprocess.run` in health-check paths), causing context-manager-related failures.
- Switched to a narrower seam: stubbing `run_command._run_service_checks` in the interactive test so only policy behavior is under test.
- Attempts in this continuation cycle for the repeated bug class: `1` successful strategy switch.

## Teaching notes
- For policy tests, isolate at the policy boundary instead of mocking deep global primitives. This lowers brittleness and keeps test intent clear.
- In Python, monkeypatching shared module attributes (like `subprocess.Popen`) can leak into unrelated call paths because imports reference the same module object.
- Agentic runtime pattern:
  - capability layer (`_run_service_checks`) produces state,
  - policy layer decides continue/abort/prompt,
  - testing each layer independently gives faster, more deterministic feedback.
