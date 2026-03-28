from __future__ import annotations

from pathlib import Path

from server.cli import main as server_cli_main
from server.storage.user_store import UserStore


def test_bootstrap_lifecycle(tmp_path, capsys):
    store_root = tmp_path / "registry-store"

    first_exit_code = server_cli_main(["bootstrap", "--store-root", str(store_root)])
    first_output = capsys.readouterr()
    first_combined = f"{first_output.out}\n{first_output.err}"

    assert first_exit_code == 0, first_combined
    assert "temporary password:" in first_output.out

    store = UserStore(Path(store_root))
    users = store.list_users()
    assert len(users) == 1

    admin_user = users[0]
    assert admin_user.role == "admin"
    assert admin_user.force_password_change is True

    temp_password_line = next(
        line for line in first_output.out.splitlines() if line.startswith("temporary password:")
    )
    temp_password = temp_password_line.split(":", 1)[1].strip()
    assert temp_password
    assert admin_user.verify_password(temp_password) is True

    second_exit_code = server_cli_main(["bootstrap", "--store-root", str(store_root)])
    second_output = capsys.readouterr()
    second_combined = f"{second_output.out}\n{second_output.err}"

    assert second_exit_code != 0, second_combined
    assert "admin already exists" in second_combined
