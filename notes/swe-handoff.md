# SWE Agent Handoff — Feature 18: Input Safety Guard

**Date:** 2026-03-13  
**From:** TechLead Agent  
**Feature:** feature18 — Input Safety Guard  
**Branch:** Create `phase2/feature18/main` from `phase2/main`; one sub-branch per task.  
**Status:** `not-started` → `in-progress` when you begin  

---

## Overview

Implement a pluggable input safety guard for `kinnoo run` that detects common injection attacks (SQL injection, shell command injection, path traversal, SSRF, XSS, template injection) in user-provided input before it reaches the agent entrypoint. The guard is **non-blocking** — it warns and prompts for confirmation, never hard-rejects. It uses a Protocol-based design so the V1 regex guard can be swapped for an ML classifier via a single factory function change.

**Key design requirement:** The guard must support both the current single-string input (`kinnoo run <path> "input"`) and a future parameterized input model (`-e <string> -i <id> -d <file-path> -u <url>`). This means the guard has two methods: `check(value, input_type)` for single values and `check_inputs(inputs)` for multi-value typed input.

---

## Task Execution Order

```
task116 → task117 → task118 → task119
```

All tasks are sequential — each depends on the previous. Implement in this exact order.

---

## Task 1: task116 — InputGuard protocol, result models, and factory function

**Files to create:** `src/kinnoo/input_guard.py`  
**Tests:** test149, test150  
**Test file:** `tests/test_input_guard.py`

### What to build

Create the foundational module `src/kinnoo/input_guard.py` with:

1. **`InputWarning`** dataclass:
   - `threat_category: str` — which category (e.g., `SQL_INJECTION`)
   - `description: str` — human-readable description of the threat
   - `param_name: str | None = None` — which parameter triggered the warning (for multi-value mode)

2. **`InputGuardResult`** dataclass:
   - `safe: bool` — True if no warnings
   - `warnings: list[InputWarning]`

3. **Threat category constants** (module-level strings):
   - `SQL_INJECTION = "SQL_INJECTION"`
   - `SHELL_INJECTION = "SHELL_INJECTION"`
   - `PATH_TRAVERSAL = "PATH_TRAVERSAL"`
   - `SSRF = "SSRF"`
   - `XSS = "XSS"`
   - `TEMPLATE_INJECTION = "TEMPLATE_INJECTION"`

4. **`InputGuard`** Protocol class:
   ```python
   class InputGuard(Protocol):
       def check(self, value: str, input_type: str = "text") -> InputGuardResult: ...
       def check_inputs(self, inputs: list[tuple[str, str, str]]) -> InputGuardResult: ...
   ```
   Where each tuple in `check_inputs` is `(param_name, value, input_type)`.

5. **`RegexInputGuard`** class — minimal placeholder that satisfies the Protocol. Full patterns come in task117. For now, `check()` can return `InputGuardResult(safe=True, warnings=[])` and `check_inputs()` can delegate to `check()` per input.

6. **`get_default_guard() -> InputGuard`** factory function returning `RegexInputGuard()`.

### Test expectations (test149, test150)
- **test149:** Verify `InputWarning` and `InputGuardResult` are constructible with the correct fields.
- **test150:** Verify `get_default_guard()` returns an object with `check()` and `check_inputs()` methods, and that `check("safe text")` returns an `InputGuardResult`.

---

## Task 2: task117 — RegexInputGuard comprehensive pattern library

**Files to modify:** `src/kinnoo/input_guard.py`  
**Tests:** test151–test159  
**Test file:** `tests/test_input_guard.py`

### What to build

Replace the placeholder `RegexInputGuard` with the full implementation. This is the core of the feature — **be thorough with patterns**.

#### Pattern structure

Organize patterns as a dict mapping threat category to a list of `(regex_str, human_description)` tuples. Compile regexes with `re.IGNORECASE` where appropriate. Example structure:

```python
PATTERNS: dict[str, list[tuple[str, str]]] = {
    SQL_INJECTION: [
        (r"(?i)\bunion\s+(all\s+)?select\b", "Possible SQL injection: UNION SELECT"),
        # ... more patterns
    ],
    SHELL_INJECTION: [...],
    # ...
}
```

#### Required patterns per category

**SQL_INJECTION:**
- `UNION SELECT` / `UNION ALL SELECT`
- `DROP TABLE` / `DROP DATABASE`
- `INSERT INTO ... VALUES`
- `DELETE FROM`
- Tautology: `OR 1=1`, `OR '1'='1'`, `AND 1=1` (pattern: `'?\s*(OR|AND)\s+['"]?\d+['"]?\s*=\s*['"]?\d+`)
- Comment injection after suspicious context: `--`, `#`, `/*` following quote/injection marker
- `WAITFOR DELAY` (time-based blind SQLi)
- `EXEC xp_` (stored procedure injection)
- Stacked queries: `;` followed by `SELECT|INSERT|UPDATE|DELETE|DROP`

**SHELL_INJECTION:**
- Command chaining: `[;&|]` followed by dangerous commands (`rm`, `cat`, `wget`, `curl`, `sudo`, `sh`, `bash`, `python`, `chmod`, `chown`, `nc`, `ncat`, `mkfifo`, `dd`, `kill`)
- `&&` and `||` with dangerous commands
- Command substitution: `$(...)` and backtick `` `...` ``
- Pipe to shell: `| sh`, `| bash`, `| /bin/sh`, `| /bin/bash`
- Output redirection to sensitive paths: `>` or `>>` followed by `/etc/`, `/var/`, etc.
- Null byte: `\x00`, `%00`

**PATH_TRAVERSAL:**
- `../` and `..\` sequences (the pattern should catch 2+ levels like `../../`)
- Single `../` is also worth flagging
- URL-encoded: `%2e%2e%2f`, `%2e%2e/`, `..%2f`
- Double-encoded: `%252e%252e%252f`
- Absolute sensitive paths: `/etc/passwd`, `/etc/shadow`, `/proc/self`, `/dev/`

**SSRF:**
- Dangerous protocols: `file://`, `gopher://`, `dict://`, `ldap://`
- Internal loopback: `127.0.0.1`, `0.0.0.0`
- Private networks: `10.\d+.\d+.\d+`, `172\.(1[6-9]|2\d|3[01])\.\d+\.\d+`, `192\.168\.\d+\.\d+`
- IPv6 loopback: `[::1]`, `::1`
- `localhost` as hostname
- Octal IP for loopback: `0177.0.0.1`
- AWS metadata: `169.254.169.254`

**XSS:**
- `<script` tags (case-insensitive)
- `javascript:` URI scheme
- Event handlers: `on\w+=` (onerror, onload, onclick, onmouseover, onfocus, etc.)
- Dangerous HTML tags with src/event: `<img`, `<iframe`, `<svg`, `<object`, `<embed`
- `data:text/html`

**TEMPLATE_INJECTION:**
- Jinja2/Twig: `{{` and `}}`
- ERB: `<%` and `%>`
- Expression language: `${...}`, `#{...}`

#### Type-aware filtering

Define a mapping of `input_type` → set of applicable threat categories:

```python
TYPE_FILTER: dict[str, set[str]] = {
    "text": {SQL_INJECTION, SHELL_INJECTION, PATH_TRAVERSAL, SSRF, XSS, TEMPLATE_INJECTION},
    "string": {SQL_INJECTION, SHELL_INJECTION, PATH_TRAVERSAL, SSRF, XSS, TEMPLATE_INJECTION},
    "file_path": {PATH_TRAVERSAL, SHELL_INJECTION},
    "url": {SSRF, SHELL_INJECTION},
    "id": {SQL_INJECTION, SHELL_INJECTION, TEMPLATE_INJECTION},
}
```

Unknown input_type defaults to "text" (full scan).

#### check() implementation

```python
def check(self, value: str, input_type: str = "text") -> InputGuardResult:
    applicable_categories = TYPE_FILTER.get(input_type, TYPE_FILTER["text"])
    warnings = []
    for category in applicable_categories:
        for regex_str, description in PATTERNS.get(category, []):
            if re.search(regex_str, value, re.IGNORECASE):
                warnings.append(InputWarning(
                    threat_category=category,
                    description=description,
                    param_name=None,
                ))
                break  # one warning per category per value is enough
    return InputGuardResult(safe=len(warnings) == 0, warnings=warnings)
```

**Important:** Break after first match per category to avoid flooding warnings for a single input. One warning per threat category per value is sufficient.

#### check_inputs() implementation

```python
def check_inputs(self, inputs: list[tuple[str, str, str]]) -> InputGuardResult:
    all_warnings = []
    for param_name, value, input_type in inputs:
        result = self.check(value, input_type)
        for warning in result.warnings:
            all_warnings.append(InputWarning(
                threat_category=warning.threat_category,
                description=warning.description,
                param_name=param_name,
            ))
    return InputGuardResult(safe=len(all_warnings) == 0, warnings=all_warnings)
```

### Test expectations (test151–test159)

Each pattern category has its own test (test151-test156) that verifies individual patterns are detected. Additionally:
- **test157:** Verify legitimate text passes clean — "Hello, how are you?", "The price is $19.99", "Tell me about SQL databases and SELECT queries", "The ratio is 3/4", "Check out https://example.com" all return `safe=True`.
- **test158:** Type-aware filtering — `check("../../etc/passwd", "file_path")` detects PATH_TRAVERSAL; `check("' OR 1=1--", "file_path")` returns safe (SQL skipped); `check("http://169.254.169.254/", "url")` detects SSRF; `check("../../etc/passwd", "url")` returns safe; etc.
- **test159:** `check_inputs` with mixed safe/unsafe inputs; verify per-param warnings and aggregated safety.

### Important notes on false positives

Be careful with patterns that are too broad. For example:
- Don't flag `SELECT` alone — only flag it in injection context (`UNION SELECT`, `'; SELECT`, etc.)
- Don't flag single `/` characters — only flag `../` sequences
- Don't flag all URLs — only flag internal/dangerous protocol URLs
- The pattern `OR 1=1` should require a quote or injection context prefix (e.g., `'?\s*OR\s+`)
- test157 explicitly validates that benign text passes clean — make sure patterns don't over-match

---

## Task 3: task118 — CLI --no-guard flag and run_command integration

**Files to modify:** `src/kinnoo/cli.py`, `src/kinnoo/run_command.py`  
**Tests:** test160–test163  
**Test file:** `tests/test_input_guard_integration.py`

### What to build

#### cli.py changes

1. Add `--no-guard` argument to the run subparser:
   ```python
   run_parser.add_argument(
       "--no-guard",
       action="store_true",
       help="Disable input safety check for CI/automation pipelines",
   )
   ```

2. Pass the flag to `run_agent()`:
   ```python
   exit_code = run_agent(
       agent_dir_arg=args.agent_dir,
       input_arg=args.input,
       preflight=preflight_mode,
       no_guard=bool(getattr(args, "no_guard", False)),
   )
   ```

3. Update the pre-parse `len(sys.argv) < 4` check — if `--no-guard` is present, the count may differ. The simplest fix is to add `"--no-guard"` to the pre-parse exclusion list alongside `"--preflight"`.

#### run_command.py changes

1. Add `no_guard: bool = False` parameter to `run_agent()` signature.

2. After env var resolution (after `trace_forbidden_values.extend(resolved_env_vars.values())`) and before entrypoint execution (before `python_exe = venv_dir / "bin" / "python"`), add the guard block:

```python
# --- Input safety guard ---
if not no_guard and input_arg is not None:
    from .input_guard import get_default_guard
    guard = get_default_guard()
    guard_result = guard.check(input_arg, "text")
    if not guard_result.safe:
        print("[kinnoo] Input safety warning:", file=sys.stderr)
        for warning in guard_result.warnings:
            print(f"  - [{warning.threat_category}] {warning.description}", file=sys.stderr)
        if sys.stdin.isatty():
            try:
                response = input("Proceed anyway? [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                return finalize(1)
            if response != "y":
                return finalize(1)
        else:
            print("Non-interactive mode: aborting due to input safety warning.", file=sys.stderr)
            return finalize(1)
```

### Test expectations (test160–test163)

- **test160 (--no-guard):** Run agent with malicious input + `--no-guard` → agent executes, no safety warning in output.
- **test161 (reject):** Run agent with malicious input, simulate `n` to prompt → agent NOT executed, exit non-zero, warning in stderr.
- **test162 (accept):** Run agent with malicious input, simulate `y` to prompt → agent executes, warning in stderr, agent output visible.
- **test163 (non-interactive):** Run agent with malicious input, stdin piped/closed → auto-aborts, "Non-interactive mode" in stderr, exit non-zero.

**Testing approach for prompt simulation:** Use `subprocess.Popen` with `stdin=subprocess.PIPE` to feed `y\n` or `n\n` to the process. For non-interactive test, pipe stdin from `/dev/null` or use `stdin=subprocess.DEVNULL`. For `--no-guard` test, no stdin manipulation needed.

---

## Task 4: task119 — Docs and regression coverage for feature18

**Files to modify:** `README.md`, `docs/manifest-schema-reference.md`, `tests/test_docs.py`  
**Tests:** test164  
**Test file:** `tests/test_docs.py`

### What to build

1. **README.md** — Add an "Input Safety Guard" section describing:
   - Guard runs automatically on `kinnoo run` before agent execution
   - Six threat categories: SQL injection, shell command injection, path traversal, SSRF, XSS, template injection
   - Non-blocking: warns and prompts, never hard-rejects
   - `--no-guard` flag for CI/automation
   - Type-aware checking for future parameterized inputs
   - Pluggable Protocol-based design for future ML guard

2. **docs/manifest-schema-reference.md** — Add input safety section describing guard behavior and threat categories.

3. **test_docs.py** — Add `test_feature18_docs_cover_input_safety_guard` that asserts key strings appear in README.md (e.g., "Input Safety Guard", "--no-guard", "SQL injection", "shell", "path traversal", "SSRF", "XSS", "template injection", "Protocol").

---

## Design Constraints & Reminders

1. **Security first:** The guard patterns must catch real injection vectors, not just toy examples. Test with realistic payloads.
2. **No false-positive floods:** Break after first match per category per value. One warning per threat category is enough.
3. **Non-blocking is non-negotiable:** The guard warns, never hard-blocks. Users must always be able to proceed after acknowledging the warning.
4. **No secret exposure:** The guard sees `input_arg` which is user-provided text. It must NOT log the input content to the run trace (the existing run trace already excludes input via `trace_forbidden_values`).
5. **`from __future__ import annotations`** at top of `input_guard.py` for Python 3.10+ compatibility with `str | None` syntax.
6. **Use `re.IGNORECASE`** for all patterns by default — attackers use mixed case to bypass regex guards.
7. **Run `python3 -m pytest -q` after each task** to verify nothing is broken.
8. **Run `python3 src/validate_project_manifests.py`** after any TASKS.txt/TESTS.txt changes.

---

## File Summary

| Task | New Files | Modified Files |
|------|-----------|----------------|
| task116 | `src/kinnoo/input_guard.py`, `tests/test_input_guard.py` | — |
| task117 | — | `src/kinnoo/input_guard.py`, `tests/test_input_guard.py` |
| task118 | `tests/test_input_guard_integration.py` | `src/kinnoo/cli.py`, `src/kinnoo/run_command.py` |
| task119 | — | `README.md`, `docs/manifest-schema-reference.md`, `tests/test_docs.py` |
