# TechLead agent and Jerry - Feature 15 Planning and Suggestions

## 1. AC1 — What yes/no prompting is needed, and why?

AC1 says:
> `kinnoo install` displays a summary of what the agent requires (env_var NAMES, dependency NAMES, runtime type) before installing and prompts for yes/no confirmation.

**What it looks like concretely:**

```
Installing agent: my-agent v1.0.0
  Runtime: python (one-shot), version >=3.10
  Dependencies: openai, pydantic, requests
  Env vars: OPENAI_API_KEY, MY_SECRET_TOKEN
Continue with install? [y/N]:
```

**Why this matters:**

The install process does two things that carry real risk:
1. **Dependency installation runs arbitrary code.** Python packages can execute arbitrary Python during `pip install` via `setup.py` or build hooks. Showing the dependency list before install gives the user a chance to spot something unexpected (e.g., a typo-squatted package like `openai-sdk` or an unrelated package like `boto3` in an agent that shouldn't need AWS access).
2. **Env var names reveal the agent's attack surface.** If you're installing an agent from a colleague or the internet and see `STRIPE_API_KEY, AWS_SECRET_ACCESS_KEY` in the summary — but you expected a simple Gemini chatbot — that's a red flag.

This is the same UX pattern as `apt install` ("The following NEW packages will be installed:"), `brew install` showing dependencies, or macOS permission prompts. It's a **consent gate** — the user explicitly opts in after seeing what the agent needs.

**My recommendation:** Keep AC1 as-is. It's the single most impactful trust feature for minimal implementation cost. The only refinement I'd suggest: add a `--yes` / `-y` flag to skip the prompt for CI/automation pipelines (like `apt install -y`).

---

## 2. AC4 — First-execution transparency display

AC4 says:
> `kinnoo run` displays the agent's declared env_var NAMES and dependency NAMES before first execution (first run only) — never values.

**Why it's a good idea (in principle):**

Consider this scenario: You install a `.kno` agent, maybe you clicked through the install prompt quickly. Days later you run it for the first time. The first-run display is a "last chance reminder" of what the agent accesses. It serves as a trust checkpoint at the point where secrets are actually being resolved and the entrypoint is about to execute.

**Why I think we should reconsider the design:**

Now that feature14 (preflight) is implemented, and `kinnoo inspect` already exists, the user has **two** on-demand ways to see this information:
- `kinnoo run --preflight <agent-dir>` — shows env vars, dependencies, runtime version
- `kinnoo inspect <agent-dir>` — shows env vars, dependencies, runtime type, metadata

Automatically printing on first run adds a third, unsolicited display of the same data. This creates:
- **Noise** for developers running their own agents during development
- **"First run" tracking state** — we'd need to persist somewhere (e.g., `~/.kinnoo/first_run_seen/<agent-name>`) that the agent has been run before, which adds filesystem state and edge cases (what if the state file is deleted? what if the agent is updated?)

**My recommendation:** Replace AC4 with something more targeted:

> **AC4 (revised):** When `kinnoo run` executes an agent that was installed via `kinnoo install` (from a `.kno` archive), display a one-line notice on first run: `"[kinnoo] First run of <name> v<version> — use 'kinnoo inspect' or '--preflight' to review agent requirements."` No env var/dependency dump — just a pointer to the tools that already exist.

This avoids duplicate output, avoids complex "first run" state, and still nudges trust-conscious users toward inspection. The alternative is to drop AC4 entirely and rely on AC1 (install prompt) + existing inspect/preflight capabilities.

What do you think — revised AC4 with the pointer approach, or drop it entirely?

**Decision:** Drop AC4 entirely. With preflight and inspect already available, AC1 (install prompt) provides the consent gate, and users can inspect on demand anytime.

---

## 3. Cursory sweep for env var value exposure in `kinnoo inspect`

**Yes, this is easy to implement.** Here's my thinking on architecture:

### Approach: Regex-based heuristic scan

Scan all `.py` files in the agent directory (excluding `.venv/`) for patterns that suggest env var values are being printed or written to files. ~50-60 lines of code.

**Concrete patterns to detect:**

| Pattern | What it catches |
|---------|----------------|
| `print(…os.environ…)` | Direct print of env var access |
| `print(…os.getenv…)` | Direct print of getenv result |
| `logging.*(…os.environ…)` | Logging env var values |
| `.write(…os.environ…)` | Writing env values to files |
| `f"…{os.environ…}"` or `f"…{os.getenv…}"` in print/write context | f-string interpolation of secrets |

**For declared env vars specifically**, also check for:
- Variable assigned from `os.environ["OPENAI_API_KEY"]`, then later that same variable name appears in a `print()` or `write()` call (simple one-hop taint tracking)

### Implementation sketch:

```python
# In inspect_command.py or a new src/kinnoo/code_sweep.py

def sweep_env_var_exposure(agent_dir: Path, declared_env_vars: list[str]) -> list[str]:
    """Heuristic scan for patterns that may expose env var values."""
    warnings: list[str] = []
    
    EXPOSURE_PATTERNS = [
        (r'print\s*\(.*os\.environ',   "print() with os.environ access"),
        (r'print\s*\(.*os\.getenv',     "print() with os.getenv() access"),
        (r'log\w*\.\w+\(.*os\.environ', "logging with os.environ access"),
        (r'log\w*\.\w+\(.*os\.getenv',  "logging with os.getenv() access"),
        (r'\.write\s*\(.*os\.environ',  "file write with os.environ access"),
        (r'\.write\s*\(.*os\.getenv',   "file write with os.getenv() access"),
    ]
    
    for py_file in agent_dir.rglob("*.py"):
        if ".venv" in py_file.parts:
            continue
        # scan lines, match patterns, collect warnings with file:line
    
    return warnings
```

### Where to surface it:

- **`kinnoo inspect`**: Add a `Security sweep:` section at the bottom of inspect output. If warnings found, print them. If clean, print `"Security sweep: no env var exposure patterns detected (heuristic)"`.
- **`kinnoo pack`**: Also run the sweep before packing, since that's the distribution point. Flag warnings as non-blocking but visible.

### Strengths and limitations:

- **Strengths:** Zero dependencies, fast (~milliseconds for typical agent codebases), catches the most common accidental leaks
- **Limitations:** Won't catch indirect leaks (assign to variable, pass through 3 functions, then print), and will have false positives on code that's behind `if __debug__:` or is commented-out-adjacent. This is **not** taint analysis — it's a linter-style heuristic.
- **Mitigation:** Add a clear disclaimer: `"(heuristic scan — may produce false positives; not a substitute for code review)"`

**Implementation effort:** ~1-2 hours for the scan + tests + integration into inspect output. Small task, high signal. I'd make this one task under feature15.

---

## 4. Input injection precursor check for `kinnoo run`

**Yes, this is easy to implement and architecturally clean.** Here's how I'd design it for replaceability:

### Architecture: Protocol-based pluggable guard

```python
# src/kinnoo/input_guard.py

class InputGuardResult:
    def __init__(self, safe: bool, warnings: list[str]):
        self.safe = safe
        self.warnings = warnings

class InputGuard(Protocol):
    """Swap implementation without changing callers."""
    def check(self, input_text: str) -> InputGuardResult: ...

class RegexInputGuard:
    """V1: regex-based heuristics for common injection patterns."""
    
    PATTERNS = [
        # SQL injection
        (r"(?i)\b(union\s+select|drop\s+table|insert\s+into|delete\s+from)\b",
         "Possible SQL injection"),
        (r"(?i)'\s*(or|and)\s+\d+\s*=\s*\d+",
         "Possible SQL tautology injection"),
        
        # Shell injection
        (r"[;&|`]\s*(rm|cat|wget|curl|sudo|sh|bash|python)\b",
         "Possible shell command injection"),
        (r"\$\([^)]+\)",
         "Possible command substitution"),
        
        # Path traversal
        (r"\.\./", "Possible path traversal"),
        
        # SSRF
        (r"(?i)(file|gopher|dict)://",
         "Possible SSRF via unusual protocol"),
    ]
    
    def check(self, input_text: str) -> InputGuardResult:
        warnings = []
        for pattern, desc in self.PATTERNS:
            if re.search(pattern, input_text):
                warnings.append(desc)
        return InputGuardResult(safe=len(warnings) == 0, warnings=warnings)

def get_default_guard() -> InputGuard:
    """Factory — replace with MLInputGuard when ready."""
    return RegexInputGuard()
```

### Integration in `kinnoo run`:

```python
guard = get_default_guard()
result = guard.check(input_arg)
if not result.safe:
    print("[kinnoo] Input safety warning:", file=sys.stderr)
    for w in result.warnings:
        print(f"  - {w}", file=sys.stderr)
    confirm = input("Proceed anyway? [y/N]: ").strip().lower()
    if confirm != "y":
        return 1
```

### Why this design is good for future replacement:

1. **Protocol-based.** Any class with a `check(str) -> InputGuardResult` method satisfies the contract. Swapping `RegexInputGuard` for `MLInputGuard` (e.g., wrapping a local classifier or calling an API) is a one-line change in `get_default_guard()`.
2. **Non-blocking.** Warns but allows user to proceed — agents may legitimately receive SQL-looking input (e.g., a database agent).
3. **Skippable.** Add `--no-guard` flag for CI/testing pipelines where input is controlled.
4. **Independently testable.** Each regex pattern and the overall guard logic can be unit tested in isolation.

### Future ML upgrade path:

```python
class MLInputGuard:
    def __init__(self):
        self.model = load_local_classifier("input_safety_v1.onnx")
    
    def check(self, input_text: str) -> InputGuardResult:
        score = self.model.predict(input_text)
        if score > 0.8:
            return InputGuardResult(safe=False, warnings=["ML classifier flagged as potentially unsafe"])
        return InputGuardResult(safe=True, warnings=[])
```

### Differentiation angle:

This is a genuine differentiator for kinnoo. No other agent packaging tool (that I'm aware of) provides input-level safety checks. Even the regex version catches obvious misuse, and the pluggable architecture means you can upgrade to an ML classifier without changing any caller code. This is a strong interview talking point for "defense in depth" and "secure-by-default" design.

**Implementation effort:** ~2-3 hours for the guard module + tests + CLI integration + `--no-guard` flag. I'd make this a separate feature (e.g., feature19 "Input Safety Guard") rather than bundling it into feature15, because:
- It's a distinct concern (input safety vs. trust transparency)
- It has its own test surface
- It will evolve independently (ML upgrade path)

### Notes
- for run logging, will add run UUID later

---

## Summary of recommendations

| Item | Verdict | Action |
|------|---------|--------|
| AC1 (install prompt) | **Keep as-is** + add `--yes` flag | Consent gate, high value, low cost |
| AC4 (first-run display) | **Drop** | Redundant with preflight + inspect |
| Env var exposure sweep | **Add as new AC under feature15** | Regex heuristic in inspect + pack, ~50 lines, high signal |
| Input injection guard | **Add as separate feature** | Protocol-based `InputGuard` in `input_guard.py`, pluggable for ML later |
