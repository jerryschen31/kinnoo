from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

FREE_TIER_QUOTA_BYTES = 5 * 1024 * 1024 * 1024


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    used_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    quota_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=FREE_TIER_QUOTA_BYTES)

    members = relationship("TenantMember", back_populates="tenant", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="tenant", cascade="all, delete-orphan")
