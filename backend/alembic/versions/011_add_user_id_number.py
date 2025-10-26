"""add user id_number field

Revision ID: 011_add_user_id_number
Revises: 010_add_subscription_metadata
Create Date: 2025-10-19 21:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "011_add_user_id_number"
down_revision: Union[str, None] = "010_add_subscription_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add id_number column to users table."""
    op.add_column("users", sa.Column("id_number", sa.String(length=14), nullable=True))


def downgrade() -> None:
    """Remove id_number column from users table."""
    op.drop_column("users", "id_number")
