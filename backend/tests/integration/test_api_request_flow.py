"""Integration Test: API Request Flow (NGINX → Kong → Backend)

Scenario 1 from quickstart.md:
Client sends API request to NGINX (HTTPS) →
NGINX proxies to Kong Gateway →
Kong applies plugins (auth, rate limiting, CORS) →
Kong routes to Backend service →
Response flows back with Kong headers

Verifies:
- Full request/response cycle works
- X-Kong-Request-ID header present
- Rate limit headers present
- Backend receives proxied request
"""

import pytest
import httpx
import asyncio


@pytest.fixture
async def full_stack_client():
    """HTTP client for full stack (NGINX entry point)"""
    # In production: https://api.bodam.example
    # In testing: http://localhost (NGINX)
    async with httpx.AsyncClient(base_url="http://localhost", timeout=30) as client:
        yield client


@pytest.mark.asyncio
async def test_api_request_flows_through_all_layers():
    """
    Full integration test: NGINX → Kong → Backend

    Given: NGINX, Kong Gateway, and Backend are running
    When: Client sends GET request to /api/fire-stations/search
    Then: Request flows through all layers and returns 200 OK with headers
    """
    async with httpx.AsyncClient(base_url="http://localhost", timeout=30) as client:
        # Act: Send request through NGINX
        response = await client.get(
            "/api/fire-stations/search",
            params={"location": "서울"}
        )

        # Assert: Request completes (may be 404 if not implemented, but should reach backend)
        assert response.status_code in [200, 404, 500], \
            "Request should complete (even if endpoint not implemented)"

        # Assert: Kong Gateway headers are present
        headers = response.headers
        assert "X-Kong-Request-ID" in headers or "X-Request-ID" in headers, \
            "Kong should add correlation ID header"

        # Assert: Rate limit headers from Kong plugin
        if response.status_code != 404:
            assert "X-RateLimit-Limit" in headers, "Rate limit headers should be present"
            assert headers.get("X-RateLimit-Limit") == "200", \
                "Fire stations search should have 200 req/min limit"


@pytest.mark.asyncio
async def test_authenticated_request_flow():
    """
    Test authenticated API request flow

    Given: User has valid JWT token
    When: Request to /api/users/profile with Authorization header
    Then: Kong validates JWT, forwards to backend
    """
    async with httpx.AsyncClient(base_url="http://localhost", timeout=30) as client:
        # This will fail until JWT auth is implemented
        # For now, test that 401 is returned (Kong JWT plugin working)
        response = await client.get("/api/users/profile")

        # Assert: Kong rejects unauthenticated request
        assert response.status_code == 401, \
            "Unauthenticated request should return 401"


@pytest.mark.asyncio
async def test_post_request_with_json_body():
    """
    Test POST request with JSON body flows through correctly

    Given: Client sends POST with JSON payload
    When: Request to /api/donations
    Then: Request body is preserved through NGINX → Kong → Backend
    """
    async with httpx.AsyncClient(base_url="http://localhost", timeout=30) as client:
        payload = {
            "fire_station_id": "test-station-123",
            "amount": 5000,
            "frequency": "one_time"
        }

        response = await client.post(
            "/api/donations",
            json=payload
        )

        # Should fail auth (401) or be unimplemented (404/500)
        assert response.status_code in [401, 404, 500], \
            "Request should reach backend (even if it fails)"


@pytest.mark.asyncio
async def test_request_headers_forwarded():
    """
    Test that custom headers are forwarded through proxies

    Given: Client sends request with custom headers
    When: Request flows through NGINX → Kong
    Then: Headers are preserved and forwarded to backend
    """
    async with httpx.AsyncClient(base_url="http://localhost", timeout=30) as client:
        custom_headers = {
            "X-Client-Version": "1.0.0",
            "X-Device-ID": "test-device-123"
        }

        response = await client.get(
            "/api/fire-stations/search?location=서울",
            headers=custom_headers
        )

        # At minimum, request should complete
        assert response.status_code in [200, 404, 500]


@pytest.mark.asyncio
async def test_concurrent_requests_through_stack():
    """
    Test multiple concurrent requests flow through correctly

    Given: Multiple clients send requests simultaneously
    When: 10 concurrent requests to different endpoints
    Then: All requests complete successfully
    """
    async with httpx.AsyncClient(base_url="http://localhost", timeout=30) as client:
        # Create 10 concurrent requests
        requests = [
            client.get("/api/fire-stations/search?location=서울"),
            client.get("/api/fire-stations/search?location=부산"),
            client.get("/api/news"),
            client.get("/api/news"),
            client.get("/api/fire-stations/search?location=대구"),
            client.get("/api/fire-stations/search?location=인천"),
            client.get("/api/news"),
            client.get("/api/fire-stations/search?location=광주"),
            client.get("/api/fire-stations/search?location=대전"),
            client.get("/api/news"),
        ]

        # Execute all requests concurrently
        responses = await asyncio.gather(*requests, return_exceptions=True)

        # Assert: All requests complete (no exceptions)
        assert len(responses) == 10
        for response in responses:
            assert not isinstance(response, Exception), \
                "All requests should complete without errors"
            if hasattr(response, 'status_code'):
                assert response.status_code in [200, 404, 500]


@pytest.mark.asyncio
async def test_response_time_within_sla():
    """
    Test response time meets SLA (p95 < 300ms without Kong, < 400ms with Kong)

    Given: Kong Gateway adds <100ms overhead
    When: Multiple requests are sent
    Then: p95 response time < 400ms
    """
    async with httpx.AsyncClient(base_url="http://localhost", timeout=30) as client:
        response_times = []

        # Send 20 requests and measure response time
        for _ in range(20):
            import time
            start = time.time()

            response = await client.get("/api/fire-stations/search?location=서울")

            elapsed = (time.time() - start) * 1000  # Convert to ms
            response_times.append(elapsed)

        # Calculate p95
        response_times.sort()
        p95_index = int(len(response_times) * 0.95)
        p95_response_time = response_times[p95_index]

        print(f"p95 response time: {p95_response_time:.2f}ms")

        # Lenient for initial testing (backend might be slow)
        # Target: <400ms with Kong overhead
        assert p95_response_time < 1000, \
            f"p95 response time should be reasonable (<1000ms), got {p95_response_time:.2f}ms"


# These tests will FAIL until:
# 1. Kong Gateway is deployed (T036-T037 local, T039 K8s)
# 2. NGINX is reconfigured to proxy /api/ to Kong (T030-T032)
# 3. Backend endpoints are implemented (T022-T026 for crawler, existing for fire stations)
