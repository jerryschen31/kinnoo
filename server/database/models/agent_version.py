from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AgentVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_versions"
    __table_args__ = (
        UniqueConstraint("agent_id", "version", name="uq_agent_versions_agent_version"),
        Index("ix_agent_versions_agent_updated", "agent_id", "updated_at"),
    )

    agent_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    manifest: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    storage_keys: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    integrity: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    publisher: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    security_status: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    security_report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    agent = relationship("Agent", back_populates="versions")
