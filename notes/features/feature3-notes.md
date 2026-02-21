## SWE Agent Implementation Notes for feature3 (`kinnoo run`)

- **Framework-Agnostic Execution:** Do not add any framework-specific logic. The CLI must treat all agents as black boxes, running the entrypoint as specified in kinnoo.yaml, regardless of framework (LangChain, CrewAI, custom, etc.).

- **Fail-Fast Principle:** Validate kinnoo.yaml and check for entrypoint file before any environment setup or dependency installation. Abort early with clear errors if validation fails or files are missing.

- **Venv Location:** Always create the Python virtual environment inside the agent directory as `.venv/`. Do not use global or user-level environments.

- **Dependency Installation:** Only install packages listed in requirements.txt. Do not attempt to auto-install missing packages or resolve dependencies outside the venv.

- **Input Handling:** Pass the user-provided input string as the first CLI argument (`sys.argv[1]`) to the entrypoint script. Do not use stdin or environment variables for input unless specified in the manifest.

- **Output Streaming:** Stream both stdout and stderr from the entrypoint process to the terminal in real-time. Avoid buffering or waiting for process completion before displaying output.

- **Exit Code Propagation:** Ensure the exit code from the entrypoint script is returned as the kinnoo process exit code. This is critical for shell scripting and CI integration.

- **Usage Errors:** Print clear usage messages for missing or invalid arguments. Do not attempt to guess or auto-correct user input.

- **Safety:** Do not overwrite or modify files outside the agent directory. All operations should be contained within the specified agent directory.

- **Manifest Validation:** Always use the feature1 validator for manifest checks. Do not duplicate validation logic.

- **Testing:** Ensure all implemented logic is covered by the corresponding tests in TESTS.txt. If any edge cases are discovered during implementation, add new tests and update TASKS.txt and FEATURES.txt accordingly.

---
These notes supplement the requirements in FEATURES.txt, TASKS.txt, and TESTS.txt, and are intended to ensure robust, maintainable, and predictable implementation of feature3.
