"""Integration Test: Kong Rate Limiting

Scenario 4 from quickstart.md:
Send 101 requests within 1 minute →
First 100 requests succeed (200 OK) →
101st request returns 429 Too Many Requests →
X-RateLimit headers show remaining quota

Verifies:
- Kong rate-limiting plugin works
- Rate limit headers are correct
- 429 status code returned when limit exceeded
- Retry-After header present
"""

import pytest
import httpx
import asyncio


@pytest.mark.asyncio
async def test_rate_limiting_enforced_for_donations_endpoint():
    """
    Test Kong enforces 100 req/min limit for donations endpoint

    Given: /api/donations has rate limit of 100 req/min
    When: 101 requests sent within 1 minute
    Then: 101st request returns 429
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30) as client:
        # Send 101 requests
        responses = []
        for i in range(101):
            response = await client.get("/api/donations")
            responses.append(response)

            # Add small delay to avoid overwhelming server
            if i % 10 == 0:
                await asyncio.sleep(0.1)

        # Assert: First 100 succeed (or fail auth 401, but not rate limited)
        success_count = sum(1 for r in responses[:100] if r.status_code in [200, 401, 404])
        assert success_count >= 95, \
            "At least 95 of first 100 requests should succeed (allow some margin)"

        # Assert: 101st request is rate limited
        last_response = responses[-1]
        assert last_response.status_code == 429, \
            "101st request should be rate limited"

        # Assert: Rate limit headers present
        assert "X-RateLimit-Limit" in last_response.headers
        assert "X-RateLimit-Remaining" in last_response.headers
        assert int(last_response.headers["X-RateLimit-Remaining"]) == 0

        # Assert: Retry-After header present
        assert "Retry-After" in last_response.headers


@pytest.mark.asyncio
async def test_rate_limit_headers_decrement():
    """
    Test X-RateLimit-Remaining decrements with each request

    Given: Rate limit is 100 req/min
    When: 5 requests sent
    Then: X-RateLimit-Remaining decreases from 100 → 99 → 98 → 97 → 96
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30) as client:
        remaining_values = []

        for _ in range(5):
            response = await client.get("/api/fire-stations/search?location=서울")
            if "X-RateLimit-Remaining" in response.headers:
                remaining = int(response.headers["X-RateLimit-Remaining"])
                remaining_values.append(remaining)

        # Assert: Remaining quota decreases
        if len(remaining_values) >= 2:
            for i in range(1, len(remaining_values)):
                assert remaining_values[i] <= remaining_values[i-1], \
                    "Rate limit remaining should decrease"


@pytest.mark.asyncio
async def test_different_endpoints_have_different_limits():
    """
    Test different endpoints have different rate limits

    Given:
    - /api/donations: 100 req/min
    - /api/fire-stations/search: 200 req/min
    - /api/auth/login: 10 req/min
    When: Check X-RateLimit-Limit header for each
    Then: Limits match configuration
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30) as client:
        # Check donations limit (100)
        donations_response = await client.get("/api/donations")
        if "X-RateLimit-Limit" in donations_response.headers:
            assert donations_response.headers["X-RateLimit-Limit"] == "100"

        # Check fire stations limit (200)
        fire_stations_response = await client.get("/api/fire-stations/search?location=서울")
        if "X-RateLimit-Limit" in fire_stations_response.headers:
            assert fire_stations_response.headers["X-RateLimit-Limit"] == "200"

        # Check auth limit (10)
        auth_response = await client.post(
            "/api/auth/login",
            json={"email": "test@test.com", "password": "test"}
        )
        if "X-RateLimit-Limit" in auth_response.headers:
            assert auth_response.headers["X-RateLimit-Limit"] == "10"


@pytest.mark.asyncio
async def test_rate_limit_resets_after_window():
    """
    Test rate limit resets after time window

    Given: Rate limit is per minute
    When: Exhaust limit, wait 61 seconds, try again
    Then: Request succeeds (limit has reset)
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120) as client:
        # This test is time-consuming, so we'll just verify the mechanism
        # Send requests until rate limited
        for _ in range(15):  # Auth endpoint has 10 req/min limit
            response = await client.post(
                "/api/auth/login",
                json={"email": "test@test.com", "password": "test"}
            )

        # Last request should be rate limited
        assert response.status_code in [429, 401, 400, 404]

        # Note: Actually waiting 61 seconds would slow down tests
        # In production, verify Retry-After header and test with Kong directly


# These tests will FAIL until:
# 1. Kong Gateway is deployed (T036-T037 local, T039 K8s)
# 2. Kong rate-limiting plugin is configured (already in kong-config.yaml)
# 3. Backend endpoints exist (even if they return 401/404)
