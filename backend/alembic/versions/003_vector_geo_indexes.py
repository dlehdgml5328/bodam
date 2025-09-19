"""Additional vector and geo indexes."""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "003_vector_geo_indexes"
down_revision = "002_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_news_content_vector_cosine ON news_content USING ivfflat (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fire_stations_geo ON fire_stations USING GIST (location)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_fire_stations_geo")
    op.execute("DROP INDEX IF EXISTS idx_news_content_vector_cosine")
