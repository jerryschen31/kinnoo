[todo] analyze the codebase for each of the LangChain agents in example-scratch/agents/ - ready code comments, metadata and linked repo for more information - and report out how each of these agents can and should be run, as a section in notes/features/feature46-notes.md. If relevant, give suggestions on how kinnoo run should be modified to accomodate running this agent - e.g., maybe a more dedicated wrapper is needed.

[todo] analyze the codebase for each of the Open AI agents in example-scratch/agents/ - ready code comments, metadata and linked repo for more information - and report out how each of these agents can and should be run, as a section in notes/features/feature46-notes.md. If relevant, give suggestions on how kinnoo run should be modified to accomodate running this agent - e.g., maybe a more dedicated wrapper is needed.

[todo] analyze the codebase for each of the Pydantic AI agents in example-scratch/agents/ - ready code comments, metadata and linked repo for more information - and report out how each of these agents can and should be run, as a section in notes/features/feature46-notes.md. If relevant, give suggestions on how kinnoo run should be modified to accomodate running this agent - e.g., maybe a more dedicated wrapper is needed.

[todo] analyze the codebase for each of the OpenClaw agents in example-scratch/agents/ - ready code comments, metadata and linked repo for more information - and report out how each of these agents can and should be run, as a section in notes/features/feature46-notes.md. If relevant, give suggestions on how kinnoo run should be modified to accomodate running this agent - e.g., maybe a more dedicated wrapper is needed.

[improvement] analyzer needs to detect the type of inputs an imported agent expects to receive - single text input? No jnput? JSON? parameterized input? What parameters? This info needs to get recorded in kinnoo.yaml in an appropriate field. Same for outputs. 

[thought] should think about adding evals sooner or later. kinnoo run —eval test-runs.evals will do runs against the evals test list and give a report. The eval score gets set in kinnoo.yaml next to version (eval-score: and eval-dataset: ). Consider if running evals should be a flag in kinnoo run, or if a separate eval or test CLI command makes more sense. Or maybe both have their place in the kinnoo CLI. In thinking about evals, consider what we’ve already discussed in our tech lead agent notes and our other planning notes. 

[thought] regarding evals, help me think about how to do “security” evals within kinnoo as a CLI command - how secure an agent is - this includes whether an agent has the potential to expose secrets, how vulnerable an agent is to SQL or other injection, how malicious an agent could be based on its default permissions, etc. Are there good eval test sets out there for doing these types of evals?

[improvement] when running kinnoo pack - maybe have a flag that allows the user to also run a preflight run, and if PASS then add a metadata field in kinnoo.yaml next to the version, indicating if preflight was run and the status (PASS / FAIL). 

[improvement] in the top-level kinnoo help usage, separate the daemon-specific commands into a separate section (attach, stop, logs). 

[improvement] analyzer should try and auto-detect model and put this model metadata in the kinnoo.yaml. Test auto-detect against default Gemini, Claude-chat and chatgpt init templates.

[improvement] since there’s so many init frameworks now, make the help usage a bit cleaner - one framework per line instead of all on one line. Each framework should have a one-liner description. 

[improvement] add a --language flag to kinnoo init for initializing agents written in different languages. Supported languages are python, js / javascript, and ts / typescript. Error on incompatible combinations (e.g., --framework openclaw --language python should error out). Make sure language-only initializations are barebones templates, while valid combinations (language and framework) should create functional templates as intended. 

[improvement] openclaw init scaffold has remnant python files - requirements.txt and run.py - I’m assuming these are not needed since openclaw is JS based?

[improvement] kinnoo import <github-agent-code-url> <import-path> works by downloading the agent code to the specified import-path on the local machine (downloads to current-working-directory/<agent-code-dir>/ by default, if import-path is not specified). Handle the edge case where <import-path> or current-working-directory/<agent-code-dir>/  already exists by erroring out saying the directory in question already exists. If kinnoo cannot clone / download the code, kinnoo should also intelligently error stating that agent code cannot be downloaded / cloned to local machine (missing credentials, or URL not found, etc…).

[improvement] Add a “kinnoo check” <agent-name | GitHub-agent-code-url> that checks if the agent is compatible with kinnoo out-of-the-box. This would involve import check, inspect check, and run preflight check - in one go, with intelligent fail messages so the dev knows what to fix for kinnoo compatibility. If pointing to a code URL, this downloads the agent code to a folder like /tmp/kinnoo-agent-check/<agent-code>/ and does the checks from there.

[improvement] Pretty print with color on import, preflight run, pack, publish, install, and any other commands where the user needs to respond to user prompts or that provides important information to the user (important = provides information that the user needs to execute subsequent commands).

[potential bug] Preflight fails on venv not found, but agent (overrode runtime.path in kinnoo.yaml) creates virtual environment and runs without error.

## SWE Handoff: feature46 (tasks 258, 259, 261, 263, 265, 266, 267)

### Scope
Implement the following feature46 tasks in one grouped SWE implementation pass:
- task258: analyzer input/output type auto-detection
- task259: `kinnoo pack --preflight`
- task261: analyzer model auto-detection
- task263: `kinnoo init --language`
- task265: `kinnoo import <github-url> [import-path]`
- task266: `kinnoo check <agent-dir | github-url>`
- task267: pretty print with color for key CLI commands

### Why This Grouping
These tasks are tightly coupled around onboarding quality and operator UX:
- Import/analyzer surface: task258, task261, task265
- Verification surface: task259, task266
- CLI UX surface: task263, task267

A single SWE agent can execute them in sequence while minimizing churn in shared files (`src/kinnoo/cli.py`, analyzer/import flows, and command output formatting).

### Ordered Implementation Plan
1. task263 (`kinnoo init --language`): establish language framework compatibility matrix and scaffold branching first.
2. task258 (I/O type detection): extend analyzer detection contracts for inputs/outputs.
3. task261 (model auto-detection): extend analyzer model extraction while analyzer changes are fresh.
4. task265 (import from URL): add URL download/clone path and collision/error behavior.
5. task266 (`kinnoo check`): orchestrate import + inspect + preflight (reuse task265 flow for URL targets).
6. task259 (`pack --preflight`): integrate preflight gate into pack flow and persist metadata.
7. task267 (colorized output): apply shared output helper across import/preflight/pack/publish/install/check.

### Dependencies
- Manifest dependencies: task258, task259, task261, task263, task265, task266, task267 are already defined in `TASKS.txt`.
- Shared internal dependencies:
	- task266 depends on task265 behavior for URL targets and temp directory workflow.
	- task259 depends on stable preflight contract in `run_command`.
	- task267 should be applied after core command behavior changes to reduce rework.

### AC/Test Coverage Map
- task258 -> test364, test365
- task259 -> test366, test367
- task261 -> test369, test370
- task263 -> test372, test373
- task265 -> test375, test376, test377
- task266 -> test378, test379
- task267 -> test380, test381

### Design Constraints (Must Follow)
- Preserve backward compatibility for existing CLI invocation patterns.
- Keep all secret-handling invariant behavior unchanged (never print env var values).
- Maintain analyzer confidence/evidence style when adding input/output/model detectors.
- URL import must fail clearly on:
	- existing target directory collision
	- clone/download not found
	- auth/credentials failure
- `kinnoo check` should produce step-specific PASS/FAIL diagnostics and actionable fix guidance.
- Color output must respect `NO_COLOR` and non-interactive/non-TTY contexts.
- `kinnoo init --language` must error on incompatible framework/language combinations with deterministic messaging.

### Expected Files to Modify
- `src/kinnoo/cli.py`
- `src/kinnoo/init_command.py`
- `src/kinnoo/analyzer.py`
- `src/kinnoo/import_command.py`
- `src/kinnoo/pack_command.py`
- `src/kinnoo/run_command.py` (reuse preflight checks where needed)
- `src/kinnoo/check_command.py` (new)
- `tests/test_cli.py`
- `tests/test_pack.py`
- `tests/test_validator.py`

### Verification Gate
- Run targeted tests first:
	- `python3 -m pytest tests/test_validator.py -k "analyzer and model"`
	- `python3 -m pytest tests/test_cli.py -k "init or import or check or color"`
	- `python3 -m pytest tests/test_pack.py -k "preflight"`
- Run broader regression before handoff completion:
	- `python3 -m pytest`
- Validate manifests after any manifest edits:
	- `python3 scripts/validate_project_manifests.py`

### Status Workflow
- Move tasks to `in-progress` at implementation start.
- Move tasks to `needs-review` only after code + tests are complete and passing.
- Do not mark `completed` until tech lead review + approval.
