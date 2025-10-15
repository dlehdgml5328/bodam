# Tasks: Kong Gateway 마이그레이션 및 Selenium 크롤러 전환

**Input**: Design documents from `/home/eugene/bodam/specs/002-kong-gateway-selenium-migration/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Loaded: Web application (backend + frontend + infra)
   → Tech stack: Kong Gateway 3.x, Selenium 4.15+, NGINX 1.24+
2. Load optional design documents:
   → ✅ data-model.md: 5 entities (KongRoute, SeleniumCrawlJob, CrawledContent, KongPlugin, NginxStaticConfig)
   → ✅ contracts/: 3 files (kong-gateway-routes.yaml, selenium-crawler-api.yaml, nginx-static-config.yaml)
   → ✅ research.md: Kong DB-less mode, Chrome headless, Canary migration
   → ✅ quickstart.md: 5 integration test scenarios
3. Generate tasks by category:
   → Setup: Dependencies, Alembic migration, Kong/NGINX configs
   → Tests: Contract tests (3), Integration tests (5)
   → Core: Database models, Selenium crawler service, Kong routes
   → Integration: Kong Gateway deployment, NGINX reconfiguration, migration
   → Polish: Performance tests, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T048)
6. Validate task completeness:
   → ✅ All contracts have tests
   → ✅ All entities have models
   → ✅ All endpoints implemented
7. Return: SUCCESS (48 tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app structure**: `backend/src/`, `frontend/src/`, `infra/k8s/`
- Paths shown below reflect actual project structure from plan.md

---

## Phase 3.1: Setup & Dependencies

### Infrastructure Setup
- [ ] **T001** Create Kong Gateway Kubernetes manifests directory `infra/k8s/kong/`
- [ ] **T002** Create NGINX reconfiguration directory `infra/k8s/nginx/`
- [ ] **T003** [P] Add Python dependencies to `backend/requirements.txt`: `selenium>=4.15.0`, `webdriver-manager>=4.0.0`
- [ ] **T004** [P] Install ChromeDriver setup script in `backend/scripts/install-chromedriver.sh`

### Database Migration
- [ ] **T005** Create Alembic migration file `backend/alembic/versions/002_add_selenium_crawler_tables.py` for `selenium_crawl_jobs` and `crawled_contents` tables

### Configuration Files
- [ ] **T006** [P] Copy Kong declarative config from `specs/002-kong-gateway-selenium-migration/contracts/kong-gateway-routes.yaml` to `infra/k8s/kong/kong-config.yaml`
- [ ] **T007** [P] Copy NGINX config from `specs/002-kong-gateway-selenium-migration/contracts/nginx-static-config.yaml` to `infra/k8s/nginx/nginx-configmap.yaml`

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (from contracts/)
- [ ] **T008** [P] Contract test for Kong Gateway routes in `backend/tests/contract/test_kong_gateway_routes.py`
  - Test all 10 routes defined in `kong-gateway-routes.yaml`
  - Verify rate limiting headers, CORS, JWT validation

- [ ] **T009** [P] Contract test for Selenium Crawler API in `backend/tests/contract/test_selenium_crawler_api.py`
  - Test POST `/api/crawler/jobs` (create job)
  - Test GET `/api/crawler/jobs/{job_id}` (get job status)
  - Test GET `/api/crawler/content/{job_id}` (get crawled content)
  - Test POST `/api/crawler/jobs/{job_id}/retry` (retry failed job)

- [ ] **T010** [P] Contract test for NGINX static file serving in `backend/tests/contract/test_nginx_static_serving.py`
  - Test `/static/` path returns correct Cache-Control headers
  - Test gzip compression for CSS/JS files
  - Verify Kong Gateway bypass for static files

### Integration Tests (from quickstart.md)
- [ ] **T011** [P] Integration test Scenario 1: API request flow (NGINX → Kong → Backend) in `backend/tests/integration/test_api_request_flow.py`
  - Verify X-Kong-Request-ID header propagation
  - Verify rate limit headers

- [ ] **T012** [P] Integration test Scenario 2: Static files bypass Kong in `backend/tests/integration/test_static_files_bypass.py`
  - Verify static assets served by NGINX
  - Verify 1-year cache headers

- [ ] **T013** [P] Integration test Scenario 3: Selenium dynamic content crawling in `backend/tests/integration/test_selenium_dynamic_crawling.py`
  - Test JavaScript-rendered content extraction
  - Test wait conditions (element_present, page_loaded)

- [ ] **T014** [P] Integration test Scenario 4: Kong rate limiting enforcement in `backend/tests/integration/test_kong_rate_limiting.py`
  - Send 101 requests, verify 429 on 101st
  - Verify X-RateLimit-Remaining headers

- [ ] **T015** [P] Integration test Scenario 5: NGINX TLS termination in `backend/tests/integration/test_nginx_tls_termination.py`
  - Verify HTTPS to NGINX, HTTP to Kong
  - Verify security headers (HSTS, X-Content-Type-Options)

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Database Models (from data-model.md)
- [ ] **T016** [P] Create `SeleniumCrawlJob` model in `backend/src/models/selenium_crawl_job.py`
  - Fields: id, url, browser_type, wait_conditions (JSONB), retry_count, max_retries, status (enum), timestamps
  - Status enum: pending, running, completed, failed, timeout

- [ ] **T017** [P] Create `CrawledContent` model in `backend/src/models/crawled_content.py`
  - Fields: id, crawl_job_id (FK), source_url, rendered_html, extracted_data (JSONB), screenshot_url, metadata (JSONB), created_at
  - Relationship: belongs_to SeleniumCrawlJob

### Selenium Crawler Service
- [ ] **T018** Create WebDriver pool manager in `backend/src/services/crawler/webdriver_pool.py`
  - Class `WebDriverPool` with acquire(), release(), cleanup() methods
  - Max pool size: 10 instances
  - Browser reset: delete cookies, clear storage between jobs

- [ ] **T019** Create Selenium crawler service in `backend/src/services/crawler/selenium_crawler.py`
  - Class `SeleniumCrawler` with crawl(job: SeleniumCrawlJob) method
  - Wait condition handlers: element_present, element_visible, page_loaded, custom_script
  - Error handling: TimeoutException, NoSuchElementException
  - Retry logic: max 3 retries with exponential backoff

- [ ] **T020** Create crawler result extractor in `backend/src/services/crawler/content_extractor.py`
  - Extract structured data from rendered HTML
  - Support for news articles (title, content, publish_date)
  - Screenshot capture (optional)

### Celery Worker for Crawler
- [ ] **T021** Create Celery task for crawl job execution in `backend/src/workers/selenium_crawler_worker.py`
  - Task: `crawl_url(job_id: UUID)`
  - Update job status: pending → running → completed/failed/timeout
  - Create CrawledContent record on success
  - Increment retry_count on failure

### API Endpoints (from selenium-crawler-api.yaml)
- [ ] **T022** POST `/api/crawler/jobs` endpoint in `backend/src/api/crawler/routes.py`
  - Create SeleniumCrawlJob record
  - Enqueue Celery task
  - Return 201 Created with job details

- [ ] **T023** GET `/api/crawler/jobs` endpoint (list with pagination)
  - Query parameters: status, limit, offset
  - Return paginated list of jobs

- [ ] **T024** GET `/api/crawler/jobs/{job_id}` endpoint (job details)
  - Return job with wait_conditions, error_message, metadata
  - Return 404 if not found

- [ ] **T025** POST `/api/crawler/jobs/{job_id}/retry` endpoint (manual retry)
  - Verify job is in failed/timeout state
  - Reset status to pending, enqueue task
  - Return 200 OK with updated job

- [ ] **T026** GET `/api/crawler/content/{job_id}` endpoint (get crawled content)
  - Return CrawledContent for completed job
  - Return 404 if job not completed or content not found

### Kong Gateway Configuration
- [ ] **T027** Create Kong Gateway Deployment YAML in `infra/k8s/kong/kong-deployment.yaml`
  - Image: kong:3.5-alpine
  - Environment: KONG_DATABASE=off, KONG_DECLARATIVE_CONFIG=/kong.yaml
  - Volume mount: kong-config ConfigMap
  - Ports: 8000 (proxy), 8001 (admin)

- [ ] **T028** Create Kong Gateway Service YAML in `infra/k8s/kong/kong-service.yaml`
  - Service name: kong-gateway
  - Ports: 8000, 8001
  - Selector: app=kong

- [ ] **T029** Create Kong Gateway ConfigMap YAML in `infra/k8s/kong/kong-configmap.yaml`
  - Mount `kong-config.yaml` from specs/002.../contracts/
  - Include all 10 routes with plugins

### NGINX Reconfiguration
- [ ] **T030** Create NGINX Deployment YAML in `infra/k8s/nginx/nginx-deployment.yaml`
  - Image: nginx:1.24-alpine
  - Volume mounts: nginx-config ConfigMap, TLS secret, static files volume
  - Ports: 80, 443

- [ ] **T031** Create NGINX Service YAML in `infra/k8s/nginx/nginx-service.yaml`
  - Type: LoadBalancer (or ClusterIP with Ingress)
  - Ports: 80, 443

- [ ] **T032** Update existing NGINX Ingress in `infra/k8s/backend/ingress.yaml`
  - Remove API routing rules (now handled by Kong)
  - Keep only static file serving rules
  - Add proxy_pass to Kong Gateway for `/api/*` paths

### TLS Certificate Management
- [ ] **T033** Create cert-manager Certificate resource in `infra/k8s/nginx/tls-certificate.yaml`
  - Domains: api.bodam.example, app.bodam.example
  - Issuer: letsencrypt-prod (ClusterIssuer)
  - Secret: bodam-tls-secret

---

## Phase 3.4: Integration & Migration

### Database Integration
- [ ] **T034** Run Alembic migration to create crawler tables
  - Execute: `alembic upgrade head`
  - Verify tables exist: `selenium_crawl_jobs`, `crawled_contents`
  - Verify indexes and constraints

### Crawler Integration
- [ ] **T035** Integrate Selenium crawler with existing news collector in `backend/src/collectors/news_collector.py`
  - Replace BeautifulSoup4 logic with SeleniumCrawler service
  - Update `fetch_latest_news()` to create CrawlJob records
  - Update return type to use CrawledContent model

### Kong Gateway Deployment (Local Testing)
- [ ] **T036** Deploy Kong Gateway locally with Docker Compose
  - Add Kong service to `docker-compose.yml`
  - Mount `kong-config.yaml`
  - Test Kong admin API: `curl http://localhost:8001/routes`

- [ ] **T037** Test Kong Gateway routing locally
  - Send test requests through Kong (port 8000)
  - Verify rate limiting, CORS, JWT plugins
  - Verify request logs in Kong output

### NGINX Local Testing
- [ ] **T038** Update local NGINX configuration for Kong upstream
  - Add Kong upstream to `infra/docker/nginx/nginx.conf` (if exists)
  - Test static file serving
  - Test API proxying to Kong

### Kubernetes Deployment (Staging)
- [ ] **T039** Deploy Kong Gateway to Kubernetes staging namespace
  - `kubectl apply -f infra/k8s/kong/`
  - Verify pods: `kubectl get pods -l app=kong`
  - Test Kong admin API: `kubectl port-forward svc/kong-gateway 8001:8001`

- [ ] **T040** Deploy updated NGINX to Kubernetes staging
  - `kubectl apply -f infra/k8s/nginx/`
  - Verify TLS certificate issued by cert-manager
  - Test HTTPS endpoint

### Migration Execution (Canary Deployment)
- [ ] **T041** Phase 1: Deploy Kong with 0% traffic (shadow mode)
  - Kong receives no traffic, only monitors
  - Monitor Kong resource usage (CPU, memory)
  - Duration: 1 week

- [ ] **T042** Phase 2: Route 10% traffic to Kong (low-traffic endpoints)
  - Update NGINX config: split_clients 10% to Kong
  - Monitor error rates, latency (target: p95 <300ms)
  - Rollback trigger: error rate >5% for 5 minutes
  - Duration: 48 hours

- [ ] **T043** Phase 3: Route 50% traffic to Kong (medium-traffic endpoints)
  - Update split_clients to 50%
  - Include user management, fire station search
  - Monitor donation endpoint (critical, not migrated yet)
  - Duration: 48 hours

- [ ] **T044** Phase 4: Route 100% traffic to Kong (full migration)
  - Update split_clients to 100%
  - Migrate donation endpoints (revenue-critical, last)
  - Monitor for 1 week

- [ ] **T045** Phase 5: Decommission old NGINX Ingress API routing
  - Remove API routing rules from old Ingress
  - Keep NGINX for static files + TLS only
  - Archive old Ingress config for rollback

---

## Phase 3.5: Polish & Validation

### Unit Tests
- [ ] **T046** [P] Unit tests for WebDriver pool in `backend/tests/unit/test_webdriver_pool.py`
  - Test pool initialization, acquire/release, cleanup
  - Test pool exhaustion (all 10 instances in use)

- [ ] **T047** [P] Unit tests for content extractor in `backend/tests/unit/test_content_extractor.py`
  - Test extraction of news articles from HTML
  - Test screenshot capture

### Performance & Load Testing
- [ ] **T048** [P] Performance test Kong Gateway overhead in `tests/performance/test_kong_overhead.sh`
  - Measure latency: Direct backend vs Kong Gateway
  - Target: <100ms p95 overhead
  - k6 load test: 1000 concurrent users

- [ ] **T049** [P] Performance test Selenium crawler throughput in `tests/performance/test_selenium_throughput.sh`
  - Measure: Jobs completed per minute
  - Target: 100+ concurrent crawl jobs
  - Memory usage: <2GB per Celery worker pod

### Documentation
- [ ] **T050** [P] Update API documentation in `docs/api.md`
  - Document new Selenium crawler endpoints
  - Document Kong Gateway plugin configurations
  - Document migration rollback procedure

---

## Dependencies

### Critical Path (Must be Sequential)
1. **Setup (T001-T007)** → All other tasks
2. **Alembic Migration (T005)** → Database Models (T016-T017)
3. **Tests (T008-T015)** → Core Implementation (T016-T026)
4. **Database Models (T016-T017)** → Crawler Service (T018-T020) → API Endpoints (T022-T026)
5. **Kong Config (T027-T029)** → Local Deployment (T036-T037) → K8s Deployment (T039)
6. **NGINX Config (T030-T032)** → Local Testing (T038) → K8s Deployment (T040)
7. **K8s Deployment (T039-T040)** → Migration Phases (T041-T045)
8. **Migration Complete (T045)** → Polish (T046-T050)

### Parallel Execution Groups
**Group 1: Setup & Config (can run in parallel)**
- T003, T004, T006, T007

**Group 2: Contract Tests (can run in parallel)**
- T008, T009, T010

**Group 3: Integration Tests (can run in parallel)**
- T011, T012, T013, T014, T015

**Group 4: Database Models (can run in parallel)**
- T016, T017

**Group 5: Kong & NGINX manifests (can run in parallel)**
- T027, T028, T029 (Kong)
- T030, T031, T032, T033 (NGINX)

**Group 6: Polish (can run in parallel)**
- T046, T047, T048, T049, T050

---

## Parallel Execution Examples

### Example 1: Run all contract tests together
```bash
# Launch T008-T010 in parallel
Task: "Contract test for Kong Gateway routes in backend/tests/contract/test_kong_gateway_routes.py"
Task: "Contract test for Selenium Crawler API in backend/tests/contract/test_selenium_crawler_api.py"
Task: "Contract test for NGINX static serving in backend/tests/contract/test_nginx_static_serving.py"
```

### Example 2: Run all integration tests together
```bash
# Launch T011-T015 in parallel
Task: "Integration test API request flow in backend/tests/integration/test_api_request_flow.py"
Task: "Integration test static files bypass in backend/tests/integration/test_static_files_bypass.py"
Task: "Integration test Selenium dynamic crawling in backend/tests/integration/test_selenium_dynamic_crawling.py"
Task: "Integration test Kong rate limiting in backend/tests/integration/test_kong_rate_limiting.py"
Task: "Integration test NGINX TLS termination in backend/tests/integration/test_nginx_tls_termination.py"
```

### Example 3: Deploy Kong and NGINX infrastructure in parallel
```bash
# Launch T027-T028-T029 and T030-T031-T032 in parallel (different services)
Task: "Create Kong Deployment in infra/k8s/kong/kong-deployment.yaml"
Task: "Create Kong Service in infra/k8s/kong/kong-service.yaml"
Task: "Create NGINX Deployment in infra/k8s/nginx/nginx-deployment.yaml"
Task: "Create NGINX Service in infra/k8s/nginx/nginx-service.yaml"
```

---

## Notes

### TDD Enforcement
- **All tests (T008-T015) MUST be written first and MUST FAIL** before implementing T016-T026
- Run tests after writing: `pytest backend/tests/contract/ backend/tests/integration/ -v`
- Expected: All tests should fail with "NotImplementedError" or "404 Not Found"

### Parallel Execution Rules
- **[P] tasks**: Different files, no shared dependencies, can run concurrently
- **Sequential tasks**: Same file modifications, dependent on previous task output
- **Example**: T016 and T017 are [P] (different model files), but T018 depends on T016 (needs SeleniumCrawlJob model)

### Migration Safety
- **Rollback Plan**: Keep old NGINX Ingress configuration for 2 weeks post-migration
- **Monitoring**: Prometheus alerts for error rate >5%, latency p95 >500ms
- **Canary Phases**: Each phase requires 48-hour stability before proceeding

### Commit Strategy
- Commit after each completed task
- Use task ID in commit message: `[T001] Create Kong Gateway manifests directory`
- Tag major milestones: `migration-phase-1-complete`, `migration-phase-2-complete`

---

## Validation Checklist

*GATE: Checked before marking tasks.md as complete*

- [x] All contracts have corresponding tests (T008-T010 cover all 3 contract files)
- [x] All entities have model tasks (T016-T017 cover SeleniumCrawlJob, CrawledContent)
- [x] All tests come before implementation (T008-T015 before T016-T026)
- [x] Parallel tasks truly independent (checked [P] markers)
- [x] Each task specifies exact file path (all tasks include file paths)
- [x] No task modifies same file as another [P] task (verified no conflicts)

---

## Summary

**Total Tasks**: 50 (T001-T050)
**Estimated Duration**: 6-8 weeks (including migration phases)

### Task Breakdown by Phase
- **Phase 3.1 (Setup)**: 7 tasks (T001-T007)
- **Phase 3.2 (Tests)**: 8 tasks (T008-T015)
- **Phase 3.3 (Core Implementation)**: 18 tasks (T016-T033)
- **Phase 3.4 (Integration & Migration)**: 12 tasks (T034-T045)
- **Phase 3.5 (Polish)**: 5 tasks (T046-T050)

### Parallel Execution Potential
- **Maximum Parallelism**: 5 tasks simultaneously (T011-T015 integration tests)
- **Critical Path Length**: ~30 sequential tasks (setup → tests → implementation → migration)
- **Time Savings**: ~40% reduction with parallel execution vs sequential

**Status**: ✅ Tasks ready for execution, TDD workflow enforced
