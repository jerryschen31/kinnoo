"""Server-side post-publish archive security checks."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile


def _check_signature(archive_path: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            if "META-INF/signature.json" not in archive.namelist():
                return "fail", "META-INF/signature.json missing"
            payload = archive.read("META-INF/signature.json").decode("utf-8")
            doc = json.loads(payload)
    except zipfile.BadZipFile:
        return "fail", "archive is not a valid zip"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "fail", "signature metadata is unreadable"

    signature = doc.get("signature") if isinstance(doc, dict) else None
    if not isinstance(signature, str) or not signature.strip():
        return "fail", "signature field missing or empty"
    return "pass", "signature metadata present"


def _check_archive_integrity(archive_path: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            _ = archive.testzip()
            if "kinnoo.yaml" not in archive.namelist():
                return "fail", "kinnoo.yaml missing"
    except zipfile.BadZipFile:
        return "fail", "archive is not a valid zip"
    except OSError:
        return "fail", "archive cannot be read"
    return "pass", "archive structure is valid"


def _check_per_file_integrity(archive_path: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            if "META-INF/integrity.json" not in archive.namelist():
                return "fail", "META-INF/integrity.json missing"

            doc = json.loads(archive.read("META-INF/integrity.json").decode("utf-8"))
            files = doc.get("files") if isinstance(doc, dict) else None
            if not isinstance(files, dict):
                return "fail", "integrity manifest missing files mapping"

            for relpath, record in files.items():
                if not isinstance(record, dict):
                    return "fail", f"integrity record invalid for {relpath}"
                expected_hash = record.get("sha256")
                if not isinstance(expected_hash, str) or not expected_hash:
                    return "fail", f"sha256 missing for {relpath}"

                expected_size = record.get("size")
                if not isinstance(expected_size, int):
                    return "fail", f"size missing for {relpath}"

                try:
                    payload = archive.read(relpath)
                except KeyError:
                    return "fail", f"file missing from archive: {relpath}"

                if len(payload) != expected_size:
                    return "fail", f"size mismatch for {relpath}"
                actual_hash = hashlib.sha256(payload).hexdigest()
                if actual_hash != expected_hash:
                    return "fail", f"hash mismatch for {relpath}"
    except zipfile.BadZipFile:
        return "fail", "archive is not a valid zip"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "fail", "integrity metadata is unreadable"

    return "pass", "integrity manifest matches archive files"


def run_post_publish_checks(archive_path: str | Path) -> dict[str, object]:
    path = Path(archive_path)
    signature_status, signature_detail = _check_signature(path)
    archive_status, archive_detail = _check_archive_integrity(path)
    per_file_status, per_file_detail = _check_per_file_integrity(path)

    checks = [
        {"check_name": "signature", "status": signature_status, "detail": signature_detail},
        {"check_name": "archive_integrity", "status": archive_status, "detail": archive_detail},
        {"check_name": "per_file_integrity", "status": per_file_status, "detail": per_file_detail},
    ]

    overall_status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    return {
        "overall_status": overall_status,
        "checks": checks,
        "security_status": {
            "signature": signature_status,
            "archive": archive_status,
            "per_file": per_file_status,
        },
    }


def run_post_publish_checks_bytes(archive_bytes: bytes) -> dict[str, object]:
    with tempfile.NamedTemporaryFile(suffix=".kno", delete=False) as temp:
        temp.write(archive_bytes)
        temp_path = Path(temp.name)
    try:
        return run_post_publish_checks(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


def invoke_security_check_lambda_async(*, tenant_slug: str, agent_slug: str, version: str) -> dict[str, object]:
    execution_mode = (os.getenv("KINNOO_SECURITY_CHECK_EXECUTION_MODE") or "").strip().lower()
    if execution_mode != "lambda":
        return {"mode": "local", "invoked": False, "detail": "lambda mode disabled"}

    function_name = (os.getenv("KINNOO_SECURITY_CHECK_LAMBDA_NAME") or "").strip()
    if not function_name:
        return {"mode": "lambda", "invoked": False, "detail": "lambda name is not configured"}

    try:
        import boto3  # type: ignore
    except Exception:
        return {"mode": "lambda", "invoked": False, "detail": "boto3 is unavailable"}

    payload = {
        "tenant_slug": tenant_slug,
        "agent_slug": agent_slug,
        "version": version,
    }

    retries_raw = (os.getenv("KINNOO_SECURITY_CHECK_LAMBDA_RETRIES") or "2").strip()
    try:
        retry_count = max(0, int(retries_raw))
    except ValueError:
        retry_count = 2

    attempts_total = retry_count + 1
    last_error: str | None = None

    lambda_client = boto3.client("lambda")
    for _ in range(attempts_total):
        try:
            lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="Event",
                Payload=json.dumps(payload).encode("utf-8"),
            )
            return {
                "mode": "lambda",
                "invoked": True,
                "detail": function_name,
                "attempts": attempts_total,
            }
        except Exception as error:
            last_error = str(error)

    # Fallback behavior: inline checks already completed in publish flow before async dispatch.
    return {
        "mode": "lambda",
        "invoked": False,
        "attempts": attempts_total,
        "detail": f"lambda invoke failed after {attempts_total} attempts: {last_error or 'unknown error'}",
        "fallback": "inline_publish_checks_preserved",
    }
