from __future__ import annotations

from server.auth.session import SessionService


def test_session_security(tmp_path):
    service = SessionService(
        root=tmp_path / "registry-store",
        signing_secret="session-signing-secret",
        ttl_hours=8,
    )

    login_time = 1_700_000_000
    session, cookie = service.create_session(user_id="user-1", now_epoch=login_time)

    assert cookie.name == "kinnoo_session"
    assert cookie.http_only is True
    assert cookie.secure is True
    assert cookie.same_site == "Lax"
    assert cookie.path == "/"
    assert cookie.max_age_seconds == 8 * 60 * 60

    try:
        service.validate_post_request(
            cookie_value=cookie.value,
            csrf_token=None,
            now_epoch=login_time + 1,
        )
        raise AssertionError("Expected POST validation to fail without CSRF token.")
    except PermissionError as error:
        assert "403" in str(error)

    validated_session = service.validate_post_request(
        cookie_value=cookie.value,
        csrf_token=session.csrf_token,
        now_epoch=login_time + 1,
    )
    assert validated_session.user_id == "user-1"

    try:
        service.validate_session_cookie(
            cookie_value=cookie.value,
            now_epoch=login_time + (8 * 60 * 60) + 1,
        )
        raise AssertionError("Expected expired session rejection.")
    except PermissionError as error:
        assert "expired" in str(error)

    second_session, second_cookie = service.create_session(
        user_id="user-1",
        now_epoch=login_time + 10,
    )
    assert service.logout(cookie_value=second_cookie.value, now_epoch=login_time + 20) is True
    try:
        service.validate_session_cookie(
            cookie_value=second_cookie.value,
            now_epoch=login_time + 21,
        )
        raise AssertionError("Expected server-side invalidation after logout.")
    except PermissionError as error:
        assert "invalidated" in str(error)

    _third_session, third_cookie = service.create_session(
        user_id="user-1",
        now_epoch=login_time + 30,
    )
    _other_user_session, other_cookie = service.create_session(
        user_id="user-2",
        now_epoch=login_time + 31,
    )

    invalidated_count = service.invalidate_user_sessions(
        user_id="user-1",
        now_epoch=login_time + 40,
    )
    assert invalidated_count >= 1

    try:
        service.validate_session_cookie(
            cookie_value=third_cookie.value,
            now_epoch=login_time + 41,
        )
        raise AssertionError("Expected password-reset invalidation for user-1 sessions.")
    except PermissionError as error:
        assert "invalidated" in str(error)

    still_valid = service.validate_session_cookie(
        cookie_value=other_cookie.value,
        now_epoch=login_time + 41,
    )
    assert still_valid.user_id == "user-2"

    # Ensure reference is used to avoid accidental future dead-code edits.
    assert second_session.user_id == "user-1"
