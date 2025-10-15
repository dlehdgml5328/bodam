"""Celery worker for Selenium crawler

Handles asynchronous crawl job execution.
"""

from __future__ import annotations

import logging
from uuid import UUID
from datetime import datetime

from src.worker import celery_app
from src.database import SessionLocal
from src.models.selenium_crawl_job import SeleniumCrawlJob, JobStatus
from src.models.crawled_content import CrawledContent
from src.services.crawler.selenium_crawler import SeleniumCrawler
from src.services.crawler.content_extractor import ContentExtractor

logger = logging.getLogger(__name__)


@celery_app.task(name="crawler.crawl_url", bind=True, max_retries=3)
def crawl_url(self, job_id: str):
    """
    Celery task: Crawl URL for given job ID

    Args:
        job_id: SeleniumCrawlJob UUID as string

    Returns:
        str: Result message
    """
    db = SessionLocal()

    try:
        # Load job from database
        job = db.query(SeleniumCrawlJob).filter(SeleniumCrawlJob.id == UUID(job_id)).first()

        if not job:
            logger.error(f"Job not found: {job_id}")
            return f"Job {job_id} not found"

        # Mark job as running
        job.mark_as_running()
        db.commit()

        logger.info(f"Starting crawl job {job_id}: {job.url}")

        # Crawl page with Selenium
        crawler = SeleniumCrawler()
        crawl_result = crawler.crawl(job)

        # Extract structured content
        extractor = ContentExtractor()
        page_type = job.metadata.get("page_type", "news") if job.metadata else "news"
        extracted_data = extractor.extract(
            html=crawl_result["html"],
            url=crawl_result["url"],
            page_type=page_type
        )

        # Save crawled content
        content = CrawledContent(
            crawl_job_id=job.id,
            source_url=crawl_result["url"],
            rendered_html=crawl_result["html"][:100000],  # Limit to 100KB
            extracted_data=extracted_data,
            metadata={
                "title": crawl_result.get("title"),
                "cookies_count": len(crawl_result.get("cookies", [])),
            }
        )
        db.add(content)

        # Mark job as completed
        job.mark_as_completed()
        db.commit()

        logger.info(f"Completed crawl job {job_id}")
        return f"Job {job_id} completed successfully"

    except Exception as e:
        logger.error(f"Error crawling job {job_id}: {e}")

        # Mark job as failed
        if job:
            job.mark_as_failed(str(e))
            db.commit()

            # Retry if retries remaining
            if job.can_retry():
                logger.info(f"Retrying job {job_id} (attempt {job.retry_count + 1})")
                raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds

        raise

    finally:
        db.close()


__all__ = ["crawl_url"]
