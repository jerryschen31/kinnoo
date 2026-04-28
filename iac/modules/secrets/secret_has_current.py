#!/usr/bin/env python3
import json
import subprocess
import sys


def _out(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload))


def main() -> int:
    query = json.load(sys.stdin)
    secret_id = query.get("secret_id", "")
    aws_region = query.get("aws_region", "us-west-2")

    if not secret_id:
        _out({"has_current": "false"})
        return 0

    cmd = [
        "aws",
        "secretsmanager",
        "describe-secret",
        "--region",
        aws_region,
        "--secret-id",
        secret_id,
        "--query",
        "VersionIdsToStages",
        "--output",
        "json",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        # During first apply the secret container may not exist yet.
        if "ResourceNotFoundException" in proc.stderr:
            _out({"has_current": "false"})
            return 0
        raise RuntimeError(proc.stderr.strip() or "aws describe-secret failed")

    raw = proc.stdout.strip()
    if not raw or raw == "null":
        _out({"has_current": "false"})
        return 0

    versions = json.loads(raw)
    has_current = any(
        "AWSCURRENT" in stages for stages in versions.values() if isinstance(stages, list)
    )
    _out({"has_current": "true" if has_current else "false"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
