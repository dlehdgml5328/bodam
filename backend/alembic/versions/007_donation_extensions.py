"""Extend donation models for allocations and subscriptions."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "007_donation_extensions"
down_revision = "006_fire_station_status_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types using raw SQL with DO block
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'donation_mode') THEN
                CREATE TYPE donation_mode AS ENUM ('single', 'multiple');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'donation_allocation_type') THEN
                CREATE TYPE donation_allocation_type AS ENUM ('primary', 'split', 'each', 'custom');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'donation_subscription_status') THEN
                CREATE TYPE donation_subscription_status AS ENUM ('active', 'paused', 'cancelled');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'donation_subscription_cycle') THEN
                CREATE TYPE donation_subscription_cycle AS ENUM ('monthly', 'quarterly', 'yearly');
            END IF;
        END
        $$;
    """))
    conn.commit()

    op.create_table(
        "donation_subscriptions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "origin_donation_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("donations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("cycle", sa.Text(), nullable=False),
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

    op.create_table(
        "donation_allocations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "donation_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("donations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fire_station_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("fire_stations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("allocation_type", sa.Text(), nullable=False, server_default="primary"),
    )
    op.create_index(
        "ix_donation_allocations_station",
        "donation_allocations",
        ["fire_station_id"],
    )

    op.add_column(
        "donations",
        sa.Column("group_id", sa.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "donations",
        sa.Column("mode", sa.Text(), nullable=False, server_default="single"),
    )
    op.add_column(
        "donations",
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="KRW"),
    )
    op.add_column(
        "donations",
        sa.Column("billing_customer_key", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "donations",
        sa.Column("billing_key", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "donations",
        sa.Column(
            "subscription_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("donation_subscriptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "donations",
        sa.Column("donor_display_name", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "donations",
        sa.Column("needs_receipt", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "donations",
        sa.Column("is_group_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "donations",
        sa.Column("metadata", sa.JSON(), nullable=True),
    )

    op.create_foreign_key(
        "fk_donations_group_id_groups",
        "donations",
        "groups",
        ["group_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_donations_mode_status", "donations", ["mode", "status"])

    # backfill defaults for existing rows
    op.execute("UPDATE donations SET mode = 'single' WHERE mode IS NULL")
    op.execute("UPDATE donations SET currency = 'KRW' WHERE currency IS NULL")

    # Convert Text columns to ENUM types
    conn.execute(sa.text("""
        ALTER TABLE donation_subscriptions
        ALTER COLUMN cycle TYPE donation_subscription_cycle USING cycle::donation_subscription_cycle;
    """))
    conn.execute(sa.text("""
        ALTER TABLE donation_subscriptions
        ALTER COLUMN status DROP DEFAULT,
        ALTER COLUMN status TYPE donation_subscription_status USING status::donation_subscription_status,
        ALTER COLUMN status SET DEFAULT 'active'::donation_subscription_status;
    """))
    conn.execute(sa.text("""
        ALTER TABLE donation_allocations
        ALTER COLUMN allocation_type DROP DEFAULT,
        ALTER COLUMN allocation_type TYPE donation_allocation_type USING allocation_type::donation_allocation_type,
        ALTER COLUMN allocation_type SET DEFAULT 'primary'::donation_allocation_type;
    """))
    conn.execute(sa.text("""
        ALTER TABLE donations
        ALTER COLUMN mode DROP DEFAULT,
        ALTER COLUMN mode TYPE donation_mode USING mode::donation_mode,
        ALTER COLUMN mode SET DEFAULT 'single'::donation_mode;
    """))
    conn.commit()


def downgrade() -> None:
    op.drop_index("ix_donations_mode_status", table_name="donations")
    op.drop_constraint("fk_donations_group_id_groups", "donations", type_="foreignkey")

    op.drop_column("donations", "metadata")
    op.drop_column("donations", "is_group_anonymous")
    op.drop_column("donations", "needs_receipt")
    op.drop_column("donations", "donor_display_name")
    op.drop_column("donations", "subscription_id")
    op.drop_column("donations", "billing_key")
    op.drop_column("donations", "billing_customer_key")
    op.drop_column("donations", "currency")
    op.drop_column("donations", "mode")
    op.drop_column("donations", "group_id")

    op.drop_index("ix_donation_allocations_station", table_name="donation_allocations")
    op.drop_table("donation_allocations")

    op.drop_index("ix_donation_subscriptions_next_billing", table_name="donation_subscriptions")
    op.drop_index("ix_donation_subscriptions_user_status", table_name="donation_subscriptions")
    op.drop_table("donation_subscriptions")

    # Drop ENUM types
    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS donation_subscription_cycle CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS donation_subscription_status CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS donation_allocation_type CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS donation_mode CASCADE"))
    conn.commit()
