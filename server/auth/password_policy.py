"""Password and registration validation helpers for auth flows."""

from __future__ import annotations

import re


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


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