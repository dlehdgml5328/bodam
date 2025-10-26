"""Add metadata field to donation_subscriptions

Revision ID: 010_add_subscription_metadata
Revises: 009_add_refresh_tokens, 009_merge_crawler_pipeline
Create Date: 2025-10-19

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "010_add_subscription_metadata"
down_revision = ("009_add_refresh_tokens", "009_merge_crawler_pipeline")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add metadata column to donation_subscriptions
    op.add_column("donation_subscriptions", sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove metadata column from donation_subscriptions
    op.drop_column("donation_subscriptions", "metadata")
