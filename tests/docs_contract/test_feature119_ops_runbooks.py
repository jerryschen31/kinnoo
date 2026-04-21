from __future__ import annotations

from pathlib import Path


def test_feature119_test731_alarm_and_runbook_contract() -> None:
    doc = Path("docs/postgres-operations.md").read_text(encoding="utf-8")
    assert "CPUUtilization" in doc
    assert "FreeStorageSpace" in doc
    assert "DatabaseConnections" in doc
    assert "ReadLatency" in doc
    assert "Cutover Runbook" in doc
    assert "Rollback Runbook" in doc
    assert "Restore / PITR Runbook" in doc
    assert "Connection Saturation Response" in doc
    assert "owned by the registry on-call operator" in doc
