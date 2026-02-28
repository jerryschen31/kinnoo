import os
import subprocess
import sys
from pathlib import Path


def _create_agent(agent_dir: Path, include_env_vars: bool) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)
    env_vars_block = ""
    if include_env_vars:
        env_vars_block = "env_vars:\n  - FEATURE10_SECRET_TOKEN\n"

    (agent_dir / "kinnoo.yaml").write_text(
        """
name: test-agent
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
        + env_vars_block,
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text(
        """
import os

status = "set" if os.getenv("FEATURE10_SECRET_TOKEN") else "missing"
print(f"FEATURE10_SECRET_TOKEN={status}")
print("RUN_OK")
""",
        encoding="utf-8",
    )


def test_env_vars_resolve_from_process_environment(tmp_path: Path) -> None:
    agent_dir = tmp_path / "env-agent"
    _create_agent(agent_dir, include_env_vars=True)

    env = os.environ.copy()
    env["FEATURE10_SECRET_TOKEN"] = "SENTINEL_SECRET_ALPHA_9f3b"

    result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), "hello"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Expected success, got stderr: {result.stderr}"
    assert "FEATURE10_SECRET_TOKEN=set" in result.stdout
    assert "RUN_OK" in result.stdout


def test_agents_without_env_vars_unaffected(tmp_path: Path) -> None:
    agent_dir = tmp_path / "no-env-agent"
    _create_agent(agent_dir, include_env_vars=False)

    env = os.environ.copy()
    env.pop("FEATURE10_SECRET_TOKEN", None)

    result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), "hello"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Expected unchanged V1 behavior, got stderr: {result.stderr}"
    assert "RUN_OK" in result.stdout
    assert "Missing required environment variables" not in result.stderr


def test_env_vars_fallback_to_dotenv(tmp_path: Path) -> None:
    agent_dir = tmp_path / "dotenv-env-agent"
    _create_agent(agent_dir, include_env_vars=True)

    (agent_dir / ".env").write_text(
        "FEATURE10_SECRET_TOKEN=SENTINEL_SECRET_BRAVO_7c21\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env.pop("FEATURE10_SECRET_TOKEN", None)

    result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), "hello"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Expected .env fallback success, got stderr: {result.stderr}"
    assert "FEATURE10_SECRET_TOKEN=set" in result.stdout
    assert "RUN_OK" in result.stdout
    assert "SENTINEL_SECRET_BRAVO_7c21" not in result.stdout
    assert "SENTINEL_SECRET_BRAVO_7c21" not in result.stderr
