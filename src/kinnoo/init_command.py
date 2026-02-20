"""
Agent scaffolding logic for kinnoo init.
"""
import os
from pathlib import Path
from kinnoo.templates import KINNOO_YAML_TEMPLATE, RUN_PY_TEMPLATE, REQUIREMENTS_TXT_TEMPLATE, README_MD_TEMPLATE

def init_agent(name: str, target_dir: Path):
    agent_dir = target_dir / name
    if agent_dir.exists():
        raise FileExistsError(f"Directory {agent_dir} already exists.")
    agent_dir.mkdir()
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()
    # Write files
    (agent_dir / "kinnoo.yaml").write_text(KINNOO_YAML_TEMPLATE.format(name=name))
    (agent_dir / "run.py").write_text(RUN_PY_TEMPLATE)
    (agent_dir / "requirements.txt").write_text(REQUIREMENTS_TXT_TEMPLATE)
    (agent_dir / "README.md").write_text(README_MD_TEMPLATE.format(name=name))
