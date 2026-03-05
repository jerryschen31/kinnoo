import subprocess
import sys


def test_inspect_missing_target_prints_usage() -> None:
    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "inspect"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Usage: kinnoo inspect <target>" in result.stderr
