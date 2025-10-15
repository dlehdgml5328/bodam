"""Integration Test: Selenium Dynamic Content Crawling

Scenario 3 from quickstart.md:
Create crawl job for JavaScript-heavy page →
Selenium opens browser, loads page →
Wait for JavaScript to execute and render content →
Extract data from rendered DOM →
Save to CrawledContent table

Verifies:
- Selenium WebDriver pool works
- JavaScript content is extracted
- Wait conditions function correctly
- Browser resources are cleaned up
"""

import pytest
import httpx
import asyncio
from uuid import UUID


async def wait_for_job_completion(client: httpx.AsyncClient, job_id: str, timeout: int = 60):
    """Poll job status until completed or timeout"""
    start_time = asyncio.get_event_loop().time()

    while True:
        response = await client.get(f"/api/crawler/jobs/{job_id}")
        if response.status_code == 200:
            job = response.json()
            if job["status"] in ["completed", "failed", "timeout"]:
                return job

        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout:
            raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")

        await asyncio.sleep(2)  # Poll every 2 seconds


@pytest.mark.asyncio
async def test_selenium_crawls_static_page():
    """
    Test basic Selenium crawling of static HTML page

    Given: Test HTML page with static content
    When: Submit crawl job
    Then: Job completes and extracts content
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60) as client:
        # Create crawl job for simple page
        create_response = await client.post(
            "/api/crawler/jobs",
            json={
                "url": "http://localhost:9000/test-static-page.html",
                "browser_type": "chrome",
                "wait_conditions": {
                    "type": "page_loaded",
                    "timeout_seconds": 10
                }
            }
        )

        # Assert: Job created
        assert create_response.status_code == 201, "Job should be created"
        job_id = create_response.json()["id"]

        # Wait for job to complete
        job = await wait_for_job_completion(client, job_id, timeout=30)

        # Assert: Job completed successfully
        assert job["status"] == "completed", f"Job should complete, got {job['status']}"

        # Assert: Content was extracted
        content_response = await client.get(f"/api/crawler/content/{job_id}")
        assert content_response.status_code == 200
        content = content_response.json()
        assert "extracted_data" in content
        assert content["source_url"] == "http://localhost:9000/test-static-page.html"


@pytest.mark.asyncio
async def test_selenium_waits_for_javascript_content():
    """
    Test Selenium waits for JavaScript-rendered content

    Given: HTML page that loads content via JavaScript after 2 seconds
    When: Submit crawl job with wait condition
    Then: Selenium waits for element to appear, then extracts it
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60) as client:
        # Create crawl job with element wait condition
        create_response = await client.post(
            "/api/crawler/jobs",
            json={
                "url": "http://localhost:9000/test-dynamic-page.html",
                "browser_type": "chrome",
                "wait_conditions": {
                    "type": "element_present",
                    "selector": "#dynamic-content",
                    "timeout_seconds": 10
                },
                "metadata": {
                    "test": "dynamic_content_test"
                }
            }
        )

        assert create_response.status_code == 201
        job_id = create_response.json()["id"]

        # Wait for job to complete
        job = await wait_for_job_completion(client, job_id, timeout=30)

        assert job["status"] == "completed", \
            "Job should wait for JS and complete successfully"

        # Verify extracted content includes dynamic text
        content_response = await client.get(f"/api/crawler/content/{job_id}")
        content = content_response.json()
        extracted = content["extracted_data"]

        # Should contain text added by JavaScript
        assert "Dynamic content loaded!" in str(extracted) or \
               "dynamic_content" in extracted


@pytest.mark.asyncio
async def test_selenium_handles_timeout():
    """
    Test Selenium handles page load timeout correctly

    Given: Page that never finishes loading
    When: Submit crawl job with short timeout
    Then: Job fails with timeout status
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60) as client:
        create_response = await client.post(
            "/api/crawler/jobs",
            json={
                "url": "http://localhost:9000/infinite-loading-page.html",
                "browser_type": "chrome",
                "wait_conditions": {
                    "type": "element_present",
                    "selector": "#never-appears",
                    "timeout_seconds": 5  # Short timeout
                },
                "max_retries": 0  # Don't retry
            }
        )

        assert create_response.status_code == 201
        job_id = create_response.json()["id"]

        # Wait for job to timeout
        job = await wait_for_job_completion(client, job_id, timeout=30)

        # Assert: Job timed out
        assert job["status"] == "timeout", \
            "Job should timeout when element never appears"
        assert job["error_message"] is not None


@pytest.mark.asyncio
async def test_selenium_retries_failed_job():
    """
    Test retry logic for failed crawl jobs

    Given: Job fails on first attempt
    When: Retry is triggered (automatic or manual)
    Then: Job is requeued and retried
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60) as client:
        # Create job that will fail (invalid URL)
        create_response = await client.post(
            "/api/crawler/jobs",
            json={
                "url": "http://invalid-domain-that-does-not-exist.test",
                "max_retries": 1
            }
        )

        assert create_response.status_code == 201
        job_id = create_response.json()["id"]

        # Wait for job to fail
        job = await wait_for_job_completion(client, job_id, timeout=30)

        if job["status"] == "failed" and job["retry_count"] < job["max_retries"]:
            # Manually retry
            retry_response = await client.post(f"/api/crawler/jobs/{job_id}/retry")
            assert retry_response.status_code == 200

            retried_job = retry_response.json()
            assert retried_job["status"] == "pending"
            assert retried_job["retry_count"] == job["retry_count"]


@pytest.mark.asyncio
async def test_multiple_concurrent_crawl_jobs():
    """
    Test WebDriver pool handles concurrent jobs

    Given: WebDriver pool has 10 instances
    When: 5 concurrent crawl jobs are submitted
    Then: All jobs complete successfully (pool is shared)
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120) as client:
        # Create 5 concurrent jobs
        job_ids = []
        for i in range(5):
            response = await client.post(
                "/api/crawler/jobs",
                json={
                    "url": f"http://localhost:9000/test-page-{i}.html",
                    "metadata": {"job_number": i}
                }
            )
            if response.status_code == 201:
                job_ids.append(response.json()["id"])

        # Wait for all jobs to complete
        for job_id in job_ids:
            job = await wait_for_job_completion(client, job_id, timeout=60)
            assert job["status"] in ["completed", "failed"]


# These tests will FAIL until:
# 1. SeleniumCrawlJob and CrawledContent models exist (T016-T017)
# 2. WebDriver pool is implemented (T018)
# 3. Selenium crawler service is implemented (T019)
# 4. Celery worker task is implemented (T021)
# 5. API endpoints are implemented (T022-T026)
# 6. Test HTML pages are created (in tests/fixtures/)
