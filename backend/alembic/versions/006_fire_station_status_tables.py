"""Add live fire station status tables for emergency endpoints."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "006_fire_station_status_tables"
down_revision = "005_additional_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types using raw SQL with DO block to avoid conflicts
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'emergency_priority_level') THEN
                CREATE TYPE emergency_priority_level AS ENUM ('high', 'medium', 'low');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'fire_station_live_status') THEN
                CREATE TYPE fire_station_live_status AS ENUM ('dispatching', 'suppressing', 'standby', 'maintenance');
            END IF;
        END
        $$;
    """))
    conn.commit()

    op.create_table(
        "fire_station_statuses",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "station_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("fire_stations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            sa.Text(),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("status_label", sa.String(length=50), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_fire_station_statuses_priority_updated",
        "fire_station_statuses",
        ["priority", "updated_at"],
    )

    op.create_table(
        "fire_station_active_incidents",
        sa.Column(
            "status_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("fire_station_statuses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "incident_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("news_content.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("status_id", "incident_id"),
    )
    op.create_index(
        "ix_fire_station_active_incidents_incident",
        "fire_station_active_incidents",
        ["incident_id"],
    )

    # Alter columns to use ENUM types
    conn.execute(sa.text("""
        ALTER TABLE fire_station_statuses
        ALTER COLUMN status TYPE fire_station_live_status USING status::fire_station_live_status,
        ALTER COLUMN priority TYPE emergency_priority_level USING priority::emergency_priority_level;
    """))
    conn.commit()


def downgrade() -> None:
    op.drop_index(
        "ix_fire_station_active_incidents_incident",
        table_name="fire_station_active_incidents",
    )
    op.drop_table("fire_station_active_incidents")

    op.drop_index(
        "ix_fire_station_statuses_priority_updated",
        table_name="fire_station_statuses",
    )
    op.drop_table("fire_station_statuses")

    # Drop ENUM types
    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS fire_station_live_status CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS emergency_priority_level CASCADE"))
    conn.commit()
