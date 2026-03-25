# [agent] test deprecated: Feature12 CLI registry tests are superseded by feature13 tests.
# def test_publish_cli_usage_and_local_flag(...) -> None:
#     ...
#
# def test_install_remote_success_downloads_and_extracts(...) -> None:
#     ...
#
# def test_install_remote_missing_error_hints_sources(...) -> None:
#     ...
#
# def test_search_remote_lists_matches_with_source_label(...) -> None:
#     ...
#
# def test_search_default_prefers_local_then_falls_back_remote(...) -> None:
#     ...
#
# def test_list_remote_lists_latest_with_source_label(...) -> None:
#     ...
#
# def test_list_default_prefers_local_then_falls_back_remote(...) -> None:
#     ...
#
# def test_publish_requires_target_and_prints_default_target(...) -> None:
#     ...

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import zipfile


CLI_PATH = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"


def _write_archive(
	archive_root: Path,
	*,
	name: str,
	version: str,
) -> Path:
	archive_path = archive_root / name / version / f"{name}.kno"
	archive_path.parent.mkdir(parents=True, exist_ok=True)

	manifest_text = (
		"\n".join(
			[
				f"name: {name}",
				f"version: {version}",
				"entrypoint: run.py",
				"runtime:",
				"  language: python",
				"  version: \">=3.10\"",
				"  type: one-shot",
				"dependencies: []",
				"inputs:",
				"  type: text",
				"outputs:",
				"  type: text",
			]
		)
		+ "\n"
	)

	with zipfile.ZipFile(archive_path, "w") as archive_zip:
		archive_zip.writestr("kinnoo.yaml", manifest_text)
		archive_zip.writestr("run.py", "print('feature56')\n")
		archive_zip.writestr("requirements.txt", "")

	return archive_path


def test_feature56_local_publish_tenant_path(tmp_path: Path) -> None:
	archive_root = tmp_path / "archive"
	registry_root = tmp_path / "registry"
	_write_archive(archive_root, name="tenant-path-agent", version="1.0.0")

	env = {
		**os.environ,
		"KINNOO_ARCHIVE_ROOT": str(archive_root),
		"KINNOO_REGISTRY_ROOT": str(registry_root),
		"KINNOO_TENANT_SLUG": "tenant-alpha",
	}

	publish = subprocess.run(
		[sys.executable, str(CLI_PATH), "publish", "tenant-path-agent", "--local"],
		capture_output=True,
		text=True,
		env=env,
	)
	output = f"{publish.stdout}\n{publish.stderr}"
	assert publish.returncode == 0, output

	tenant_archive = (
		registry_root
		/ "tenants"
		/ "tenant-alpha"
		/ "tenant-path-agent"
		/ "1.0.0"
		/ "tenant-path-agent.kno"
	)
	tenant_metadata = tenant_archive.parent / "manifest-metadata.json"

	assert tenant_archive.exists()
	assert tenant_metadata.exists()
