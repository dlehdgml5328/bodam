"""add refunds table

Revision ID: 013_add_refunds_table
Revises: 012_add_fcm_token
Create Date: 2025-10-21
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "013_add_refunds_table"
down_revision = "012_add_fcm_token"
branch_labels = None
depends_on = None


REFUND_STATUS_VALUES = ("pending", "approved", "rejected")


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'refund_status'
            ) THEN
                CREATE TYPE refund_status AS ENUM ('pending', 'approved', 'rejected');
            END IF;
        END$$;
        """
    )

    op.create_table(
        "refunds",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "donation_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("donations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "status",
            sa.dialects.postgresql.ENUM(
                *REFUND_STATUS_VALUES,
                name="refund_status",
                create_type=False,
            ),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("reviewer_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_refunds_donation_id",
        "refunds",
        ["donation_id"],
    )
    op.create_index("ix_refunds_status", "refunds", ["status"])
    op.create_index("ix_refunds_created_at", "refunds", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_refunds_created_at", table_name="refunds")
    op.drop_index("ix_refunds_status", table_name="refunds")
    op.drop_index("ix_refunds_donation_id", table_name="refunds")
    op.drop_table("refunds")

    op.execute("DROP TYPE IF EXISTS refund_status")
