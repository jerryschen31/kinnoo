"""task525 / test748: REGISTRY_DATABASE_URL stub-secret bootstrap idempotence.

Uses a fake `aws` shim on PATH to simulate Secrets Manager state so the test
exercises the script's create / no-op / refuse-to-overwrite branches without
touching real AWS.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ops" / "create_registry_database_url_stub_secret.sh"


def _make_fake_aws(bin_dir: Path, state_file: Path) -> None:
    """Install a Python-based aws shim that simulates a tiny subset of
    secretsmanager (describe-secret, get-secret-value, create-secret,
    put-secret-value). State is persisted as JSON on disk so we can inspect it.
    """
    aws_path = bin_dir / "aws"
    state_path_str = str(state_file)
    aws_path.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            import json, sys, os
            STATE = {state_path_str!r}

            def load():
                if os.path.exists(STATE):
                    with open(STATE) as fh:
                        return json.load(fh)
                return {{}}

            def save(s):
                with open(STATE, 'w') as fh:
                    json.dump(s, fh)

            args = sys.argv[1:]
            if not args or args[0] != 'secretsmanager':
                sys.exit(0)
            sub = args[1]
            kv = {{}}
            i = 2
            while i < len(args):
                a = args[i]
                if a.startswith('--') and i + 1 < len(args) and not args[i+1].startswith('--'):
                    kv[a[2:]] = args[i+1]
                    i += 2
                else:
                    i += 1
            secret_id = kv.get('secret-id') or kv.get('name')
            state = load()
            if sub == 'describe-secret':
                if secret_id in state:
                    print(f"arn:aws:secretsmanager:us-west-2:000000000000:secret:{{secret_id}}")
                    sys.exit(0)
                print("None")
                sys.exit(255)
            if sub == 'get-secret-value':
                if secret_id in state:
                    print(state[secret_id])
                    sys.exit(0)
                sys.exit(255)
            if sub == 'create-secret':
                state[secret_id] = kv.get('secret-string', '')
                save(state)
                sys.exit(0)
            if sub == 'put-secret-value':
                state[secret_id] = kv.get('secret-string', '')
                save(state)
                sys.exit(0)
            sys.exit(0)
            """
        )
    )
    aws_path.chmod(0o755)


@pytest.mark.regression_integration
@pytest.mark.ops
@pytest.mark.security_checks
def test_feature121_test748_stub_secret_idempotence(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    state_file = tmp_path / "secrets.json"
    _make_fake_aws(bin_dir, state_file)

    bash = shutil.which("bash")
    assert bash is not None
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    secret_name = "/kinnoo/prod/REGISTRY_DATABASE_URL"

    # 1) First run creates the stub.
    r1 = subprocess.run(
        [bash, str(SCRIPT), "--environment", "prod"],
        env=env, capture_output=True, text=True, timeout=20,
    )
    assert r1.returncode == 0, r1.stderr
    state = json.loads(state_file.read_text())
    assert secret_name in state
    payload = json.loads(state[secret_name])
    assert "REGISTRY_DATABASE_URL_STUB_PLACEHOLDER" in payload["REGISTRY_DATABASE_URL"]

    # 2) Second run is a no-op (placeholder still present).
    r2 = subprocess.run(
        [bash, str(SCRIPT), "--environment", "prod"],
        env=env, capture_output=True, text=True, timeout=20,
    )
    assert r2.returncode == 0, r2.stderr
    assert "no-op" in (r2.stdout + r2.stderr)
    # Value unchanged.
    state2 = json.loads(state_file.read_text())
    assert state2[secret_name] == state[secret_name]

    # 3) Pre-populate with a real value; script must NOT overwrite.
    real_payload = json.dumps({
        "REGISTRY_DATABASE_URL": "postgresql+psycopg://realuser:realpass@db.prod/kinnoo_registry"
    })
    state2[secret_name] = real_payload
    state_file.write_text(json.dumps(state2))

    r3 = subprocess.run(
        [bash, str(SCRIPT), "--environment", "prod"],
        env=env, capture_output=True, text=True, timeout=20,
    )
    assert r3.returncode == 0, r3.stderr
    state3 = json.loads(state_file.read_text())
    assert state3[secret_name] == real_payload, "real value must be preserved"
    combined = r3.stdout + r3.stderr
    assert "refusing to overwrite" in combined or "non-placeholder" in combined
