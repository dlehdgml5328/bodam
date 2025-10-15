"""Selenium 크롤 작업 모델

Selenium WebDriver를 사용한 크롤링 작업을 나타냅니다.
상태 전이: pending → running → completed/failed/timeout
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Text, CheckConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship

from src.models.base import Base


class JobStatus(str, enum.Enum):
    """작업 상태"""
    PENDING = "pending"      # 대기 중
    RUNNING = "running"      # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"        # 실패
    TIMEOUT = "timeout"      # 시간 초과


class BrowserType(str, enum.Enum):
    """지원되는 브라우저 타입"""
    CHROME = "chrome"
    FIREFOX = "firefox"


class SeleniumCrawlJob(Base):
    """
    Selenium 크롤 작업 모델

    Selenium WebDriver를 사용한 웹 크롤링 작업 정보를 저장합니다.
    실패 시 자동으로 재시도할 수 있습니다.
    """

    __tablename__ = "selenium_crawl_jobs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)  # 작업 ID
    url = Column(String(2048), nullable=False, index=True)  # 크롤링 대상 URL
    browser_type = Column(  # 브라우저 타입
        SQLEnum(BrowserType, name="browser_type_enum"),
        nullable=False,
        default=BrowserType.CHROME,
        server_default="chrome"
    )
    wait_conditions = Column(JSONB, nullable=True)  # 대기 조건 (JavaScript 실행 대기 등)
    retry_count = Column(Integer, nullable=False, default=0, server_default="0")  # 재시도 횟수
    max_retries = Column(Integer, nullable=False, default=3, server_default="3")  # 최대 재시도 횟수
    status = Column(  # 작업 상태
        SQLEnum(JobStatus, name="job_status_enum"),
        nullable=False,
        default=JobStatus.PENDING
    )
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)  # 생성 시간
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)  # 시작 시간
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)  # 완료 시간
    error_message = Column(Text, nullable=True)  # 오류 메시지
    job_metadata = Column(JSONB, nullable=True)  # 작업 메타데이터 (출처, 태그 등)

    # 크롤링된 콘텐츠와의 관계
    crawled_contents = relationship(
        "CrawledContent",
        back_populates="crawl_job",
        cascade="all, delete-orphan"
    )

    # 제약 조건
    __table_args__ = (
        CheckConstraint("retry_count <= max_retries", name="ck_retry_limit"),
    )

    def __repr__(self) -> str:
        return f"<SeleniumCrawlJob(id={self.id}, url={self.url[:50]}, status={self.status})>"

    def to_dict(self) -> Dict[str, Any]:
        """모델을 딕셔너리로 변환"""
        return {
            "id": str(self.id),
            "url": self.url,
            "browser_type": self.browser_type.value,
            "wait_conditions": self.wait_conditions,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "job_metadata": self.job_metadata,
        }

    def can_retry(self) -> bool:
        """작업 재시도 가능 여부 확인"""
        return self.retry_count < self.max_retries and self.status in [
            JobStatus.FAILED,
            JobStatus.TIMEOUT
        ]

    def mark_as_running(self) -> None:
        """작업을 실행 중으로 표시"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_as_completed(self) -> None:
        """작업을 완료로 표시"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        """작업을 실패로 표시"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.retry_count += 1

    def mark_as_timeout(self, error_message: str) -> None:
        """작업을 시간 초과로 표시"""
        self.status = JobStatus.TIMEOUT
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.retry_count += 1

    def reset_for_retry(self) -> None:
        """재시도를 위해 작업 상태를 pending으로 초기화"""
        self.status = JobStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.error_message = None
