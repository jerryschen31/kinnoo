# Task254 - Community Agent Corpus Sourcing and Download Staging

## Summary
- Goal completed: expand from the initial 7 framework samples to a full staged corpus of 42 examples.
- Final coverage: 6 examples per framework across 7 supported frameworks.
- Complexity target satisfied for every framework:
  - 2 simple
  - 2 medium
  - 2 high

## Source and Inventory Files
- Primary inventory file:
  - `example-scratch/agents-list.md`
- Canonical machine-readable mapping used to stage local folders:
  - `example-scratch/agents-map.txt`
- Staged local corpus root (one agent per subfolder):
  - `example-scratch/agents/`

## Download Results
- Total staged local agent folders: 42
- Frameworks covered:
  - PydanticAI
  - LangChain
  - LangGraph
  - OpenAI Agents SDK
  - MCP client
  - MCP server
  - OpenClaw

## Complexity Distribution Verification
Per-framework counts from `example-scratch/agents-map.txt`:
- PydanticAI: simple=2, medium=2, high=2
- LangChain: simple=2, medium=2, high=2
- LangGraph: simple=2, medium=2, high=2
- OpenAI Agents SDK: simple=2, medium=2, high=2
- MCP client: simple=2, medium=2, high=2
- MCP server: simple=2, medium=2, high=2
- OpenClaw: simple=2, medium=2, high=2

## Local Folder Paths (All 42)
1. `example-scratch/agents/pydanticai-weather-agent`
2. `example-scratch/agents/pydanticai-roulette-wheel-agent`
3. `example-scratch/agents/pydanticai-bank-support-agent`
4. `example-scratch/agents/pydanticai-flight-booking-agent`
5. `example-scratch/agents/pydanticai-rag-agent`
6. `example-scratch/agents/pydanticai-data-analyst-agent`
7. `example-scratch/agents/langchain-mrkl-agent-base`
8. `example-scratch/agents/langchain-self-ask-search-agent`
9. `example-scratch/agents/langchain-structured-chat-agent`
10. `example-scratch/agents/langchain-tool-calling-agent`
11. `example-scratch/agents/langchain-openai-functions-multi-agent`
12. `example-scratch/agents/langchain-openai-assistant-agent`
13. `example-scratch/agents/langgraph-react-from-scratch`
14. `example-scratch/agents/langgraph-tool-calling-graph`
15. `example-scratch/agents/langgraph-plan-and-execute`
16. `example-scratch/agents/langgraph-customer-support-graph`
17. `example-scratch/agents/langgraph-hierarchical-agent-teams`
18. `example-scratch/agents/langgraph-web-voyager`
19. `example-scratch/agents/openai-agents-hello-world`
20. `example-scratch/agents/openai-agents-basic-tools`
21. `example-scratch/agents/openai-agents-message-filter-handoff`
22. `example-scratch/agents/openai-agents-customer-service`
23. `example-scratch/agents/openai-agents-research-bot`
24. `example-scratch/agents/openai-agents-financial-research-agent`
25. `example-scratch/agents/mcp-client-stdio-client`
26. `example-scratch/agents/mcp-client-completion-client`
27. `example-scratch/agents/mcp-client-pagination-client`
28. `example-scratch/agents/mcp-client-oauth-client`
29. `example-scratch/agents/mcp-client-streamable-basic-client`
30. `example-scratch/agents/mcp-client-url-elicitation-client`
31. `example-scratch/agents/mcp-server-time-server`
32. `example-scratch/agents/mcp-server-memory-server`
33. `example-scratch/agents/mcp-server-fetch-server`
34. `example-scratch/agents/mcp-server-filesystem-server`
35. `example-scratch/agents/mcp-server-git-server`
36. `example-scratch/agents/mcp-server-sequentialthinking-server`
37. `example-scratch/agents/openclaw-diffs-extension-agent`
38. `example-scratch/agents/openclaw-ollama-extension-agent`
39. `example-scratch/agents/openclaw-llm-task-extension-agent`
40. `example-scratch/agents/openclaw-lobster-extension-agent`
41. `example-scratch/agents/openclaw-open-prose-extension-agent`
42. `example-scratch/agents/openclaw-voice-call-extension-agent`

## Staging Method
- Each staged folder includes source material copied from already-cloned upstream framework repositories under `example-scratch/`.
- Each staged folder includes `METADATA.md` with:
  - framework
  - complexity bucket
  - example name
  - source URL
  - source path used for staging

## Notes
- The curated list intentionally mixes file-level and directory-level examples depending on how each framework publishes canonical agent examples.
- Complexity tagging is based on relative implementation scope (single-purpose examples -> orchestration/multi-agent/multi-module workflows).
