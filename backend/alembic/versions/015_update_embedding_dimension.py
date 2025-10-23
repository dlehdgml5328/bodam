"""update embedding dimension to 1024

Revision ID: 015_update_embedding_dimension
Revises: 014_add_knowledge_documents
Create Date: 2025-10-23 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '015_update_embedding_dimension'
down_revision = ('009_observability', '014_add_knowledge_documents')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    임베딩 차원 변경: 768 → 1024
    BAAI/bge-large-en-v1.5 모델 사용
    """

    # 1. 기존 인덱스 삭제
    op.execute("DROP INDEX IF EXISTS ix_knowledge_documents_embedding_ivfflat")

    # 2. embedding 컬럼 타입 변경 (768 -> 1024)
    op.execute("ALTER TABLE knowledge_documents ALTER COLUMN embedding TYPE vector(1024)")

    # 3. 기존 임베딩 데이터 NULL로 초기화 (재생성 필요)
    op.execute("UPDATE knowledge_documents SET embedding = NULL")

    # 4. 새로운 인덱스 생성 (1024차원)
    op.execute("""
        CREATE INDEX ix_knowledge_documents_embedding_ivfflat
        ON knowledge_documents
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)


def downgrade() -> None:
    """
    롤백: 1024 → 768
    """

    # 1. 인덱스 삭제
    op.execute("DROP INDEX IF EXISTS ix_knowledge_documents_embedding_ivfflat")

    # 2. embedding 컬럼 타입 변경 (1024 -> 768)
    op.execute("ALTER TABLE knowledge_documents ALTER COLUMN embedding TYPE vector(768)")

    # 3. 임베딩 데이터 NULL로 초기화
    op.execute("UPDATE knowledge_documents SET embedding = NULL")

    # 4. 인덱스 재생성 (768차원)
    op.execute("""
        CREATE INDEX ix_knowledge_documents_embedding_ivfflat
        ON knowledge_documents
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)
