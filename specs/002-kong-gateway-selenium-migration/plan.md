
# Implementation Plan: Kong Gateway 마이그레이션 및 Selenium 크롤러 전환

**Branch**: `wonuk` | **Date**: 2025-10-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/home/eugene/bodam/specs/002-kong-gateway-selenium-migration/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ Project Type: Web application (backend + frontend)
   → ✅ Structure Decision: Option 2 (backend/ + frontend/)
3. Fill the Constitution Check section
   → Constitution is template-based, using general principles
4. Evaluate Constitution Check section
   → In Progress
5. Execute Phase 0 → research.md
   → Pending
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → Pending
7. Re-evaluate Constitution Check section
   → Pending
8. Plan Phase 2 → Describe task generation approach
   → Pending
9. STOP - Ready for /tasks command
   → Pending
```

## Summary
NGINX Ingress 기반 아키텍처를 Kong Gateway + NGINX 하이브리드 구조로 마이그레이션하고, BeautifulSoup4 기반 정적 크롤러를 Selenium 기반 동적 크롤러로 전환합니다. NGINX는 HTTPS 터미네이션 및 정적 파일 서빙에 집중하고, Kong Gateway가 모든 API 라우팅, 인증, 레이트 리미팅, 로깅을 담당합니다. Selenium을 통해 JavaScript로 렌더링되는 동적 웹 콘텐츠를 수집할 수 있도록 크롤러를 개선합니다.

## Technical Context
**Language/Version**: Python 3.11+ (backend), TypeScript/Node.js 18+ (frontend)
**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy, Celery, Redis, selenium, webdriver-manager
- Infrastructure: Kong Gateway 3.x, NGINX 1.24+, Kubernetes
**Storage**: PostgreSQL + pgvector + PostGIS
**Testing**: pytest (backend), Jest + Playwright (frontend), k6 (performance)
**Target Platform**: Kubernetes (Linux containers)
**Project Type**: Web application (backend + frontend)
**Performance Goals**:
- API Gateway: <100ms p95 latency overhead
- Selenium Crawler: Handle 100+ concurrent crawl jobs
- Static files: <50ms p95 serving time
**Constraints**:
- Zero-downtime migration from NGINX Ingress to Kong Gateway
- Backward compatibility with existing API clients
- Selenium crawler memory usage <2GB per instance
- HTTPS/TLS certificates managed by cert-manager
**Scale/Scope**:
- 10k+ daily API requests
- 50+ Kong Gateway routes
- 1000+ daily crawl jobs
- Support for 100+ concurrent Selenium browser instances

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file is template-based. Using general software engineering principles:

### Core Principles Applied
1. **Test-First Development**: All Kong Gateway routes and Selenium crawlers will have integration tests before implementation
2. **Observability**: Structured logging for Kong Gateway plugins and Selenium crawler operations
3. **Simplicity**: Start with minimal Kong Gateway plugins, add complexity only when needed
4. **Backward Compatibility**: Existing NGINX Ingress routes must work during transition period

### Potential Violations & Justifications
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Additional infrastructure component (Kong) | Specialized API gateway features (advanced auth, rate limiting, plugin ecosystem) | NGINX Ingress lacks native support for complex API management patterns |
| Selenium resource overhead | Dynamic JavaScript content is business-critical for news/emergency data | BeautifulSoup cannot access client-side rendered content |

**Initial Assessment**: PASS with justified complexity additions

## Project Structure

### Documentation (this feature)
```
specs/002-kong-gateway-selenium-migration/
├── plan.md              # This file (/plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command)
```

### Source Code (repository root)
```
# Option 2: Web application (current structure)
backend/
├── src/
│   ├── models/
│   ├── services/
│   │   └── crawler/           # NEW: Selenium crawler service
│   ├── api/
│   ├── collectors/
│   │   └── news_collector.py  # MODIFIED: Use Selenium
│   └── workers/
└── tests/
    ├── contract/              # NEW: Kong Gateway route tests
    ├── integration/
    │   └── test_selenium_crawler.py  # NEW
    └── unit/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

infra/
├── k8s/
│   ├── backend/
│   │   └── ingress.yaml       # MODIFIED: Kong Gateway routes
│   ├── kong/                  # NEW: Kong Gateway configs
│   │   ├── kong-deployment.yaml
│   │   ├── kong-service.yaml
│   │   ├── kong-plugins.yaml
│   │   └── kong-routes.yaml
│   └── nginx/                 # MODIFIED: Static files + TLS only
│       ├── nginx-deployment.yaml
│       ├── nginx-configmap.yaml
│       └── nginx-service.yaml
└── ci-cd/
```

**Structure Decision**: Option 2 (Web application) - backend/ + frontend/ + infra/

## Phase 0: Outline & Research
*Status: Pending execution*

### Research Tasks to Execute
1. **Kong Gateway Architecture**
   - Decision needed: Kong Gateway deployment model (DB-less vs PostgreSQL)
   - Best practices: Kong plugin selection for auth, rate limiting, logging
   - Integration: Kong Gateway + Kubernetes Ingress patterns

2. **Selenium WebDriver Setup**
   - Decision needed: Browser choice (Chrome headless vs Firefox)
   - Best practices: WebDriver connection pooling and lifecycle management
   - Patterns: Selenium Grid vs standalone instances in Kubernetes

3. **NGINX Static File Optimization**
   - Decision needed: NGINX caching strategy for static files
   - Best practices: TLS termination with cert-manager integration
   - Patterns: NGINX upstream configuration for Kong Gateway

4. **Migration Strategy**
   - Decision needed: Blue-green vs canary deployment for Kong rollout
   - Best practices: Route migration sequence (low-traffic → high-traffic)
   - Rollback: NGINX Ingress fallback mechanism

**Output**: research.md with all decisions and rationale

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

### Artifacts to Generate

1. **data-model.md**
   - Entity: KongRoute (path, service, plugins, auth_required, rate_limit)
   - Entity: SeleniumCrawlJob (url, browser_type, wait_conditions, retry_count, status)
   - Entity: CrawledContent (source_url, rendered_html, extracted_data, metadata)
   - Relationships: CrawlJob → CrawledContent (one-to-many)

2. **contracts/** (API/Configuration Schemas)
   - `/contracts/kong-gateway-routes.yaml` - Kong Gateway declarative config
   - `/contracts/selenium-crawler-api.yaml` - OpenAPI spec for crawler service
   - `/contracts/nginx-static-config.yaml` - NGINX configuration for static serving

3. **quickstart.md** - Integration test scenarios:
   - Scenario 1: API request flows through NGINX → Kong → Backend
   - Scenario 2: Static file request served directly by NGINX
   - Scenario 3: Selenium crawler fetches dynamic content from test page
   - Scenario 4: Kong Gateway applies rate limiting to API endpoint
   - Scenario 5: TLS termination at NGINX for both static and API traffic

4. **CLAUDE.md** - Update with new technologies:
   - Add Kong Gateway commands and testing
   - Add Selenium + WebDriver setup
   - Update infrastructure deployment commands

**Output**: data-model.md, contracts/, failing tests, quickstart.md, updated CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate infrastructure tasks:
   - T001-T005: Kong Gateway deployment and configuration
   - T006-T010: NGINX reconfiguration for static files + TLS
   - T011-T015: Selenium crawler service implementation
3. Generate contract test tasks:
   - Each Kong route → contract test task [P]
   - Each Selenium crawler endpoint → contract test task [P]
4. Generate integration tasks:
   - End-to-end request flow tests
   - Migration validation tests
5. Generate migration tasks:
   - Staged rollout plan
   - Rollback procedures

**Ordering Strategy**:
- Phase 1: Infrastructure setup (Kong, NGINX reconfiguration)
- Phase 2: Selenium crawler implementation (parallel with Phase 1)
- Phase 3: Integration testing
- Phase 4: Staged migration
- Phase 5: Validation and rollback testing

**Estimated Output**: 40-50 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following TDD principles)
**Phase 5**: Validation (integration tests, performance benchmarks, migration dry-run)

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Kong Gateway (additional component) | Advanced API management: auth strategies, rate limiting per route, plugin ecosystem, centralized logging | NGINX Ingress lacks native support for per-route rate limiting and lacks plugin extensibility |
| Selenium (heavyweight crawler) | Business requirement: Dynamic JavaScript-rendered emergency news and fire data | BeautifulSoup cannot execute JavaScript or wait for async content loading |
| Dual proxy layer (NGINX + Kong) | NGINX: TLS termination + static files, Kong: API gateway | Single-layer solutions force compromise: Kong lacks NGINX static file performance, NGINX lacks Kong API features |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (with justified complexity)
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

**Artifacts Generated**:
- [x] plan.md - Implementation plan with technical context
- [x] research.md - Technology decisions and best practices
- [x] data-model.md - Entity definitions and relationships
- [x] contracts/kong-gateway-routes.yaml - Kong Gateway configuration
- [x] contracts/selenium-crawler-api.yaml - Selenium crawler API spec
- [x] contracts/nginx-static-config.yaml - NGINX static file configuration
- [x] quickstart.md - Integration test scenarios
- [x] CLAUDE.md - Updated with Kong Gateway and Selenium commands

---
*Based on general software engineering principles - See Constitution template for guidance*
