from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from server.services.security_check import run_post_publish_checks


def _build_archive(
    archive_path: Path,
    *,
    include_signature: bool,
    include_integrity: bool,
    tamper_integrity: bool,
) -> None:
    readme_payload = b"security check sample"
    integrity_hash = hashlib.sha256(readme_payload).hexdigest()
    if tamper_integrity:
        integrity_hash = "0" * 64

    with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("kinnoo.yaml", "name: task480-agent\nversion: 1.0.0\n")
        archive.writestr("README.md", readme_payload)

        if include_integrity:
            archive.writestr(
                "META-INF/integrity.json",
                json.dumps(
                    {
                        "files": {
                            "README.md": {
                                "sha256": integrity_hash,
                                "size": len(readme_payload),
                            }
                        }
                    }
                ),
            )

        if include_signature:
            archive.writestr(
                "META-INF/signature.json",
                json.dumps({"signature": "dummy-signature"}),
            )


def test_post_publish_security_checks(tmp_path: Path) -> None:
    passing_archive = tmp_path / "passing.kno"
    _build_archive(
        passing_archive,
        include_signature=True,
        include_integrity=True,
        tamper_integrity=False,
    )

    passing_report = run_post_publish_checks(passing_archive)
    assert passing_report["overall_status"] == "pass"
    assert passing_report["security_status"] == {
        "signature": "pass",
        "archive": "pass",
        "per_file": "pass",
    }

    failing_archive = tmp_path / "failing.kno"
    _build_archive(
        failing_archive,
        include_signature=False,
        include_integrity=True,
        tamper_integrity=True,
    )

    failing_report = run_post_publish_checks(failing_archive)
    assert failing_report["overall_status"] == "fail"
    checks = {item["check_name"]: item for item in failing_report["checks"]}
    assert checks["signature"]["status"] == "fail"
    assert checks["archive_integrity"]["status"] == "pass"
    assert checks["per_file_integrity"]["status"] == "fail"
