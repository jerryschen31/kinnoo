# Task255 Notes - LangChain Subset Trial (Import / Inspect / Run / Pack)

Date: 2026-03-21
Scope in this run: LangChain examples only (6 agents)
- `example-scratch/agents/langchain-mrkl-agent-base`
- `example-scratch/agents/langchain-self-ask-search-agent`
- `example-scratch/agents/langchain-structured-chat-agent`
- `example-scratch/agents/langchain-tool-calling-agent`
- `example-scratch/agents/langchain-openai-functions-multi-agent`
- `example-scratch/agents/langchain-openai-assistant-agent`

Input used for run step: `"What is 2+2?"`

## Preconditions and Discovery Commands

Command:
```bash
python3 src/kinnoo/cli.py --help
```
Output (excerpt):
```text
usage: kinnoo ... {init,run,stop,attach,logs,install,pack,keygen,inspect,publish,list,search,import}
```
Assessment: CLI surface is available and includes all required task255 subcommands.

Command:
```bash
python3 src/kinnoo/cli.py import --help
```
Output (excerpt):
```text
usage: kinnoo import [-h] [--force] [path]
```
Assessment: Import is interactive and does not expose an explicit non-interactive mode.

Command:
```bash
python3 src/kinnoo/cli.py inspect --help
python3 src/kinnoo/cli.py run --help
python3 src/kinnoo/cli.py pack --help
```
Assessment: Syntax for inspect/run/pack confirmed.

## Agent-by-Agent Results

## 1) langchain-mrkl-agent-base

### Step 1 - Import
Command:
```bash
python3 src/kinnoo/cli.py import example-scratch/agents/langchain-mrkl-agent-base
```
Output (excerpt):
```text
Detected values from analyzer:
  - entrypoint: base.py
  - framework: None
...
Provide value for framework (optional): langchain
Generated manifest validation: PASS
Imported project in-place: .../langchain-mrkl-agent-base
```
Assessment: Import succeeded (first pass).

Additional import command attempted later:
```bash
python3 src/kinnoo/cli.py import --force example-scratch/agents/langchain-mrkl-agent-base
```
Output (excerpt):
```text
UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800' ...
```
Assessment: `--force` re-import fails with analyzer Unicode handling bug.

### Step 2 - Inspect
Command:
```bash
python3 src/kinnoo/cli.py inspect example-scratch/agents/langchain-mrkl-agent-base
```
Output:
```text
Error: Missing required file 'requirements.txt' in target directory.
```
Assessment: Inspect failed due hard requirement for `requirements.txt`.

### Step 3 - Run (with up to 5 correction attempts)
Attempt 1 command:
```bash
python3 src/kinnoo/cli.py run example-scratch/agents/langchain-mrkl-agent-base "What is 2+2?"
```
Output (excerpt):
```text
ModuleNotFoundError: No module named 'langchain_core'
```
Correction command:
```bash
example-scratch/agents/langchain-mrkl-agent-base/.venv/bin/pip install langchain-core
```
Output (excerpt):
```text
Successfully installed ... langchain-core-1.2.20 ...
```

Attempt 2 command:
```bash
python3 src/kinnoo/cli.py run example-scratch/agents/langchain-mrkl-agent-base "What is 2+2?"
```
Output (excerpt):
```text
ModuleNotFoundError: No module named 'langchain_classic'
```
Correction command:
```bash
example-scratch/agents/langchain-mrkl-agent-base/.venv/bin/pip install langchain_classic
```
Output (excerpt):
```text
Successfully installed langchain_classic-1.0.3 ...
```

Attempt 3 command:
```bash
python3 src/kinnoo/cli.py run example-scratch/agents/langchain-mrkl-agent-base "What is 2+2?"
```
Output (excerpt):
```text
[kinnoo monitor] policy summary: ...
[exit_code=0]
```
Assessment: Process exited 0, but produced no answer text for input prompt. By task255 criteria (proper response required), run is not functionally successful.

### Step 4 - Pack (only attempted because process exited 0)
Command:
```bash
python3 src/kinnoo/cli.py pack example-scratch/agents/langchain-mrkl-agent-base
```
Output:
```text
Error: requirements.txt not found in example-scratch/agents/langchain-mrkl-agent-base
```
Assessment: Pack failed.

## 2) langchain-self-ask-search-agent

### Step 1 - Import
Initial scripted import attempts were interrupted by interactive prompt handling.
Final successful import command:
```bash
printf 'Y\nbase.py\nlangchain\n\n' | python3 src/kinnoo/cli.py import example-scratch/agents/langchain-self-ask-search-agent
```
Output (excerpt):
```text
Generated manifest validation: PASS
Imported project in-place: .../langchain-self-ask-search-agent
```
Assessment: Import succeeded.

### Step 2 - Inspect
Command:
```bash
python3 src/kinnoo/cli.py inspect example-scratch/agents/langchain-self-ask-search-agent
```
Output:
```text
Error: Missing required file 'requirements.txt' in target directory.
```
Assessment: Inspect failed due missing `requirements.txt`.

### Step 3 - Run (with corrections)
Attempt 1:
```text
ModuleNotFoundError: No module named 'langchain_core'
```
Correction:
```bash
.../.venv/bin/pip install langchain-core
```
Attempt 2:
```text
ModuleNotFoundError: No module named 'langchain_classic'
```
Correction:
```bash
.../.venv/bin/pip install langchain_classic
```
Attempt 3 output (excerpt):
```text
[kinnoo monitor] policy summary: ...
[exit_code=0]
```
Assessment: Exit 0, but no response content emitted. Not functionally successful for prompt-response criteria.

### Step 4 - Pack
Command:
```bash
python3 src/kinnoo/cli.py pack example-scratch/agents/langchain-self-ask-search-agent
```
Output:
```text
Error: requirements.txt not found ...
```
Assessment: Pack failed.

## 3) langchain-structured-chat-agent

### Step 1 - Import
Command:
```bash
printf 'Y\nbase.py\nlangchain\n\n' | python3 src/kinnoo/cli.py import example-scratch/agents/langchain-structured-chat-agent
```
Output (excerpt):
```text
Generated manifest validation: PASS
Imported project in-place: .../langchain-structured-chat-agent
```
Assessment: Import succeeded.

### Step 2 - Inspect
Command:
```bash
python3 src/kinnoo/cli.py inspect example-scratch/agents/langchain-structured-chat-agent
```
Output:
```text
Error: Missing required file 'requirements.txt' in target directory.
```
Assessment: Inspect failed.

### Step 3 - Run (with corrections)
Attempt 1:
```text
ModuleNotFoundError: No module named 'langchain_core'
```
Correction:
```bash
.../.venv/bin/pip install langchain-core
```
Attempt 2:
```text
ModuleNotFoundError: No module named 'langchain_classic'
```
Correction:
```bash
.../.venv/bin/pip install langchain_classic
```
Attempt 3 output:
```text
[kinnoo monitor] policy summary: ...
[exit_code=0]
```
Assessment: Exit 0 but no user-facing response. Not functionally successful.

### Step 4 - Pack
Command:
```bash
python3 src/kinnoo/cli.py pack example-scratch/agents/langchain-structured-chat-agent
```
Output:
```text
Error: requirements.txt not found ...
```
Assessment: Pack failed.

## 4) langchain-tool-calling-agent

### Step 1 - Import
Command:
```bash
printf 'Y\nbase.py\nlangchain\n\n' | python3 src/kinnoo/cli.py import example-scratch/agents/langchain-tool-calling-agent
```
Output (excerpt):
```text
Generated manifest validation: PASS
Imported project in-place: .../langchain-tool-calling-agent
```
Assessment: Import succeeded.

### Step 2 - Inspect
Command:
```bash
python3 src/kinnoo/cli.py inspect example-scratch/agents/langchain-tool-calling-agent
```
Output:
```text
Error: Missing required file 'requirements.txt' in target directory.
```
Assessment: Inspect failed.

### Step 3 - Run (with corrections)
Attempt 1:
```text
ModuleNotFoundError: No module named 'langchain_core'
```
Correction:
```bash
.../.venv/bin/pip install langchain-core
```
Attempt 2:
```text
ModuleNotFoundError: No module named 'langchain_classic'
```
Correction:
```bash
.../.venv/bin/pip install langchain_classic
```
Attempt 3 output:
```text
[kinnoo monitor] policy summary: ...
[exit_code=0]
```
Assessment: Exit 0 but no response body. Not functionally successful.

### Step 4 - Pack
Command:
```bash
python3 src/kinnoo/cli.py pack example-scratch/agents/langchain-tool-calling-agent
```
Output:
```text
Error: requirements.txt not found ...
```
Assessment: Pack failed.

## 5) langchain-openai-functions-multi-agent

### Step 1 - Import
Command:
```bash
printf 'Y\nbase.py\nlangchain\n\n' | python3 src/kinnoo/cli.py import example-scratch/agents/langchain-openai-functions-multi-agent
```
Output (excerpt):
```text
Generated manifest validation: PASS
Imported project in-place: .../langchain-openai-functions-multi-agent
```
Assessment: Import succeeded.

### Step 2 - Inspect
Command:
```bash
python3 src/kinnoo/cli.py inspect example-scratch/agents/langchain-openai-functions-multi-agent
```
Output:
```text
Error: Missing required file 'requirements.txt' in target directory.
```
Assessment: Inspect failed.

### Step 3 - Run (with corrections)
Attempt 1:
```text
ModuleNotFoundError: No module named 'langchain_core'
```
Correction:
```bash
.../.venv/bin/pip install langchain-core
```
Attempt 2:
```text
ModuleNotFoundError: No module named 'langchain_classic'
```
Correction:
```bash
.../.venv/bin/pip install langchain_classic
```
Attempt 3 output:
```text
[kinnoo monitor] policy summary: ...
[exit_code=0]
```
Assessment: Exit 0 but no prompt response output. Not functionally successful.

### Step 4 - Pack
Command:
```bash
python3 src/kinnoo/cli.py pack example-scratch/agents/langchain-openai-functions-multi-agent
```
Output:
```text
Error: requirements.txt not found ...
```
Assessment: Pack failed.

## 6) langchain-openai-assistant-agent

### Step 1 - Import
Command:
```bash
printf 'Y\nbase.py\nlangchain\n\n' | python3 src/kinnoo/cli.py import example-scratch/agents/langchain-openai-assistant-agent
```
Output (excerpt):
```text
Detected values from analyzer:
  - framework: chatgpt
Generated manifest validation: PASS
Imported project in-place: .../langchain-openai-assistant-agent
```
Assessment: Import succeeded; analyzer framework detection differs from supplied framework value.

### Step 2 - Inspect
Command:
```bash
python3 src/kinnoo/cli.py inspect example-scratch/agents/langchain-openai-assistant-agent
```
Output:
```text
Error: Missing required file 'requirements.txt' in target directory.
```
Assessment: Inspect failed.

### Step 3 - Run (with corrections)
Attempt 1:
```text
ModuleNotFoundError: No module named 'langchain_core'
```
Correction:
```bash
.../.venv/bin/pip install langchain-core
```
Attempt 2 output:
```text
[kinnoo monitor] policy summary: ...
[exit_code=0]
```
Assessment: Exit 0 but no answer output for the input prompt. Not functionally successful.

### Step 4 - Pack
Command:
```bash
python3 src/kinnoo/cli.py pack example-scratch/agents/langchain-openai-assistant-agent
```
Output:
```text
Error: requirements.txt not found ...
```
Assessment: Pack failed.

## Aggregate Assessment (LangChain 6/6)

- Import:
  - 6/6 eventually imported successfully (interactive prompt orchestration required).
  - 1 reproducible import bug on re-import with `--force` (`UnicodeEncodeError` in analyzer path processing).
- Inspect:
  - 0/6 successful.
  - Primary blocker: strict `requirements.txt` requirement.
- Run:
  - 6/6 reached process exit code 0 after dependency correction installs.
  - 0/6 produced an actual prompt-response payload for `"What is 2+2?"`.
  - These files appear to be framework internals/modules, not one-shot executable agent entrypoints.
- Pack:
  - 0/6 successful.
  - Primary blocker: missing `requirements.txt` in imported project roots.

## Corrections Performed (No codebase implementation changes)

Runtime dependency correction commands executed in per-agent virtual environments:
```bash
<agent>/.venv/bin/pip install langchain-core
<agent>/.venv/bin/pip install langchain_classic
```

These corrections removed `ModuleNotFoundError` for LangChain imports, but did not produce functional prompt-response behavior.

## What Needs to Be Fixed in the Codebase to Accommodate This Agent Family

1. Import non-interactive mode
- Add a flag such as `kinnoo import --yes --entrypoint ... --framework ...` for CI/matrix runs.
- Current interactive prompts are brittle for automation.

2. Import analyzer Unicode robustness
- Fix `src/kinnoo/analyzer.py` path literal handling so invalid/surrogate-containing literals do not crash (`UnicodeEncodeError`) during `--force` re-import.

3. Entrypoint executability validation
- Import should detect when selected entrypoint is a library module (no CLI contract / no response path) and either:
  - fail early with actionable message, or
  - auto-generate a wrapper entrypoint that actually invokes an agent chain with stdin/sys.argv input.

4. Requirements synthesis at import time
- Import should generate or infer a baseline `requirements.txt` when absent, or mark import as incomplete.
- Missing `requirements.txt` blocks both inspect and pack workflows.

5. Inspect ergonomics
- `kinnoo inspect` should support a degraded mode when `requirements.txt` is missing (manifest-only metadata + warning), rather than hard fail.

6. Run success criteria / UX
- Add optional check mode where run success requires non-empty stdout response (`--expect-output`) for matrix validation.
- Exit code alone is insufficient for agent functional readiness.

7. Pack preflight guidance
- `kinnoo pack` already errors correctly, but import should leave projects in a packable state or emit a generated TODO file listing exactly what to add.

## Testing Command Requested in SWE Guidance

Command:
```bash
python3 -m pytest tests/test_corpus_matrix.py -k task255 -q
```
Output:
```text
ERROR: file or directory not found: tests/test_corpus_matrix.py
```
Assessment: task255 matrix test module is not present yet in this branch/workspace state.

## Conclusion

For this LangChain subset, the current pipeline can import metadata and can be dependency-corrected to process-exit success, but it does not yet achieve functional run responses or packable artifacts from these source snapshots. The import/inspect contract and executable-entrypoint expectations need to be tightened for corpus-scale reliability.
