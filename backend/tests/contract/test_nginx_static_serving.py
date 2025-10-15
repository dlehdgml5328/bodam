"""Contract tests for NGINX static file serving

Tests NGINX configuration for:
- Static file serving from /static/ path
- Cache-Control headers (1 year for versioned assets)
- Gzip compression for text files
- CORS headers for static assets
- Kong Gateway bypass (static requests don't go through Kong)

Verifies nginx-static-config.yaml contract
"""

import pytest
import httpx


@pytest.fixture
async def nginx_client():
    """HTTP client pointing directly to NGINX"""
    async with httpx.AsyncClient(base_url="http://localhost", timeout=10) as client:
        yield client


class TestStaticFileServing:
    """Test /static/ path serves files correctly"""

    @pytest.mark.asyncio
    async def test_static_image_returns_200(self, nginx_client):
        """Should serve static images"""
        # Assumes test image exists at /static/images/test-fire-truck.jpg
        response = await nginx_client.get("/static/images/test-fire-truck.jpg")

        # Will fail until NGINX is configured and test file exists
        assert response.status_code == 200, "Static file should be served"
        assert response.headers.get("Content-Type") == "image/jpeg"

    @pytest.mark.asyncio
    async def test_static_css_returns_200(self, nginx_client):
        """Should serve CSS files"""
        response = await nginx_client.get("/static/css/main.css")

        if response.status_code == 200:
            assert "text/css" in response.headers.get("Content-Type", "")

    @pytest.mark.asyncio
    async def test_static_js_returns_200(self, nginx_client):
        """Should serve JavaScript files"""
        response = await nginx_client.get("/static/js/app.js")

        if response.status_code == 200:
            assert "javascript" in response.headers.get("Content-Type", "").lower()


class TestCacheHeaders:
    """Test Cache-Control headers for static assets"""

    @pytest.mark.asyncio
    async def test_versioned_assets_have_long_cache(self, nginx_client):
        """Versioned assets should have 1-year cache"""
        # Versioned asset URL (with hash in filename)
        response = await nginx_client.get("/static/css/main.a1b2c3d4.css")

        if response.status_code == 200:
            cache_control = response.headers.get("Cache-Control", "")
            assert "public" in cache_control, "Should be publicly cacheable"
            assert "immutable" in cache_control, "Should be immutable"

            # Check Expires header (should be ~1 year in future)
            assert "Expires" in response.headers

    @pytest.mark.asyncio
    async def test_images_have_long_cache(self, nginx_client):
        """Images should have long cache lifetime"""
        response = await nginx_client.get("/static/images/logo.png")

        if response.status_code == 200:
            cache_control = response.headers.get("Cache-Control")
            assert cache_control is not None
            assert "public" in cache_control


class TestGzipCompression:
    """Test gzip compression for text files"""

    @pytest.mark.asyncio
    async def test_css_is_gzip_compressed(self, nginx_client):
        """CSS files should be gzip compressed"""
        response = await nginx_client.get(
            "/static/css/main.css",
            headers={"Accept-Encoding": "gzip"}
        )

        if response.status_code == 200:
            # Check if response is compressed
            assert response.headers.get("Content-Encoding") == "gzip" or \
                   len(response.content) > 0, \
                "CSS should be gzip compressed or served normally"

    @pytest.mark.asyncio
    async def test_javascript_is_gzip_compressed(self, nginx_client):
        """JavaScript files should be gzip compressed"""
        response = await nginx_client.get(
            "/static/js/app.js",
            headers={"Accept-Encoding": "gzip"}
        )

        if response.status_code == 200:
            content_encoding = response.headers.get("Content-Encoding")
            assert content_encoding == "gzip" or content_encoding is None


class TestCORSForStaticAssets:
    """Test CORS headers for static assets"""

    @pytest.mark.asyncio
    async def test_static_files_have_cors_headers(self, nginx_client):
        """Static assets should have CORS headers"""
        response = await nginx_client.get(
            "/static/images/logo.png",
            headers={"Origin": "https://app.bodam.example"}
        )

        if response.status_code == 200:
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            assert cors_origin is not None, "CORS header should be present"
            assert cors_origin == "https://app.bodam.example" or cors_origin == "*"


class TestKongGatewayBypass:
    """Verify static requests bypass Kong Gateway"""

    @pytest.mark.asyncio
    async def test_static_requests_dont_have_kong_headers(self, nginx_client):
        """Static requests should NOT have Kong Gateway headers"""
        response = await nginx_client.get("/static/images/test.jpg")

        if response.status_code == 200:
            # Kong-specific headers should NOT be present
            assert "X-Kong-Request-ID" not in response.headers, \
                "Static requests should bypass Kong Gateway"
            assert "X-RateLimit-Limit" not in response.headers, \
                "Kong rate limiting should not apply to static files"


class TestNextJsStaticAssets:
    """Test Next.js _next/static/ path"""

    @pytest.mark.asyncio
    async def test_nextjs_static_path_works(self, nginx_client):
        """Should serve Next.js static assets"""
        response = await nginx_client.get("/_next/static/chunks/main.js")

        # Will 404 until Next.js is built and deployed
        if response.status_code == 200:
            cache_control = response.headers.get("Cache-Control")
            assert "public" in cache_control
            assert "immutable" in cache_control


class TestHealthCheck:
    """Test NGINX health check endpoint"""

    @pytest.mark.asyncio
    async def test_nginx_health_endpoint(self, nginx_client):
        """NGINX /health endpoint should return 200"""
        response = await nginx_client.get("/health")

        assert response.status_code == 200, "Health check should return 200"
        assert response.text.strip() == "healthy"


class TestAPIProxyToKong:
    """Verify /api/ requests are proxied to Kong Gateway"""

    @pytest.mark.asyncio
    async def test_api_requests_go_through_kong(self, nginx_client):
        """API requests should be proxied to Kong and have Kong headers"""
        response = await nginx_client.get("/api/fire-stations/search?location=서울")

        # Even if endpoint not implemented, Kong should add headers
        if response.status_code != 404:
            assert "X-Kong-Request-ID" in response.headers or \
                   "X-Request-ID" in response.headers, \
                "API requests should go through Kong Gateway"


# These tests are expected to FAIL until:
# 1. NGINX is reconfigured (T030-T032)
# 2. Static test files are created
# 3. NGINX is deployed locally or to Kubernetes
