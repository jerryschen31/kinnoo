"""
Templates for kinnoo agent scaffolding files.
"""

KINNOO_YAML_TEMPLATE = """name: {name}
version: 0.1.0
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
