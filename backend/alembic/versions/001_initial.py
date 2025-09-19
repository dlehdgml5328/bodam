"""Initial schema creation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = "000_ext_pgvector_postgis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = sa.Enum("donor", "admin", "moderator", name="user_role")
    station_status = sa.Enum("active", "closed", "merged", name="station_status")
    donation_type = sa.Enum("one_time", "recurring", name="donation_type")
    donation_status = sa.Enum("pending", "completed", "failed", "refunded", name="donation_status")
    content_status = sa.Enum(
        "auto_approved", "pending_review", "rejected", name="content_status"
    )
    notification_type = sa.Enum("donation_success", "incident_alert", "system", name="notification_type")
    notification_status = sa.Enum("pending", "sent", "failed", name="notification_status")
    group_status = sa.Enum("active", "completed", "expired", name="group_status")
    ranking_period = sa.Enum("monthly", "yearly", "all_time", name="ranking_period")

    user_role.create(op.get_bind(), checkfirst=True)
    station_status.create(op.get_bind(), checkfirst=True)
    donation_type.create(op.get_bind(), checkfirst=True)
    donation_status.create(op.get_bind(), checkfirst=True)
    content_status.create(op.get_bind(), checkfirst=True)
    notification_type.create(op.get_bind(), checkfirst=True)
    notification_status.create(op.get_bind(), checkfirst=True)
    group_status.create(op.get_bind(), checkfirst=True)
    ranking_period.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=20)),
        sa.Column("role", user_role, nullable=False, server_default="donor"),
        sa.Column("social_provider", sa.String(length=50)),
        sa.Column("social_id", sa.String(length=120)),
        sa.Column("tier", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_donated", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "fire_stations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("location", Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("station_code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("status", station_status, nullable=False, server_default="active"),
        sa.Column("total_received", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("donor_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_incident_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("target_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("current_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("fire_station_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fire_stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("invite_code", sa.String(length=24), nullable=False, unique=True),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column("status", group_status, nullable=False, server_default="active"),
        sa.Column("member_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "donations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fire_station_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fire_stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("type", donation_type, nullable=False),
        sa.Column("frequency", sa.String(length=20)),
        sa.Column("status", donation_status, nullable=False, server_default="pending"),
        sa.Column("payment_method", sa.String(length=50)),
        sa.Column("toss_payment_key", sa.String(length=120)),
        sa.Column("toss_order_id", sa.String(length=120), nullable=False, unique=True),
        sa.Column("message", sa.String(length=500)),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("receipt_url", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("refunded_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "news_content",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("analysis_job_id", postgresql.UUID(as_uuid=True)),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=255), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", Geometry(geometry_type="POINT", srid=4326)),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("relevance_score", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("keywords", postgresql.ARRAY(sa.String(length=50)), nullable=False),
        sa.Column("status", content_status, nullable=False, server_default="pending_review"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_news_content_analysis_job_id", "news_content", ["analysis_job_id"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_id", postgresql.UUID(as_uuid=True)),
        sa.Column("channels", postgresql.ARRAY(sa.String(length=20)), nullable=False),
        sa.Column("status", notification_status, nullable=False, server_default="pending"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "group_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
        sa.Column("contributed_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "rankings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("fire_station_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fire_stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("donation_count", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("period", ranking_period, nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("donation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("donations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("receipt_number", sa.String(length=50), nullable=False, unique=True),
        sa.Column("recipient_name", sa.String(length=120), nullable=False),
        sa.Column("recipient_phone", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("pdf_url", sa.String(length=255), nullable=False),
        sa.Column("email_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("receipts")
    op.drop_table("rankings")
    op.drop_table("group_memberships")
    op.drop_table("notifications")
    op.drop_index("ix_news_content_analysis_job_id", table_name="news_content")
    op.drop_table("news_content")
    op.drop_table("donations")
    op.drop_table("groups")
    op.drop_table("fire_stations")
    op.drop_table("users")

    sa.Enum(name="ranking_period").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="group_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="notification_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="notification_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="content_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="donation_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="donation_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="station_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
