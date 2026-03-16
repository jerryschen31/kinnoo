# --- Framework-specific templates ---

GEMINI_RUN_PY = '''import sys
import asyncio
from google import genai
import os

async def main(input_text):
  api_key = os.getenv("GOOGLE_API_KEY")
  if not api_key:
    print("Missing GOOGLE_API_KEY environment variable.")
    sys.exit(1)
  client = genai.Client(api_key=api_key)
  response = await asyncio.to_thread(
    client.models.generate_content,
    model="gemini-2.5-flash-lite",
    contents=input_text
  )
  print(response.text)

if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

GEMINI_REQUIREMENTS = "google-genai\n"

GEMINI_README = '''# {name}

This agent uses Google Gemini (Flash Lite) via the `google-genai` library.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export GOOGLE_API_KEY=your-key-here`

## Run Example
```
python run.py "Hello Gemini!"
```
'''

CHATGPT_RUN_PY = '''import sys
import asyncio
import openai
import os

async def main(input_text):
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
    print("Missing OPENAI_API_KEY environment variable.")
    sys.exit(1)
  client = openai.AsyncOpenAI(api_key=api_key)
  response = await client.chat.completions.create(
    model="gpt-5-nano",
    messages=[{"role": "user", "content": input_text}]
  )
  print(response.choices[0].message.content)

if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

CHATGPT_REQUIREMENTS = "openai\n"

CHATGPT_README = '''# {name}

This agent uses OpenAI ChatGPT via the `openai` library.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export OPENAI_API_KEY=your-key-here`

## Run Example
```
python run.py "Hello ChatGPT!"
```
'''

CLAUDE_RUN_PY = '''import sys
import asyncio
import anthropic
import os

async def main(input_text):
  api_key = os.getenv("ANTHROPIC_API_KEY")
  if not api_key:
    print("Missing ANTHROPIC_API_KEY environment variable.")
    sys.exit(1)
  client = anthropic.AsyncAnthropic(api_key=api_key)
  response = await client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=256,
    messages=[{"role": "user", "content": input_text}]
  )
  print(response.content[0].text)

if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

CLAUDE_REQUIREMENTS = "anthropic\n"

CLAUDE_README = '''# {name}

This agent uses Anthropic Claude via the `anthropic` library.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export ANTHROPIC_API_KEY=your-key-here`

## Run Example
```
python run.py "Hello Claude!"
```
'''

PYDANTIC_AI_RUN_PY = '''import os
import sys
import asyncio


async def _run_framework_mode(input_text):
  # Framework-native path: use pydantic-ai Agent when dependencies/env are available.
  from pydantic_ai import Agent

  agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt="You are a concise assistant.",
  )
  result = await agent.run(input_text)
  print(result.output)


async def _run_test_safe_mode(input_text):
  # Deterministic CI-safe path for environments without external API access.
  print(f"[pydantic-ai template] test-safe response: {input_text}")


async def main(input_text):
  test_safe_mode = os.getenv("KINNOO_TEST_SAFE_MODE", "").lower() in {"1", "true", "yes"}
  if test_safe_mode:
    await _run_test_safe_mode(input_text)
    return

  try:
    await _run_framework_mode(input_text)
  except Exception:
    # Fall back to deterministic output when framework dependencies or credentials are unavailable.
    await _run_test_safe_mode(input_text)


if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

PYDANTIC_AI_REQUIREMENTS = "pydantic-ai>=0.0,<0.1\n"

PYDANTIC_AI_README = '''# {name}

This agent scaffold targets the `pydantic-ai` framework.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export OPENAI_API_KEY=your-key-here`

## Runtime Paths
- Production framework path: uses `pydantic_ai.Agent` with an OpenAI model.
- Deterministic test-safe path: set `KINNOO_TEST_SAFE_MODE=1` to run without external API calls.

## Model Configuration
- Update model/provider settings in `run.py` for your target backend.

## Run Example
```
python run.py "Hello PydanticAI!"
```

## Test-Safe Example
```
KINNOO_TEST_SAFE_MODE=1 python run.py "Hello PydanticAI!"
```
'''

LANGGRAPH_RUN_PY = '''import os
import sys
import asyncio
from typing import TypedDict


class GraphState(TypedDict):
  user_input: str
  response: str


def _build_graph():
  # Framework-native graph path: state schema + node + edges.
  from langgraph.graph import END, START, StateGraph

  graph_builder = StateGraph(GraphState)

  def respond_node(state: GraphState) -> GraphState:
    return {
      "user_input": state["user_input"],
      "response": f"[langgraph template] graph response: {state['user_input']}",
    }

  graph_builder.add_node("respond", respond_node)
  graph_builder.add_edge(START, "respond")
  graph_builder.add_edge("respond", END)
  return graph_builder.compile()


async def _run_framework_mode(input_text):
  graph = _build_graph()
  result = await asyncio.to_thread(graph.invoke, {"user_input": input_text, "response": ""})
  print(result["response"])


async def _run_test_safe_mode(input_text):
  # Deterministic CI-safe path for environments without external API access.
  print(f"[langgraph template] test-safe response: {input_text}")


async def main(input_text):
  test_safe_mode = os.getenv("KINNOO_TEST_SAFE_MODE", "").lower() in {"1", "true", "yes"}
  if test_safe_mode:
    await _run_test_safe_mode(input_text)
    return

  try:
    await _run_framework_mode(input_text)
  except Exception:
    # Fall back to deterministic output when framework dependencies are unavailable.
    await _run_test_safe_mode(input_text)


if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

LANGGRAPH_REQUIREMENTS = "langgraph>=0.2,<0.3\n"

LANGGRAPH_README = '''# {name}

This agent scaffold targets the `langgraph` framework.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export OPENAI_API_KEY=your-key-here`

## Runtime Paths
- Production framework path: uses `StateGraph`, explicit START/END edges, and graph invocation.
- Deterministic test-safe path: set `KINNOO_TEST_SAFE_MODE=1` to run without external API calls.

## Graph Configuration
- Define state schema and graph nodes/edges in `run.py`.

## Run Example
```
python run.py "Hello LangGraph!"
```

## Test-Safe Example
```
KINNOO_TEST_SAFE_MODE=1 python run.py "Hello LangGraph!"
```
'''

OPENAI_AGENTS_RUN_PY = '''import os
import sys
import asyncio


def _build_agent():
  # Framework-native path: define an OpenAI Agent with instructions.
  from agents import Agent

  return Agent(
    name="KinnooAssistant",
    instructions="You are a concise assistant.",
  )


async def _run_framework_mode(input_text):
  from agents import Runner

  agent = _build_agent()
  result = await Runner.run(agent, input_text)
  final_output = getattr(result, "final_output", None)
  print(final_output if final_output is not None else str(result))


async def _run_test_safe_mode(input_text):
  # Deterministic CI-safe path for environments without external API access.
  print(f"[openai-agents template] test-safe response: {input_text}")


async def main(input_text):
  test_safe_mode = os.getenv("KINNOO_TEST_SAFE_MODE", "").lower() in {"1", "true", "yes"}
  if test_safe_mode:
    await _run_test_safe_mode(input_text)
    return

  try:
    await _run_framework_mode(input_text)
  except Exception:
    # Fall back to deterministic output when framework dependencies are unavailable.
    await _run_test_safe_mode(input_text)


if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

OPENAI_AGENTS_REQUIREMENTS = "openai-agents>=0.1,<0.2\n"

OPENAI_AGENTS_README = '''# {name}

This agent scaffold targets the `openai-agents` SDK.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export OPENAI_API_KEY=your-key-here`

## Runtime Paths
- Production framework path: uses `Agent` construction and `Runner.run(...)` workflow.
- Deterministic test-safe path: set `KINNOO_TEST_SAFE_MODE=1` to run without external API calls.

## Agent Configuration
- Define agent roles, handoffs, and guardrails in `run.py`.

## Run Example
```
python run.py "Hello OpenAI Agents!"
```

## Test-Safe Example
```
KINNOO_TEST_SAFE_MODE=1 python run.py "Hello OpenAI Agents!"
```
'''
"""
Templates for kinnoo agent scaffolding files.
"""

# [agent] Keep this minimal manifest example synchronized with required manifest
# fields whenever schema/template changes affect minimum valid kinnoo.yaml shape.
INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE = """name: my-agent
version: 0.1.0
entrypoint: run.py
runtime:
  language: python
  version: "3.10"
  type: one-shot
dependencies: []
inputs:
  type: string
outputs:
  type: string
"""

INSPECT_MISSING_REQUIREMENTS_GUIDANCE_LINES = (
    "Recommended generation steps:",
    "pip install uv",
    "uv export --format requirements-txt > requirements.txt",
)

KINNOO_YAML_TEMPLATE = """name: {name}
version: 0.1.0
description: "TODO: Add a short agent description"
author: "TODO: Add author name"
entrypoint: run.py
runtime:
  language: python
  version: ">=3.10"
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
"""

RUN_PY_TEMPLATE = """import sys
import asyncio

async def main(input_text):
    print(f'Hello, world! Input: {input_text}')

if __name__ == '__main__':
    input_text = sys.argv[1] if len(sys.argv) > 1 else ''
    asyncio.run(main(input_text))
"""

REQUIREMENTS_TXT_TEMPLATE = ""  # Empty for MVP

README_MD_TEMPLATE = """# {name}

This is a Kinnoo agent scaffolded with `kinnoo init`.

- Edit `run.py` to implement your agent logic.
- See `kinnoo.yaml` for manifest fields.
"""
