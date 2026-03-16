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


def test_feature20_does_not_regress_v2_behavior():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_cli.py",
        "-k",
        "run",
        "tests/test_install.py",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature20 regression gate failed for V2 run/install behavior.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature21_framework_templates_do_not_regress_existing_frameworks():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_init.py::test_framework_templates_generate_correct_files",
        "tests/test_init.py::test_framework_valid",
        "tests/test_init.py::test_framework_manifests_pass_validation",
        "tests/test_init.py::test_feature21_regression_existing_frameworks_unchanged",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature21 regression gate failed for existing framework templates.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature22_no_assets_regression_unchanged():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_pack.py::test_pack_creates_correct_archive_structure",
        "tests/test_cli_install_extract.py::test_install_extracts_archive",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature22 no-assets regression gate failed for pack/install behavior.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
