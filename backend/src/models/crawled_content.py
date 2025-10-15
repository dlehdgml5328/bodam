"""CrawledContent model

Stores extracted content from Selenium crawl jobs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship

from src.models.base import Base


class CrawledContent(Base):
    """
    Crawled content model

    Stores the result of a successful crawl job, including:
    - Rendered HTML after JavaScript execution
    - Extracted structured data
    - Optional screenshot
    """

    __tablename__ = "crawled_contents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    crawl_job_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("selenium_crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source_url = Column(String(2048), nullable=False)
    rendered_html = Column(Text, nullable=True)
    extracted_data = Column(JSONB, nullable=False)
    screenshot_url = Column(String(2048), nullable=True)
    content_metadata = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationship to crawl job
    crawl_job = relationship("SeleniumCrawlJob", back_populates="crawled_contents")

    def __repr__(self) -> str:
        return f"<CrawledContent(id={self.id}, crawl_job_id={self.crawl_job_id}, source_url={self.source_url[:50]})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "crawl_job_id": str(self.crawl_job_id),
            "source_url": self.source_url,
            "extracted_data": self.extracted_data,
            "screenshot_url": self.screenshot_url,
            "content_metadata": self.content_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def has_screenshot(self) -> bool:
        """Check if content has screenshot"""
        return self.screenshot_url is not None

    @property
    def content_size(self) -> int:
        """Get approximate content size in bytes"""
        size = len(self.source_url)
        if self.rendered_html:
            size += len(self.rendered_html)
        if self.extracted_data:
            import json
            size += len(json.dumps(self.extracted_data))
        return size
