## SWE Handoff: task255 - 42-Agent Corpus Validation Matrix (Import/Inspect/Run/Pack)

### Scope
Implement task255 from [TASKS.txt](TASKS.txt), using the corpus curated in task254 and test coverage defined by test356-test359 in [TESTS.txt](TESTS.txt).

This task adds a deterministic validation matrix that exercises all 42 staged agents across four workflows:
- import
- inspect
- run
- pack

### Intent
Create a resilient, CI-friendly matrix harness that:
- Enumerates the full corpus from [example-scratch/agents-map.txt](example-scratch/agents-map.txt)
- Executes all four workflows for each mapped agent
- Produces stable per-agent diagnostics and aggregate summaries by framework and complexity
- Continues execution even when individual agents fail, so one bad sample does not hide the rest of the matrix

### Canonical Inputs
- Corpus mapping: [example-scratch/agents-map.txt](example-scratch/agents-map.txt)
- Human-readable inventory: [example-scratch/agents-list.md](example-scratch/agents-list.md)
- Corpus summary and provenance notes: [notes/tasks/task254-notes.md](notes/tasks/task254-notes.md)
- Staged local agents root: [example-scratch/agents](example-scratch/agents)

### Task Execution Plan (Ordered)
1. Build matrix loader utilities
- Add parsing/validation helpers to read [example-scratch/agents-map.txt](example-scratch/agents-map.txt).
- Enforce deterministic ordering (for example, source order from map file).
- Validate expected corpus size (42) and detect malformed map rows early.

2. Add shared matrix execution primitives
- Implement shared helpers for command invocation, timeout handling, and normalized result objects.
- Include per-agent context in every result: framework, complexity, name, local folder.
- Make failures non-fatal to the global matrix run.

3. Implement import matrix (test356)
- Execute import-validation flow for each agent entry.
- Capture per-agent status and actionable error snippets.
- Emit aggregate summary grouped by framework and complexity.

4. Implement inspect matrix (test357)
- Run inspect flow per agent.
- Assert stable output shape/required manifest identity fields.
- Record per-agent failures without aborting the full matrix.

5. Implement run matrix (test358)
- Run each agent via CLI script-path convention:
  - python src/kinnoo/cli.py run <agent-path> "<sample-input>"
- Use deterministic sample input and bounded timeout.
- Capture exit code + concise stdout/stderr diagnostics.

6. Implement pack matrix (test359)
- Run pack for each agent via CLI script path:
  - python src/kinnoo/cli.py pack <agent-path>
- Verify artifact-status outcome (`.kno` produced vs failed) per row.
- Summarize outcomes by framework/complexity and globally.

7. Finalize regression and reporting quality
- Ensure matrix output is stable enough for test assertions.
- Ensure no secret values are logged; diagnostics should be path-safe and concise.
- Keep implementation modular to support future expansion (e.g., install matrix).

### AC/Test Mapping
- task255 step2/step6 -> test356 (import matrix)
- task255 step3 -> test357 (inspect matrix)
- task255 step4 -> test358 (run matrix)
- task255 step5 -> test359 (pack matrix)

### Suggested Files to Modify
Primary:
- tests/test_corpus_matrix.py (new)

Likely support changes (only if needed):
- tests/helpers/* (shared matrix helpers, if repository already uses helper modules)
- src/kinnoo/cli.py (only if a missing deterministic behavior blocks matrix assertions)
- src/kinnoo/import_command.py (only if required for stable import reporting)
- src/kinnoo/inspect_command.py (only if required for stable inspect reporting)
- src/kinnoo/run_command.py (only if required for stable run diagnostics)
- src/kinnoo/pack_command.py (only if required for stable pack diagnostics)

### Non-Negotiable Constraints
- Use [example-scratch/agents-map.txt](example-scratch/agents-map.txt) as the single source of truth for enumeration.
- Do not hand-curate ad hoc subsets in tests.
- Preserve matrix continuation on per-agent failure.
- Keep output deterministic and assertion-friendly.
- Use Python CLI script path in tests (python src/kinnoo/cli.py ...), not python -m kinnoo.
- Do not expose secrets in logs, stdout, stderr, or persisted artifacts.

### Verification Gate
Run targeted tests:
- python3 -m pytest tests/test_corpus_matrix.py -k task255

Run full suite before final handoff:
- python3 -m pytest

Validate manifests after any task/test manifest updates:
- python3 src/validate_project_manifests.py

### Status Workflow
- Move task255: not-started -> in-progress at implementation start.
- Move task255: in-progress -> needs-review after code + tests pass.
- Do not move to completed until Tech Lead review + human approval.

### Risks and Pitfalls to Watch
- Some curated agents may depend on external APIs/services and fail at runtime without credentials.
- Packaging may fail for agents lacking strict pack prerequisites.
- Long-running or hanging agents can destabilize CI if per-agent timeouts are not enforced.

Mitigation strategy:
- Treat matrix as execution-and-reporting validation, not universal success guarantee.
- Enforce per-agent timeouts and continue-on-failure behavior.
- Produce explicit categorized outcomes (pass/fail/timeout/skipped) for downstream triage.
