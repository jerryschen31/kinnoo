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
