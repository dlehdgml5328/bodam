"""
Knowledge Document Ingestion Worker

PDF, Markdown, 텍스트 문서를 읽어서 청크로 분할하고
임베딩을 생성하여 knowledge_documents 테이블에 저장하는 Celery 태스크
"""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import session_scope
from src.integrations.together_ai import TogetherAIHttpClient
from src.models.knowledge_document import KnowledgeDocument
from src.monitoring.logging import get_logger

logger = get_logger(__name__)


# 문서 청킹 설정
DEFAULT_CHUNK_SIZE = 800  # 문자 단위
DEFAULT_CHUNK_OVERLAP = 100  # 겹침 크기
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # 1024 dimensions


class DocumentIngestor:
    """문서 수집 및 임베딩 생성 클래스"""

    def __init__(
        self,
        together_ai_client: Optional[TogetherAIHttpClient] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.together_ai = together_ai_client or TogetherAIHttpClient()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def ingest_file(
        self,
        file_path: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[uuid.UUID]:
        """
        단일 파일 수집

        Args:
            file_path: 파일 경로
            title: 문서 제목 (기본: 파일명)
            metadata: 추가 메타데이터

        Returns:
            생성된 문서 ID 리스트
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"[Ingestor] File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        # 파일 해시 계산 (중복 방지)
        file_hash = self._compute_file_hash(path)
        file_mtime = datetime.fromtimestamp(path.stat().st_mtime)

        # 이미 처리된 파일인지 확인 (해시 + 수정시각 기준)
        async with session_scope() as session:
            existing = await self._check_existing_document(
                session, source=str(path), file_hash=file_hash
            )
            if existing:
                logger.info(f"[Ingestor] File already ingested (skipping): {file_path}")
                return []

        # 텍스트 추출
        content = await self._extract_text(path)
        if not content.strip():
            logger.warning(f"[Ingestor] Empty content: {file_path}")
            return []

        # 청크 분할
        chunks = self._split_into_chunks(content)
        logger.info(f"[Ingestor] Split into {len(chunks)} chunks: {file_path}")

        # 문서 저장
        doc_ids = await self._save_chunks(
            source=str(path),
            title=title or path.stem,
            chunks=chunks,
            metadata={
                **(metadata or {}),
                "file_hash": file_hash,
                "file_mtime": file_mtime.isoformat(),
                "file_size": path.stat().st_size,
            },
        )

        logger.info(f"[Ingestor] Ingested {len(doc_ids)} chunks from {file_path}")
        return doc_ids

    async def ingest_directory(
        self,
        directory_path: str,
        extensions: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """
        디렉터리 전체 수집

        Args:
            directory_path: 디렉터리 경로
            extensions: 허용 확장자 (기본: [.pdf, .md, .txt])
            recursive: 재귀적 탐색 여부

        Returns:
            수집 결과 요약
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory_path}")

        if extensions is None:
            extensions = [".pdf", ".md", ".txt", ".markdown"]

        # 파일 목록 수집
        if recursive:
            files = [
                f
                for f in directory.rglob("*")
                if f.is_file() and f.suffix.lower() in extensions
            ]
        else:
            files = [
                f
                for f in directory.iterdir()
                if f.is_file() and f.suffix.lower() in extensions
            ]

        logger.info(f"[Ingestor] Found {len(files)} files in {directory_path}")

        success_count = 0
        failed_files: List[str] = []
        total_chunks = 0

        for file_path in files:
            try:
                doc_ids = await self.ingest_file(str(file_path))
                if doc_ids:
                    success_count += 1
                    total_chunks += len(doc_ids)
            except Exception as e:
                logger.error(f"[Ingestor] Failed to ingest {file_path}: {e}", exc_info=True)
                failed_files.append(str(file_path))

        return {
            "total_files": len(files),
            "success_count": success_count,
            "failed_count": len(failed_files),
            "failed_files": failed_files,
            "total_chunks": total_chunks,
        }

    def _compute_file_hash(self, path: Path) -> str:
        """파일 SHA256 해시 계산"""
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def _check_existing_document(
        self, session: AsyncSession, source: str, file_hash: str
    ) -> bool:
        """이미 수집된 문서인지 확인"""
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.source == source
        ).limit(1)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing and existing.doc_metadata:
            existing_hash = existing.doc_metadata.get("file_hash")
            if existing_hash == file_hash:
                return True

        return False

    async def _extract_text(self, path: Path) -> str:
        """파일에서 텍스트 추출"""
        extension = path.suffix.lower()

        if extension == ".pdf":
            return await self._extract_text_from_pdf(path)
        elif extension in [".md", ".markdown", ".txt"]:
            return path.read_text(encoding="utf-8")
        else:
            logger.warning(f"[Ingestor] Unsupported file type: {extension}")
            return ""

    async def _extract_text_from_pdf(self, path: Path) -> str:
        """PDF에서 텍스트 추출 (pdfplumber 사용)"""
        try:
            import pdfplumber  # type: ignore
        except ImportError:
            logger.error("[Ingestor] pdfplumber not installed. Run: pip install pdfplumber")
            return ""

        text_parts: List[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n\n".join(text_parts)

    def _split_into_chunks(self, content: str) -> List[str]:
        """
        텍스트를 청크로 분할

        겹침(overlap)을 두어 컨텍스트가 끊기지 않도록 함
        """
        chunks: List[str] = []
        start = 0

        while start < len(content):
            end = start + self.chunk_size
            chunk = content[start:end]

            if chunk.strip():
                chunks.append(chunk)

            start += self.chunk_size - self.chunk_overlap

        return chunks

    async def _save_chunks(
        self,
        source: str,
        title: str,
        chunks: List[str],
        metadata: Dict[str, Any],
    ) -> List[uuid.UUID]:
        """
        청크를 DB에 저장하고 임베딩 생성

        Args:
            source: 문서 출처
            title: 문서 제목
            chunks: 텍스트 청크 리스트
            metadata: 메타데이터

        Returns:
            생성된 문서 ID 리스트
        """
        doc_ids: List[uuid.UUID] = []

        async with session_scope() as session:
            for i, chunk_content in enumerate(chunks):
                # 임베딩 생성
                try:
                    embedding_vector = await self._generate_embedding(chunk_content)
                except Exception as e:
                    logger.error(f"[Ingestor] Embedding generation failed for chunk {i}: {e}")
                    embedding_vector = None

                # 문서 생성
                doc = KnowledgeDocument(
                    id=uuid.uuid4(),
                    source=source,
                    title=title,
                    content=chunk_content,
                    doc_metadata=metadata,
                    embedding=embedding_vector.tolist() if embedding_vector is not None else None,
                    chunk_index=i,
                )

                session.add(doc)
                doc_ids.append(doc.id)

            await session.commit()

        return doc_ids

    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Together AI로 임베딩 생성"""
        embedding, _ = await self.together_ai.create_embedding(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return np.array(embedding, dtype=float)


@shared_task(name="knowledge.ingest_file", bind=True)
def ingest_file_task(
    self,
    file_path: str,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    단일 파일 수집 태스크

    Args:
        file_path: 파일 경로
        title: 문서 제목 (선택)
        metadata: 추가 메타데이터 (선택)

    Returns:
        수집 결과 (doc_ids, status 등)
    """
    import asyncio

    logger.info(f"[IngestTask] Starting file ingestion: {file_path}")

    try:
        ingestor = DocumentIngestor()
        doc_ids = asyncio.run(ingestor.ingest_file(file_path, title, metadata))

        result = {
            "status": "success",
            "file_path": file_path,
            "doc_ids": [str(doc_id) for doc_id in doc_ids],
            "count": len(doc_ids),
        }

        logger.info(f"[IngestTask] Success: {file_path} ({len(doc_ids)} chunks)")
        return result

    except Exception as e:
        logger.error(f"[IngestTask] Failed: {file_path}: {e}", exc_info=True)
        return {
            "status": "failed",
            "file_path": file_path,
            "error": str(e),
        }


@shared_task(name="knowledge.ingest_directory", bind=True)
def ingest_directory_task(
    self,
    directory_path: str,
    extensions: Optional[List[str]] = None,
    recursive: bool = True,
) -> Dict[str, Any]:
    """
    디렉터리 수집 태스크

    Args:
        directory_path: 디렉터리 경로
        extensions: 허용 확장자 리스트 (선택)
        recursive: 재귀 탐색 여부 (기본: True)

    Returns:
        수집 결과 요약
    """
    import asyncio

    logger.info(f"[IngestTask] Starting directory ingestion: {directory_path}")

    try:
        ingestor = DocumentIngestor()
        result = asyncio.run(ingestor.ingest_directory(directory_path, extensions, recursive))

        result["status"] = "success"
        result["directory_path"] = directory_path

        logger.info(
            f"[IngestTask] Directory ingestion complete: "
            f"{result['success_count']}/{result['total_files']} files, "
            f"{result['total_chunks']} chunks"
        )

        return result

    except Exception as e:
        logger.error(f"[IngestTask] Failed: {directory_path}: {e}", exc_info=True)
        return {
            "status": "failed",
            "directory_path": directory_path,
            "error": str(e),
        }


__all__ = ["DocumentIngestor", "ingest_file_task", "ingest_directory_task"]
