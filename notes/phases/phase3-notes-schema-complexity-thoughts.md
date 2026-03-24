Good. Now I have the full picture. Here's my strategic analysis:

---

## The Onboarding Friction Problem

You're right to worry. Here's what a complex agent's `kinnoo.yaml` will look like after features 23-26:

```yaml
name: my-mcp-agent
version: 1.0.0
description: "RAG agent with MCP server and vector DB"
author: "dev@example.com"
license: MIT
entrypoint: server.py
framework: langchain
model: gpt-4o

runtime:
  language: python
  version: "3.11"
  type: mcp-server         # feature23
  port: 8080               # feature23

inputs:
  type: string
  required: false           # feature20

outputs:
  type: string

dependencies:
  - langchain
  - chromadb
  - fastmcp

env_vars:
  - OPENAI_API_KEY
  - CHROMA_DB_HOST

assets:                      # feature22
  paths:
    - data/embeddings.npz
    - models/classifier.onnx
  bundle: true
  max_bundle_size_mb: 200

services:                    # feature24
  - name: chroma
    type: vector-db
    health_check:
      method: tcp
      port: 8000
  - name: redis-cache
    type: database
    health_check:
      method: tcp
      port: 6379
```

That's **~45 lines of YAML** a developer needs to write correctly from scratch. Nobody's going to do that voluntarily. Compare this to `docker init` which generates a Dockerfile by asking ~4 questions.

## Three Strategies (from simplest to most powerful)

### Strategy 1: Smart Defaults + Minimal Viable Manifest

**Idea:** Make it so a developer only *needs* to write 3-5 lines. Everything else is inferred or defaulted.

```yaml
name: my-agent
version: 1.0.0
entrypoint: server.py
```

The validator and runtime would infer:
- `runtime.language: python` (from entrypoint extension)
- `runtime.version` (from `.python-version`, `pyproject.toml`, or current interpreter)
- `runtime.type` (from entrypoint analysis — does it start a server or exit?)
- `dependencies` (from `requirements.txt` or `pyproject.toml`)
- `inputs/outputs` (sensible defaults already exist)
- `env_vars` (scan for `os.environ` / `os.getenv` in source)

**Pros:** Lowest possible friction. Works retroactively for all complexity levels.  
**Cons:** Inference can be wrong; "magic" can be confusing when it guesses wrong.  
**Effort:** Medium — requires an inference engine, but each inference rule is simple.

### Strategy 2: Interactive Wizard (`kinnoo init --interactive` or `kinnoo import`)

**Idea:** A guided Q&A that builds `kinnoo.yaml` step-by-step:

```
$ kinnoo import ./my-existing-agent

Analyzing project...
  ✓ Found entrypoint: server.py
  ✓ Found requirements.txt (47 dependencies)
  ✓ Detected framework: langchain (from imports)
  ✓ Detected runtime: python 3.11 (from .python-version)

Questions:
  Is this a one-shot agent or long-running server? [one-shot/mcp-server]: mcp-server
  What port does it listen on? [8080]: 8080
  Does it require user input to start? [Y/n]: n

  Found these data files that might be assets:
    data/embeddings.npz (45 MB)
    models/classifier.onnx (120 MB)
  Bundle these as assets? [Y/n]: y

  Found os.getenv() calls for: OPENAI_API_KEY, CHROMA_DB_HOST
  Add these as required env vars? [Y/n]: y

Generated kinnoo.yaml ✓
Validating... ✓ All checks passed.
```

This is basically **feature19 revived and enhanced** for the Phase 3 schema. The key additions beyond what feature19 currently defines:
- **Static analysis** of the entrypoint to detect runtime type, framework, env vars
- **File system scanning** for assets, data directories, model files
- **Dependency detection** from `requirements.txt` / `pyproject.toml` / `setup.py`
- **Service inference** (detect redis/DB connection strings in code → suggest service declarations)

**Pros:** Developers answer simple questions; analysis does the heavy lifting.  
**Cons:** More complex to implement; analysis heuristics can miss things.  
**Effort:** High — but most value per developer minute saved.

### Strategy 3: LLM-Assisted Generation (`kinnoo import --ai`)

**Idea:** Point an LLM at the project and let it generate `kinnoo.yaml`:

```
$ kinnoo import ./my-existing-agent --ai

Analyzing project with AI assistance...
Scanning 23 Python files, requirements.txt, README.md...

Generated kinnoo.yaml:
  (displays the full manifest with explanatory comments)

Does this look correct? [Y/n/edit]:
```

The LLM reads the codebase (entrypoint, README, requirements, config files) and produces a complete manifest. The developer reviews and tweaks.

**Pros:** Handles edge cases better than hand-coded heuristics; understands README instructions.  
**Cons:** Requires API key / LLM access; non-deterministic; adds dependency on external service.  
**Effort:** Medium — the prompt engineering is straightforward if you have an LLM client.

## My Recommendation: **Combine 1 + 2, defer 3**

Here's the practical play:

1. **Immediately** (cheap, high ROI): Expand `normalize_manifest_defaults()` to infer more fields. A 3-field manifest should be packable. This means the validator warns about missing optional fields rather than erroring. You're already doing this for `dependencies`, `inputs`, `outputs`, and `assets` — extend it to `runtime.language`, `runtime.version`, and `runtime.type`.

2. **Feature19 revival** (feature23-26 timeframe): Redesign feature19 as `kinnoo import` with static analysis + interactive wizard. The wizard asks only what can't be inferred. For simple agents, it might ask 0 questions. For MCP servers, it asks 2-3. This is the biggest bang-for-buck feature for adoption.

3. **Later** (post-Phase 3): Add `--ai` flag to `kinnoo import` for LLM-assisted generation. This is a nice-to-have that relies on the same `kinnoo import` infrastructure.

## Key Insight: The Inference Engine

The real reusable piece across all three strategies is a **project analyzer module** — a standalone `src/kinnoo/analyzer.py` that takes a directory path and returns a dict of inferred manifest fields:

```python
def analyze_project(project_dir: Path) -> dict:
    """Analyze an existing project and infer kinnoo.yaml fields."""
    result = {}
    result["entrypoint"] = _detect_entrypoint(project_dir)
    result["runtime"] = _detect_runtime(project_dir)
    result["framework"] = _detect_framework(project_dir)
    result["dependencies"] = _detect_dependencies(project_dir)
    result["env_vars"] = _detect_env_vars(project_dir)
    result["assets"] = _detect_assets(project_dir)
    result["services"] = _detect_services(project_dir)
    return {k: v for k, v in result.items() if v is not None}
```

Each `_detect_*` function is a focused heuristic:
- **`_detect_entrypoint`**: Look for `run.py`, `main.py`, `server.py`, `app.py`, or a file with `if __name__ == "__main__"`
- **`_detect_runtime`**: Check `.python-version`, `pyproject.toml [requires-python]`, `Pipfile`, or `sys.version`
- **`_detect_framework`**: Scan imports in entrypoint (`from langchain`, `from pydantic_ai`, `import fastmcp`)
- **`_detect_dependencies`**: Read `requirements.txt` or `pyproject.toml [project.dependencies]`
- **`_detect_env_vars`**: Regex scan for `os.environ["X"]`, `os.getenv("X")` across `.py` files
- **`_detect_assets`**: Find large non-code files (`.npz`, `.onnx`, `.pkl`, `.bin`, `.db`) or `data/` dirs
- **`_detect_services`**: Look for connection strings (redis://, postgresql://, localhost:PORT patterns)

This module becomes the backbone for `kinnoo import`, for smarter defaults in `kinnoo init`, and later for `--ai` assisted generation.

## Where This Fits in Your Roadmap

I'd suggest **unpausing feature19 and redesigning it** to incorporate the analyzer concept, then scheduling it as a **Wave 1.5** item — after the quick wins (feature20, 21, 22 ✓) but before the heavy schema features (23-26). The rationale: developers will need `kinnoo import` most urgently *when* the schema grows.

Alternatively, if you want to ship features 23-26 first and reduce friction retroactively, keep feature19 paused but **implement Strategy 1 now** (smarter defaults, fewer required fields) as a small task within feature23 or as a standalone micro-feature. That way the schema can grow without the barrier growing proportionally.

---

**What's your gut reaction?** Do you want to prioritize the smart-defaults approach (quick, incremental) or invest in the full analyzer/wizard (bigger but more transformative)? Or both in sequence?

Quick note: I agree to do 1 and 2 and defer 3.
