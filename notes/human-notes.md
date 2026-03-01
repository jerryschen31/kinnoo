## Random Notes and Learnings

- One task at a time for an SWE agent. It is tempting to combine tasks for an agent to do - but as I found out with trying to have an agent do task10 and task11 at the same time, an agent gets very confused and gets stuck with bugs
- Coding models are not always up to date with latests API docs (e.g., recent google.genai API doc updates). Sometimes I need to manually give them a URL to the newest docs.

## Why is `framework` an optional field in `kinnoo.yaml`?

The MVP runtime contract treats every agent as a **black box** — `kinnoo` only needs
to know `entrypoint` + `runtime` to execute it. It doesn't actually use the `framework`
field at runtime.

The reasons it's optional rather than omitted entirely:

1. **Discoverability** — a developer installing an agent can `kinnoo inspect` it and
   immediately know what framework it uses, without reading the source code.

2. **Future adapter system** — in V2, when Kinnoo builds framework-specific adapters
   (e.g., special handling for LangGraph's streaming output, or CrewAI's multi-agent
   lifecycle hooks), the CLI will use this field to select the right adapter. Making it
   optional now means agents that don't need an adapter work fine without it.

3. **Registry/marketplace metadata** — when agents are published to a registry,
   `framework` becomes a searchable/filterable attribute ("show me all LangChain agents").

4. **Not all agents use a named framework** — someone could write a pure OpenAI API agent
   with no framework at all. Requiring the field would force them to put `framework: none`
   or similar, which is noise.

The short answer: it provides useful metadata today and enables future features, but the
agent runs correctly whether it's present or not.

## Preflight validation and advanced checks (future feature in Phase1)

**Preflight validation** and **advanced checks** are steps that help ensure an agent package will work correctly on another machine before you pack or run it. Examples include:

### Preflight Validation Examples
- **Dependency check:** Make sure all required Python packages are listed in `requirements.txt` and can be installed.
- **Python version check:** Confirm the agent specifies a compatible Python version and that it’s available.
- **Entrypoint check:** Verify the entrypoint file (like `run.py`) exists and is executable.
- **Manifest validation:** Ensure `kinnoo.yaml` is present and follows the schema.
- **Missing files:** Check that all files referenced in the manifest (like prompt templates or tools) actually exist.
- **Environment variables:** Warn if required environment variables (API keys, etc.) are missing.

### Advanced Checks Examples
- **System dependencies:** Detect if the agent needs system tools (like `ffmpeg`, `tesseract`) and warn if they’re missing.
- **GPU/CPU compatibility:** Check if the agent requires a GPU and if one is available.
- **Service availability:** For agents needing background services (like Redis, Postgres), check if those services are running or accessible.
- **Port conflicts:** Warn if the agent tries to use a network port that’s already in use.
- **Security scan:** Optionally scan for secrets or unsafe code before packaging.

**Summary:**  
Preflight validation helps catch problems early, so agents are more likely to “just work” when shared or run elsewhere.

## Considerations - value to dev community if Kinnoo only supports running single agents

If kinnoo only supports running single agents (but can package multi-agent systems for sharing):

### Value Provided:

- Streamlines single-agent workflows: Makes it much easier for devs to package, share, and run individual agents across machines and teams.
- Standardizes agent packaging: Introduces a manifest and packaging convention, reducing “works on my machine” problems for single-agent projects.
- Lowers onboarding friction: New users can quickly try, run, and modify single-agent projects without manual setup.
- Lays groundwork for a registry: Even if multi-agent systems can’t be run, they can be published/discovered, encouraging ecosystem growth.
- Lays groundwork for orchestrating cross-framework multi-agent systems. Regardless of orchestration framework (e.g., Kubernetes), individual agents within a multi-agent system can be run with "kinnoo run", and the individual agents themselves can be written with any supported framework. This greatly simplifies the runtime and management of these multi-agent systems, and prevents having to "lock into" a specific multi-agent framework like CrewAI.

### Limitations:

- Misses the cutting edge: The most exciting agentic research and production use cases are increasingly multi-agent (collaboration, tool use, orchestration).
- Perceived as “not future-proof”: Advanced users may see kinnoo as limited if it can’t run the latest multi-agent workflows.
- Registry is less useful: If users can’t run what they find, the value of publishing multi-agent systems is reduced.

**Summary:**
Kinnoo would still provide real value for reproducibility, sharing, and onboarding in the single-agent space, but would be seen as incomplete for the most advanced and collaborative agent use cases.

### V2 thoughts

- V2 should support specifying an available model (e.g. gpt-4o-mini, gpt-5-nano, etc) in addition to the platform (framework) when initializing an agent
- V2 should support tools that interact with commonly available MCP servers - i.e., speciying the MCP servers as "plugins"
- V2 should support interactive mode with "kinnoo run"
- V2 should support secure MCP server for interacting with filesystem (Filesystem MCP server)
- need to decide on a direction for V3+. Do I support more "scaffolding" and focus on init (building an agent), or focus more on runtime capabilities (kinnoo run), or just focus on the registry aspect, or something else? Need some good ideas and guidance here

### kinnoo import tasks (for later)


  - id: task62
    title: Add kinnoo import CLI command
    type: task
    description: |
      Add `kinnoo import <existing-agent-path> <new-agent-dir>` to CLI parsing
      and route execution to a dedicated import command module.
    files:
      - src/kinnoo/cli.py
      - src/kinnoo/import_command.py
    steps:
      - step1: Add `import` subcommand with required positional args `existing-agent-path` and `new-agent-dir`
      - step2: Print clear usage and examples when args are missing or invalid
      - step3: Delegate command execution to `import_command.py` to keep CLI modular
      - step4: Ensure command exits with stable non-zero codes on validation failure
    dependencies: [task39]
    tests: []
    status: not-started

  - id: task63
    title: Implement source project analysis and inference
    type: task
    description: |
      Analyze an existing agent project to infer likely entrypoint,
      requirements source, and baseline manifest metadata.
    files:
      - src/kinnoo/import_command.py
      - src/kinnoo/schema.py
    steps:
      - step1: Detect candidate entrypoint files using deterministic priority rules (for example run.py/main.py)
      - step2: Detect requirements source (`requirements.txt`, fallback heuristics) and capture dependencies list
      - step3: Infer manifest fields (`name`, `entrypoint`, runtime defaults, inputs/outputs defaults) with explicit fallback behavior
      - step4: Emit actionable warnings when inference confidence is low instead of silently guessing
    dependencies: [task62, task48, task49]
    tests: []
    status: not-started

  - id: task64
    title: Generate kinnoo scaffold from inferred metadata
    type: task
    description: |
      Create the target Kinnoo agent directory and generate required files from
      inferred metadata while preserving source files unchanged.
    files:
      - src/kinnoo/import_command.py
      - src/kinnoo/templates.py
      - src/kinnoo/validator.py
    steps:
      - step1: Create `<new-agent-dir>` with required Kinnoo structure and copy/import selected source files
      - step2: Generate kinnoo.yaml and requirements.txt with inferred/default values
      - step3: Validate generated kinnoo.yaml via feature1 validator before finalizing output
      - step4: Surface guidance for user edits when generated values need manual refinement
    dependencies: [task63, task5, task18]
    tests: []
    status: not-started

  - id: task65
    title: Add collision safety and force controls
    type: task
    description: |
      Prevent destructive writes when target directories already exist and add a
      deliberate override path for advanced users.
    files:
      - src/kinnoo/cli.py
      - src/kinnoo/import_command.py
    steps:
      - step1: Detect target directory collisions before file writes
      - step2: Abort safely by default with clear remediation message
      - step3: Add explicit override behavior (force/confirm) with guarded semantics
      - step4: Ensure source project paths are never modified during import
    dependencies: [task62]
    tests: []
    status: not-started

  - id: task66
    title: Implement rollback and interruption-safe cleanup
    type: task
    description: |
      Ensure partial import state is cleaned up when failures or user
      interruptions occur during onboarding flows.
    files:
      - src/kinnoo/import_command.py
      - src/kinnoo/cli.py
    steps:
      - step1: Track created files/directories transactionally during import
      - step2: On exceptions, remove partially created artifacts and print concise failure summary
      - step3: Handle KeyboardInterrupt/EOF as controlled aborts with deterministic cleanup
      - step4: Guarantee no broken partial Kinnoo agent remains after failed/aborted import
    dependencies: [task64, task65]
    tests: []
    status: not-started

  - id: task67
    title: Document kinnoo import onboarding workflow
    type: task
    description: |
      Add documentation for importing existing agents, including expected input
      structure, inferred defaults, safe override behavior, and failure recovery.
    files:
      - README.md
      - docs/manifest-schema-reference.md
    steps:
      - step1: Add quickstart for `kinnoo import <existing-agent-path> <new-agent-dir>`
      - step2: Document inference behavior, when manual edits are expected, and common troubleshooting paths
      - step3: Document cleanup and interruption guarantees so users trust failure handling
      - step4: Keep examples concise and aligned with command help output
    dependencies: [task62, task63, task64, task66]
    tests: []
    status: not-started