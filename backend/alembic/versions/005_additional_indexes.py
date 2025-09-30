"""Add additional performance indexes for common queries."""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "005_additional_indexes"
down_revision = "004_password_reset_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User indexes for authentication and search
    op.create_index("idx_users_email_active", "users", ["email", "is_active"])
    op.create_index("idx_users_social", "users", ["social_provider", "social_id"])
    op.create_index("idx_users_tier_donations", "users", ["tier", "total_donated"])

    # Donation status and payment tracking
    op.create_index("idx_donations_status_created", "donations", ["status", "created_at"])
    op.create_index("idx_donations_toss_order", "donations", ["toss_order_id"])
    op.create_index("idx_donations_amount_type", "donations", ["amount", "type"])

    # Password reset tokens
    op.create_index("idx_password_reset_user_expires", "password_reset_tokens", ["user_id", "expires_at"])
    op.create_index("idx_password_reset_token_used", "password_reset_tokens", ["token", "used"])

    # Fire station performance

    # Group and receipt tracking
    op.create_index("idx_groups_user_created", "groups", ["creator_id", "created_at"])
    op.create_index("idx_receipts_donation_created", "receipts", ["donation_id", "created_at"])

    # Refund tracking


def downgrade() -> None:
    op.drop_index("idx_receipts_donation_created", table_name="receipts")
    op.drop_index("idx_groups_user_created", table_name="groups")
    op.drop_index("idx_password_reset_token_used", table_name="password_reset_tokens")
    op.drop_index("idx_password_reset_user_expires", table_name="password_reset_tokens")
    op.drop_index("idx_donations_amount_type", table_name="donations")
    op.drop_index("idx_donations_toss_order", table_name="donations")
    op.drop_index("idx_donations_status_created", table_name="donations")
    op.drop_index("idx_users_tier_donations", table_name="users")
    op.drop_index("idx_users_social", table_name="users")
    op.drop_index("idx_users_email_active", table_name="users")
