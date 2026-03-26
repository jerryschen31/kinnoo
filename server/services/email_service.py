"""Email service abstraction for auth-related notifications."""

from __future__ import annotations

from typing import Protocol


class EmailService(Protocol):
    """Contract for registration/reset email dispatch providers."""

    def send_registration_verification(self, *, email: str, verification_link: str) -> None:
        ...

    def send_password_reset(self, *, email: str, reset_link: str) -> None:
        ...
