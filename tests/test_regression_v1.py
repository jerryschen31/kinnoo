import subprocess
import sys


# [agent] Run this regression gate before opening/merging PRs that change CLI behavior,
# command modules, packaging/install flows, or shared test utilities; it verifies V1
# baseline modules still pass together after refactors.
def test_v1_suite_passes_after_feature7():
    modules = [
        "tests/test_validator.py",
        "tests/test_init.py",
        "tests/test_cli.py",
        "tests/test_pack.py",
        "tests/test_install.py",
        "tests/test_cli_install.py",
    ]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *modules],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "V1 regression suite failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
