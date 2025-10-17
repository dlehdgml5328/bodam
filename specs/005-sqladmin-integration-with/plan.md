# Implementation Plan: SQLAdmin Integration with Llama AI Chat Interface

**Branch**: `005-sqladmin-integration-with` | **Date**: 2025-10-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/home/eugene/bodam/specs/005-sqladmin-integration-with/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✅
2. Fill Technical Context (scan for NEEDS CLARIFICATION) ✅
3. Fill the Constitution Check section ✅
4. Evaluate Constitution Check section → In Progress
5. Execute Phase 0 → research.md → Pending
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md → Pending
7. Re-evaluate Constitution Check section → Pending
8. Plan Phase 2 → Describe task generation approach → Pending
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phase 2 is executed by /tasks command.

## Summary

This feature adds a comprehensive admin panel using SQLAdmin for CRUD operations on all existing system entities (users, donations, fire stations, refunds) and integrates a Llama AI-powered chat interface that can query the Knowledge Graph, Semantic Cache, and all Celery-processed data (crawled news, AI analysis results, LangGraph matching scores). The admin panel is restricted to users with admin role and provides bulk refund processing, entity management, and an AI assistant for operational insights through natural language queries.

**Technical Approach**: Build on existing FastAPI infrastructure by adding SQLAdmin library for admin UI generation, create a custom Llama chat page within the admin panel, and integrate with existing Together AI client, Knowledge Graph (GraphClient), and Semantic Cache (Redis) to enable AI-powered queries across all system data including crawler results and LLM evaluation outputs.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- FastAPI >= 0.104.0 (existing)
- SQLAlchemy >= 2.0.0 with asyncpg (existing)
- **sqladmin >= 0.16.0** (NEW - for admin UI)
- httpx >= 0.25.0 (existing, for HTTP connection pool)
- Together AI SDK (existing, for Llama 3.3 70B)
- tenacity >= 8.2.0 (existing, for retry policy)

**Storage**:
- PostgreSQL 16 with pgvector extension (1536-dimensional embeddings) and PostGIS
- Redis (two instances: standard cache + semantic cache)
- Knowledge Graph (PostgreSQL-based, via GraphClient)

**Testing**: pytest with async support (pytest-asyncio)

**Target Platform**: Linux server (Kubernetes deployment)

**Project Type**: Web (backend FastAPI + frontend Next.js, this feature is backend-only)

**Performance Goals**:
- Admin panel page load < 2 seconds
- AI chat response < 10 seconds
- Semantic cache hit rate > 60% for similar queries

**Constraints**:
- Admin role only (UserRole.ADMIN)
- No new database tables (reuses all existing SQLAlchemy models)
- Must integrate with existing Kong Gateway rate limiting
- Session-based conversation context (not persisted to DB)
- Audit logging required for all admin actions and AI queries

**Scale/Scope**:
- ~12 main entities to manage (User, Donation, FireStation, Refund, NewsContent, NewsMatch, SeleniumCrawlJob, CrawledContent, etc.)
- ~50 functional requirements (FR-001 to FR-050)
- Expected admin users: 5-10 concurrent

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Constitutional Principles (from CLAUDE.md)

✅ **TDD Mandatory**: Tests first, then implementation
- Contract tests for admin API endpoints
- Integration tests for admin UI pages
- Unit tests for Llama chat service

✅ **Korean Comments**: Preferred for documentation
- All new code comments in Korean
- API documentation in Korean

✅ **FastAPI + SQLAlchemy 2.0 Async Patterns**: Required
- Use async/await throughout
- Leverage existing database connection pool
- Follow existing service patterns

✅ **Library-First Approach**: Prefer libraries over custom code
- Use SQLAdmin library (not custom admin UI)
- Reuse existing TogetherAIHttpClient
- Reuse existing GraphClient and semantic cache

✅ **No New Data Entities**: Reuse existing models
- All CRUD operations on existing tables
- No migrations required for this feature

✅ **Observability**: Structured logging and audit trails
- Log all admin actions with user identity
- Log all AI chat queries and responses
- Integrate with existing structlog setup

### Constitutional Violations: **NONE**

This feature aligns with all constitutional principles:
- Uses library-first approach (SQLAdmin)
- Reuses existing infrastructure (FastAPI, SQLAlchemy, Together AI, GraphClient, Semantic Cache)
- No new database tables
- TDD approach with contract/integration/unit tests
- Korean comments and documentation

## Project Structure

### Documentation (this feature)
```
specs/005-sqladmin-integration-with/
├── spec.md              # Feature specification (✅ complete)
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (pending)
├── data-model.md        # Phase 1 output (pending)
├── quickstart.md        # Phase 1 output (pending)
├── contracts/           # Phase 1 output (pending)
│   ├── admin-ui-routes.yaml          # SQLAdmin page routes
│   ├── admin-chat-api.yaml           # Llama chat API contract
│   └── admin-refund-actions.yaml     # Bulk refund API contract
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── admin/                        # 🆕 NEW - Admin panel code
│   │   ├── __init__.py
│   │   ├── auth.py                   # Admin authentication
│   │   ├── config.py                 # SQLAdmin configuration
│   │   ├── views/                    # SQLAdmin ModelView classes
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # UserAdmin view
│   │   │   ├── donation.py           # DonationAdmin view
│   │   │   ├── refund.py             # RefundAdmin view
│   │   │   ├── fire_station.py       # FireStationAdmin view
│   │   │   ├── news_content.py       # NewsContentAdmin view
│   │   │   ├── selenium_job.py       # SeleniumCrawlJobAdmin view
│   │   │   └── crawled_content.py    # CrawledContentAdmin view
│   │   ├── actions/                  # Custom admin actions
│   │   │   ├── __init__.py
│   │   │   └── refund_actions.py     # Bulk approve/reject refunds
│   │   └── llama_chat/               # Llama AI chat interface
│   │       ├── __init__.py
│   │       ├── page.py               # SQLAdmin custom page for chat
│   │       ├── service.py            # LlamaChatService
│   │       └── templates/            # Jinja2 templates for chat UI
│   │           └── llama_chat.html
│   │
│   ├── models/                       # Existing models (NO changes)
│   ├── api/                          # Existing API routes
│   │   └── admin/                    # Existing stub endpoints
│   │       ├── search.py             # Will integrate with LlamaChatService
│   │       └── refunds.py            # Will implement actual logic
│   ├── services/                     # Existing services
│   │   └── admin/
│   │       └── llm_search_service.py # Existing stub (will enhance)
│   ├── integrations/                 # Existing integrations (reuse)
│   │   ├── together_ai.py            # ✅ Reuse TogetherAIHttpClient
│   │   ├── graph.py                  # ✅ Reuse GraphClient
│   │   └── http_client.py            # ✅ Reuse HTTP pool
│   ├── cache/                        # Existing cache (reuse)
│   │   ├── semantic.py               # ✅ Reuse semantic cache
│   │   └── clients.py                # ✅ Reuse Redis clients
│   └── main.py                       # 🔧 UPDATE - Register SQLAdmin
│
└── tests/
    ├── contract/                     # 🆕 NEW - Contract tests
    │   ├── test_admin_ui_routes.py
    │   ├── test_admin_chat_api.py
    │   └── test_admin_refund_actions.py
    ├── integration/                  # 🆕 NEW - Integration tests
    │   ├── test_admin_authentication.py
    │   ├── test_admin_crud_operations.py
    │   ├── test_admin_refund_bulk_actions.py
    │   └── test_llama_chat_integration.py
    └── unit/                         # 🆕 NEW - Unit tests
        ├── test_llama_chat_service.py
        ├── test_refund_actions_service.py
        └── test_admin_auth.py
```

**Structure Decision**: Option 2 (Web application) - Backend only for this feature

## Phase 0: Outline & Research

### Unknowns from Technical Context
No NEEDS CLARIFICATION markers - all technical choices are clear from existing codebase.

### Research Tasks

1. **SQLAdmin Best Practices** (Haiku 4.5)
   - Research: SQLAdmin library documentation and patterns
   - Focus: ModelView customization, async SQLAlchemy support, custom pages
   - Output: How to add custom Llama chat page within SQLAdmin

2. **Llama Chat UI Integration** (Haiku 4.5)
   - Research: Integrating custom HTML/JS chat UI within SQLAdmin
   - Focus: Jinja2 templates, WebSocket vs REST for chat, conversation state management
   - Output: Architecture for chat interface (REST + session storage vs WebSocket)

3. **Knowledge Graph Query Patterns** (Haiku 4.5)
   - Research: Best practices for LLM querying graph databases
   - Focus: GraphClient usage, Cypher query generation by LLM, entity relationship traversal
   - Output: Pattern for Llama to generate and execute graph queries

4. **Semantic Cache Integration** (Haiku 4.5)
   - Research: Embedding-based semantic caching for LLM queries
   - Focus: Query similarity calculation, cache key generation, TTL策略
   - Output: How to integrate existing semantic cache with Llama chat

5. **Admin Actions in SQLAdmin** (Haiku 4.5)
   - Research: Custom bulk actions in SQLAdmin
   - Focus: Row selection, bulk operations, confirmation dialogs
   - Output: Implementation pattern for bulk refund approve/reject

**Output**: `/home/eugene/bodam/specs/005-sqladmin-integration-with/research.md` with consolidated findings

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

### 1. Data Model (`data-model.md`)

**No new entities** - this feature reuses all existing SQLAlchemy models:
- User (existing)
- Donation (existing)
- Refund (existing - assuming exists or will map to donation refund_status)
- FireStation (existing)
- NewsContent (existing - with AI analysis fields)
- NewsMatch (existing - with LangGraph similarity scores)
- SeleniumCrawlJob (existing)
- CrawledContent (existing)

**New service layer entities** (not database tables):
- `AdminSession` (session-based conversation context)
- `LlamaChatMessage` (in-memory chat history)
- `RefundBulkAction` (DTO for bulk operations)

Document in `data-model.md`:
- Existing model fields relevant to admin operations
- Service layer DTOs for admin actions
- Session management for chat context

### 2. API Contracts (`/contracts/`)

#### Contract 1: `admin-ui-routes.yaml` (OpenAPI)
SQLAdmin page routes (HTTP GET):
- `GET /admin` - Admin dashboard (SQLAdmin auto-generated)
- `GET /admin/user/list` - User list page
- `GET /admin/user/details/{id}` - User details
- `GET /admin/donation/list` - Donation list page
- `GET /admin/refund/list` - Refund list page
- `GET /admin/fire-station/list` - Fire station list page
- `GET /admin/news-content/list` - News content list page
- `GET /admin/selenium-job/list` - Selenium job list page
- `GET /admin/llama-chat` - Llama chat interface (custom page)

#### Contract 2: `admin-chat-api.yaml` (OpenAPI)
Llama chat API endpoints:
- `POST /admin/api/chat/query` - Send query to Llama
  - Request: `{query: string, session_id: string}`
  - Response: `{response: string, sources: [...]}`
- `POST /admin/api/chat/clear` - Clear conversation history
  - Request: `{session_id: string}`
  - Response: `{status: "cleared"}`
- `GET /admin/api/chat/history` - Get conversation history
  - Response: `{messages: [{role: "user"|"assistant", content: string}]}`

#### Contract 3: `admin-refund-actions.yaml` (OpenAPI)
Bulk refund management:
- `POST /admin/api/refunds/bulk-approve` - Approve multiple refunds
  - Request: `{refund_ids: [UUID], admin_note: string}`
  - Response: `{approved: number, failed: [{id: UUID, reason: string}]}`
- `POST /admin/api/refunds/bulk-reject` - Reject multiple refunds
  - Request: `{refund_ids: [UUID], rejection_reason: string}`
  - Response: `{rejected: number, failed: [{id: UUID, reason: string}]}`

### 3. Contract Tests (TDD - Must Fail)

Generate contract test files:
- `tests/contract/test_admin_ui_routes.py` - Assert SQLAdmin pages return 200 for admin, 403 for non-admin
- `tests/contract/test_admin_chat_api.py` - Assert chat API request/response schemas
- `tests/contract/test_admin_refund_actions.py` - Assert bulk action request/response schemas

These tests MUST FAIL initially (no implementation yet).

### 4. Test Scenarios from User Stories (`quickstart.md`)

Extract from spec.md Scenario 6 (Llama AI Chat Interface):
1. Admin login → Navigate to AI Chat → See chat interface
2. Query: "How many donations were received this month?" → Get AI response
3. Query: "Which fire station received the most donations last week?" → Get ranked answer
4. Query: "Show me news articles crawled today with relevance score above 0.8" → Get filtered news list
5. Query: "What fire stations are connected to incident ID XXX?" → Get Knowledge Graph results
6. Ask similar question → Response retrieved from semantic cache (faster)

`quickstart.md` will contain:
- Manual test steps for admin login and navigation
- Sample queries to test Llama integration
- Expected response formats
- Verification of semantic cache hits

### 5. Update CLAUDE.md

Run: `.specify/scripts/bash/update-agent-context.sh claude`

Add to CLAUDE.md:
- **Active Technologies**: sqladmin>=0.16.0
- **Project Structure**: `backend/src/admin/` directory
- **Commands**: Admin development commands
- **Dependencies**: sqladmin library
- **Recent Changes**: 005-sqladmin-integration-with feature

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, updated CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate tasks from Phase 1 design docs:
   - Each contract → contract test task [P]
   - Each admin view (User, Donation, Refund, etc.) → view implementation task
   - Llama chat service → multiple tasks (service, UI, integration)
   - Bulk refund actions → service + UI tasks
   - Integration tests → one task per user scenario

**Task Categories**:
- **Setup & Dependencies** (T001-T003): Install sqladmin, configure SQLAdmin, register in main.py
- **Admin Views** (T004-T010): Implement ModelView classes for each entity [P]
- **Admin Authentication** (T011-T012): Auth middleware, session validation
- **Llama Chat** (T013-T020): Service, UI template, API endpoints, KG integration, semantic cache
- **Bulk Refund Actions** (T021-T023): Service, UI actions, notifications
- **Contract Tests** (T024-T026): One task per contract file [P]
- **Integration Tests** (T027-T032): One task per user scenario
- **Documentation** (T033-T034): Update CLAUDE.md, write deployment docs

**Ordering Strategy**:
- TDD order: Contract tests before implementation
- Dependency order:
  1. Setup & Dependencies first
  2. Admin authentication (required for all pages)
  3. Admin views (can be parallel)
  4. Llama chat (depends on views for data access)
  5. Bulk actions (depends on refund view)
  6. Integration tests last

**Parallelization**: Mark [P] for independent tasks (views, contract tests)

**Estimated Output**: 30-35 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following TDD and Korean comments)
**Phase 5**: Validation (run tests, execute quickstart.md, verify semantic cache)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

**No violations** - this table is empty.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅ research.md generated
- [x] Phase 1: Design complete (/plan command) ✅ data-model.md, contracts/, quickstart.md, CLAUDE.md updated
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅ Task generation strategy documented
- [ ] Phase 3: Tasks generated (/tasks command) - Ready to execute
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅ No violations, library-first approach confirmed
- [x] All NEEDS CLARIFICATION resolved (none present) ✅
- [x] Complexity deviations documented (none) ✅

**Generated Artifacts**:
- [x] `/home/eugene/bodam/specs/005-sqladmin-integration-with/research.md` (한글, Haiku 4.5)
- [x] `/home/eugene/bodam/specs/005-sqladmin-integration-with/data-model.md` (619줄, 한글)
- [x] `/home/eugene/bodam/specs/005-sqladmin-integration-with/contracts/admin-ui-routes.yaml` (531줄)
- [x] `/home/eugene/bodam/specs/005-sqladmin-integration-with/contracts/admin-chat-api.yaml` (551줄)
- [x] `/home/eugene/bodam/specs/005-sqladmin-integration-with/contracts/admin-refund-actions.yaml` (850줄)
- [x] `/home/eugene/bodam/specs/005-sqladmin-integration-with/quickstart.md` (494줄, 한글)
- [x] `/home/eugene/bodam/CLAUDE.md` (updated with SQLAdmin context)

---
*Based on Constitution v2.1.1 - See `.specify/memory/constitution.md`*
