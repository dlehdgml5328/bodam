"""External news collector with Selenium crawler integration."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.selenium_crawl_job import SeleniumCrawlJob, JobStatus
from src.workers.selenium_crawler_worker import crawl_url

NEWS_ENDPOINT = "https://example.com/news"

# News sources that require JavaScript rendering
DYNAMIC_NEWS_SOURCES = [
    "https://news.naver.com",
    "https://n.news.naver.com",
    "https://www.yna.co.kr",
]


async def fetch_latest_news(limit: int = 10, db: Optional[AsyncSession] = None, use_selenium: bool = False) -> list[dict]:
    """
    Fetch latest news articles.

    If use_selenium=True and db session provided, creates Selenium crawl jobs
    for dynamic content sources. Otherwise, uses simple HTTP fetch.

    Args:
        limit: Maximum number of articles to fetch
        db: Database session for creating crawl jobs
        use_selenium: Whether to use Selenium for dynamic sources

    Returns:
        List of news article dictionaries
    """
    if use_selenium and db:
        # Create crawl jobs for dynamic news sources
        jobs = []
        for url in DYNAMIC_NEWS_SOURCES[:limit]:
            job = SeleniumCrawlJob(
                url=url,
                wait_conditions={
                    "type": "element_present",
                    "selector": "article",
                    "timeout_seconds": 10
                },
                job_metadata={"source_type": "news", "collector": "news_collector"}
            )
            db.add(job)
            jobs.append(job)

        await db.commit()

        # Enqueue Celery tasks for async crawling
        for job in jobs:
            crawl_url.delay(str(job.id))

        return [
            {
                "title": f"News article from {job.url}",
                "content": "Content will be available after crawling completes",
                "source": job.url,
                "url": job.url,
                "published_at": datetime.utcnow().isoformat() + "Z",
                "crawl_job_id": str(job.id),
                "status": job.status.value
            }
            for job in jobs
        ]

    # Fallback to simple HTTP fetch (original behavior)
    async with httpx.AsyncClient(timeout=10) as client:
        await client.get(NEWS_ENDPOINT)
    return [
        {
            "title": "서울 강남구 화재",
            "content": "강남구 소재 상가에서 화재가 발생했습니다.",
            "source": "naver_news",
            "url": "https://news.example.com/article",
            "published_at": datetime.utcnow().isoformat() + "Z",
        }
        for _ in range(limit)
    ]


async def check_crawl_job_status(job_id: UUID, db: AsyncSession) -> dict:
    """
    Check status of a Selenium crawl job.

    Args:
        job_id: UUID of the crawl job
        db: Database session

    Returns:
        Dictionary with job status and content (if completed)
    """
    job = await db.get(SeleniumCrawlJob, job_id)
    if not job:
        raise ValueError(f"Crawl job {job_id} not found")

    result = {
        "job_id": str(job.id),
        "url": job.url,
        "status": job.status.value,
        "created_at": job.created_at.isoformat(),
        "retry_count": job.retry_count,
        "error_message": job.error_message
    }

    if job.status == JobStatus.COMPLETED and job.content:
        result["content"] = {
            "extracted_data": job.content.extracted_data,
            "page_load_time_ms": job.content.page_load_time_ms
        }

    return result


__all__ = ["fetch_latest_news", "check_crawl_job_status"]
