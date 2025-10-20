"""add fcm_token to users

Revision ID: 012_add_fcm_token
Revises: 011_add_user_id_number
Create Date: 2025-10-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012_add_fcm_token'
down_revision = '011_add_user_id_number'
branch_labels = None
depends_on = None


def upgrade():
    # Add fcm_token column to users table
    op.add_column('users', sa.Column('fcm_token', sa.String(length=255), nullable=True))


def downgrade():
    # Remove fcm_token column from users table
    op.drop_column('users', 'fcm_token')
