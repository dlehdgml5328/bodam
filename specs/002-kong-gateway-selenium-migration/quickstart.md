# Quickstart: Kong Gateway & Selenium Crawler Integration Tests

**Date**: 2025-10-15
**Feature**: Kong Gateway 마이그레이션 및 Selenium 크롤러 전환

## Overview
이 문서는 Kong Gateway 라우팅과 Selenium 크롤러의 통합 테스트 시나리오를 정의합니다. 각 시나리오는 실제 사용자 스토리를 검증하며, 모든 테스트는 구현 전에 작성되어야 합니다 (TDD).

---

## Prerequisites

### Local Development Setup
```bash
# 1. Start infrastructure services
docker-compose up -d db redis

# 2. Apply database migrations
cd backend
alembic upgrade head

# 3. Start Kong Gateway (local mode)
docker run -d --name kong \
  --network bodam_default \
  -e "KONG_DATABASE=off" \
  -e "KONG_DECLARATIVE_CONFIG=/kong.yaml" \
  -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
  -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
  -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
  -p 8000:8000 \
  -p 8443:8443 \
  -p 8001:8001 \
  -v $(pwd)/specs/002-kong-gateway-selenium-migration/contracts/kong-gateway-routes.yaml:/kong.yaml \
  kong:3.5-alpine

# 4. Start NGINX (optional, for full stack testing)
docker run -d --name nginx \
  --network bodam_default \
  -p 443:443 \
  -p 80:80 \
  -v $(pwd)/specs/002-kong-gateway-selenium-migration/contracts/nginx-static-config.yaml:/etc/nginx/nginx.conf:ro \
  nginx:1.24-alpine

# 5. Install Selenium dependencies
pip install selenium webdriver-manager pytest-selenium

# 6. Start backend server
uvicorn src.main:app --reload
```

### Verification
```bash
# Check Kong Gateway health
curl -i http://localhost:8001/status

# Check backend health
curl -i http://localhost:8000/health

# Check NGINX health (if running)
curl -i http://localhost/health
```

---

## Test Scenarios

### Scenario 1: API Request Flow (NGINX → Kong → Backend)

**Given**: NGINX, Kong Gateway, and Backend are running
**When**: Client sends API request to NGINX
**Then**: Request flows through Kong Gateway to Backend with proper headers

#### Test Steps
```bash
# 1. Send request to NGINX (HTTPS endpoint)
curl -i -X GET https://localhost/api/fire-stations/search?location=서울 \
  -H "Authorization: Bearer <valid-jwt-token>"

# Expected: 200 OK
# Expected Headers:
#   X-Kong-Request-ID: <uuid>
#   X-RateLimit-Limit: 200
#   X-RateLimit-Remaining: 199

# 2. Verify Kong Gateway received request
curl -i http://localhost:8001/status/requests

# 3. Verify Backend logs show X-Kong-Request-ID header
docker logs bodam-backend | grep "X-Kong-Request-ID"
```

#### Automated Test (pytest)
```python
# tests/integration/test_kong_gateway_routing.py

import pytest
import httpx

@pytest.mark.asyncio
async def test_api_request_flows_through_kong():
    """Test that API requests flow through Kong Gateway to Backend"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Arrange: Get valid JWT token
        token = await get_test_jwt_token(client)

        # Act: Send request to Kong Gateway
        response = await client.get(
            "/api/fire-stations/search",
            params={"location": "서울"},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert: Response is successful
        assert response.status_code == 200

        # Assert: Kong Gateway headers are present
        assert "X-Kong-Request-ID" in response.headers
        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "200"

        # Assert: Response body matches expected schema
        data = response.json()
        assert "fire_stations" in data
        assert isinstance(data["fire_stations"], list)
```

---

### Scenario 2: Static File Served by NGINX (Bypass Kong)

**Given**: NGINX is serving static files from `/static/` directory
**When**: Client requests a static asset (CSS, JS, image)
**Then**: NGINX serves file directly without proxying to Kong Gateway

#### Test Steps
```bash
# 1. Place test image in static directory
mkdir -p frontend/public/static/images
cp test-fire-truck.jpg frontend/public/static/images/

# 2. Request static file through NGINX
curl -i http://localhost/static/images/test-fire-truck.jpg

# Expected: 200 OK
# Expected Headers:
#   Cache-Control: public, immutable
#   Expires: <1 year from now>
#   Content-Type: image/jpeg

# 3. Verify Kong Gateway did NOT receive this request
curl http://localhost:8001/status/requests | jq '.requests[] | select(.url | contains("/static/"))'
# Expected: Empty result (Kong should not see /static/ requests)
```

#### Automated Test (pytest)
```python
# tests/integration/test_nginx_static_serving.py

@pytest.mark.asyncio
async def test_static_files_bypass_kong_gateway():
    """Test that static files are served directly by NGINX"""
    async with httpx.AsyncClient(base_url="http://localhost") as client:
        # Act: Request static file
        response = await client.get("/static/images/test-fire-truck.jpg")

        # Assert: File is served successfully
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/jpeg"

        # Assert: Cache headers are set correctly
        assert "public" in response.headers["Cache-Control"]
        assert "immutable" in response.headers["Cache-Control"]

        # Assert: Kong Gateway was not involved
        # (Check Kong admin API for request logs)
        kong_admin = httpx.AsyncClient(base_url="http://localhost:8001")
        status = await kong_admin.get("/status")
        # Verify /static/ requests are not in Kong's metrics
```

---

### Scenario 3: Selenium Crawler Fetches Dynamic Content

**Given**: Selenium crawler service is running
**When**: A crawl job is submitted for a JavaScript-heavy page
**Then**: Crawler renders page with browser, extracts dynamic content

#### Test Steps
```bash
# 1. Create test HTML page with JavaScript content
cat > /tmp/test-dynamic-page.html <<EOF
<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
  <div id="static-content">Initial content</div>
  <div id="dynamic-content">Loading...</div>
  <script>
    setTimeout(() => {
      document.getElementById('dynamic-content').innerText = 'Dynamic content loaded!';
    }, 2000);
  </script>
</body>
</html>
EOF

# 2. Serve test page locally
python -m http.server 9000 --directory /tmp &

# 3. Submit crawl job
curl -X POST http://localhost:8000/api/crawler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:9000/test-dynamic-page.html",
    "browser_type": "chrome",
    "wait_conditions": {
      "type": "element_present",
      "selector": "#dynamic-content",
      "timeout_seconds": 10
    }
  }'

# Expected: 201 Created
# Response: { "id": "<job-id>", "status": "pending", ... }

# 4. Wait for job completion (poll status)
curl http://localhost:8000/api/crawler/jobs/<job-id>

# Expected after ~5 seconds: { "status": "completed", ... }

# 5. Retrieve crawled content
curl http://localhost:8000/api/crawler/content/<job-id>

# Expected:
# {
#   "extracted_data": {
#     "dynamic_content": "Dynamic content loaded!"
#   }
# }
```

#### Automated Test (pytest)
```python
# tests/integration/test_selenium_crawler.py

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.mark.asyncio
async def test_selenium_crawler_handles_dynamic_content():
    """Test that Selenium crawler waits for JavaScript-rendered content"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Arrange: Create crawl job
        response = await client.post(
            "/api/crawler/jobs",
            json={
                "url": "http://localhost:9000/test-dynamic-page.html",
                "browser_type": "chrome",
                "wait_conditions": {
                    "type": "element_present",
                    "selector": "#dynamic-content",
                    "timeout_seconds": 10
                }
            }
        )
        assert response.status_code == 201
        job_id = response.json()["id"]

        # Act: Wait for job to complete (with timeout)
        await wait_for_job_completion(client, job_id, timeout=30)

        # Assert: Job completed successfully
        job = await client.get(f"/api/crawler/jobs/{job_id}")
        assert job.json()["status"] == "completed"

        # Assert: Dynamic content was extracted
        content = await client.get(f"/api/crawler/content/{job_id}")
        extracted = content.json()["extracted_data"]
        assert "Dynamic content loaded!" in extracted["dynamic_content"]

@pytest.fixture
def chrome_driver():
    """Fixture to provide Selenium WebDriver for direct testing"""
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    yield driver

    driver.quit()

def test_selenium_webdriver_pool_reuse(chrome_driver):
    """Test that WebDriver pool efficiently reuses browser instances"""
    # Arrange: Navigate to first page
    chrome_driver.get("http://localhost:9000/test-page-1.html")
    session_id_1 = chrome_driver.session_id

    # Act: Clear state and navigate to second page (simulating pool reuse)
    chrome_driver.delete_all_cookies()
    chrome_driver.get("http://localhost:9000/test-page-2.html")
    session_id_2 = chrome_driver.session_id

    # Assert: Same browser instance was reused
    assert session_id_1 == session_id_2
```

---

### Scenario 4: Kong Gateway Rate Limiting

**Given**: Kong Gateway has rate limiting configured for API endpoints
**When**: Client exceeds rate limit (100 requests/minute)
**Then**: Kong Gateway returns 429 Too Many Requests

#### Test Steps
```bash
# 1. Send 101 requests within 1 minute
for i in {1..101}; do
  curl -i http://localhost:8000/api/donations \
    -H "Authorization: Bearer <valid-jwt>" \
    --silent | grep "HTTP/1.1"
done

# Expected:
# - First 100 requests: HTTP/1.1 200 OK
# - 101st request: HTTP/1.1 429 Too Many Requests

# 2. Check rate limit headers
curl -i http://localhost:8000/api/donations -H "Authorization: Bearer <valid-jwt>"

# Expected Headers:
#   X-RateLimit-Limit: 100
#   X-RateLimit-Remaining: 0
#   X-RateLimit-Reset: <timestamp>
#   Retry-After: 60
```

#### Automated Test (pytest)
```python
# tests/integration/test_kong_rate_limiting.py

@pytest.mark.asyncio
async def test_kong_rate_limiting_enforced():
    """Test that Kong Gateway enforces rate limits"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        token = await get_test_jwt_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Act: Send requests up to limit
        responses = []
        for _ in range(101):
            response = await client.get("/api/donations", headers=headers)
            responses.append(response)

        # Assert: First 100 succeed
        assert all(r.status_code == 200 for r in responses[:100])

        # Assert: 101st request is rate limited
        assert responses[100].status_code == 429
        assert "X-RateLimit-Limit" in responses[100].headers
        assert responses[100].headers["X-RateLimit-Remaining"] == "0"
```

---

### Scenario 5: TLS Termination at NGINX

**Given**: NGINX is configured with TLS certificates
**When**: Client sends HTTPS request
**Then**: NGINX terminates TLS, forwards HTTP request to Kong Gateway

#### Test Steps
```bash
# 1. Generate self-signed certificate for testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/nginx-selfsigned.key \
  -out /tmp/nginx-selfsigned.crt \
  -subj "/CN=localhost"

# 2. Mount certificates in NGINX container
docker exec nginx mkdir -p /etc/nginx/tls
docker cp /tmp/nginx-selfsigned.crt nginx:/etc/nginx/tls/tls.crt
docker cp /tmp/nginx-selfsigned.key nginx:/etc/nginx/tls/tls.key
docker exec nginx nginx -s reload

# 3. Send HTTPS request
curl -k -i https://localhost/api/fire-stations/search

# Expected: 200 OK
# Expected: Connection is encrypted (TLSv1.2 or TLSv1.3)

# 4. Verify Kong Gateway received HTTP (not HTTPS) request
docker logs kong | grep "GET /api/fire-stations/search HTTP/1.1"
# Expected: Request from NGINX to Kong is HTTP (internal network)
```

#### Automated Test (pytest)
```python
# tests/integration/test_nginx_tls_termination.py

@pytest.mark.asyncio
async def test_nginx_terminates_tls_to_kong():
    """Test that NGINX handles TLS, sends HTTP to Kong Gateway"""
    # Act: Send HTTPS request to NGINX
    async with httpx.AsyncClient(verify=False) as client:  # Ignore self-signed cert
        response = await client.get("https://localhost/api/fire-stations/search")

        # Assert: Request succeeded
        assert response.status_code == 200

        # Assert: HTTPS security headers are present
        assert "Strict-Transport-Security" in response.headers

    # Assert: Kong Gateway logs show HTTP request (not HTTPS)
    # (This would require log parsing or Kong admin API inspection)
```

---

## Running All Tests

### Single Command Execution
```bash
# Run all integration tests
cd backend
pytest tests/integration/ -v --tb=short

# Run specific scenario
pytest tests/integration/test_kong_gateway_routing.py -v

# Run with coverage
pytest tests/integration/ --cov=src --cov-report=html
```

### Expected Test Results
- **Total Scenarios**: 5
- **Test Cases**: ~10-15 (including edge cases)
- **Expected Duration**: 2-3 minutes (with Selenium)
- **Success Criteria**: All tests pass with 0 failures

---

## Troubleshooting

### Kong Gateway Issues
```bash
# Check Kong configuration
docker exec kong kong config parse /kong.yaml

# View Kong logs
docker logs kong -f

# Test Kong admin API
curl http://localhost:8001/routes
```

### Selenium Issues
```bash
# Check ChromeDriver version
chromedriver --version

# Test Selenium directly
python -c "from selenium import webdriver; driver = webdriver.Chrome(); driver.get('http://example.com'); print(driver.title); driver.quit()"

# Check browser process
ps aux | grep chrome
```

### NGINX Issues
```bash
# Test NGINX configuration
docker exec nginx nginx -t

# Reload NGINX
docker exec nginx nginx -s reload

# View NGINX logs
docker logs nginx -f
```

---

## Summary

| Scenario | Purpose | Key Validation |
|----------|---------|----------------|
| 1 | API routing through Kong | Request headers, rate limit headers |
| 2 | Static file serving | Cache headers, Kong bypass |
| 3 | Dynamic content crawling | JavaScript execution, wait conditions |
| 4 | Rate limiting | 429 response, retry headers |
| 5 | TLS termination | HTTPS to NGINX, HTTP to Kong |

**Status**: ✅ Quickstart complete, ready for implementation
