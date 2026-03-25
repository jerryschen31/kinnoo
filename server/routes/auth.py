"""Auth API routes."""

from __future__ import annotations

import importlib
from typing import Any

from starlette.requests import Request

from server.api.endpoints import post_auth_token
from server.auth.middleware import authenticate_session_identity
from server.auth.session import SessionService
from server.auth.token import TokenService
from server.models.user import username_to_tenant_slug
from server.routes.errors import build_error_envelope, resolve_request_id
from server.storage.user_store import UserStore


def create_auth_router(
    *, token_service: TokenService, user_store: UserStore, session_service: SessionService
) -> Any:
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

    @router.get("/api/auth/me")
    async def auth_me(request: Request) -> dict[str, object]:
        request_id = resolve_request_id(request)
        cookie_value = request.cookies.get(session_service.cookie_name)

        try:
            user = authenticate_session_identity(
                cookie_value=cookie_value,
                session_service=session_service,
                user_store=user_store,
            )
        except PermissionError as error:
            return JSONResponse(
                status_code=401,
                content=build_error_envelope(
                    status_code=401,
                    message=str(error),
                    request_id=request_id,
                ),
            )

        return {
            "user_id": user.id,
            "tenant_slug": username_to_tenant_slug(user.username),
            "username": user.username,
        }

    return router
