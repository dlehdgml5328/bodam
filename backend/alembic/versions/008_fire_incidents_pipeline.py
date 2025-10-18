"""Add fire incidents pipeline tables.

Adds tables for:
- fire_incidents: 화재 사고 정보
- dispatch_events: 출동 이벤트
- news_matches: 뉴스-사고 매칭
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "008_fire_incidents_pipeline"
down_revision = "007_donation_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # fire_incidents 테이블
    # ============================================
    op.create_table(
        "fire_incidents",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("location_address", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),  # dispatching, suppressing, contained, resolved
        sa.Column("severity", sa.String(20), nullable=True),  # critical, high, medium, low
        sa.Column("casualties_injured", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("casualties_dead", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_damage", sa.BigInteger(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # fire_incidents 인덱스
    op.create_index("idx_fire_incidents_occurred_at", "fire_incidents", ["occurred_at"], postgresql_using="btree")
    op.create_index("idx_fire_incidents_status", "fire_incidents", ["status"])

    # ============================================
    # dispatch_events 테이블
    # ============================================
    op.create_table(
        "dispatch_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("incident_id", sa.String(50), nullable=False),
        sa.Column("fire_station_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("units_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("personnel_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["incident_id"], ["fire_incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fire_station_id"], ["fire_stations.id"], ondelete="SET NULL"),
    )

    # dispatch_events 인덱스
    op.create_index("idx_dispatch_events_incident", "dispatch_events", ["incident_id"])
    op.create_index("idx_dispatch_events_station", "dispatch_events", ["fire_station_id"])
    op.create_index("idx_dispatch_events_dispatched_at", "dispatch_events", ["dispatched_at"], postgresql_using="btree")

    # ============================================
    # news_matches 테이블
    # ============================================
    op.create_table(
        "news_matches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("incident_id", sa.String(50), nullable=False),
        sa.Column("news_type", sa.String(20), nullable=False),  # naver, youtube
        sa.Column("news_id", sa.String(200), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["incident_id"], ["fire_incidents.id"], ondelete="CASCADE"),
    )

    # news_matches 인덱스
    op.create_index("idx_news_matches_incident", "news_matches", ["incident_id"])
    op.create_index("idx_news_matches_news_id", "news_matches", ["news_id"])
    op.create_index("idx_news_matches_type", "news_matches", ["news_type"])

    # Unique constraint for incident_id + news_type + news_id
    op.create_index(
        "idx_news_matches_unique",
        "news_matches",
        ["incident_id", "news_type", "news_id"],
        unique=True
    )


def downgrade() -> None:
    # news_matches 삭제
    op.drop_index("idx_news_matches_unique", table_name="news_matches")
    op.drop_index("idx_news_matches_type", table_name="news_matches")
    op.drop_index("idx_news_matches_news_id", table_name="news_matches")
    op.drop_index("idx_news_matches_incident", table_name="news_matches")
    op.drop_table("news_matches")

    # dispatch_events 삭제
    op.drop_index("idx_dispatch_events_dispatched_at", table_name="dispatch_events")
    op.drop_index("idx_dispatch_events_station", table_name="dispatch_events")
    op.drop_index("idx_dispatch_events_incident", table_name="dispatch_events")
    op.drop_table("dispatch_events")

    # fire_incidents 삭제
    op.drop_index("idx_fire_incidents_status", table_name="fire_incidents")
    op.drop_index("idx_fire_incidents_occurred_at", table_name="fire_incidents")
    op.drop_table("fire_incidents")
