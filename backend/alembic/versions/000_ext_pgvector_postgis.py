"""Enable PostGIS and pgvector extensions."""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "000_ext_pgvector_postgis"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS postgis")
