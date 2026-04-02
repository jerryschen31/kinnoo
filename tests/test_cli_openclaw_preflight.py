from __future__ import annotations

import subprocess

from kinnoo.openclaw_preflight import ensure_openclaw_cli, parse_openclaw_version


def test_feature76_cli_detection_version_gate(monkeypatch):
    # Missing CLI path should fail deterministically.
    monkeypatch.setattr("kinnoo.openclaw_preflight.shutil.which", lambda _name: None)
    missing = ensure_openclaw_cli("2026.3.28")
    assert missing.ok is False
    assert missing.category == "openclaw_cli_missing"

    # Present CLI but old version should fail with upgrade guidance.
    monkeypatch.setattr("kinnoo.openclaw_preflight.shutil.which", lambda _name: "/usr/bin/openclaw")

    def fake_run_old(_args, capture_output, text, check):
        return subprocess.CompletedProcess(_args, 0, stdout="openclaw 2026.3.27\n", stderr="")

    monkeypatch.setattr("kinnoo.openclaw_preflight.subprocess.run", fake_run_old)
    old = ensure_openclaw_cli("2026.3.28")
    assert old.ok is False
    assert old.category == "openclaw_cli_version_unsupported"
    assert "Upgrade OpenClaw CLI" in old.message

    # Suffix versions must parse and pass when >= minimum.
    def fake_run_new(_args, capture_output, text, check):
        return subprocess.CompletedProcess(_args, 0, stdout="v2026.3.31-beta.1\n", stderr="")

    monkeypatch.setattr("kinnoo.openclaw_preflight.subprocess.run", fake_run_new)
    modern = ensure_openclaw_cli("2026.3.28")
    assert modern.ok is True
    assert modern.category == "openclaw_cli_precheck_ok"
    assert modern.version == "2026.3.31"

    assert parse_openclaw_version("openclaw 2026.4.1") == (2026, 4, 1)
    assert parse_openclaw_version("v2026.3.31-beta.1") == (2026, 3, 31)
    assert parse_openclaw_version("no-version") is None
