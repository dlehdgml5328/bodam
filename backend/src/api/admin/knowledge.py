"""
Admin Knowledge Document API

RAG용 문서 관리 API 엔드포인트
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from src.database.connection import session_scope
from src.models.knowledge_document import KnowledgeDocument
from src.monitoring.logging import get_logger
from src.workers.knowledge_ingestor import ingest_directory_task, ingest_file_task

logger = get_logger(__name__)

router = APIRouter(prefix="/admin-api/knowledge", tags=["admin-knowledge"])


# Pydantic 모델
class DocumentMetadata(BaseModel):
    """문서 메타데이터"""
    doc_id: UUID = Field(..., description="문서 ID")
    source: str = Field(..., description="문서 출처")
    title: str = Field(..., description="문서 제목")
    section: Optional[str] = Field(None, description="문서 섹션")
    chunk_index: int = Field(..., description="청크 인덱스")
    created_at: str = Field(..., description="생성 시각")


class DocumentListResponse(BaseModel):
    """문서 목록 응답"""
    total: int = Field(..., description="전체 문서 수")
    documents: List[DocumentMetadata] = Field(..., description="문서 목록")


class DocumentDetailResponse(BaseModel):
    """문서 상세 응답"""
    doc_id: UUID = Field(..., description="문서 ID")
    source: str = Field(..., description="문서 출처")
    title: str = Field(..., description="문서 제목")
    section: Optional[str] = Field(None, description="문서 섹션")
    content: str = Field(..., description="문서 내용")
    chunk_index: int = Field(..., description="청크 인덱스")
    metadata: Optional[dict] = Field(None, description="추가 메타데이터")
    created_at: str = Field(..., description="생성 시각")


class IngestRequest(BaseModel):
    """수집 요청"""
    path: str = Field(..., description="파일 또는 디렉터리 경로")
    title: Optional[str] = Field(None, description="문서 제목 (파일만)")
    recursive: bool = Field(True, description="재귀 탐색 (디렉터리만)")


class IngestResponse(BaseModel):
    """수집 응답"""
    status: str = Field(..., description="수집 상태")
    task_id: str = Field(..., description="Celery 태스크 ID")
    message: str = Field(..., description="메시지")


class SuccessResponse(BaseModel):
    """성공 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field(..., description="메시지")


class EmbedAllResponse(BaseModel):
    """전체 임베딩 생성 응답"""
    total_files: int = Field(..., description="전체 파일 수")
    processed: int = Field(..., description="처리된 파일 수")
    failed: int = Field(..., description="실패한 파일 수")
    skipped: int = Field(..., description="건너뛴 파일 수 (이미 임베딩 있음)")
    details: List[dict] = Field(..., description="처리 상세 내역")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    source_filter: Optional[str] = None,
) -> DocumentListResponse:
    """
    문서 목록 조회

    **Query Parameters**:
    - skip: 건너뛸 개수 (기본: 0)
    - limit: 최대 개수 (기본: 50, 최대: 100)
    - source_filter: 출처 필터 (부분 일치)

    **Example Response**:
    ```json
    {
        "total": 42,
        "documents": [
            {
                "doc_id": "550e8400-e29b-41d4-a716-446655440000",
                "source": "data/knowledge_base/pdfs/manual.pdf",
                "title": "운영 매뉴얼",
                "section": "제1장",
                "chunk_index": 0,
                "created_at": "2025-10-23T10:00:00Z"
            }
        ]
    }
    ```
    """
    try:
        if limit > 100:
            limit = 100

        async with session_scope() as session:
            # 전체 개수 조회
            count_stmt = select(func.count(KnowledgeDocument.id))
            if source_filter:
                count_stmt = count_stmt.where(KnowledgeDocument.source.ilike(f"%{source_filter}%"))

            total_result = await session.execute(count_stmt)
            total = total_result.scalar() or 0

            # 문서 목록 조회
            stmt = select(KnowledgeDocument).offset(skip).limit(limit).order_by(KnowledgeDocument.created_at.desc())
            if source_filter:
                stmt = stmt.where(KnowledgeDocument.source.ilike(f"%{source_filter}%"))

            result = await session.execute(stmt)
            docs = result.scalars().all()

        documents = [
            DocumentMetadata(
                doc_id=doc.id,
                source=doc.source,
                title=doc.title,
                section=doc.section,
                chunk_index=doc.chunk_index,
                created_at=doc.created_at.isoformat(),
            )
            for doc in docs
        ]

        return DocumentListResponse(total=total, documents=documents)

    except Exception as e:
        logger.error(f"[KnowledgeAPI] Failed to list documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 목록 조회 중 오류가 발생했습니다.",
        ) from e


@router.get("/documents/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: UUID) -> DocumentDetailResponse:
    """
    문서 상세 조회

    **Path Parameters**:
    - doc_id: 문서 ID (UUID)

    **Example Response**:
    ```json
    {
        "doc_id": "550e8400-e29b-41d4-a716-446655440000",
        "source": "data/knowledge_base/pdfs/manual.pdf",
        "title": "운영 매뉴얼",
        "section": "제1장",
        "content": "운영 절차는 다음과 같습니다...",
        "chunk_index": 0,
        "metadata": {"file_hash": "abc123", "file_size": 1024},
        "created_at": "2025-10-23T10:00:00Z"
    }
    ```
    """
    try:
        async with session_scope() as session:
            stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
            result = await session.execute(stmt)
            doc = result.scalar_one_or_none()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"문서를 찾을 수 없습니다: {doc_id}",
            )

        return DocumentDetailResponse(
            doc_id=doc.id,
            source=doc.source,
            title=doc.title,
            section=doc.section,
            content=doc.content,
            chunk_index=doc.chunk_index,
            metadata=doc.doc_metadata,
            created_at=doc.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[KnowledgeAPI] Failed to get document {doc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 조회 중 오류가 발생했습니다.",
        ) from e


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest) -> IngestResponse:
    """
    문서 수집 시작 (Celery 태스크)

    **Request Body**:
    ```json
    {
        "path": "data/knowledge_base/pdfs",
        "title": "운영 매뉴얼",
        "recursive": true
    }
    ```

    **Example Response**:
    ```json
    {
        "status": "submitted",
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "문서 수집 태스크가 시작되었습니다."
    }
    ```
    """
    try:
        from pathlib import Path

        path = Path(request.path)

        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"경로를 찾을 수 없습니다: {request.path}",
            )

        # 파일인지 디렉터리인지 확인
        if path.is_file():
            # 단일 파일 수집
            task = ingest_file_task.delay(
                file_path=str(path),
                title=request.title,
            )
            message = f"파일 수집 태스크 시작: {path.name}"

        elif path.is_dir():
            # 디렉터리 수집
            task = ingest_directory_task.delay(
                directory_path=str(path),
                recursive=request.recursive,
            )
            message = f"디렉터리 수집 태스크 시작: {path.name} (recursive={request.recursive})"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="파일 또는 디렉터리만 지원합니다.",
            )

        logger.info(f"[KnowledgeAPI] Ingestion task started: {task.id} for {request.path}")

        return IngestResponse(
            status="submitted",
            task_id=task.id,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[KnowledgeAPI] Failed to start ingestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 수집 시작 중 오류가 발생했습니다.",
        ) from e


@router.delete("/documents/{doc_id}", response_model=SuccessResponse)
async def delete_document(doc_id: UUID) -> SuccessResponse:
    """
    문서 삭제

    **Path Parameters**:
    - doc_id: 문서 ID (UUID)

    **Example Response**:
    ```json
    {
        "success": true,
        "message": "문서가 삭제되었습니다."
    }
    ```
    """
    try:
        async with session_scope() as session:
            stmt = delete(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
            result = await session.execute(stmt)
            await session.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"문서를 찾을 수 없습니다: {doc_id}",
            )

        logger.info(f"[KnowledgeAPI] Document deleted: {doc_id}")

        return SuccessResponse(
            success=True,
            message="문서가 삭제되었습니다.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[KnowledgeAPI] Failed to delete document {doc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 삭제 중 오류가 발생했습니다.",
        ) from e


@router.delete("/documents", response_model=SuccessResponse)
async def delete_documents_by_source(source: str) -> SuccessResponse:
    """
    출처별 문서 일괄 삭제

    **Query Parameters**:
    - source: 삭제할 문서의 출처 (정확히 일치)

    **Example Response**:
    ```json
    {
        "success": true,
        "message": "3개의 문서가 삭제되었습니다."
    }
    ```
    """
    try:
        async with session_scope() as session:
            stmt = delete(KnowledgeDocument).where(KnowledgeDocument.source == source)
            result = await session.execute(stmt)
            await session.commit()

        deleted_count = result.rowcount

        logger.info(f"[KnowledgeAPI] Deleted {deleted_count} documents from source: {source}")

        return SuccessResponse(
            success=True,
            message=f"{deleted_count}개의 문서가 삭제되었습니다.",
        )

    except Exception as e:
        logger.error(f"[KnowledgeAPI] Failed to delete documents by source {source}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 삭제 중 오류가 발생했습니다.",
        ) from e


@router.post("/embed-all", response_model=EmbedAllResponse)
async def embed_all_documents() -> EmbedAllResponse:
    """
    knowledge_docs 폴더의 모든 파일에 대해 임베딩 생성

    이미 임베딩이 있는 파일은 건너뜁니다.

    **Example Response**:
    ```json
    {
        "total_files": 5,
        "processed": 3,
        "failed": 0,
        "skipped": 2,
        "details": [
            {
                "file": "document.pdf",
                "status": "success",
                "chunks": 3
            }
        ]
    }
    ```
    """
    try:
        import hashlib
        from pathlib import Path

        from src.workers.knowledge_ingestor import DocumentIngestor

        knowledge_dir = Path("/app/knowledge_docs")

        if not knowledge_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="knowledge_docs 디렉토리를 찾을 수 없습니다."
            )

        # 지원 파일 형식
        supported_extensions = {".pdf", ".md", ".txt"}
        files = [
            f for f in knowledge_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]

        total_files = len(files)
        processed = 0
        failed = 0
        skipped = 0
        details = []

        # 이미 처리된 파일 해시 조회
        async with session_scope() as session:
            stmt = select(KnowledgeDocument.doc_metadata).where(
                KnowledgeDocument.doc_metadata.isnot(None)
            )
            result = await session.execute(stmt)
            existing_hashes = {
                row[0].get("file_hash")
                for row in result
                if row[0] and "file_hash" in row[0]
            }

        ingestor = DocumentIngestor()

        for file_path in files:
            try:
                # 파일 해시 계산
                file_content = file_path.read_bytes()
                file_hash = hashlib.sha256(file_content).hexdigest()

                # 이미 처리된 파일인지 확인
                if file_hash in existing_hashes:
                    skipped += 1
                    details.append({
                        "file": file_path.name,
                        "status": "skipped",
                        "reason": "이미 임베딩 존재"
                    })
                    logger.info(f"[EmbedAll] Skipped (already exists): {file_path.name}")
                    continue

                # 임베딩 생성
                await ingestor.ingest_file(
                    str(file_path),
                    title=file_path.stem
                )

                processed += 1
                details.append({
                    "file": file_path.name,
                    "status": "success"
                })
                logger.info(f"[EmbedAll] Processed: {file_path.name}")

            except Exception as e:
                failed += 1
                details.append({
                    "file": file_path.name,
                    "status": "failed",
                    "error": str(e)
                })
                logger.error(f"[EmbedAll] Failed to process {file_path.name}: {e}")

        logger.info(
            f"[EmbedAll] Complete - Total: {total_files}, "
            f"Processed: {processed}, Failed: {failed}, Skipped: {skipped}"
        )

        return EmbedAllResponse(
            total_files=total_files,
            processed=processed,
            failed=failed,
            skipped=skipped,
            details=details
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[KnowledgeAPI] Failed to embed all documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전체 임베딩 생성 중 오류가 발생했습니다."
        ) from e


__all__ = ["router"]
