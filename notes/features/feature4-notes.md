---
# SWE Agent Handoff Brief — Feature4: kinnoo init --framework Flag

## Feature Overview

**Title:** kinnoo init --framework flag for LLM agent templates  
**Goal:** Extend kinnoo init CLI to support a --framework flag, generating agent directories pre-populated with boilerplate for Gemini, ChatGPT, or Claude-Chat LLM APIs.

---

## Task Breakdown

### Task 16: CLI Argument Parsing and Validation

- Update kinnoo init CLI to accept an optional --framework flag.
- Validate the value of --framework:
  - Supported values: gemini, chatgpt, claude-chat
  - If an unsupported value is provided (e.g., langgraph, pigglypoo), print:
    - "Unsupported framework. The supported frameworks are: gemini, chatgpt, claude-chat."
    - General usage message for kinnoo init.
  - Exit without creating files/directories.

**Acceptance Criteria:**
- CLI accepts --framework flag and validates value.
- Invalid values print error and usage, no files created.

---

### Task 17: Framework-Specific Template Generation

- For each supported framework, generate:
  - run.py with LLM API call boilerplate (Gemini Pro, OpenAI ChatGPT, Anthropic Claude).
  - requirements.txt with correct dependency (google-generativeai, openai, anthropic).
  - README.md with API key setup instructions and run example.
- All other files/directories (kinnoo.yaml, tools/, prompts/) remain as before.

**Acceptance Criteria:**
- Directory contains correct files for each framework.
- requirements.txt lists correct dependency.
- README.md includes API key setup and run instructions.

---

### Task 18: Manifest Validation

- Ensure generated kinnoo.yaml passes validation using feature1 validator.
- Entry point and fields must be correct for each template.

**Acceptance Criteria:**
- kinnoo.yaml passes validation (no errors).

---

### Task 19: General Usage and Error Handling

- If kinnoo init is run without agent name, print usage message.
- If agent directory already exists, print error and do not overwrite.
- If --framework is omitted, generate vanilla agent as before.

**Acceptance Criteria:**
- Usage and error messages are clear and actionable.
- No files are overwritten or created in error cases.

---

### Task 20: Unit Tests

- Add unit tests for:
  - Each framework template (directory structure, file contents, requirements, README).
  - Invalid framework values (error and usage message).
  - Manifest validation for generated agents.

**Acceptance Criteria:**
- All tests pass, covering positive and negative cases.

---

## Design Constraints

- Do not change kinnoo run CLI or validator logic (remains framework-agnostic).
- Templates must be minimal but runnable (hello-world for each LLM).
- No Docker, remote, or MCP server support in this feature.

---

## Files to Create/Modify

- src/kinnoo/init_command.py (main logic)
- src/kinnoo/templates.py (framework templates)
- tests/test_init.py (unit tests)
- requirements.txt (if new dependencies needed for testing)
- README.md (if CLI usage changes)

---

## Task Grouping

All tasks are logically sequential and can be handled by a single SWE agent session.

---

## Notes

- Reference acceptance criteria in FEATURES.txt for completeness.
- Update documentation if CLI usage changes.


## Task16 Summary: kinnoo init --framework Flag

**Date:** 2026-02-23

### Implementation
- Updated `kinnoo init` CLI to accept an optional `--framework` flag.
- Supported frameworks: `gemini`, `chatgpt`, `claude-chat`.
- If an unsupported value is provided, prints error and usage message, exits without creating files/directories.
- Prints usage if agent name is missing.
- Refactored CLI logic for proper entrypoint and validation.

### Unit Tests
- Added tests for:
  - Valid frameworks (should succeed, create agent directory).
  - Invalid frameworks (should print error and usage, no files created).
  - Missing agent name (should print usage, no files created).
- Used temporary directories for test isolation.
- All tests passed:

```
============================== 12 passed in 0.73s ==============================
```

### Manifest Validation
- Ran manifest validator after changes.
- Manifest parsing error detected in FEATURES.txt (unrelated to task16).

### Coding Standards & Notes
- Followed project modularity, error handling, and naming conventions.
- Inline comments and clear error messages for user feedback.
- Summary and results logged for traceability.

---

### Q&A: CLI Testing and main() Addition

**Q: Why was a main() added to init_command.py? Why wasn't it needed before?**
A main() function was added to init_command.py to ensure CLI logic executes when the script is run directly (e.g., via python or subprocess in tests). Previously, init_command.py was called from cli.py as a module, so it didn't need its own entrypoint. With task16, direct script execution was needed for unit tests and CLI use, so main() and the entrypoint block were added. This is standard for robust CLI tools and improves testability.

**Q: Why the change, if init_command was previously called from cli.py?**
Previously, init_command.py was imported and invoked by cli.py, so CLI logic was handled there. For task16, unit tests needed to run init_command.py directly, simulating CLI usage and validating argument parsing and error handling. Adding main() allows dual-mode use: as a module (for cli.py) and as a standalone CLI (for direct execution and testing).

**Q: Would it be harder to test if you ran all tests via cli.py?**
Yes, it would be harder. cli.py is the main entrypoint and handles multiple commands and logic. Testing init_command.py features through cli.py would require simulating the full CLI environment, reducing test isolation and making failures harder to diagnose. Direct script execution allows focused, isolated tests of init logic, improving testability and modularity.

---
**Next Steps:**
- Task16 is ready for review and integration.
- Manifest parsing error in FEATURES.txt should be addressed separately.

## Task17 Summary: Framework-Specific Template Generation

**Date:** 2026-02-23

### Implementation
- Added framework-specific templates for `gemini`, `chatgpt`, and `claude-chat` to `templates.py`.
- Updated `init_command.py` to generate the correct `run.py`, `requirements.txt`, and `README.md` for each framework when `--framework` is specified.
- All other files/directories (kinnoo.yaml, tools/, prompts/) remain as before.

### Unit Tests
- Added tests to verify:
  - Directory structure and file contents for each framework.
  - `requirements.txt` lists correct dependency.
  - `README.md` includes API key setup and run instructions.
  - `run.py` contains correct model hints.
- Used temporary directories for test isolation.
- All tests passed:

```
============================== 13 passed in 0.81s ==============================
```

### Manifest Validation
- Ran manifest validator after changes.
- Manifest parsing error detected in FEATURES.txt (unrelated to task17).

### Coding Standards & Notes
- Followed project modularity, error handling, and naming conventions.
- Inline comments and clear error messages for user feedback.
- Summary and results logged for traceability.


## Task18 Summary: Manifest Validation for Generated Agents

**Date:** 2026-02-23

### Implementation
- Added a test to verify that kinnoo.yaml generated for each framework (`gemini`, `chatgpt`, `claude-chat`) passes validation using the feature1 validator.
- Ensured agent names use hyphens (not underscores) to conform to manifest requirements.
- Confirmed that entry point and manifest fields are correct for all templates.

### Unit Tests
- Added test to:
  - Generate an agent for each framework.
  - Validate the generated kinnoo.yaml using the validator.
  - Assert that validation passes (no errors).
- All tests passed:

```
============================== 14 passed in 0.91s ==============================
```

### Coding Standards & Notes
- Followed project modularity, error handling, and naming conventions.
- Used temporary directories for test isolation.
- Summary and results logged for traceability.


## Task19 Summary: General Usage and Error Handling

**Date:** 2026-02-23

### Implementation
- Confirmed and tested:
  - Usage message is printed if kinnoo init is run without agent name.
  - Error is printed and no overwrite occurs if agent directory already exists.
  - If --framework is omitted, a vanilla agent is generated (empty requirements.txt, no API key in README, hello-world run.py).
- All edge cases and error handling requirements are covered.

### Unit Tests
- Added/verified tests for:
  - Usage message for missing agent name.
  - Error and no overwrite for existing directory.
  - Vanilla agent generation when --framework is omitted.
- All tests passed:

```
============================== 15 passed in 0.97s ==============================
```

### Coding Standards & Notes
- Followed project modularity, error handling, and naming conventions.
- Used temporary directories for test isolation.
- Summary and results logged for traceability.

---
**Next Steps:**
- Task19 is ready for review and integration.
- Proceed to next task or address manifest linkage issues as needed.
