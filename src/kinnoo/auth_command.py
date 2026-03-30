"""Authentication command handlers for kinnoo login/logout."""

from __future__ import annotations

import getpass
import json
import sys
from urllib import error as urllib_error
from urllib import request as urllib_request

from .config import (
    clear_registry_auth_state,
    load_registry_config,
    save_registry_auth_state,
)


def login_command(
    *,
    email: str | None,
    password: str | None,
    registry: str | None,
    tenant_slug: str | None,
) -> int:
    config = load_registry_config()

    resolved_registry = (registry or config.registry_url or "").strip()
    if not resolved_registry:
        print(
            "Error: Registry URL is required. Use --registry or set KINNOO_REGISTRY_URL.",
        )
        return 1

    resolved_tenant = (tenant_slug or config.tenant_slug or "global").strip() or "global"

    resolved_email = (email or "").strip()
    if not resolved_email:
        resolved_email = input("Email: ").strip()

    resolved_password = password
    if resolved_password is None:
        # getpass can block on /dev/tty in subprocess-driven tests/CI; fall back to stdin when non-interactive.
        if sys.stdin.isatty():
            resolved_password = getpass.getpass("Password: ")
        else:
            resolved_password = input("Password: ")

    if not resolved_email:
        print("Error: Email is required.")
        return 1
    if not resolved_password:
        print("Error: Password is required.")
        return 1

    token, error_message = _issue_token(
        registry_url=resolved_registry,
        email=resolved_email,
        password=resolved_password,
        tenant_slug=resolved_tenant,
    )
    if error_message is not None:
        print(f"Error: {error_message}")
        return 1

    save_registry_auth_state(
        registry_url=resolved_registry,
        registry_token=token,
        tenant_slug=resolved_tenant,
    )

    print("Login successful.")
    print(f"Registry: {resolved_registry}")
    print(f"Tenant: {resolved_tenant}")
    return 0


def logout_command() -> int:
    removed = clear_registry_auth_state()
    if removed:
        print("Logout successful. Cleared stored registry auth state.")
    else:
        print("No stored registry auth state found.")
    return 0


def _issue_token(
    *,
    registry_url: str,
    email: str,
    password: str,
    tenant_slug: str,
) -> tuple[str, str | None]:
    payload = json.dumps(
        {
            "username": email,
            "password": password,
            "tenant_slug": tenant_slug,
        }
    ).encode("utf-8")

    token_url = f"{registry_url.rstrip('/')}/api/auth/token"
    request = urllib_request.Request(
        url=token_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=15.0) as response:
            body = response.read().decode("utf-8")
    except urllib_error.HTTPError as error:
        message = _extract_error_message(_read_http_error_payload(error))
        if not message:
            message = f"Token request failed with HTTP {error.code}."
        return "", message
    except urllib_error.URLError as error:
        reason = getattr(error, "reason", None)
        reason_text = str(reason) if reason is not None else "unknown network error"
        return "", f"Failed to reach registry auth endpoint. Reason: {reason_text}"

    try:
        decoded = json.loads(body)
    except json.JSONDecodeError:
        return "", "Registry auth endpoint returned invalid JSON."

    if not isinstance(decoded, dict):
        return "", "Registry auth endpoint returned invalid response payload."

    token = decoded.get("access_token")
    if not isinstance(token, str) or not token.strip():
        return "", "Registry auth response did not include access_token."

    return token.strip(), None


def _read_http_error_payload(error: urllib_error.HTTPError) -> dict[str, object] | None:
    try:
        body = error.read().decode("utf-8", errors="replace")
    except Exception:
        return None

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None

    if isinstance(payload, dict):
        return payload
    return None


def _extract_error_message(payload: dict[str, object] | None) -> str:
    if payload is None:
        return ""

    error_value = payload.get("error")
    if isinstance(error_value, str):
        return error_value
    if isinstance(error_value, dict):
        nested = error_value.get("message")
        if isinstance(nested, str):
            return nested

    message_value = payload.get("message")
    if isinstance(message_value, str):
        return message_value

    return ""
