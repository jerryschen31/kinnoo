"""Development email provider that logs messages to console and optional sink."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from server.services.email_service import EmailService


@dataclass
class ConsoleEmailService(EmailService):
    sink: list[dict[str, str]] = field(default_factory=list)
    logger: Callable[[str], None] = print

    def send_registration_verification(self, *, email: str, verification_link: str) -> None:
        self.sink.append(
            {
                "email": email,
                "verification_link": verification_link,
                "event_type": "registration_verification",
            }
        )
        self.logger(f"[email:registration] to={email} link={verification_link}")

    def send_password_reset(self, *, email: str, reset_link: str) -> None:
        self.sink.append(
            {
                "email": email,
                "reset_link": reset_link,
                "event_type": "password_reset",
            }
        )
        self.logger(f"[email:password-reset] to={email} link={reset_link}")
