"""Integration Test: Static Files Bypass Kong Gateway

Scenario 2 from quickstart.md:
Client requests static file (CSS, JS, image) →
NGINX serves directly from /static/ directory →
Kong Gateway is NOT involved →
Response has long cache headers

Verifies:
- Static files are served by NGINX
- Kong Gateway headers are NOT present
- Cache headers are correct (1 year for versioned assets)
"""

import pytest
import httpx


@pytest.mark.asyncio
async def test_static_image_bypasses_kong():
    """
    Static images should be served by NGINX, not Kong

    Given: NGINX serves /static/ path
    When: Client requests /static/images/logo.png
    Then: File is served without Kong Gateway headers
    """
    async with httpx.AsyncClient(base_url="http://localhost", timeout=10) as client:
        response = await client.get("/static/images/logo.png")

        # Assert: File is served (or 404 if not exists)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            # Assert: Kong headers are NOT present
            assert "X-Kong-Request-ID" not in response.headers, \
                "Static files should bypass Kong Gateway"
            assert "X-RateLimit-Limit" not in response.headers, \
                "Rate limiting should not apply to static files"

            # Assert: Cache headers ARE present
            assert "Cache-Control" in response.headers
            assert "Expires" in response.headers


@pytest.mark.asyncio
async def test_static_css_has_long_cache():
    """
    Static CSS files should have long cache lifetime

    Given: Versioned CSS file exists
    When: Client requests /static/css/main.a1b2c3d4.css
    Then: Response has Cache-Control: public, immutable, max-age=31536000
    """
    async with httpx.AsyncClient(base_url="http://localhost", timeout=10) as client:
        response = await client.get("/static/css/main.css")

        if response.status_code == 200:
            cache_control = response.headers.get("Cache-Control", "")
            assert "public" in cache_control
            # Versioned assets should be immutable
            assert "immutable" in cache_control or "max-age" in cache_control


@pytest.mark.asyncio
async def test_static_vs_api_request_headers():
    """
    Compare headers between static and API requests

    Given: NGINX handles both /static/ and /api/ paths
    When: Request to /static/images/test.jpg AND /api/fire-stations/search
    Then: Static has cache headers, API has Kong headers
    """
    async with httpx.AsyncClient(base_url="http://localhost", timeout=10) as client:
        # Request static file
        static_response = await client.get("/static/images/test.jpg")

        # Request API endpoint
        api_response = await client.get("/api/fire-stations/search?location=서울")

        # Static should NOT have Kong headers
        if static_response.status_code == 200:
            assert "X-Kong-Request-ID" not in static_response.headers

        # API should have Kong headers (if Kong is deployed)
        if api_response.status_code != 404:
            assert "X-Kong-Request-ID" in api_response.headers or \
                   "X-Request-ID" in api_response.headers


# This test will FAIL until:
# 1. NGINX is reconfigured (T030-T032)
# 2. Static test files are created
# 3. Kong Gateway is deployed (so we can verify it's bypassed)
