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
