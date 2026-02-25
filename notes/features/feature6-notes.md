# Feature6 — kinnoo install: SWE Agent Handoff Notes

## Overview
Feature6 implements the `kinnoo install` CLI command for installing packaged agent archives (.kno). The command extracts files, validates the manifest, sets up the environment, installs dependencies, and ensures the agent is runnable.

## Tasks to Implement
- task29: CLI argument parsing and usage error for kinnoo install
- task30: Extract .kno archive to new directory with collision handling
- task31: Validate manifest before installation
- task32: Create Python venv and install dependencies from wheels
- task33: Ensure agent is runnable with kinnoo run after install
- task34: Error handling for invalid archive or missing files
- task35: Prevent overwrites unless --force flag is provided

## Implementation Guidance
- Follow modular coding standards: each task should be implemented in a dedicated function or module.
- Use clear error messages and handle all edge cases (missing arguments, directory collisions, invalid manifest, missing files, etc.).
- Reference the validator from feature1 for manifest validation (do not duplicate validation logic).
- Use Python's standard library for venv creation and file extraction (tar/gzip).
- Ensure all dependencies are installed from wheel files included in the archive.
- The install command should not overwrite directories unless --force is specified.
- After install, the agent must be runnable with `kinnoo run <agent-dir> "<input>"`.

## Testing
- Each task is linked to a test case (test51–test57) in TESTS.txt. Implement unit and integration tests as specified.
- Run `python3 src/validate_project_manifests.py` after changes to ensure manifest integrity.

## Manifest and Documentation
- Update TASKS.txt and TESTS.txt as you implement and test each task.
- Document any design decisions or edge case handling in this file for future reference.

## Questions or Issues
- If you encounter ambiguous requirements or edge cases, document them here and notify the TechLead agent for clarification.

---
Handoff prepared by TechLead Agent, 2026-02-24.

## Task29 Implementation Summary (2026-02-24)

### Overview
- Implemented the `kinnoo install` CLI subcommand argument parsing and usage error handling.
- Added `install` subcommand to the CLI parser with required `archive_path` argument.
- If the argument is missing, prints a clear usage error and exits with a non-zero code.
- Inline comments added to explain logic and decisions.

### Test Coverage
- Created `tests/test_cli_install.py` for test51 (usage error for missing archive argument).
- Test runs the CLI via script path and verifies:
  - Exit code is non-zero when argument is missing.
  - Usage error message is printed to stderr.

### Test Results
- Test51 passed successfully:
  - CLI prints correct usage error.
  - Exits with code 1 when archive argument is missing.

### Best Practices & Teaching Notes
- CLI argument validation is performed before main logic to prevent runtime errors.
- Tests use script path for local development, not module entry point.
- Modular, maintainable CLI code structure.

### Next Steps
- Proceed to implement extraction and validation logic for task30 and beyond.
- Continue to follow modular coding standards and robust error handling.

---
# kinnoo install command (task29) implementation summary

## Implementation
- Added `kinnoo install` command block to src/kinnoo/cli.py.
- Implements extraction of .kno archive, manifest validation, venv setup, dependency install, collision handling, force overwrite, and error handling.
- Modularized logic for maintainability and clarity.
- Inline comments explain design decisions and error handling.

## Tests (test51–test57)
- Added tests to tests/test_cli.py:
  - test51: Archive missing prints usage error and exits non-zero.
  - test52: Extracts archive and creates agent directory.
  - test53: Validates manifest and aborts if invalid.
  - test54: Sets up venv and installs wheels.
  - test55: Aborts if directory exists and --force not given.
  - test56: Overwrites directory if --force is given.
  - test57: Installed agent is runnable with kinnoo run.

## Results
- Ran `python3 -m pytest --maxfail=5 --disable-warnings -v`.
- All tests passed (49/49), including install command tests.
- Implementation meets requirements for task28 and feature6.

## Notes
- Error handling covers all edge cases: missing archive, invalid manifest, directory collision, missing files.
- Manifest validation uses feature1 validator for consistency.
- Venv and dependency install use Python standard library and pip.
- Agent is confirmed runnable after install.

## Next Steps
- Review for further edge cases or improvements.
- Update documentation if needed.

### Teaching Notes (CLI Argument Validation & Testing)
- Always validate CLI arguments before main logic to prevent runtime errors and improve user experience.
- Usage errors should be clear and actionable, guiding the user to correct usage.
- When testing CLI tools in Python, ensure the entry point is accessible. If not installed as a package, use the script path for testing.
- Modular CLI design and robust error handling are key for maintainability.

---
SWE agent implementation complete for task289