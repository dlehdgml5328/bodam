"""Celery tasks orchestrating Selenium crawl jobs."""

from __future__ import annotations

import asyncio
import logging
from typing import Tuple
from uuid import UUID

from src.database import SessionLocal
from src.models.crawled_content import CrawledContent
from src.models.selenium_crawl_job import SeleniumCrawlJob
from src.services.crawler.content_extractor import ContentExtractor
from src.services.crawler.selenium_crawler import SeleniumCrawler
from src.worker import celery_app

logger = logging.getLogger(__name__)

_ASYNC_LOOP = None


def _run_async(coro):
    """Run coroutine on a dedicated event loop per worker process."""
    global _ASYNC_LOOP
    if _ASYNC_LOOP is None or _ASYNC_LOOP.is_closed():
        _ASYNC_LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_ASYNC_LOOP)
    return _ASYNC_LOOP.run_until_complete(coro)


async def _process_crawl_job(job_uuid: UUID) -> Tuple[str, bool, str]:
    """Execute crawl job inside an async DB session."""
    async with SessionLocal() as session:
        job = await session.get(SeleniumCrawlJob, job_uuid)

        if not job:
            logger.error("Crawl job not found: %s", job_uuid)
            return ("missing", False, f"Job {job_uuid} not found")

        job.mark_as_running()
        await session.commit()
        await session.refresh(job)

        logger.info("Starting crawl job %s: %s", job_uuid, job.url)

        crawler = SeleniumCrawler()
        extractor = ContentExtractor()

        try:
            crawl_result = crawler.crawl(job)

            page_type = (job.job_metadata or {}).get("page_type", "news")
            extracted_data = extractor.extract(
                html=crawl_result["html"],
                url=crawl_result["url"],
                page_type=page_type,
            )

            content = CrawledContent(
                crawl_job_id=job.id,
                source_url=crawl_result["url"],
                rendered_html=crawl_result["html"][:100000],
                extracted_data=extracted_data,
                metadata={
                    "title": crawl_result.get("title"),
                    "cookies_count": len(crawl_result.get("cookies", [])),
                },
            )
            session.add(content)

            job.mark_as_completed()
            await session.commit()

            logger.info("Completed crawl job %s", job_uuid)
            return ("completed", False, f"Job {job_uuid} completed successfully")

        except Exception as exc:
            logger.error("Error crawling job %s: %s", job_uuid, exc, exc_info=True)
            job.mark_as_failed(str(exc))
            await session.commit()
            return ("failed", job.can_retry(), str(exc))


@celery_app.task(name="crawler.crawl_url", bind=True, max_retries=3)
def crawl_url(self, job_id: str):
    """
    Celery task: Crawl URL for given job ID.
    """
    status, can_retry, message = _run_async(_process_crawl_job(UUID(job_id)))

    if status == "missing":
        return message

    if status == "failed":
        if can_retry:
            raise self.retry(exc=RuntimeError(message), countdown=60)
        raise RuntimeError(message)

    return message


async def _schedule_dynamic_news_jobs(limit: int) -> list[str]:
    """Create Selenium crawl jobs for dynamic news sources."""
    async with SessionLocal() as session:
        from src.collectors.news_collector import fetch_latest_news

        responses = await fetch_latest_news(
            limit=limit,
            db=session,
            use_selenium=True,
        )

        return [
            item["crawl_job_id"]
            for item in responses
            if item.get("crawl_job_id")
        ]


@celery_app.task(name="crawler.schedule_dynamic_news")
def schedule_dynamic_news(limit: int = 3) -> dict:
    """
    Periodic task: enqueue Selenium crawl jobs for dynamic news sources.
    """
    job_ids = _run_async(_schedule_dynamic_news_jobs(limit))

    if job_ids:
        logger.info("Scheduled %d Selenium news crawl jobs: %s", len(job_ids), job_ids)
    else:
        logger.info("No Selenium news crawl jobs scheduled (already pending/running)")

    return {"scheduled_jobs": job_ids}


__all__ = ["crawl_url", "schedule_dynamic_news"]
