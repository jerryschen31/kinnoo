# Task 514 Notes

## User Prompt (verbatim)
Create a new feature120 in FEATURES.txt titled "UAT 3 - fixes". The description should be around "3rd round of User Acceptance Testing ... UI tweaks and bug fixes as necessary." Add what you just fixed (tenant-qualified install/fetch selector and remote checksum verification behavior) as a new task514 in TASKS.txt and add associated tests you created to TESTS.txt. Set statuses to needs-review. Put my prompt and your response verbatim into notes/tasks/task514-notes.md.

## Assistant Response (verbatim)
Implemented the requested fixes and test coverage for tenant-qualified selectors and remote checksum verification behavior across CLI, server, and web paths.

What was fixed:
- Updated selector parsing and resolution to support tenant-qualified targets in install/fetch flows.
- Corrected web modal install command exact-version syntax to use `==`.
- Added remote checksum metadata support so archive verification works even when temp downloads have no adjacent sidecar.
- Added/updated regression tests for parser behavior and install/fetch tenant-qualified selector flows.

Validation:
- Targeted pytest suites for parser/install/fetch changes passed.
- Targeted web vitest suites passed for modal/registry command behavior.