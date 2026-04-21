"""Database engine and session helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from server.database.exceptions import DatabaseUnavailableError


def _normalize_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


@dataclass(frozen=True)
class DatabaseRuntime:
    sync_engine: Engine
    sync_session_factory: sessionmaker[Session]
    async_engine: AsyncEngine
    async_session_factory: async_sessionmaker[AsyncSession]


def create_database_runtime(
    *,
    database_url: str,
    pool_size: int,
    max_overflow: int,
    pool_recycle_seconds: int,
) -> DatabaseRuntime:
    sync_engine = create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle_seconds,
    )
    sync_session_factory = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False, future=True)

    async_database_url = _normalize_async_database_url(database_url)
    async_engine = create_async_engine(
        async_database_url,
        future=True,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle_seconds,
    )
    async_session_factory = async_sessionmaker(bind=async_engine, autoflush=False, autocommit=False, future=True)
    return DatabaseRuntime(
        sync_engine=sync_engine,
        sync_session_factory=sync_session_factory,
        async_engine=async_engine,
        async_session_factory=async_session_factory,
    )


def ping_database(engine: Engine) -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise DatabaseUnavailableError("Database connectivity check failed.") from error


def close_database_runtime(runtime: DatabaseRuntime) -> None:
    runtime.sync_engine.dispose()


def sqlalchemy_error_message(error: SQLAlchemyError) -> str:
    return str(getattr(error, "orig", error))


def to_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, list):
        return list(value)
    return value
