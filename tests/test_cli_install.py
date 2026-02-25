import subprocess
import sys
import pytest

# Test51: kinnoo install usage error

def test_install_missing_archive_prints_usage():
    # Run kinnoo install with no arguments
    # Use script path for local CLI testing
    cli_path = "src/kinnoo/cli.py"
    result = subprocess.run([
        sys.executable, cli_path, "install"
    ], capture_output=True, text=True)
    # Should print usage error and exit with non-zero code
    assert result.returncode != 0
    assert "Usage: kinnoo install <archive-path>" in result.stderr
