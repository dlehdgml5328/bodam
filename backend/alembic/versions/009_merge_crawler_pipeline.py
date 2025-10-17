"""Merge crawler and pipeline heads while backfilling donation schema."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "009_merge_crawler_pipeline"
down_revision = ("004_selenium_crawler", "008_fire_incidents_pipeline")
branch_labels = None
depends_on = None


def _table_exists(inspector: Inspector) -> set[str]:
    return set(inspector.get_table_names())


def _column_exists(inspector: Inspector, table: str, column: str) -> bool:
    return column in {col["name"] for col in inspector.get_columns(table)}


def _index_exists(inspector: Inspector, table: str, index: str) -> bool:
    return index in {idx["name"] for idx in inspector.get_indexes(table)}


def _fk_exists(inspector: Inspector, table: str, fk_name: str) -> bool:
    return fk_name in {fk["name"] for fk in inspector.get_foreign_keys(table)}


def _ensure_enum(enum_name: str, values: list[str]) -> None:
    enum_values = ", ".join(f"'{value}'" for value in values)
    op.execute(
        f"DO $$ BEGIN "
        f"IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN "
        f"CREATE TYPE {enum_name} AS ENUM ({enum_values}); "
        "END IF; "
        "END $$;"
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = _table_exists(inspector)

    _ensure_enum("donation_mode", ["single", "multiple"])
    _ensure_enum("donation_allocation_type", ["primary", "split", "each", "custom"])
    _ensure_enum("donation_subscription_status", ["active", "paused", "cancelled"])
    _ensure_enum("donation_subscription_cycle", ["monthly", "quarterly", "yearly"])

    if "donation_subscriptions" not in existing_tables:
        op.create_table(
            "donation_subscriptions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "origin_donation_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("donations.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "status",
                postgresql.ENUM(
                    "active",
                    "paused",
                    "cancelled",
                    name="donation_subscription_status",
                    create_type=False,
                ),
                nullable=False,
                server_default="active",
            ),
            sa.Column(
                "cycle",
                postgresql.ENUM(
                    "monthly",
                    "quarterly",
                    "yearly",
                    name="donation_subscription_cycle",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="KRW"),
            sa.Column("next_billing_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "started_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("toss_customer_key", sa.String(length=120), nullable=True),
            sa.Column("toss_billing_key", sa.String(length=120), nullable=True),
        )
        op.create_index(
            "ix_donation_subscriptions_user_status",
            "donation_subscriptions",
            ["user_id", "status"],
        )
        op.create_index(
            "ix_donation_subscriptions_next_billing",
            "donation_subscriptions",
            ["next_billing_at"],
        )
    else:
        inspector = sa.inspect(bind)
        if not _index_exists(
            inspector, "donation_subscriptions", "ix_donation_subscriptions_user_status"
        ):
            op.create_index(
                "ix_donation_subscriptions_user_status",
                "donation_subscriptions",
                ["user_id", "status"],
            )
        if not _index_exists(
            inspector, "donation_subscriptions", "ix_donation_subscriptions_next_billing"
        ):
            op.create_index(
                "ix_donation_subscriptions_next_billing",
                "donation_subscriptions",
                ["next_billing_at"],
            )

    inspector = sa.inspect(bind)
    existing_tables = _table_exists(inspector)

    if "donation_allocations" not in existing_tables:
        op.create_table(
            "donation_allocations",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "donation_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("donations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "fire_station_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("fire_stations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column(
                "allocation_type",
                postgresql.ENUM(
                    "primary",
                    "split",
                    "each",
                    "custom",
                    name="donation_allocation_type",
                    create_type=False,
                ),
                nullable=False,
                server_default="primary",
            ),
        )
        op.create_index(
            "ix_donation_allocations_station",
            "donation_allocations",
            ["fire_station_id"],
        )
    else:
        inspector = sa.inspect(bind)
        if not _index_exists(inspector, "donation_allocations", "ix_donation_allocations_station"):
            op.create_index(
                "ix_donation_allocations_station",
                "donation_allocations",
                ["fire_station_id"],
            )

    inspector = sa.inspect(bind)

    donations_columns = {col["name"] for col in inspector.get_columns("donations")}

    if "group_id" not in donations_columns:
        op.add_column(
            "donations",
            sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if "mode" not in donations_columns:
        op.add_column(
            "donations",
            sa.Column(
                "mode",
                postgresql.ENUM("single", "multiple", name="donation_mode", create_type=False),
                nullable=False,
                server_default="single",
            ),
        )
    if "currency" not in donations_columns:
        op.add_column(
            "donations",
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="KRW"),
        )
    if "billing_customer_key" not in donations_columns:
        op.add_column(
            "donations",
            sa.Column("billing_customer_key", sa.String(length=120), nullable=True),
        )
    if "billing_key" not in donations_columns:
        op.add_column(
            "donations",
            sa.Column("billing_key", sa.String(length=120), nullable=True),
        )
    if "subscription_id" not in donations_columns:
        op.add_column(
            "donations",
            sa.Column(
                "subscription_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("donation_subscriptions.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
    if "donor_display_name" not in donations_columns:
        op.add_column(
            "donations",
            sa.Column("donor_display_name", sa.String(length=120), nullable=True),
        )
    if "needs_receipt" not in donations_columns:
        op.add_column(
            "donations",
            sa.Column("needs_receipt", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "is_group_anonymous" not in donations_columns:
        op.add_column(
            "donations",
            sa.Column("is_group_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "metadata" not in donations_columns:
        op.add_column(
            "donations",
            sa.Column("metadata", sa.JSON(), nullable=True),
        )

    inspector = sa.inspect(bind)
    if not _fk_exists(inspector, "donations", "fk_donations_group_id_groups"):
        op.create_foreign_key(
            "fk_donations_group_id_groups",
            "donations",
            "groups",
            ["group_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not _index_exists(inspector, "donations", "ix_donations_mode_status"):
        op.create_index("ix_donations_mode_status", "donations", ["mode", "status"])

    op.execute("UPDATE donations SET mode = 'single' WHERE mode IS NULL")
    op.execute("UPDATE donations SET currency = 'KRW' WHERE currency IS NULL")


def downgrade() -> None:
    # 병합 리비전은 스키마 병합을 위해 사용되므로 별도 다운그레이드는 제공하지 않습니다.
    pass
