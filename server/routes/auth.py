"""Auth API routes."""

from __future__ import annotations

import importlib
from typing import Any

from starlette.requests import Request

from server.api.endpoints import post_auth_token
from server.auth.token import TokenService
from server.routes.errors import build_error_envelope, resolve_request_id
from server.storage.user_store import UserStore


def create_auth_router(*, token_service: TokenService, user_store: UserStore) -> Any:
    fastapi_module = importlib.import_module("fastapi")
    APIRouter = getattr(fastapi_module, "APIRouter")

    responses_module = importlib.import_module("fastapi.responses")
    JSONResponse = getattr(responses_module, "JSONResponse")

    router = APIRouter()

    @router.post("/api/auth/token")
    async def issue_token(request: Request) -> dict[str, object]:
        request_id = resolve_request_id(request)

        try:
            payload = await request.json()
        except Exception:
            payload = {}

        if not isinstance(payload, dict):
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="request body must be a JSON object",
                    request_id=request_id,
                ),
            )

        status, response_payload = post_auth_token(
            payload=payload,
            token_service=token_service,
            user_store=user_store,
        )
        if status >= 400:
            return JSONResponse(
                status_code=status,
                content=build_error_envelope(
                    status_code=status,
                    message=str(response_payload.get("error", "request failed")),
                    request_id=request_id,
                ),
            )

        return response_payload

    return router
