"""Add performance indexes."""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "002_indexes"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_fire_stations_location", "fire_stations", ["location"], postgresql_using="gist")
    op.create_index(
        "ix_news_content_embedding",
        "news_content",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_l2_ops"},
        postgresql_with={"lists": 100},
    )
    op.create_index(
        "idx_donations_user_created",
        "donations",
        ["user_id", "created_at"],
    )
    op.create_index(
        "idx_donations_station_created",
        "donations",
        ["fire_station_id", "created_at"],
    )
    op.create_index(
        "idx_notifications_user_created",
        "notifications",
        ["user_id", "created_at"],
    )
    op.create_index(
        "idx_notifications_unread",
        "notifications",
        ["user_id", "is_read", "created_at"],
    )
    op.create_index(
        "idx_rankings_station_period_rank",
        "rankings",
        ["fire_station_id", "period", "rank"],
    )


def downgrade() -> None:
    op.drop_index("idx_rankings_station_period_rank", table_name="rankings")
    op.drop_index("idx_notifications_unread", table_name="notifications")
    op.drop_index("idx_notifications_user_created", table_name="notifications")
    op.drop_index("idx_donations_station_created", table_name="donations")
    op.drop_index("idx_donations_user_created", table_name="donations")
    op.drop_index("ix_news_content_embedding", table_name="news_content")
    op.drop_index("ix_fire_stations_location", table_name="fire_stations")
