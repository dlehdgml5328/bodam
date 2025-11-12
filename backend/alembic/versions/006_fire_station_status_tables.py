"""Add live fire station status tables for emergency endpoints."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "006_fire_station_status_tables"
down_revision = "005_additional_indexes"
branch_labels = None
depends_on = None


_priority_enum = sa.Enum(
    "high", "medium", "low", name="emergency_priority_level"
)
_status_enum = sa.Enum(
    "dispatching", "suppressing", "standby", "maintenance", name="fire_station_live_status"
)


def upgrade() -> None:
    bind = op.get_bind()

    # Check if ENUM types already exist before creating
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT typname FROM pg_type WHERE typname IN ('emergency_priority_level', 'fire_station_live_status')"
    ))
    existing_enums = {row[0] for row in result}

    if 'emergency_priority_level' not in existing_enums:
        _priority_enum.create(bind, checkfirst=False)
    if 'fire_station_live_status' not in existing_enums:
        _status_enum.create(bind, checkfirst=False)

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
        sa.Column("status", _status_enum, nullable=False),
        sa.Column(
            "priority",
            _priority_enum,
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

    bind = op.get_bind()
    _status_enum.drop(bind, checkfirst=True)
    _priority_enum.drop(bind, checkfirst=True)
