"""add tenant storage quota columns and usage triggers"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260424_0002"
down_revision = "20260420_0001"
branch_labels = None
depends_on = None

FREE_TIER_QUOTA_BYTES = 5 * 1024 * 1024 * 1024


def upgrade() -> None:
    op.add_column(
        "agent_versions",
        sa.Column("archive_size_bytes", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "tenant_members",
        sa.Column("used_bytes", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "tenant_members",
        sa.Column("quota_bytes", sa.BigInteger(), nullable=False, server_default=sa.text(str(FREE_TIER_QUOTA_BYTES))),
    )

    op.execute(
        """
        UPDATE tenant_members tm
        SET used_bytes = COALESCE((
            SELECT SUM(av.archive_size_bytes)::bigint
            FROM agents a
            JOIN agent_versions av ON av.agent_id = a.id
            WHERE a.tenant_id = tm.tenant_id
        ), 0)
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION refresh_tenant_storage_usage(target_tenant_id uuid)
        RETURNS void
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF target_tenant_id IS NULL THEN
                RETURN;
            END IF;

            UPDATE tenant_members tm
            SET used_bytes = COALESCE((
                SELECT SUM(av.archive_size_bytes)::bigint
                FROM agents a
                JOIN agent_versions av ON av.agent_id = a.id
                WHERE a.tenant_id = tm.tenant_id
            ), 0),
            updated_at = now()
            WHERE tm.tenant_id = target_tenant_id;
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION refresh_tenant_storage_usage_from_agent_versions()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            old_tenant_id uuid;
            new_tenant_id uuid;
        BEGIN
            IF TG_OP <> 'INSERT' THEN
                SELECT tenant_id INTO old_tenant_id FROM agents WHERE id = OLD.agent_id;
                PERFORM refresh_tenant_storage_usage(old_tenant_id);
            END IF;

            IF TG_OP <> 'DELETE' THEN
                SELECT tenant_id INTO new_tenant_id FROM agents WHERE id = NEW.agent_id;
                IF new_tenant_id IS DISTINCT FROM old_tenant_id THEN
                    PERFORM refresh_tenant_storage_usage(new_tenant_id);
                END IF;
            END IF;

            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION refresh_tenant_storage_usage_on_member_insert()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            PERFORM refresh_tenant_storage_usage(NEW.tenant_id);
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_tenant_quota_consistency_on_member()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            existing_quota bigint;
        BEGIN
            SELECT quota_bytes
            INTO existing_quota
            FROM tenant_members
            WHERE tenant_id = NEW.tenant_id
              AND id <> NEW.id
            LIMIT 1;

            IF existing_quota IS NULL THEN
                RETURN NEW;
            END IF;

            IF NEW.quota_bytes IS DISTINCT FROM existing_quota THEN
                RAISE EXCEPTION 'tenant_members.quota_bytes must match existing tenant quota (%).', existing_quota;
            END IF;

            RETURN NEW;
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_refresh_tenant_storage_usage_agent_versions
        AFTER INSERT OR UPDATE OR DELETE ON agent_versions
        FOR EACH ROW
        EXECUTE FUNCTION refresh_tenant_storage_usage_from_agent_versions();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_refresh_tenant_storage_usage_tenant_members
        AFTER INSERT ON tenant_members
        FOR EACH ROW
        EXECUTE FUNCTION refresh_tenant_storage_usage_on_member_insert();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_enforce_tenant_quota_consistency_tenant_members
        BEFORE INSERT OR UPDATE OF quota_bytes ON tenant_members
        FOR EACH ROW
        EXECUTE FUNCTION enforce_tenant_quota_consistency_on_member();
        """
    )

    op.alter_column("agent_versions", "archive_size_bytes", server_default=None)
    op.alter_column("tenant_members", "used_bytes", server_default=None)
    op.alter_column("tenant_members", "quota_bytes", server_default=None)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_enforce_tenant_quota_consistency_tenant_members ON tenant_members")
    op.execute("DROP TRIGGER IF EXISTS trg_refresh_tenant_storage_usage_tenant_members ON tenant_members")
    op.execute("DROP TRIGGER IF EXISTS trg_refresh_tenant_storage_usage_agent_versions ON agent_versions")
    op.execute("DROP FUNCTION IF EXISTS enforce_tenant_quota_consistency_on_member()")
    op.execute("DROP FUNCTION IF EXISTS refresh_tenant_storage_usage_on_member_insert()")
    op.execute("DROP FUNCTION IF EXISTS refresh_tenant_storage_usage_from_agent_versions()")
    op.execute("DROP FUNCTION IF EXISTS refresh_tenant_storage_usage(uuid)")

    op.drop_column("tenant_members", "quota_bytes")
    op.drop_column("tenant_members", "used_bytes")
    op.drop_column("agent_versions", "archive_size_bytes")
