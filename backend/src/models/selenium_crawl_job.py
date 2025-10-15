"""SeleniumCrawlJob model

Represents a crawl job for Selenium WebDriver.
Status transitions: pending → running → completed/failed/timeout
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Text, CheckConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship

from src.database import Base


class JobStatus(str, enum.Enum):
    """Job status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class BrowserType(str, enum.Enum):
    """Supported browser types"""
    CHROME = "chrome"
    FIREFOX = "firefox"


class SeleniumCrawlJob(Base):
    """
    Selenium crawl job model

    Stores information about web crawling jobs using Selenium WebDriver.
    Jobs can be retried automatically if they fail.
    """

    __tablename__ = "selenium_crawl_jobs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    url = Column(String(2048), nullable=False, index=True)
    browser_type = Column(
        SQLEnum(BrowserType, name="browser_type_enum"),
        nullable=False,
        default=BrowserType.CHROME,
        server_default="chrome"
    )
    wait_conditions = Column(JSONB, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0, server_default="0")
    max_retries = Column(Integer, nullable=False, default=3, server_default="3")
    status = Column(
        SQLEnum(JobStatus, name="job_status_enum"),
        nullable=False,
        default=JobStatus.PENDING
    )
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)

    # Relationship to crawled content
    crawled_contents = relationship(
        "CrawledContent",
        back_populates="crawl_job",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("retry_count <= max_retries", name="ck_retry_limit"),
    )

    def __repr__(self) -> str:
        return f"<SeleniumCrawlJob(id={self.id}, url={self.url[:50]}, status={self.status})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
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
            "metadata": self.metadata,
        }

    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.retry_count < self.max_retries and self.status in [
            JobStatus.FAILED,
            JobStatus.TIMEOUT
        ]

    def mark_as_running(self) -> None:
        """Mark job as running"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_as_completed(self) -> None:
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.retry_count += 1

    def mark_as_timeout(self, error_message: str) -> None:
        """Mark job as timed out"""
        self.status = JobStatus.TIMEOUT
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.retry_count += 1

    def reset_for_retry(self) -> None:
        """Reset job status to pending for retry"""
        self.status = JobStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.error_message = None
