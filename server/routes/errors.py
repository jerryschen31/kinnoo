"""Shared API error envelope helpers for feature29 contracts."""

from __future__ import annotations

import uuid


def error_code_for_status(status_code: int) -> str:
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        413: "payload_too_large",
        409: "conflict",
        429: "too_many_requests",
    }
    return mapping.get(status_code, "internal_error")


def resolve_request_id(request) -> str:
    header_value = request.headers.get("x-request-id") if request is not None else None
    if isinstance(header_value, str) and header_value.strip():
        return header_value.strip()
    return uuid.uuid4().hex


def build_error_envelope(*, status_code: int, message: str, request_id: str) -> dict[str, object]:
    return {
        "error": {
            "code": error_code_for_status(status_code),
            "message": message,
            "request_id": request_id,
        }
    }
