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
"""
Templates for kinnoo agent scaffolding files.
"""

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
