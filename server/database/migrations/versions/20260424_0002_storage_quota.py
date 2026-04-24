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
        "tenants",
        sa.Column("used_bytes", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "tenants",
        sa.Column("quota_bytes", sa.BigInteger(), nullable=False, server_default=sa.text(str(FREE_TIER_QUOTA_BYTES))),
    )

    op.execute(
        """
        UPDATE tenants t
        SET used_bytes = COALESCE((
            SELECT SUM(av.archive_size_bytes)::bigint
            FROM agents a
            JOIN agent_versions av ON av.agent_id = a.id
            WHERE a.tenant_id = t.id
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

            UPDATE tenants t
            SET used_bytes = COALESCE((
                SELECT SUM(av.archive_size_bytes)::bigint
                FROM agents a
                JOIN agent_versions av ON av.agent_id = a.id
                WHERE a.tenant_id = t.id
            ), 0),
            updated_at = now()
            WHERE t.id = target_tenant_id;
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
        CREATE TRIGGER trg_refresh_tenant_storage_usage_agent_versions
        AFTER INSERT OR UPDATE OR DELETE ON agent_versions
        FOR EACH ROW
        EXECUTE FUNCTION refresh_tenant_storage_usage_from_agent_versions();
        """
    )
    op.alter_column("agent_versions", "archive_size_bytes", server_default=None)
    op.alter_column("tenants", "used_bytes", server_default=None)
    op.alter_column("tenants", "quota_bytes", server_default=None)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_refresh_tenant_storage_usage_agent_versions ON agent_versions")
    op.execute("DROP FUNCTION IF EXISTS refresh_tenant_storage_usage_from_agent_versions()")
    op.execute("DROP FUNCTION IF EXISTS refresh_tenant_storage_usage(uuid)")

    op.drop_column("tenants", "quota_bytes")
    op.drop_column("tenants", "used_bytes")
    op.drop_column("agent_versions", "archive_size_bytes")
