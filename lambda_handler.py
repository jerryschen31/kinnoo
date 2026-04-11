"""Lambda entrypoint for post-publish security checks on uploaded .kno archives."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from typing import Any
from urllib.parse import unquote_plus
import zipfile


def _utc_now_iso() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_registry_archive_key(key: str) -> tuple[str, str, str, str]:
  parts = key.split("/")
  # Expected: archives/tenants/{tenant}/agents/{agent}/versions/{version}/{archive}.kno
  if len(parts) < 8:
    raise ValueError("archive key is too short to infer tenant/agent/version")
  if parts[0] != "archives" or parts[1] != "tenants" or parts[3] != "agents" or parts[5] != "versions":
    raise ValueError("archive key does not match expected tenant/agent/version layout")

  tenant_slug = parts[2].strip()
  agent_slug = parts[4].strip()
  version = parts[6].strip()
  archive_name = parts[-1].strip()
  if not tenant_slug or not agent_slug or not version or not archive_name.endswith(".kno"):
    raise ValueError("archive key is missing inferred metadata")
  return tenant_slug, agent_slug, version, archive_name


def _check_signature(archive: zipfile.ZipFile) -> tuple[str, str]:
  if "META-INF/signature.json" not in archive.namelist():
    return "unsigned", "META-INF/signature.json missing"
  try:
    payload = archive.read("META-INF/signature.json").decode("utf-8")
    doc = json.loads(payload)
  except (KeyError, UnicodeDecodeError, json.JSONDecodeError):
    return "fail", "signature metadata is unreadable"

  signature = doc.get("signature") if isinstance(doc, dict) else None
  if not isinstance(signature, str) or not signature.strip():
    return "unsigned", "signature field missing or empty"
  return "pass", "signature metadata present"


def _check_archive_integrity(archive: zipfile.ZipFile) -> tuple[str, str]:
  if archive.testzip() is not None:
    return "fail", "archive contains corrupt zip entries"
  if "kinnoo.yaml" not in archive.namelist():
    return "fail", "kinnoo.yaml missing"
  return "pass", "archive structure is valid"


def _check_per_file_integrity(archive: zipfile.ZipFile) -> tuple[str, str]:
  if "META-INF/integrity.json" not in archive.namelist():
    return "fail", "META-INF/integrity.json missing"
  try:
    doc = json.loads(archive.read("META-INF/integrity.json").decode("utf-8"))
  except (KeyError, UnicodeDecodeError, json.JSONDecodeError):
    return "fail", "integrity metadata is unreadable"

  files = doc.get("files") if isinstance(doc, dict) else None
  if not isinstance(files, dict):
    return "fail", "integrity manifest missing files mapping"

  for relpath, record in files.items():
    if not isinstance(record, dict):
      return "fail", f"integrity record invalid for {relpath}"
    expected_hash = record.get("sha256")
    expected_size = record.get("size")
    if not isinstance(expected_hash, str) or not expected_hash:
      return "fail", f"sha256 missing for {relpath}"
    if not isinstance(expected_size, int):
      return "fail", f"size missing for {relpath}"
    try:
      payload = archive.read(relpath)
    except KeyError:
      return "fail", f"file missing from archive: {relpath}"

    if len(payload) != expected_size:
      return "fail", f"size mismatch for {relpath}"
    if hashlib.sha256(payload).hexdigest() != expected_hash:
      return "fail", f"hash mismatch for {relpath}"

  return "pass", "integrity manifest matches archive files"


def _check_sha256_sidecar(archive_bytes: bytes, checksum_sidecar_bytes: bytes | None) -> tuple[str, str]:
  if checksum_sidecar_bytes is None:
    return "fail", "checksum sidecar (.sha256) missing"

  expected_hash = checksum_sidecar_bytes.decode("utf-8", errors="ignore").strip()
  actual_hash = hashlib.sha256(archive_bytes).hexdigest()
  if expected_hash != actual_hash:
    return "fail", "checksum sidecar mismatch"
  return "pass", "checksum sidecar matches archive payload"


def _run_checks(archive_bytes: bytes, checksum_sidecar_bytes: bytes | None) -> dict[str, Any]:
  try:
    archive = zipfile.ZipFile(BytesIO(archive_bytes), "r")
  except zipfile.BadZipFile:
    checks = [
      {"check_name": "archive_integrity", "status": "fail", "detail": "archive is not a valid zip"},
      {"check_name": "signature", "status": "fail", "detail": "signature metadata unavailable"},
      {"check_name": "per_file_integrity", "status": "fail", "detail": "integrity metadata unavailable"},
      {"check_name": "checksum_sidecar", "status": "fail", "detail": "archive unreadable"},
    ]
    return {
      "overall_status": "fail",
      "checks": checks,
      "security_status": {"signature": "fail", "archive": "fail", "per_file": "fail"},
    }

  with archive:
    signature_status, signature_detail = _check_signature(archive)
    archive_status, archive_detail = _check_archive_integrity(archive)
    per_file_status, per_file_detail = _check_per_file_integrity(archive)

  checksum_status, checksum_detail = _check_sha256_sidecar(archive_bytes, checksum_sidecar_bytes)
  checks = [
    {"check_name": "signature", "status": signature_status, "detail": signature_detail},
    {"check_name": "archive_integrity", "status": archive_status, "detail": archive_detail},
    {"check_name": "per_file_integrity", "status": per_file_status, "detail": per_file_detail},
    {"check_name": "checksum_sidecar", "status": checksum_status, "detail": checksum_detail},
  ]
  overall_status = (
    "pass"
    if all(item["status"] in {"pass", "unsigned"} for item in checks)
    else "fail"
  )
  return {
    "overall_status": overall_status,
    "checks": checks,
    "security_status": {
      "signature": signature_status,
      "archive": archive_status,
      "per_file": per_file_status,
    },
  }


def _write_results_object(
  *,
  s3_client: Any,
  bucket: str,
  tenant_slug: str,
  agent_slug: str,
  version: str,
  payload: dict[str, Any],
) -> str:
  prefix = (os.getenv("KINNOO_SECURITY_RESULTS_PREFIX") or "security-check/tenants").strip("/")
  key = f"{prefix}/{tenant_slug}/agents/{agent_slug}/versions/{version}/report.json"
  s3_client.put_object(
    Bucket=bucket,
    Key=key,
    Body=(json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    ContentType="application/json",
  )
  return key


def _update_version_metadata(
  *,
  s3_client: Any,
  bucket: str,
  tenant_slug: str,
  agent_slug: str,
  version: str,
  check_report: dict[str, Any],
  timestamp: str,
  result_key: str,
) -> str:
  metadata_key = f"metadata/tenants/{tenant_slug}/agents/{agent_slug}/versions/{version}.v1.json"
  metadata_obj = s3_client.get_object(Bucket=bucket, Key=metadata_key)
  metadata = json.loads(metadata_obj["Body"].read().decode("utf-8"))

  report_rows = []
  for item in check_report.get("checks", []):
    if not isinstance(item, dict):
      continue
    report_rows.append(
      {
        "check_name": str(item.get("check_name", "")),
        "status": str(item.get("status", "")),
        "detail": str(item.get("detail", "")),
        "timestamp": timestamp,
      }
    )

  metadata["security_status"] = check_report.get("security_status", "")
  metadata["security_report"] = report_rows
  metadata["updated_at"] = timestamp
  metadata["security_result_key"] = result_key

  s3_client.put_object(
    Bucket=bucket,
    Key=metadata_key,
    Body=(json.dumps(metadata, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    ContentType="application/json",
  )
  return metadata_key


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
  del context
  import boto3  # type: ignore

  s3_client = boto3.client("s3")
  processed: list[dict[str, Any]] = []
  skipped: list[dict[str, str]] = []

  for record in event.get("Records", []):
    bucket = str(record.get("s3", {}).get("bucket", {}).get("name", "")).strip()
    encoded_key = str(record.get("s3", {}).get("object", {}).get("key", "")).strip()
    key = unquote_plus(encoded_key)
    if not bucket or not key:
      skipped.append({"reason": "missing_bucket_or_key"})
      continue
    if not key.endswith(".kno"):
      skipped.append({"bucket": bucket, "key": key, "reason": "not_archive"})
      continue

    try:
      tenant_slug, agent_slug, version, archive_name = _parse_registry_archive_key(key)
    except ValueError as error:
      skipped.append({"bucket": bucket, "key": key, "reason": str(error)})
      continue

    archive_obj = s3_client.get_object(Bucket=bucket, Key=key)
    archive_bytes = archive_obj["Body"].read()

    version_prefix = key.rsplit("/", 1)[0] + "/"
    listing = s3_client.list_objects_v2(Bucket=bucket, Prefix=version_prefix)
    sidecars = [obj.get("Key", "") for obj in listing.get("Contents", []) if obj.get("Key", "") != key]

    checksum_sidecar_key = f"{key}.sha256"
    checksum_sidecar_bytes = None
    try:
      checksum_obj = s3_client.get_object(Bucket=bucket, Key=checksum_sidecar_key)
      checksum_sidecar_bytes = checksum_obj["Body"].read()
    except Exception:
      checksum_sidecar_bytes = None

    check_report = _run_checks(archive_bytes, checksum_sidecar_bytes)
    timestamp = _utc_now_iso()
    result_payload = {
      "mode": "lambda",
      "trigger": {"bucket": bucket, "archive_key": key},
      "tenant_slug": tenant_slug,
      "agent_slug": agent_slug,
      "version": version,
      "archive_name": archive_name,
      "sidecar_keys": sidecars,
      "checked_at": timestamp,
      "report": check_report,
    }
    result_key = _write_results_object(
      s3_client=s3_client,
      bucket=bucket,
      tenant_slug=tenant_slug,
      agent_slug=agent_slug,
      version=version,
      payload=result_payload,
    )
    metadata_key = _update_version_metadata(
      s3_client=s3_client,
      bucket=bucket,
      tenant_slug=tenant_slug,
      agent_slug=agent_slug,
      version=version,
      check_report=check_report,
      timestamp=timestamp,
      result_key=result_key,
    )

    processed.append(
      {
        "bucket": bucket,
        "archive_key": key,
        "metadata_key": metadata_key,
        "result_key": result_key,
        "overall_status": check_report.get("overall_status", "fail"),
      }
    )

  return {"processed": processed, "skipped": skipped, "processed_count": len(processed)}
