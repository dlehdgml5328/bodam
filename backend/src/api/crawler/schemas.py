"""Pydantic schemas for Crawler API"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class WaitConditions(BaseModel):
    """Wait conditions for page rendering"""
    type: str = Field(..., description="Wait condition type: element_present, element_visible, page_loaded, custom_script")
    selector: Optional[str] = Field(None, description="CSS selector or XPath")
    timeout_seconds: int = Field(30, ge=5, le=60, description="Wait timeout in seconds")
    script: Optional[str] = Field(None, description="Custom JavaScript for custom_script type")


class CreateCrawlJobRequest(BaseModel):
    """Request schema for creating crawl job"""
    url: HttpUrl = Field(..., max_length=2048, description="Target URL to crawl")
    browser_type: Optional[str] = Field("chrome", description="Browser type: chrome or firefox")
    wait_conditions: Optional[WaitConditions] = Field(None, description="Wait conditions before extraction")
    max_retries: Optional[int] = Field(3, ge=0, le=5, description="Maximum retry attempts")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CrawlJobResponse(BaseModel):
    """Response schema for crawl job"""
    id: UUID
    url: str
    browser_type: str
    status: str
    retry_count: int
    max_retries: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True


class CrawlJobDetailResponse(CrawlJobResponse):
    """Detailed crawl job response with wait conditions and errors"""
    wait_conditions: Optional[Dict[str, Any]]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]


class CrawlJobListResponse(BaseModel):
    """Paginated list of crawl jobs"""
    total: int
    limit: int
    offset: int
    jobs: List[CrawlJobResponse]


class CrawledContentResponse(BaseModel):
    """Response schema for crawled content"""
    id: UUID
    crawl_job_id: UUID
    source_url: str
    extracted_data: Dict[str, Any]
    screenshot_url: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
