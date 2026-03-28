"""Password and registration validation helpers for auth flows."""

from __future__ import annotations

import re


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 128
COMMON_PASSWORDS = {
    "password",
    "password123",
    "1234567890",
    "qwerty12345",
    "letmein123",
}


def validate_registration_email(email: str) -> str | None:
    """Return a user-safe error message when the email is invalid."""
    normalized = email.strip()
    if not normalized:
        return "email is required"
    if not EMAIL_PATTERN.match(normalized):
        return "email must be a valid address"
    if len(normalized) > 254:
        return "email must be at most 254 characters"
    return None


def validate_registration_password(password: str) -> str | None:
    """Return a user-safe error message when password fails baseline requirements."""
    normalized = password.strip()
    if not normalized:
        return "password is required"
    if len(normalized) < PASSWORD_MIN_LENGTH:
        return f"password must be at least {PASSWORD_MIN_LENGTH} characters"
    if len(normalized) > PASSWORD_MAX_LENGTH:
        return f"password must be at most {PASSWORD_MAX_LENGTH} characters"
    return None


def validate_account_password_policy(password: str, *, account_identifier: str) -> str | None:
    """Return a user-safe error for compromised/common or account-similar passwords."""
    normalized_password = password.strip()
    lowered_password = normalized_password.lower()
    if lowered_password in COMMON_PASSWORDS:
        return "password is too common"

    identifier = account_identifier.strip().lower()
    local_part = identifier.split("@", 1)[0]
    if len(local_part) >= 3 and local_part in lowered_password:
        return "password is too similar to account identifier"

    return None