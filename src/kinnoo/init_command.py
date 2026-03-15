
"""
Agent scaffolding logic for kinnoo init.
"""
import argparse
import sys
import os
from pathlib import Path
from typing import Optional
from kinnoo.templates import (
    KINNOO_YAML_TEMPLATE, RUN_PY_TEMPLATE, REQUIREMENTS_TXT_TEMPLATE, README_MD_TEMPLATE,
    GEMINI_RUN_PY, GEMINI_REQUIREMENTS, GEMINI_README,
    CHATGPT_RUN_PY, CHATGPT_REQUIREMENTS, CHATGPT_README,
    CLAUDE_RUN_PY, CLAUDE_REQUIREMENTS, CLAUDE_README
)

SUPPORTED_FRAMEWORKS = [
    "gemini",
    "chatgpt",
    "claude-chat",
    "pydantic-ai",
    "langgraph",
    "openai-agents",
]

def init_agent(name: str, target_dir: Path, framework: Optional[str] = None):
    agent_dir = target_dir / name
    if agent_dir.exists():
        raise FileExistsError(f"Directory {agent_dir} already exists.")
    agent_dir.mkdir()
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()
    # Write files
    (agent_dir / "kinnoo.yaml").write_text(KINNOO_YAML_TEMPLATE.format(name=name))
    if framework == "gemini":
        (agent_dir / "run.py").write_text(GEMINI_RUN_PY)
        (agent_dir / "requirements.txt").write_text(GEMINI_REQUIREMENTS)
        (agent_dir / "README.md").write_text(GEMINI_README.format(name=name))
    elif framework == "chatgpt":
        (agent_dir / "run.py").write_text(CHATGPT_RUN_PY)
        (agent_dir / "requirements.txt").write_text(CHATGPT_REQUIREMENTS)
        (agent_dir / "README.md").write_text(CHATGPT_README.format(name=name))
    elif framework == "claude-chat":
        (agent_dir / "run.py").write_text(CLAUDE_RUN_PY)
        (agent_dir / "requirements.txt").write_text(CLAUDE_REQUIREMENTS)
        (agent_dir / "README.md").write_text(CLAUDE_README.format(name=name))
    else:
        (agent_dir / "run.py").write_text(RUN_PY_TEMPLATE)
        (agent_dir / "requirements.txt").write_text(REQUIREMENTS_TXT_TEMPLATE)
        (agent_dir / "README.md").write_text(README_MD_TEMPLATE.format(name=name))

def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new Kinnoo agent directory with manifest and templates."
    )
    parser.add_argument("agent_name", nargs="?", help="Name of the agent directory to create.")
    parser.add_argument("--framework", type=str, default=None, help="Optional framework for agent template.")
    args = parser.parse_args()

    # Print usage if agent_name is missing
    if not args.agent_name:
        print("Usage: kinnoo init <agent_name> [--framework <framework>]", file=sys.stderr)
        sys.exit(1)

    framework = args.framework
    if framework is not None:
        fw = framework.lower()
        if fw not in SUPPORTED_FRAMEWORKS:
            print(f"Unsupported framework. The supported frameworks are: {', '.join(SUPPORTED_FRAMEWORKS)}.", file=sys.stderr)
            print("Usage: kinnoo init <agent_name> [--framework <framework>]", file=sys.stderr)
            sys.exit(1)

    # Directory creation and template generation
    try:
        init_agent(args.agent_name, Path(os.getcwd()), framework=framework)
    except FileExistsError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
