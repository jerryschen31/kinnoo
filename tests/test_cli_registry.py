import os
import subprocess
import sys
import zipfile
from pathlib import Path


def test_publish_cli_usage_and_local_flag(tmp_path: Path) -> None:
    usage_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "publish"],
        capture_output=True,
        text=True,
    )

    assert usage_result.returncode != 0
    assert "Usage: kinnoo publish <archive.kno> [--local]" in usage_result.stderr

    archive_path = tmp_path / "demo-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr(
            "kinnoo.yaml",
            """
name: demo-agent
version: 1.2.3
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
""",
        )
        archive_zip.writestr("run.py", "print('hello')\n")

    registry_root = tmp_path / "registry-sandbox"
    env = dict(**os.environ, KINNOO_REGISTRY_ROOT=str(registry_root))

    publish_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "publish", str(archive_path), "--local"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert publish_result.returncode == 0
    assert "Published demo-agent==1.2.3" in publish_result.stdout

    expected_archive = (
        registry_root / "demo-agent" / "1.2.3" / "demo-agent.kno"
    )
    assert expected_archive.exists()


def test_publish_extracts_metadata_and_blocks_duplicate_version(tmp_path: Path) -> None:
    archive_path = tmp_path / "duplicate-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr(
            "nested/kinnoo.yaml",
            """
name: duplicate-agent
version: 2.0.0
description: Duplicate publish test fixture
author: SWE Agent
license: MIT
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
""",
        )
        archive_zip.writestr("run.py", "print('hello')\n")

    registry_root = tmp_path / "registry-sandbox"
    env = dict(**os.environ, KINNOO_REGISTRY_ROOT=str(registry_root))

    first_publish = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "publish", str(archive_path)],
        capture_output=True,
        text=True,
        env=env,
    )

    assert first_publish.returncode == 0
    assert "Published duplicate-agent==2.0.0" in first_publish.stdout

    expected_archive_path = (
        registry_root / "duplicate-agent" / "2.0.0" / "duplicate-agent.kno"
    )
    expected_metadata_path = (
        registry_root / "duplicate-agent" / "2.0.0" / "manifest-metadata.json"
    )
    assert expected_archive_path.exists()
    assert expected_metadata_path.exists()

    duplicate_publish = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "publish", str(archive_path)],
        capture_output=True,
        text=True,
        env=env,
    )

    combined_output = f"{duplicate_publish.stdout}\n{duplicate_publish.stderr}"
    assert duplicate_publish.returncode != 0
    assert "Registry already contains published version 'duplicate-agent==2.0.0'" in combined_output
    assert "Refusing to overwrite" in combined_output


def test_install_selector_parsing_preserves_file_install(tmp_path: Path) -> None:
    archive_path = tmp_path / "installable-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr(
            "kinnoo.yaml",
            """
name: installable-agent
version: 1.0.0
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
""",
        )
        archive_zip.writestr("run.py", "print('ok')\n")
        archive_zip.writestr("requirements.txt", "")

    install_target_dir = tmp_path / "installed-from-file"
    file_install_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(install_target_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert file_install_result.returncode == 0
    assert "[kinnoo install] Extracted" in file_install_result.stdout
    assert (install_target_dir / "kinnoo.yaml").exists()

    registry_latest_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", "sample-agent"],
        capture_output=True,
        text=True,
    )
    latest_output = f"{registry_latest_result.stdout}\n{registry_latest_result.stderr}"
    assert registry_latest_result.returncode != 0
    assert "Registry agent 'sample-agent' was not found" in latest_output

    registry_exact_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", "sample-agent==1.2.3"],
        capture_output=True,
        text=True,
    )
    exact_output = f"{registry_exact_result.stdout}\n{registry_exact_result.stderr}"
    assert registry_exact_result.returncode != 0
    assert "Registry agent 'sample-agent' was not found" in exact_output

    invalid_selector_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", "sample-agent=="],
        capture_output=True,
        text=True,
    )
    invalid_output = f"{invalid_selector_result.stdout}\n{invalid_selector_result.stderr}"
    assert invalid_selector_result.returncode != 0
    assert "Invalid registry selector format" in invalid_output


def test_install_from_registry_name_and_version_uses_existing_pipeline(tmp_path: Path) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        cli_path = repo_root / "src" / "kinnoo" / "cli.py"

        registry_root = tmp_path / "registry-sandbox"
        env = dict(**os.environ, KINNOO_REGISTRY_ROOT=str(registry_root))

        archive_v1 = tmp_path / "registry-agent-v1.kno"
        with zipfile.ZipFile(archive_v1, "w") as archive_zip:
                archive_zip.writestr(
                        "kinnoo.yaml",
                        """
name: registry-agent
version: 1.0.0
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
""",
                )
                archive_zip.writestr("run.py", "import sys\nprint('registry-1.0.0:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n")
                archive_zip.writestr("requirements.txt", "")

        archive_v2 = tmp_path / "registry-agent-v2.kno"
        with zipfile.ZipFile(archive_v2, "w") as archive_zip:
                archive_zip.writestr(
                        "kinnoo.yaml",
                        """
name: registry-agent
version: 2.0.0
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
""",
                )
                archive_zip.writestr("run.py", "import sys\nprint('registry-2.0.0:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n")
                archive_zip.writestr("requirements.txt", "")

        publish_v1 = subprocess.run(
                [sys.executable, str(cli_path), "publish", str(archive_v1)],
                capture_output=True,
                text=True,
                env=env,
        )
        assert publish_v1.returncode == 0

        publish_v2 = subprocess.run(
                [sys.executable, str(cli_path), "publish", str(archive_v2)],
                capture_output=True,
                text=True,
                env=env,
        )
        assert publish_v2.returncode == 0

        latest_install = subprocess.run(
                [sys.executable, str(cli_path), "install", "registry-agent"],
                capture_output=True,
                text=True,
                env=env,
                cwd=tmp_path,
        )
        assert latest_install.returncode == 0
        assert "Resolved registry selector 'registry-agent'" in latest_install.stdout

        latest_run = subprocess.run(
                [sys.executable, str(cli_path), "run", str(tmp_path / "registry-agent"), "hello"],
                capture_output=True,
                text=True,
                env=env,
                cwd=tmp_path,
        )
        assert latest_run.returncode == 0
        assert "registry-2.0.0:hello" in f"{latest_run.stdout}\n{latest_run.stderr}"

        exact_install = subprocess.run(
                [sys.executable, str(cli_path), "install", "registry-agent==1.0.0"],
                capture_output=True,
                text=True,
                env=env,
                cwd=tmp_path,
        )
        assert exact_install.returncode == 0
        assert "Resolved registry selector 'registry-agent==1.0.0'" in exact_install.stdout

        exact_run = subprocess.run(
                [sys.executable, str(cli_path), "run", str(tmp_path / "registry-agent-1.0.0"), "hello"],
                capture_output=True,
                text=True,
                env=env,
                cwd=tmp_path,
        )
        assert exact_run.returncode == 0
        assert "registry-1.0.0:hello" in f"{exact_run.stdout}\n{exact_run.stderr}"


def test_list_shows_name_latest_version_and_description(tmp_path: Path) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        cli_path = repo_root / "src" / "kinnoo" / "cli.py"

        registry_root = tmp_path / "registry-sandbox"
        env = dict(**os.environ, KINNOO_REGISTRY_ROOT=str(registry_root))

        alpha_v1 = tmp_path / "alpha-v1.kno"
        with zipfile.ZipFile(alpha_v1, "w") as archive_zip:
                archive_zip.writestr(
                        "kinnoo.yaml",
                        """
name: alpha-agent
version: 1.0.0
description: Alpha stable description
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
""",
                )
                archive_zip.writestr("run.py", "print('alpha-v1')\n")
                archive_zip.writestr("requirements.txt", "")

        alpha_v2 = tmp_path / "alpha-v2.kno"
        with zipfile.ZipFile(alpha_v2, "w") as archive_zip:
                archive_zip.writestr(
                        "kinnoo.yaml",
                        """
name: alpha-agent
version: 2.0.0
description: Alpha latest description
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
""",
                )
                archive_zip.writestr("run.py", "print('alpha-v2')\n")
                archive_zip.writestr("requirements.txt", "")

        beta_v1 = tmp_path / "beta-v1.kno"
        with zipfile.ZipFile(beta_v1, "w") as archive_zip:
                archive_zip.writestr(
                        "kinnoo.yaml",
                        """
name: beta-agent
version: 0.5.0
description: Beta description
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
""",
                )
                archive_zip.writestr("run.py", "print('beta-v1')\n")
                archive_zip.writestr("requirements.txt", "")

        for archive in (alpha_v1, alpha_v2, beta_v1):
                publish_result = subprocess.run(
                        [sys.executable, str(cli_path), "publish", str(archive)],
                        capture_output=True,
                        text=True,
                        env=env,
                )
                assert publish_result.returncode == 0

        list_result = subprocess.run(
                [sys.executable, str(cli_path), "list"],
                capture_output=True,
                text=True,
                env=env,
        )

        output = f"{list_result.stdout}\n{list_result.stderr}"
        assert list_result.returncode == 0
        assert "Local registry agents:" in output
        assert "alpha-agent | latest: 2.0.0 | description: Alpha latest description" in output
        assert "beta-agent | latest: 0.5.0 | description: Beta description" in output


def test_search_filters_by_name_and_description_substring(tmp_path: Path) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        cli_path = repo_root / "src" / "kinnoo" / "cli.py"

        registry_root = tmp_path / "registry-sandbox"
        env = dict(**os.environ, KINNOO_REGISTRY_ROOT=str(registry_root))

        alpha_archive = tmp_path / "alpha-search.kno"
        with zipfile.ZipFile(alpha_archive, "w") as archive_zip:
            archive_zip.writestr(
                "kinnoo.yaml",
                """
    name: alpha-agent
    version: 1.0.0
    description: Handles finance forecasting workflows
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
    """,
            )
            archive_zip.writestr("run.py", "print('alpha')\n")
            archive_zip.writestr("requirements.txt", "")

        beta_archive = tmp_path / "beta-search.kno"
        with zipfile.ZipFile(beta_archive, "w") as archive_zip:
            archive_zip.writestr(
                "kinnoo.yaml",
                """
    name: data-helper
    version: 1.2.0
    description: General analytics assistant
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
    """,
            )
            archive_zip.writestr("run.py", "print('beta')\n")
            archive_zip.writestr("requirements.txt", "")

        for archive in (alpha_archive, beta_archive):
            publish_result = subprocess.run(
                [sys.executable, str(cli_path), "publish", str(archive)],
                capture_output=True,
                text=True,
                env=env,
            )
            assert publish_result.returncode == 0

        name_search = subprocess.run(
            [sys.executable, str(cli_path), "search", "alpha"],
            capture_output=True,
            text=True,
            env=env,
        )
        name_output = f"{name_search.stdout}\n{name_search.stderr}"
        assert name_search.returncode == 0
        assert "alpha-agent | latest: 1.0.0" in name_output
        assert "data-helper" not in name_output

        description_search = subprocess.run(
            [sys.executable, str(cli_path), "search", "analytics"],
            capture_output=True,
            text=True,
            env=env,
        )
        description_output = f"{description_search.stdout}\n{description_search.stderr}"
        assert description_search.returncode == 0
        assert "data-helper | latest: 1.2.0" in description_output
        assert "alpha-agent | latest: 1.0.0" not in description_output

        no_match_search = subprocess.run(
            [sys.executable, str(cli_path), "search", "no-such-registry-agent"],
            capture_output=True,
            text=True,
            env=env,
        )
        no_match_output = f"{no_match_search.stdout}\n{no_match_search.stderr}"
        assert no_match_search.returncode == 0
        assert "No local registry matches found for query: no-such-registry-agent" in no_match_output
