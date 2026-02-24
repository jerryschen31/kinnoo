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

### Limitations:

- Misses the cutting edge: The most exciting agentic research and production use cases are increasingly multi-agent (collaboration, tool use, orchestration).
- Perceived as “not future-proof”: Advanced users may see kinnoo as limited if it can’t run the latest multi-agent workflows.
- Registry is less useful: If users can’t run what they find, the value of publishing multi-agent systems is reduced.

**Summary:**
Kinnoo would still provide real value for reproducibility, sharing, and onboarding in the single-agent space, but would be seen as incomplete for the most advanced and collaborative agent use cases.

