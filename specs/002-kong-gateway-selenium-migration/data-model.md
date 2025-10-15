# Data Model: Kong Gateway 마이그레이션 및 Selenium 크롤러 전환

**Date**: 2025-10-15
**Feature**: Kong Gateway 마이그레이션 및 Selenium 크롤러 전환

## Overview
이 문서는 Kong Gateway 라우팅 규칙과 Selenium 크롤러 작업을 위한 데이터 모델을 정의합니다. 기존 데이터베이스 스키마에 새로운 엔티티를 추가하거나 구성 파일 형태로 관리됩니다.

---

## Entities

### 1. KongRoute (Configuration Entity)
**Description**: Kong Gateway 라우팅 규칙을 정의하는 선언적 구성 엔티티

**Storage**: Kubernetes ConfigMap (`kong.yaml`)

**Fields**:
- `name` (string, required): Route identifier (e.g., `donations-api`, `fire-stations-search`)
- `paths` (array of strings, required): URL path patterns (e.g., `["/api/donations", "/api/donations/*"]`)
- `methods` (array of strings, optional): HTTP methods (e.g., `["GET", "POST"]`, default: all methods)
- `service` (object, required):
  - `name` (string): Target Kubernetes service name (e.g., `bodam-backend`)
  - `url` (string): Service URL (e.g., `http://bodam-backend.default.svc.cluster.local:80`)
- `plugins` (array of objects, optional): Kong plugins for this route
  - `name` (string): Plugin name (e.g., `rate-limiting`, `jwt`)
  - `config` (object): Plugin-specific configuration
- `strip_path` (boolean, default: true): Remove path prefix before proxying
- `preserve_host` (boolean, default: false): Forward original Host header

**Example**:
```yaml
routes:
  - name: donations-api
    paths:
      - /api/donations
    methods:
      - GET
      - POST
    service:
      name: bodam-backend
      url: http://bodam-backend.default.svc.cluster.local:80
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          policy: local
      - name: jwt
        config:
          secret_is_base64: false
    strip_path: false
    preserve_host: true
```

**Validation Rules**:
- `paths` must not be empty
- `service.url` must be a valid HTTP/HTTPS URL
- `plugins[].name` must be a valid Kong plugin
- No duplicate `name` across routes

**Relationships**:
- One route can have multiple plugins (one-to-many)
- Multiple routes can target the same service (many-to-one)

---

### 2. SeleniumCrawlJob (Database Entity)
**Description**: Selenium 크롤러가 실행하는 개별 작업 정의

**Storage**: PostgreSQL table `selenium_crawl_jobs`

**Fields**:
- `id` (UUID, primary key): Unique job identifier
- `url` (string, required, max 2048 chars): Target URL to crawl
- `browser_type` (enum, default: `chrome`): Browser type (`chrome`, `firefox`)
- `wait_conditions` (JSONB, optional): Wait conditions before extraction
  - `type` (string): `element_present`, `element_visible`, `page_loaded`, `custom_script`
  - `selector` (string, optional): CSS selector or XPath
  - `timeout_seconds` (integer, default: 30): Max wait time
- `retry_count` (integer, default: 0): Number of retries attempted
- `max_retries` (integer, default: 3): Maximum retry attempts
- `status` (enum, required): Job status
  - `pending`: Queued, not started
  - `running`: Browser instance active
  - `completed`: Successfully extracted data
  - `failed`: Exceeded max retries or fatal error
  - `timeout`: Exceeded wait timeout
- `created_at` (timestamp, required): Job creation time
- `started_at` (timestamp, nullable): Job start time
- `completed_at` (timestamp, nullable): Job completion time
- `error_message` (text, nullable): Error details if status = failed/timeout
- `metadata` (JSONB, optional): Additional context (source, tags, etc.)

**Indexes**:
- `idx_crawl_jobs_status` on `status`
- `idx_crawl_jobs_created_at` on `created_at`
- `idx_crawl_jobs_url` on `url` (for duplicate detection)

**Validation Rules**:
- `url` must be a valid HTTP/HTTPS URL
- `retry_count` <= `max_retries`
- `status` transitions: `pending` → `running` → `completed|failed|timeout`
- `started_at` >= `created_at`
- `completed_at` >= `started_at`

**Relationships**:
- One SeleniumCrawlJob can produce multiple CrawledContent (one-to-many)

---

### 3. CrawledContent (Database Entity)
**Description**: Selenium 크롤러가 추출한 콘텐츠 저장

**Storage**: PostgreSQL table `crawled_contents`

**Fields**:
- `id` (UUID, primary key): Unique content identifier
- `crawl_job_id` (UUID, foreign key, required): Reference to SeleniumCrawlJob
- `source_url` (string, required, max 2048 chars): Original URL (same as job.url)
- `rendered_html` (text, nullable): Full page HTML after JavaScript execution
- `extracted_data` (JSONB, required): Structured data extracted from page
  - Schema depends on crawler type (news, emergency alerts, etc.)
  - Example for news: `{ "title": "...", "content": "...", "publish_date": "..." }`
- `screenshot_url` (string, nullable): S3/local path to page screenshot
- `metadata` (JSONB, optional): Browser info, user agent, viewport size
- `created_at` (timestamp, required): Content extraction time

**Indexes**:
- `idx_crawled_content_job_id` on `crawl_job_id`
- `idx_crawled_content_created_at` on `created_at`

**Validation Rules**:
- `crawl_job_id` must reference existing SeleniumCrawlJob
- `extracted_data` must be valid JSON
- `source_url` must match `crawl_job.url`

**Relationships**:
- Many CrawledContent belong to one SeleniumCrawlJob (many-to-one)

---

### 4. KongPlugin (Configuration Entity)
**Description**: Kong Gateway 플러그인 전역 설정

**Storage**: Kubernetes ConfigMap (`kong.yaml`)

**Fields**:
- `name` (string, required): Plugin identifier (e.g., `global-rate-limiting`)
- `plugin` (string, required): Kong plugin type (e.g., `rate-limiting`, `cors`)
- `config` (object, required): Plugin configuration
- `enabled` (boolean, default: true): Plugin activation status
- `scope` (enum, required): Application scope (`global`, `service`, `route`)

**Example**:
```yaml
plugins:
  - name: global-cors
    plugin: cors
    enabled: true
    config:
      origins:
        - https://app.bodam.example
      methods:
        - GET
        - POST
        - PUT
        - DELETE
      headers:
        - Authorization
        - Content-Type
      credentials: true
      max_age: 3600
```

**Validation Rules**:
- `plugin` must be a valid Kong plugin name
- `config` must match plugin's schema
- Global plugins cannot conflict with route-specific plugins

---

### 5. NginxStaticConfig (Configuration Entity)
**Description**: NGINX 정적 파일 서빙 설정

**Storage**: Kubernetes ConfigMap (`nginx-config.conf`)

**Fields**:
- `static_root` (string, required): Root directory for static files (e.g., `/usr/share/nginx/html/static`)
- `cache_max_age` (integer, default: 31536000): Cache-Control max-age in seconds (1 year)
- `gzip_enabled` (boolean, default: true): Gzip compression for text files
- `allowed_origins` (array of strings, optional): CORS allowed origins for static files

**Example**:
```nginx
location /static/ {
    alias /usr/share/nginx/html/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    gzip on;
    gzip_types text/css application/javascript image/svg+xml;
}
```

**Validation Rules**:
- `static_root` must be an absolute path
- `cache_max_age` must be > 0

---

## Relationships Diagram

```
┌─────────────────────┐
│  KongRoute          │
│  (ConfigMap)        │
│  - name             │
│  - paths            │
│  - service          │
│  - plugins[]        │
└──────────┬──────────┘
           │ 1:N
           ▼
┌─────────────────────┐
│  KongPlugin         │
│  (ConfigMap)        │
│  - name             │
│  - plugin           │
│  - config           │
└─────────────────────┘

┌─────────────────────┐
│ SeleniumCrawlJob    │
│ (PostgreSQL)        │
│ - id                │
│ - url               │
│ - status            │
│ - wait_conditions   │
└──────────┬──────────┘
           │ 1:N
           ▼
┌─────────────────────┐
│ CrawledContent      │
│ (PostgreSQL)        │
│ - id                │
│ - crawl_job_id (FK) │
│ - rendered_html     │
│ - extracted_data    │
└─────────────────────┘
```

---

## State Transitions

### SeleniumCrawlJob Status
```
pending ──────► running ──────► completed
                  │
                  ├──────────► failed (retry_count < max_retries → back to pending)
                  │
                  └──────────► timeout (retry_count < max_retries → back to pending)
```

**Transition Rules**:
1. `pending` → `running`: Celery worker acquires job, sets `started_at`
2. `running` → `completed`: Successful extraction, creates CrawledContent
3. `running` → `failed`: Fatal error (invalid URL, network error, etc.), increments `retry_count`
4. `running` → `timeout`: Wait condition not met within timeout, increments `retry_count`
5. `failed|timeout` → `pending`: If `retry_count` < `max_retries`, requeue job

---

## Migration Requirements

### New Database Tables
```sql
-- SeleniumCrawlJob table
CREATE TABLE selenium_crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url VARCHAR(2048) NOT NULL,
    browser_type VARCHAR(20) DEFAULT 'chrome' CHECK (browser_type IN ('chrome', 'firefox')),
    wait_conditions JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'timeout')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB,
    CONSTRAINT retry_limit CHECK (retry_count <= max_retries)
);

CREATE INDEX idx_crawl_jobs_status ON selenium_crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_created_at ON selenium_crawl_jobs(created_at);
CREATE INDEX idx_crawl_jobs_url ON selenium_crawl_jobs(url);

-- CrawledContent table
CREATE TABLE crawled_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crawl_job_id UUID NOT NULL REFERENCES selenium_crawl_jobs(id) ON DELETE CASCADE,
    source_url VARCHAR(2048) NOT NULL,
    rendered_html TEXT,
    extracted_data JSONB NOT NULL,
    screenshot_url VARCHAR(2048),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_crawled_content_job_id ON crawled_contents(crawl_job_id);
CREATE INDEX idx_crawled_content_created_at ON crawled_contents(created_at);
```

### Alembic Migration
- **Migration file**: `backend/alembic/versions/002_add_selenium_crawler_tables.py`
- **Upgrade**: Create tables, indexes, constraints
- **Downgrade**: Drop tables (CASCADE will remove dependent rows)

---

## Summary
- **Configuration Entities**: KongRoute, KongPlugin, NginxStaticConfig (stored in Kubernetes ConfigMaps)
- **Database Entities**: SeleniumCrawlJob, CrawledContent (stored in PostgreSQL)
- **Key Relationships**: CrawlJob (1) → CrawledContent (N)
- **State Management**: SeleniumCrawlJob status transitions with retry logic

**Status**: ✅ Data model complete, ready for contracts generation
