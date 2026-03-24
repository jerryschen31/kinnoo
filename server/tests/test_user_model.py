from __future__ import annotations

import json

from server.models.user import User
from server.storage.user_store import UserStore


def test_password_hashing(tmp_path):
    store = UserStore(tmp_path)

    created = store.create_user(
        username="registry-admin",
        plaintext_password="CorrectHorseBatteryStaple",
        role="admin",
    )

    assert created.password_hash != "CorrectHorseBatteryStaple"
    assert created.verify_password("CorrectHorseBatteryStaple") is True
    assert created.verify_password("definitely-wrong") is False

    loaded = store.get_by_id(created.id)
    assert loaded is not None
    assert loaded.verify_password("CorrectHorseBatteryStaple") is True

    serialized = json.dumps(created.to_document(), sort_keys=True)
    assert "CorrectHorseBatteryStaple" not in serialized
    assert "password_hash" in serialized
