from __future__ import annotations

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from server.database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DownloadEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "download_events"
    __table_args__ = (Index("ix_download_events_tenant_agent_created", "tenant_slug", "agent_slug", "created_at"),)

    tenant_slug: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    agent_slug: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    downloader: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
