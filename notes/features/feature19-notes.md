# Feature19 brainstorming with Gemini

** Prompt **
Based on best practice principles from other frameworks, what would be some good ways for a developer to convert or import their existing agent into an Agnt -compatible agent? It seems like a bottleneck if a dev can’t easily convert into Agnt

** Response **
You’ve hit on the "Migration Friction" problem, which is the #1 killer of new platforms. If it takes a developer more than 5 minutes to "Agnt-ify" their existing agent, they won't do it.

To solve this, we should look at how **Docker** (with `docker init`) and **Vercel** handle onboarding. The goal is to move from a "manual rewrite" to a **"Guided Discovery"** model.

Here are the three best-practice strategies for converting existing agents into the Agnt ecosystem.

---

### ## 1. The "Agnt Init" CLI (Guided Discovery)
Instead of asking the developer to write a YAML file from scratch, provide a CLI command that "scans" their project.

**The Workflow:**
1.  Developer runs `agnt init` in their project folder.
2.  Agnt scans for `requirements.txt`, `pyproject.toml`, or `import pydantic_ai`.
3.  Agnt uses a local LLM to guess the `entrypoint`.
4.  **The Result:** A pre-filled `agnt.yaml` is generated for them.

> **Pro-Tip:** Include a "Compatibility Score." If Agnt sees `import crewai`, it can say: *"I see you're using CrewAI. I've added the CrewAI-Bridge to your manifest automatically."*

---

### ## 2. The "Shim" Pattern (Wrappers)
One of the most successful ways to support legacy systems is through **Wrappers**. You provide a small library (`agnt-shim`) that the developer adds to their existing code to make it "Agnt-compliant" without changing their logic.

**Example for a Pydantic AI agent:**
```python
# Existing code
from pydantic_ai import Agent
from agnt_shim import wrap_for_agnt # Your library

my_agent = Agent('openai:gpt-4o')

# Instead of my_agent.run(), they use:
if __name__ == "__main__":
    wrap_for_agnt(my_agent)
```
The `wrap_for_agnt` function handles the "Handshake" with your runtime, sets up the logging, and connects the memory folders automatically.

---

### ## 3. Framework-Specific "Translators"
You should build (or the community will build) specific "Import Adapters" for the major frameworks we discussed.

| Framework | The "Bridge" Strategy |
| :--- | :--- |
| **OpenClaw** | A tool that converts `SOUL.md` and `SKILL.md` into an `agnt.yaml` manifest. |
| **LangGraph** | A wrapper that injects Agnt’s SQLite path into the LangGraph `Checkpointer`. |
| **Agno** | A utility that maps Agno's `SessionID` to Agnt’s `Session_UUID`. |



---

### ## 4. The "Import" Command (Registry Migration)
To populate your registry quickly, you should allow developers to "point and shoot" at existing GitHub repos.

**Command:** `agnt import https://github.com/user/my-crew-agent`
**What happens under the hood:**
1.  Agnt clones the repo to a temporary sandbox.
2.  It identifies the framework.
3.  It generates the `agnt.yaml`.
4.  It runs a `dry-run` to see if it crashes.
5.  If it passes, it says: *"This agent is 90% compatible. Just add your API keys to test."*

---

### ## Summary: The "Conversion Funnel"

| Level | Developer Effort | Platform Value |
| :--- | :--- | :--- |
| **Manual** | High (Write YAML by hand) | Low (High friction) |
| **CLI Init** | Medium (Review generated YAML) | High (Guided onboarding) |
| **Auto-Import** | Low (One CLI command) | **Maximum** (Instant Registry growth) |

### ### The Strategy Recommendation
For **V1.0.0**, focus on the **`agnt init`** command. It’s the highest ROI for your engineering time. It makes the developer feel like the platform is "smart" and "helpful" without you having to build complex wrappers for every single framework version.

**Would you like me to draft the "Heuristics Logic" for the `agnt init` command so you can see how it would detect different frameworks in a codebase?**

# Feature 19 Strategy Review — Tech Lead Feedback

## The Core Problem

The current feature19 spec (`kinnoo import <src> <new-dir>`) creates a **copy** of the
developer's agent in a new kinnoo directory. This has three fundamental friction points:

1. **Two codebases to maintain.** The original project keeps evolving; the kinnoo copy
   drifts immediately. Developers won't maintain both.
2. **"Move your stuff into our house" UX.** Psychologically, this feels invasive. Developers
   identify with their project structure. Asking them to abandon it is a non-starter for
   adoption.
3. **Low compatibility ceiling.** Copying files into a rigid scaffold only works for the
   simplest agents. Multi-file projects, custom directory layouts, monorepos, or agents
   with build steps will hit walls.

The planning-agent conversation in scratch.md correctly identifies this as the "Migration
Friction" problem and proposes four strategies. Let me evaluate each against what we
already have, and recommend the best V1 approach.

---

## Evaluating the Four Strategies

### Strategy 1: CLI Init Scanning ("kinnoo init" with auto-detection)

**What scratch.md proposes:** `kinnoo init` scans the project, infers fields, generates
`kinnoo.yaml` pre-filled.

**What we already have:** feature27's `analyze_project()` does exactly this — 7 detectors,
confidence scores, evidence strings. The init command already scaffolds 7 framework
templates. The machinery is 80% built.

**Verdict:** This is the right foundation, but the UX target should be different. Instead
of creating a *new* directory, the command should generate a `kinnoo.yaml` **inside the
developer's existing project**. Think `npm init` or `cargo init` — they don't copy your
code elsewhere; they add a manifest file to your current directory.

---

### Strategy 2: Shim Pattern (Wrappers / agnt-shim)

**What scratch.md proposes:** A library (`agnt-shim`) that wraps the developer's agent
class/function to make it kinnoo-compliant without restructuring.

**Assessment:**
- **Pro:** Zero-disruption to developer's code. Smallest possible change.
- **Con:** Requires the developer to modify their source code (add an import line). Also,
  kinnoo's value proposition is packaging and distribution, not runtime wrapping — we
  don't *need* to wrap their agent at runtime. We need to know how to *describe* it
  (manifest) and how to *invoke* it (entrypoint).
- **Con:** Shims create a runtime dependency on kinnoo inside the agent. This is a leaky
  abstraction — the agent should work with or without kinnoo.

**Verdict:** Not the right V1 approach. The value of kinnoo is in the metadata layer
(manifest + packaging), not in a runtime shim. If we ever need runtime hooks (e.g.,
structured I/O, memory management), that's a V3+ concern and should be opt-in.

---

### Strategy 3: Framework-Specific Translators

**What scratch.md proposes:** Build import adapters per framework (CrewAI bridge,
LangGraph checkpoint injector, etc.).

**Assessment:**
- **Pro:** Deep integration = higher compatibility for supported frameworks.
- **Con:** Massive surface area. Each framework has its own configuration format, lifecycle,
  and versioning cadence. Maintaining N translators is an ongoing tax.
- **Con:** We'd be chasing framework versions forever. When LangGraph releases a new
  `Checkpointer` API, our translator breaks.

**Verdict:** Wrong granularity for V1. Feature27's analyzer already does lightweight
framework detection (import → framework name mapping). That's the right level of
framework awareness for now. Deep framework-specific translators are a community-driven
V3+ opportunity, not a core platform responsibility.

---

### Strategy 4: Remote Import (`kinnoo import https://github.com/...`)

**What scratch.md proposes:** Point-and-shoot at a GitHub repo, auto-clone + analyze +
generate.

**Assessment:**
- **Pro:** Extremely low friction. One command.
- **Con:** Introduces git as a dependency, needs network access, sandboxing concerns,
  authentication for private repos. Significant implementation complexity.
- **Con:** The analysis quality depends on the repo structure. Many repos have nested agent
  code, monorepo setups, or Docker-only entrypoints.

**Verdict:** Nice-to-have for V2, but not the right first step. The local-first approach
(`kinnoo import .`) should work perfectly before we add remote support.

---

## My Recommendation: "In-Place Import" (The `npm init` Model)

### The Key Insight

The best conversion strategy is **not copying the developer's code** — it's **adding kinnoo
metadata to their existing project**. The developer's project structure, entrypoint, and
dependencies stay exactly where they are. Kinnoo adds:

1. A `kinnoo.yaml` manifest (inferred by the analyzer, confirmed by the developer)
2. Optionally, a thin entrypoint wrapper if the existing entrypoint doesn't match kinnoo's
   contract (accepts CLI input, prints output)

That's it. The agent is now kinnoo-compatible. `kinnoo run .` works. `kinnoo pack .` works.
No copying. No second codebase.

### The Command

```
kinnoo import [path]     # default: current directory
```

**Not** `kinnoo import <src> <dest>`. No destination directory. The developer runs this
inside their project (or points to it), and kinnoo drops a manifest in place.

### The Flow

```
$ cd ~/my-existing-agent
$ kinnoo import

Analyzing project...

  Entrypoint:   run.py (confidence: 0.95, found conventional name)
  Framework:    pydantic-ai (confidence: 0.85, detected import)
  Runtime:      python >=3.10, one-shot
  Dependencies: 12 packages from requirements.txt
  Env vars:     OPENAI_API_KEY (from os.getenv call)
  Assets:       data/embeddings.json (from directory scan)
  Services:     none detected

Accept these values? [Y/n]  y

Generated kinnoo.yaml
```

One command. One confirmation. The developer's project is now a kinnoo agent.

### Why This Beats the Copy Model

| Aspect | Copy Model (current spec) | In-Place Model (proposed) |
|--------|---------------------------|---------------------------|
| Developer friction | High — must maintain two codebases | Minimal — adds one file |
| Compatibility | ~40% — rigid scaffold assumptions | ~85% — adapts to existing structure |
| Time to convert | Minutes (review copied files, fix paths) | Seconds (confirm inferred values) |
| Ongoing maintenance | Developer must sync changes to kinnoo copy | Zero — kinnoo.yaml lives with the code |
| Pack/run workflow | `kinnoo run ./my-kinnoo-copy/` | `kinnoo run .` (works in-place) |
| Git-friendly | Awkward — separate repo or nested dir | Natural — kinnoo.yaml committed alongside code |


### What Changes from Current Feature19 Spec

1. **Drop the `<new-agent-dir>` argument.** Import targets the source project in-place.
2. **Drop file copying logic.** No need to copy `run.py`, `requirements.txt`, etc. They
   already exist in the right place.
3. **The wizard becomes a confirmation step**, not a creation step. Show inferred values,
   ask "accept?", write `kinnoo.yaml`.
4. **Entrypoint compatibility check** becomes the main "hard problem." If the developer's
   entrypoint doesn't accept CLI input / print output, we need to either:
   - (a) Generate a thin wrapper (`kinnoo_entry.py`) that invokes their entrypoint, or
   - (b) Note it as a TODO in the manifest and let the developer fix it.
5. **AC2 changes**: Instead of "creates a new directory with all expected files", it becomes
   "generates `kinnoo.yaml` in the target directory without modifying existing files."

### The Entrypoint Bridge Problem

This is the one genuine hard problem. Kinnoo expects:
- Entrypoint accepts input (CLI arg or stdin)
- Entrypoint produces output (stdout)

Many existing agents don't follow this contract. They might:
- Read input from a config file or environment variable
- Write output to a file or database
- Run as a server (already handled by `runtime.type: mcp-server`)
- Use a framework-specific runner (`python -m langgraph serve`)

**Proposed solution for V1:** The import wizard detects the entrypoint signature using AST
analysis (feature27 already does this). If the entrypoint doesn't match kinnoo's
input/output contract:

1. **Warn the developer** with a clear message:
   ```
   ⚠ Entrypoint run.py does not appear to accept CLI input.
     kinnoo agents expect: python run.py "<input>"
     You may need to add input handling. See: kinnoo docs import-guide
   ```
2. **Offer to generate a wrapper** (optional, not default):
   ```
   Generate a kinnoo_entry.py wrapper that calls your entrypoint? [y/N]
   ```
3. **Set `entrypoint` in the manifest** to whatever the developer confirms, even if it's
   not perfectly kinnoo-compatible yet. Let them iterate.

This is the pragmatic approach: get the manifest generated and the developer on the platform
first. They can fix the entrypoint contract incrementally.

---

## Addressing the 80-90% Compatibility Goal

The in-place model combined with the analyzer detectors should cover the vast majority of
existing Python agents:

| Agent Type | Coverage | Notes |
|------------|----------|-------|
| Single-file script agents | ✅ High | Entrypoint obvious, deps from requirements.txt |
| Framework-based (LangChain, PydanticAI, etc.) | ✅ High | Framework detected, deps present |
| Multi-file packages | ✅ Medium-High | Entrypoint needs confirmation but detectable |
| Agents with assets/data | ✅ Medium-High | Asset detector finds data dirs + model files |
| MCP servers | ✅ High | Port/protocol detection via analyzer |
| Server-based agents (FastAPI, etc.) | ⚠ Medium | Need runtime.type inference, wrapper may help |
| Monorepo sub-agents | ⚠ Low-Medium | Need path scoping, but `kinnoo import ./agents/foo` works |
| Docker-only agents | ❌ Low | Out of scope for V1, need container runtime support |
| Non-Python agents | ❌ Out of scope | Analyzer is Python-only currently |

Estimate: **~80-85% of standalone Python agents** can be imported with the in-place model
and current analyzer detectors. The remaining 15-20% need either manual manifest authoring
or future enhancements (Docker runtime, non-Python support).

---

## Recommended Implementation Phases

### Phase A: Core In-Place Import (Feature19 V1)

**This is the minimum viable import:**

1. `kinnoo import [path]` — runs analyzer, shows inferred values, writes `kinnoo.yaml`
2. Confirmation wizard (confirm-first, prompt only for missing/ambiguous fields)
3. Entrypoint compatibility warning (informational, not blocking)
4. Collision detection (don't overwrite existing `kinnoo.yaml` without `--force`)
5. Validation: generated manifest passes schema validation

**Does NOT include:** file copying, directory creation, wrapper generation, remote import.

### Phase B: Entrypoint Wrapper Generation (Optional, can be separate feature)

1. AST-based entrypoint contract analysis (does it accept args? produce output?)
2. Thin wrapper generation for common patterns (FastAPI adapter, function-call wrapper)
3. `--wrapper` flag on import to opt in

### Phase C: Remote Import (V2, separate feature)

1. `kinnoo import https://github.com/user/repo`
2. Clone to temp dir, analyze, generate manifest
3. Option to fork + add kinnoo.yaml via PR

---

## Impact on Current Feature19 ACs

| AC | Current Spec | Proposed Change |
|----|-------------|-----------------|
| AC1 | Validates `<existing-agent-path> <new-agent-dir>` args | Change to `[path]` (optional, defaults to `.`) |
| AC2 | Creates new directory with all files | **Rewrite:** Generates `kinnoo.yaml` in target dir, no file copying |
| AC3 | Invokes analyzer, generates kinnoo.yaml with confidence warnings | **Unchanged** — this is the core |
| AC4 | Interactive confirm-first wizard | **Unchanged** |
| AC5 | Cleanup partial output on failure | Simpler — only `kinnoo.yaml` to remove on failure |
| AC6 | Ctrl+C safety | **Unchanged** |
| AC7 | Collision/overwrite safety | **Unchanged** (applies to existing `kinnoo.yaml`) |
| AC8 | Imported agent runnable via `kinnoo run` | **Unchanged** (but now runs in-place) |
| AC9 | Conditional wizard prompts for schema extensions | **Unchanged** |

---

## Teaching Moment: Why This Matters for AI Engineering

This is a textbook example of **developer experience (DX) design** in the AI tooling space.
The key principle: **meet developers where they are, don't make them come to you.**

The same principle applies to:
- **Hugging Face** succeeded partly because `from_pretrained()` works with existing model
  files — no special format conversion needed.
- **Docker** succeeded because `Dockerfile` adds a thin layer *around* your existing app,
  not *instead of* it.
- **npm/pip** succeeded because `package.json`/`pyproject.toml` sits alongside your code.

The failed pattern is: "rewrite your project in our format" (e.g., early AWS Lambda with
rigid handler signatures, or early Android requiring Java-specific project structure).

For AI engineer interviews, this translates to: when designing agent platforms, the
**manifest layer** should be additive (metadata alongside code), not transformative
(restructuring code into a new layout). The conversion cost should be proportional to the
metadata gap, not to the project size.

---

## Summary

**Recommendation:** Redesign feature19 from "copy into new kinnoo directory" to "add
`kinnoo.yaml` to existing project in-place." This is the `npm init` / `docker init` model.
It dramatically reduces friction, increases compatibility, and leverages the feature27
analyzer investment directly.

**Next step:** If you agree with this direction, I'll rewrite the feature19 description,
ACs, and create tasks. The scope is actually *smaller* than the current spec (no file
copying, no directory creation), so implementation should be leaner.

---

## Tech Lead Review 1

### Verdict

Feature19 is **not approved for merge yet**. Implementation is close, but there are
blocking behavior gaps versus AC intent and the full regression suite is currently red.

### Findings (ordered by severity)

1. **High - Import flow is not automation-safe and fails on non-interactive stdin paths.**
   - Evidence: [src/kinnoo/import_command.py](src/kinnoo/import_command.py#L386) always prompts and treats EOF as interrupt; several tests invoke import without stdin input and expect default accept behavior.
   - Failing tests: [tests/test_cli_import.py](tests/test_cli_import.py#L12), [tests/test_cli_import.py](tests/test_cli_import.py#L45), [tests/test_cli_import.py](tests/test_cli_import.py#L124), [tests/test_cli_import.py](tests/test_cli_import.py#L158), [tests/test_cli_import.py](tests/test_cli_import.py#L183)
   - Impact: Breaks developer/CI ergonomics and causes multiple AC-aligned tests to fail before manifest generation path is reached.

2. **Medium - Prompt minimization logic asks for services when none are inferred (false positive prompting).**
   - Evidence: [src/kinnoo/import_command.py](src/kinnoo/import_command.py#L77) + [src/kinnoo/import_command.py](src/kinnoo/import_command.py#L279). Empty list `[]` is treated as resolvable value for missing-check but still forced by low-confidence branch.
   - Impact: Violates confirm-first/prompt-minimization intent (AC4), contributes to unexpected EOF interruptions in tests.

3. **Medium - Collision safety check happens too late (after wizard interaction).**
   - Evidence: existing-manifest guard is inside write path [src/kinnoo/import_command.py](src/kinnoo/import_command.py#L340), not at command preflight stage.
   - Failing symptom: [tests/test_cli_import.py](tests/test_cli_import.py#L91) receives interrupt path instead of immediate collision message.
   - Impact: Poor UX; user is prompted unnecessarily before deterministic early failure.

4. **Medium - AC7 explicit override path is not implemented.**
   - Evidence: no `--force`/explicit override option exists in import command parser/handler; collision message references override concept only textually.
   - Impact: Partial AC7 fulfillment (prevention exists, explicit force/confirm path does not).

5. **Low - Wrapper prompt can trigger in low-confidence scenarios where entrypoint file is missing, increasing interruption risk.**
   - Evidence: warning branch at [src/kinnoo/import_command.py](src/kinnoo/import_command.py#L395) prompts wrapper option for all warning cases, including non-existent entrypoint situations.
   - Impact: Adds avoidable prompt branch and contributes to scripted input mismatch in low-confidence test paths.

### AC Coverage Assessment

- **Traceability status:** AC1-AC10 each have mapped tests (`test252`-`test262`) in [TESTS.txt](TESTS.txt).
- **Execution status:** Coverage exists on paper, but implementation does not currently satisfy all mapped behaviors due to the failing feature19 test subset.
- **Task linkage status:** `task163`-`task167` are correctly set to `needs-review` in [TASKS.txt](TASKS.txt#L3190).

### Full Regression Result

- Command run: `python3 -m pytest`
- Result: **7 failed, 252 passed, 1 skipped**
- Failures are all in [tests/test_cli_import.py](tests/test_cli_import.py):
  - [tests/test_cli_import.py](tests/test_cli_import.py#L12)
  - [tests/test_cli_import.py](tests/test_cli_import.py#L45)
  - [tests/test_cli_import.py](tests/test_cli_import.py#L70)
  - [tests/test_cli_import.py](tests/test_cli_import.py#L91)
  - [tests/test_cli_import.py](tests/test_cli_import.py#L124)
  - [tests/test_cli_import.py](tests/test_cli_import.py#L158)
  - [tests/test_cli_import.py](tests/test_cli_import.py#L183)

### Recommended Fix Plan for SWE

1. Add a non-interactive-safe path for confirmation defaults (or explicit non-interactive flag semantics) so import can run deterministically under automated test harnesses.
2. Refine `_should_prompt_field()` behavior for list-like fields so empty inferred service lists do not force unnecessary prompts.
3. Move `kinnoo.yaml` collision check to early preflight before any interactive prompts.
4. Implement explicit override path for AC7 (flag or confirmation mode), and add/adjust tests to verify both default-safe and explicit-override behaviors.
5. Narrow wrapper prompt conditions so missing entrypoint files do not trigger optional wrapper prompt flow.

### Merge Recommendation

- Keep feature19 tasks in `needs-review` and return to SWE for fixes.
- Re-run focused import tests, then full `python3 -m pytest` before requesting Tech Lead Review 2.

# Feature19 TechLead Review 1 - remediation pass (SWE agent)

## Summary
- Fixed automation-safety for import wizard in non-interactive contexts by defaulting on EOF instead of hard-interrupting.
- Fixed prompt-minimization false positives by skipping prompts for empty inferred list values (especially `services: []`).
- Moved collision safety to preflight, before any wizard interaction.
- Added explicit AC7 override path: `kinnoo import [path] --force`.
- Narrowed wrapper prompt to true entrypoint contract mismatch warnings only.

## Tests and results
- `python3 -m pytest tests/test_cli_import.py` -> `11 passed`

## Teaching notes
- For CI-safe interactive tooling, EOF behavior should be mode-aware: non-interactive contexts generally require deterministic defaults rather than interruption semantics.
- Prompt-minimization logic should treat "none detected" list values as resolved state, not as missing values.
- Safety checks with deterministic outcomes (like collision detection) should run in preflight so users do not spend effort answering prompts before guaranteed failure paths.

## Tech Lead Review 2

### Verdict

Feature19 is **approved for merge** to `phase3/main`.

### Verification Summary

- Reviewed remediation deltas in `import_command` and CLI wiring:
   - non-interactive-safe prompt defaults,
   - preflight collision guard,
   - explicit `--force` override path,
   - conditional wrapper prompt narrowing,
   - prompt minimization fix for empty inferred lists.
- Confirmed feature19 task set (`task163`-`task167`) now matches implemented behavior and test evidence.

### Test Evidence

- Focused feature19 suite:
   - `python3 -m pytest tests/test_cli_import.py`
   - result: `11 passed`
- Full regression:
   - `python3 -m pytest`
   - result: `259 passed, 1 skipped`

### AC Coverage Assessment

- AC1-AC10 remain fully mapped to `test252`-`test262` and are now passing as implemented.
- No unresolved blocking gaps found in the prior Tech Lead Review 1 findings.

### Merge Recommendation

- Proceed with merge.
- Post-approval governance updates completed:
   - feature19 status advanced to `completed`.
   - tasks `task163`-`task167` advanced to `completed`.
   - project version bumped to `v0.12.1`.
   - changelog updated with feature19 implementation notes and test evidence.