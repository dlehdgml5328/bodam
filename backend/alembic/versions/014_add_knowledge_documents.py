"""add knowledge_documents table for RAG

Revision ID: 014_add_knowledge_documents
Revises: 013_add_refunds_table
Create Date: 2025-10-23
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = "014_add_knowledge_documents"
down_revision = "013_add_refunds_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    knowledge_documents 테이블 생성
    - RAG(Retrieval-Augmented Generation)을 위한 문서 저장소
    - pgvector를 사용한 임베딩 기반 유사도 검색
    """
    op.create_table(
        "knowledge_documents",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("source", sa.Text(), nullable=False, comment="문서 출처 (파일명, URL 등)"),
        sa.Column("title", sa.Text(), nullable=False, comment="문서 제목"),
        sa.Column("section", sa.Text(), nullable=True, comment="문서 섹션/챕터"),
        sa.Column("content", sa.Text(), nullable=False, comment="문서 내용 (청크)"),
        sa.Column("metadata", sa.JSON(), nullable=True, comment="추가 메타데이터 (JSON)"),
        sa.Column(
            "embedding",
            Vector(768),  # Together AI m2-bert-80M-8k-retrieval 임베딩 차원
            nullable=True,
            comment="문서 임베딩 벡터 (768차원)",
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0", comment="청크 인덱스"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # 인덱스 생성
    op.create_index(
        "ix_knowledge_documents_source",
        "knowledge_documents",
        ["source"],
    )
    op.create_index(
        "ix_knowledge_documents_created_at",
        "knowledge_documents",
        ["created_at"],
    )

    # pgvector ivfflat 인덱스 (유사도 검색 최적화)
    # lists 파라미터는 행 수의 제곱근 정도가 권장 (100~1000 권장)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_documents_embedding_ivfflat
        ON knowledge_documents
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_documents_embedding_ivfflat")
    op.drop_index("ix_knowledge_documents_created_at", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_source", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
