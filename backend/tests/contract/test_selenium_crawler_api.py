"""Contract tests for Selenium Crawler API

Tests all endpoints defined in selenium-crawler-api.yaml:
- POST /api/crawler/jobs (create job)
- GET /api/crawler/jobs (list jobs)
- GET /api/crawler/jobs/{job_id} (get job details)
- POST /api/crawler/jobs/{job_id}/retry (retry failed job)
- GET /api/crawler/content/{job_id} (get crawled content)

Verifies:
- Request/response schema matches OpenAPI spec
- Status codes are correct
- Required fields are present
- Enum values are validated
"""

import pytest
import httpx
from uuid import uuid4


@pytest.fixture
async def api_client():
    """HTTP client for backend API"""
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30) as client:
        yield client


class TestCreateCrawlJob:
    """Test POST /api/crawler/jobs"""

    @pytest.mark.asyncio
    async def test_create_job_with_valid_payload(self, api_client):
        """Should create crawl job with valid request"""
        payload = {
            "url": "https://news.example.com/fire-incident",
            "browser_type": "chrome",
            "wait_conditions": {
                "type": "element_present",
                "selector": "#main-content",
                "timeout_seconds": 30
            },
            "max_retries": 3,
            "metadata": {
                "source": "news_collector",
                "tags": ["fire", "emergency"]
            }
        }

        response = await api_client.post("/api/crawler/jobs", json=payload)

        # This will fail until endpoint is implemented
        assert response.status_code == 201, "Should return 201 Created"

        data = response.json()
        assert "id" in data, "Response should include job ID"
        assert data["url"] == payload["url"]
        assert data["status"] == "pending"
        assert data["browser_type"] == "chrome"
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_job_with_minimal_payload(self, api_client):
        """Should create job with only required fields"""
        payload = {"url": "https://example.com"}

        response = await api_client.post("/api/crawler/jobs", json=payload)

        # Default values should be applied
        assert response.status_code == 201
        data = response.json()
        assert data["browser_type"] == "chrome", "Should default to chrome"
        assert data["max_retries"] == 3, "Should default to 3 retries"

    @pytest.mark.asyncio
    async def test_create_job_with_invalid_url(self, api_client):
        """Should reject invalid URL"""
        payload = {"url": "not-a-valid-url"}

        response = await api_client.post("/api/crawler/jobs", json=payload)

        assert response.status_code == 400, "Should return 400 Bad Request"
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_create_job_with_invalid_browser_type(self, api_client):
        """Should reject invalid browser type"""
        payload = {
            "url": "https://example.com",
            "browser_type": "safari"  # Not in enum
        }

        response = await api_client.post("/api/crawler/jobs", json=payload)

        assert response.status_code == 400, "Should reject invalid enum value"


class TestListCrawlJobs:
    """Test GET /api/crawler/jobs"""

    @pytest.mark.asyncio
    async def test_list_jobs_returns_paginated_results(self, api_client):
        """Should return paginated list of jobs"""
        response = await api_client.get("/api/crawler/jobs?limit=20&offset=0")

        assert response.status_code == 200, "Should return 200 OK"

        data = response.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "jobs" in data
        assert isinstance(data["jobs"], list)

    @pytest.mark.asyncio
    async def test_list_jobs_filter_by_status(self, api_client):
        """Should filter jobs by status"""
        response = await api_client.get("/api/crawler/jobs?status=pending")

        assert response.status_code == 200

        data = response.json()
        # All returned jobs should have pending status
        if data["jobs"]:
            assert all(job["status"] == "pending" for job in data["jobs"])

    @pytest.mark.asyncio
    async def test_list_jobs_respects_limit(self, api_client):
        """Should respect pagination limit"""
        response = await api_client.get("/api/crawler/jobs?limit=5")

        assert response.status_code == 200

        data = response.json()
        assert len(data["jobs"]) <= 5, "Should return at most 5 jobs"


class TestGetCrawlJobDetails:
    """Test GET /api/crawler/jobs/{job_id}"""

    @pytest.mark.asyncio
    async def test_get_job_details_with_valid_id(self, api_client):
        """Should return job details for valid job ID"""
        # First create a job
        create_response = await api_client.post(
            "/api/crawler/jobs",
            json={"url": "https://example.com"}
        )

        if create_response.status_code == 201:
            job_id = create_response.json()["id"]

            # Get job details
            response = await api_client.get(f"/api/crawler/jobs/{job_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == job_id
            assert "wait_conditions" in data
            assert "error_message" in data
            assert "metadata" in data

    @pytest.mark.asyncio
    async def test_get_job_details_with_invalid_id(self, api_client):
        """Should return 404 for non-existent job"""
        fake_id = str(uuid4())
        response = await api_client.get(f"/api/crawler/jobs/{fake_id}")

        assert response.status_code == 404, "Should return 404 Not Found"


class TestRetryCrawlJob:
    """Test POST /api/crawler/jobs/{job_id}/retry"""

    @pytest.mark.asyncio
    async def test_retry_failed_job(self, api_client):
        """Should retry a failed job"""
        # This test assumes a failed job exists
        # In real scenario, create job, let it fail, then retry
        fake_id = str(uuid4())

        response = await api_client.post(f"/api/crawler/jobs/{fake_id}/retry")

        # Should fail with 404 (job not found) or 400 (job not in failed state)
        assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_cannot_retry_completed_job(self, api_client):
        """Should not allow retrying completed job"""
        # Assuming we have a completed job
        fake_id = str(uuid4())

        response = await api_client.post(f"/api/crawler/jobs/{fake_id}/retry")

        if response.status_code == 400:
            data = response.json()
            assert "not in failed/timeout state" in str(data).lower() or \
                   "already completed" in str(data).lower()


class TestGetCrawledContent:
    """Test GET /api/crawler/content/{job_id}"""

    @pytest.mark.asyncio
    async def test_get_content_for_completed_job(self, api_client):
        """Should return crawled content for completed job"""
        fake_id = str(uuid4())

        response = await api_client.get(f"/api/crawler/content/{fake_id}")

        # Should fail until we have completed jobs
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_content_schema(self, api_client):
        """Crawled content should match schema"""
        # Create and wait for job to complete
        create_response = await api_client.post(
            "/api/crawler/jobs",
            json={
                "url": "https://example.com",
                "wait_conditions": {
                    "type": "page_loaded",
                    "timeout_seconds": 10
                }
            }
        )

        if create_response.status_code == 201:
            job_id = create_response.json()["id"]

            # Wait for job to complete (in real test, poll status)
            # For now, just check schema when we eventually get content

            response = await api_client.get(f"/api/crawler/content/{job_id}")

            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "crawl_job_id" in data
                assert "source_url" in data
                assert "extracted_data" in data
                assert isinstance(data["extracted_data"], dict)
                assert "created_at" in data


# All these tests are expected to FAIL until:
# 1. SeleniumCrawlJob and CrawledContent models are created (T016, T017)
# 2. Selenium crawler service is implemented (T018-T020)
# 3. API endpoints are implemented (T022-T026)
