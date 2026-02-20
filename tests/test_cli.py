import subprocess
import sys
import pytest

def test_cli_installable_and_runnable():
    # This test checks that the CLI is installable and runnable via pyproject.toml
    result = subprocess.run([sys.executable, "-m", "kinnoo.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "init" in result.stdout
