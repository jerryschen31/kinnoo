"""Repository boundary for registry database access."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, desc, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from server.database.exceptions import DatabaseConflictError, DatabaseError
from server.database.models import Agent, AgentVersion, AuditLog, Tenant, TenantMember, User
from server.database.models.tenant_member import FREE_TIER_QUOTA_BYTES
from server.metadata.models import AgentIndex, AgentVersionSummary, GlobalAgentSummary, GlobalIndex, VersionMetadata, utc_now_iso


def _to_iso(value: datetime | None) -> str:
    if value is None:
        return utc_now_iso()
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class RegistryRepository:
    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert_version_metadata(self, metadata: VersionMetadata) -> None:
        try:
            with self._session_factory() as session:
                tenant = self._get_or_create_tenant(session=session, tenant_slug=metadata.tenant_slug)
                agent = self._get_or_create_agent(
                    session=session,
                    tenant=tenant,
                    agent_slug=metadata.agent_slug,
                    visibility=metadata.visibility,
                )
                existing = session.execute(
                    select(AgentVersion).where(
                        AgentVersion.agent_id == agent.id,
                        AgentVersion.version == metadata.version,
                    )
                ).scalar_one_or_none()
                if existing is None:
                    existing = AgentVersion(
                        agent_id=agent.id,
                        version=metadata.version,
                    )
                    session.add(existing)

                existing.manifest = dict(metadata.manifest)
                existing.storage_keys = dict(metadata.storage_keys)
                existing.integrity = dict(metadata.integrity)
                existing.publisher = dict(metadata.publisher)
                existing.security_status = str(metadata.security_status or "")
                existing.security_report = metadata.security_report
                existing.archive_size_bytes = int(metadata.archive_size_bytes or 0)
                session.commit()
        except IntegrityError as error:
            raise DatabaseConflictError("Unable to upsert metadata due to uniqueness conflict.") from error
        except SQLAlchemyError as error:
            raise DatabaseError("Unable to upsert metadata in registry database.") from error

    def get_version_metadata(self, *, tenant_slug: str, agent_slug: str, version: str) -> VersionMetadata | None:
        try:
            with self._session_factory() as session:
                row = session.execute(
                    select(AgentVersion, Agent, Tenant)
                    .join(Agent, AgentVersion.agent_id == Agent.id)
                    .join(Tenant, Agent.tenant_id == Tenant.id)
                    .where(
                        Tenant.slug == tenant_slug,
                        Agent.slug == agent_slug,
                        AgentVersion.version == version,
                    )
                ).first()
                if row is None:
                    return None
                version_row, agent_row, tenant_row = row
                return VersionMetadata(
                    tenant_slug=tenant_row.slug,
                    agent_slug=agent_row.slug,
                    version=version_row.version,
                    visibility=agent_row.visibility,
                    manifest=dict(version_row.manifest or {}),
                    storage_keys=dict(version_row.storage_keys or {}),
                    integrity=dict(version_row.integrity or {}),
                    publisher=dict(version_row.publisher or {}),
                    created_at=_to_iso(version_row.created_at),
                    updated_at=_to_iso(version_row.updated_at),
                    security_status=version_row.security_status,
                    security_report=version_row.security_report,
                    archive_size_bytes=int(version_row.archive_size_bytes or 0),
                )
        except SQLAlchemyError as error:
            raise DatabaseError("Unable to fetch version metadata from registry database.") from error

    def get_tenant_storage_usage(self, *, tenant_slug: str) -> tuple[int, int]:
        try:
            with self._session_factory() as session:
                tenant_id = session.execute(select(Tenant.id).where(Tenant.slug == tenant_slug)).scalar_one_or_none()
                if tenant_id is None:
                    return 0, FREE_TIER_QUOTA_BYTES

                used_bytes = session.execute(
                    select(func.coalesce(func.sum(AgentVersion.archive_size_bytes), 0))
                    .join(Agent, AgentVersion.agent_id == Agent.id)
                    .where(Agent.tenant_id == tenant_id)
                ).scalar_one()

                quota_bytes = session.execute(
                    select(func.max(TenantMember.quota_bytes)).where(TenantMember.tenant_id == tenant_id)
                ).scalar_one_or_none()

                effective_quota = int(quota_bytes or FREE_TIER_QUOTA_BYTES)
                return int(used_bytes or 0), effective_quota
        except SQLAlchemyError as error:
            raise DatabaseError("Unable to fetch tenant storage usage from registry database.") from error

    def get_agent_index(self, *, tenant_slug: str, agent_slug: str) -> AgentIndex | None:
        try:
            with self._session_factory() as session:
                agent_row = session.execute(
                    select(Agent, Tenant)
                    .join(Tenant, Agent.tenant_id == Tenant.id)
                    .where(Tenant.slug == tenant_slug, Agent.slug == agent_slug)
                ).first()
                if agent_row is None:
                    return None
                agent, tenant = agent_row
                versions = session.execute(
                    select(AgentVersion).where(AgentVersion.agent_id == agent.id).order_by(AgentVersion.version)
                ).scalars()
                version_summaries = tuple(
                    AgentVersionSummary(
                        version=row.version,
                        created_at=_to_iso(row.created_at),
                        updated_at=_to_iso(row.updated_at),
                        integrity=dict(row.integrity or {}),
                    )
                    for row in versions
                )
                return AgentIndex(
                    tenant_slug=tenant.slug,
                    agent_slug=agent.slug,
                    visibility=agent.visibility,
                    versions=version_summaries,
                )
        except SQLAlchemyError as error:
            raise DatabaseError("Unable to build agent index from registry database.") from error

    def get_global_index(self) -> GlobalIndex:
        try:
            with self._session_factory() as session:
                rows = session.execute(
                    select(Tenant.slug, Agent.slug, Agent.visibility, AgentVersion.version, AgentVersion.updated_at)
                    .join(Agent, Agent.tenant_id == Tenant.id)
                    .join(AgentVersion, AgentVersion.agent_id == Agent.id)
                    .order_by(Tenant.slug, Agent.slug, desc(AgentVersion.updated_at))
                ).all()

                latest_by_agent: dict[tuple[str, str], GlobalAgentSummary] = {}
                for tenant_slug, agent_slug, visibility, version, updated_at in rows:
                    key = (tenant_slug, agent_slug)
                    if key in latest_by_agent:
                        continue
                    latest_by_agent[key] = GlobalAgentSummary(
                        agent_slug=agent_slug,
                        visibility=visibility,
                        latest_version=version,
                        latest_updated_at=_to_iso(updated_at),
                    )

                tenant_lists: dict[str, list[GlobalAgentSummary]] = {}
                for (tenant_slug, _), summary in latest_by_agent.items():
                    tenant_lists.setdefault(tenant_slug, []).append(summary)
                tenant_map = {
                    tenant_slug: tuple(sorted(summaries, key=lambda item: item.agent_slug))
                    for tenant_slug, summaries in tenant_lists.items()
                }
                return GlobalIndex(generated_at=utc_now_iso(), tenants=tenant_map)
        except SQLAlchemyError as error:
            raise DatabaseError("Unable to build global index from registry database.") from error

    def list_tenants(self) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            rows = session.execute(
                select(Tenant.slug, Tenant.display_name, func.count(Agent.id))
                .outerjoin(Agent, Agent.tenant_id == Tenant.id)
                .group_by(Tenant.slug, Tenant.display_name)
                .order_by(Tenant.slug)
            ).all()
            return [{"slug": slug, "display_name": display_name, "agent_count": count} for slug, display_name, count in rows]

    def list_users(self) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            rows = session.execute(select(User.email, User.display_name, User.created_at).order_by(User.email)).all()
            return [{"email": email, "display_name": display_name, "created_at": _to_iso(created_at)} for email, display_name, created_at in rows]

    def list_agents(self) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            rows = session.execute(
                select(Tenant.slug, Agent.slug, Agent.visibility, func.count(AgentVersion.id))
                .join(Tenant, Agent.tenant_id == Tenant.id)
                .outerjoin(AgentVersion, AgentVersion.agent_id == Agent.id)
                .group_by(Tenant.slug, Agent.slug, Agent.visibility)
                .order_by(Tenant.slug, Agent.slug)
            ).all()
            return [
                {"tenant_slug": tenant_slug, "agent_slug": agent_slug, "visibility": visibility, "version_count": version_count}
                for tenant_slug, agent_slug, visibility, version_count in rows
            ]

    def list_audit_log(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            rows = session.execute(
                select(AuditLog.event_type, AuditLog.entity_type, AuditLog.tenant_slug, AuditLog.created_at)
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
            ).all()
            return [
                {
                    "event_type": event_type,
                    "entity_type": entity_type,
                    "tenant_slug": tenant_slug,
                    "created_at": _to_iso(created_at),
                }
                for event_type, entity_type, tenant_slug, created_at in rows
            ]

    def _get_or_create_tenant(self, *, session: Session, tenant_slug: str) -> Tenant:
        tenant = session.execute(select(Tenant).where(Tenant.slug == tenant_slug)).scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(slug=tenant_slug, display_name=tenant_slug)
            session.add(tenant)
            session.flush()
        return tenant

    def _get_or_create_agent(self, *, session: Session, tenant: Tenant, agent_slug: str, visibility: str) -> Agent:
        agent = session.execute(
            select(Agent).where(Agent.tenant_id == tenant.id, Agent.slug == agent_slug)
        ).scalar_one_or_none()
        if agent is None:
            agent = Agent(tenant_id=tenant.id, slug=agent_slug, visibility=visibility)
            session.add(agent)
            session.flush()
        else:
            agent.visibility = visibility
        return agent
