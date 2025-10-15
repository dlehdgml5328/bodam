"""Add Selenium crawler tables

Revision ID: 004_selenium_crawler
Revises: 003_vector_geo_indexes
Create Date: 2025-10-15 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_selenium_crawler'
down_revision: Union[str, None] = '003_vector_geo_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create selenium_crawl_jobs and crawled_contents tables"""

    # Create selenium_crawl_jobs table
    op.create_table(
        'selenium_crawl_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('browser_type', sa.String(20), nullable=False, server_default='chrome'),
        sa.Column('wait_conditions', postgresql.JSONB, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.CheckConstraint("browser_type IN ('chrome', 'firefox')", name='ck_browser_type'),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'timeout')", name='ck_status'),
        sa.CheckConstraint('retry_count <= max_retries', name='ck_retry_limit'),
    )

    # Create indexes for selenium_crawl_jobs
    op.create_index('idx_crawl_jobs_status', 'selenium_crawl_jobs', ['status'])
    op.create_index('idx_crawl_jobs_created_at', 'selenium_crawl_jobs', ['created_at'])
    op.create_index('idx_crawl_jobs_url', 'selenium_crawl_jobs', ['url'])

    # Create crawled_contents table
    op.create_table(
        'crawled_contents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('crawl_job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_url', sa.String(2048), nullable=False),
        sa.Column('rendered_html', sa.Text, nullable=True),
        sa.Column('extracted_data', postgresql.JSONB, nullable=False),
        sa.Column('screenshot_url', sa.String(2048), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['crawl_job_id'], ['selenium_crawl_jobs.id'], ondelete='CASCADE'),
    )

    # Create indexes for crawled_contents
    op.create_index('idx_crawled_content_job_id', 'crawled_contents', ['crawl_job_id'])
    op.create_index('idx_crawled_content_created_at', 'crawled_contents', ['created_at'])


def downgrade() -> None:
    """Drop selenium_crawl_jobs and crawled_contents tables"""

    # Drop indexes first
    op.drop_index('idx_crawled_content_created_at', 'crawled_contents')
    op.drop_index('idx_crawled_content_job_id', 'crawled_contents')
    op.drop_index('idx_crawl_jobs_url', 'selenium_crawl_jobs')
    op.drop_index('idx_crawl_jobs_created_at', 'selenium_crawl_jobs')
    op.drop_index('idx_crawl_jobs_status', 'selenium_crawl_jobs')

    # Drop tables (CASCADE will remove dependent rows)
    op.drop_table('crawled_contents')
    op.drop_table('selenium_crawl_jobs')
