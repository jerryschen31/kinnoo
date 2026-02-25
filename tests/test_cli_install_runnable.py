import subprocess
import sys
import tempfile
from pathlib import Path
import zipfile
import shutil
import os
import pytest

def make_minimal_kno(tmp_path, agent_name="runnableagent"):
    """Helper to create a minimal .kno archive with a valid manifest and run.py at the correct structure."""
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    manifest = (
        'entrypoint: run.py\n'
        'dependencies: []\n'
        'inputs:\n  type: string\n'
        'outputs:\n  type: string\n'
        'runtime:\n'
        '  type: one-shot\n'
        '  language: python\n'
        '  version: "3.10"\n'
        'name: ' + agent_name + '\n'
        'version: 0.1.0\n'
    )
    (agent_dir / "kinnoo.yaml").write_text(manifest)
    (agent_dir / "run.py").write_text(
        "import sys\nprint(f'agent ran: {sys.argv[1]}')\n"
    )
    archive_path = tmp_path / f"{agent_name}.kno"
    # Archive should contain kinnoo.yaml and run.py at the root
    with zipfile.ZipFile(archive_path, "w") as z:
        for file in ["kinnoo.yaml", "run.py"]:
            z.write(agent_dir / file, arcname=file)
    return archive_path, agent_name

@pytest.mark.integration
def test_install_makes_agent_runnable(tmp_path):
    """Test that kinnoo install makes agent runnable with kinnoo run (test55)."""
    import shutil
    archive_path, agent_name = make_minimal_kno(tmp_path)
    agent_dir = tmp_path / agent_name
    cli_path = Path(__file__).parent.parent / "src" / "kinnoo" / "cli.py"
    # Debug: print archive contents
    import zipfile
    with zipfile.ZipFile(archive_path, "r") as z:
        print("Archive contents:", z.namelist())
    # Remove the agent directory so kinnoo install can create it
    shutil.rmtree(agent_dir)
    # Install the agent
    result = subprocess.run([
        sys.executable, str(cli_path), "install", str(archive_path)
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"kinnoo install failed: {result.stderr}"
    assert agent_dir.exists(), "Agent directory not created"
    # Run the agent
    run_result = subprocess.run([
        sys.executable, str(cli_path), "run", str(agent_dir), "test input"
    ], capture_output=True, text=True)
    assert run_result.returncode == 0, f"kinnoo run failed: {run_result.stderr}"
    assert "agent ran: test input" in run_result.stdout, f"Unexpected output: {run_result.stdout}"
