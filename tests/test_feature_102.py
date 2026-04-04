from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from server.cli import main
from server.models.user import PasswordManager
from server.storage.user_store import UserStore


def _extract_value(lines: list[str], prefix: str) -> str:
    for line in lines:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def _is_locked(locked_until: str | None) -> bool:
    if not locked_until:
        return False
    return datetime.fromisoformat(locked_until.replace("Z", "+00:00")) > datetime.now(timezone.utc)


def test_feature102_group1(tmp_path: Path, capsys) -> None:
    store_root = tmp_path / "store"

    create_rc = main(
        [
            "user",
            "create",
            "--store-root",
            str(store_root),
            "--email",
            "alice@example.com",
            "--role",
            "admin",
        ]
    )
    assert create_rc == 0
    create_out = capsys.readouterr().out.splitlines()
    assert any("created user: alice@example.com" in line for line in create_out)
    temp_password = _extract_value(create_out, "temporary password:")
    assert temp_password

    list_rc = main(["user", "list", "--store-root", str(store_root)])
    assert list_rc == 0
    list_out = capsys.readouterr().out
    assert "alice@example.com" in list_out
    assert "active" in list_out

    reset_rc = main(
        [
            "user",
            "reset-password",
            "--store-root",
            str(store_root),
            "--email",
            "alice@example.com",
        ]
    )
    assert reset_rc == 0
    reset_lines = capsys.readouterr().out.splitlines()
    new_temp_password = _extract_value(reset_lines, "temporary password:")
    assert new_temp_password
    assert new_temp_password != temp_password

    store = UserStore(store_root)
    user = store.get_by_username("alice@example.com")
    assert user is not None
    manager = PasswordManager()
    assert manager.verify_password(new_temp_password, user.password_hash)

    # Force a lock state and verify unlock clears it.
    for _ in range(5):
        user = store.increment_failed_login(user=user)
    assert _is_locked(user.locked_until)

    unlock_rc = main(
        [
            "user",
            "unlock",
            "--store-root",
            str(store_root),
            "--email",
            "alice@example.com",
        ]
    )
    assert unlock_rc == 0
    capsys.readouterr()
    unlocked_user = store.get_by_username("alice@example.com")
    assert unlocked_user is not None
    assert unlocked_user.failed_login_attempts == 0
    assert not _is_locked(unlocked_user.locked_until)

    delete_rc = main(
        [
            "user",
            "delete",
            "--store-root",
            str(store_root),
            "--email",
            "alice@example.com",
            "--force",
        ]
    )
    assert delete_rc == 0
    capsys.readouterr()
    assert store.get_by_username("alice@example.com") is None


def test_feature102_group2(tmp_path: Path, capsys) -> None:
    store_root = tmp_path / "store"

    create_rc = main(
        [
            "invite",
            "create",
            "--store-root",
            str(store_root),
            "--email",
            "bob@example.com",
            "--days-valid",
            "14",
        ]
    )
    assert create_rc == 0
    create_lines = capsys.readouterr().out.splitlines()
    token = _extract_value(create_lines, "invite token:")
    assert token
    assert any("url:" in line for line in create_lines)

    list_rc = main(["invite", "list", "--store-root", str(store_root)])
    assert list_rc == 0
    list_out = capsys.readouterr().out
    assert "bob@example.com" in list_out
    assert "pending" in list_out

    store = UserStore(store_root)
    assert store.validate_invite(token=token) is not None
    assert store.consume_invite(token=token)
    assert store.validate_invite(token=token) is None

    invalid_days_rc = main(
        [
            "invite",
            "create",
            "--store-root",
            str(store_root),
            "--email",
            "carol@example.com",
            "--days-valid",
            "0",
        ]
    )
    assert invalid_days_rc == 1
    assert "days_valid must be positive" in capsys.readouterr().err
