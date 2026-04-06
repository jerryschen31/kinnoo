"""Authentication command handlers for kinnoo login/logout."""

from __future__ import annotations

import getpass
import base64
import json
import sys
from urllib import error as urllib_error
from urllib import request as urllib_request

from .config import (
    clear_registry_auth_state,
    load_registry_config,
    save_registry_auth_state,
)


DEFAULT_REGISTRY_URL = "https://registry.kinnoo.ai"


def login_command(
    *,
    email: str | None,
    password: str | None,
) -> int:
    config = load_registry_config()

    resolved_registry = (config.registry_url or DEFAULT_REGISTRY_URL).strip()

    resolved_email = (email or "").strip()
    if not resolved_email:
        resolved_email = input("Email/Username: ").strip()

    resolved_password = password
    if resolved_password is None:
        # getpass hides keyboard input (including pasted passwords) in interactive shells.
        resolved_password = _prompt_for_password()

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
        tenant_slug=None,
    )
    if error_message is not None:
        print(f"Error: {error_message}")
        return 1

    resolved_tenant = _tenant_slug_from_token(token)
    if not resolved_tenant:
        print(
            "Error: Registry auth response did not include tenant context. "
            "Contact the registry administrator.",
        )
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


def _prompt_for_password() -> str:
    # In non-interactive subprocess contexts (tests/CI), getpass may fail because no TTY exists.
    try:
        if sys.stdin.isatty():
            return getpass.getpass("Password: ")
    except Exception:
        pass
    return input("Password: ")


def _tenant_slug_from_token(token: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_segment = parts[1]
        padding = "=" * ((4 - len(payload_segment) % 4) % 4)
        decoded = base64.urlsafe_b64decode((payload_segment + padding).encode("utf-8"))
        payload = json.loads(decoded.decode("utf-8"))
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None
    tenant_slug = payload.get("tenant_slug")
    if isinstance(tenant_slug, str) and tenant_slug.strip():
        return tenant_slug.strip()
    return None


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
    tenant_slug: str | None,
) -> tuple[str, str | None]:
    payload_data: dict[str, str] = {
        "username": email,
        "password": password,
    }
    if isinstance(tenant_slug, str) and tenant_slug.strip():
        payload_data["tenant_slug"] = tenant_slug.strip()

    payload = json.dumps(payload_data).encode("utf-8")

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
