"""Crawler API routes

Implements all 5 endpoints from selenium-crawler-api.yaml contract.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.selenium_crawl_job import SeleniumCrawlJob, JobStatus
from src.models.crawled_content import CrawledContent
from src.api.crawler.schemas import (
    CreateCrawlJobRequest,
    CrawlJobResponse,
    CrawlJobDetailResponse,
    CrawlJobListResponse,
    CrawledContentResponse,
)
from src.workers.selenium_crawler_worker import crawl_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crawler", tags=["crawler"])


@router.post("/jobs", response_model=CrawlJobResponse, status_code=201)
async def create_crawl_job(
    request: CreateCrawlJobRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new crawl job

    Creates a SeleniumCrawlJob and enqueues Celery task.
    """
    # Create job in database
    job = SeleniumCrawlJob(
        url=str(request.url),
        browser_type=request.browser_type,
        wait_conditions=request.wait_conditions.dict() if request.wait_conditions else None,
        max_retries=request.max_retries or 3,
        status=JobStatus.PENDING,
        metadata=request.metadata,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    logger.info(f"Created crawl job {job.id} for URL: {job.url}")

    # Enqueue Celery task
    crawl_url.delay(str(job.id))

    return job


@router.get("/jobs", response_model=CrawlJobListResponse)
async def list_crawl_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List crawl jobs with pagination

    Optionally filter by status.
    """
    query = db.query(SeleniumCrawlJob)

    # Filter by status if provided
    if status:
        try:
            job_status = JobStatus(status)
            query = query.filter(SeleniumCrawlJob.status == job_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    # Get total count
    total = query.count()

    # Paginate
    jobs = query.order_by(SeleniumCrawlJob.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "jobs": jobs,
    }


@router.get("/jobs/{job_id}", response_model=CrawlJobDetailResponse)
async def get_crawl_job(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get crawl job details

    Returns detailed information including wait_conditions and error_message.
    """
    job = db.query(SeleniumCrawlJob).filter(SeleniumCrawlJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return job


@router.post("/jobs/{job_id}/retry", response_model=CrawlJobResponse)
async def retry_crawl_job(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Manually retry a failed/timed-out job

    Resets job to pending status and re-enqueues Celery task.
    """
    job = db.query(SeleniumCrawlJob).filter(SeleniumCrawlJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Check if job can be retried
    if not job.can_retry():
        raise HTTPException(
            status_code=400,
            detail=f"Job cannot be retried (status={job.status}, retry_count={job.retry_count})"
        )

    # Reset job for retry
    job.reset_for_retry()
    db.commit()
    db.refresh(job)

    logger.info(f"Manually retrying job {job_id}")

    # Re-enqueue Celery task
    crawl_url.delay(str(job.id))

    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def cancel_crawl_job(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Cancel a pending or running crawl job

    Note: Cannot truly cancel a running Celery task,
    but marks job as cancelled in database.
    """
    job = db.query(SeleniumCrawlJob).filter(SeleniumCrawlJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.TIMEOUT]:
        raise HTTPException(
            status_code=409,
            detail=f"Job already completed/failed (status={job.status})"
        )

    # Mark as failed with cancellation message
    job.mark_as_failed("Cancelled by user")
    db.commit()

    logger.info(f"Cancelled job {job_id}")

    return None


@router.get("/content/{job_id}", response_model=CrawledContentResponse)
async def get_crawled_content(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get crawled content for completed job

    Returns extracted structured data.
    """
    # Check if job exists and is completed
    job = db.query(SeleniumCrawlJob).filter(SeleniumCrawlJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=404,
            detail=f"Content not available (job status={job.status})"
        )

    # Get crawled content
    content = db.query(CrawledContent).filter(CrawledContent.crawl_job_id == job_id).first()

    if not content:
        raise HTTPException(status_code=404, detail=f"Content not found for job {job_id}")

    return content
