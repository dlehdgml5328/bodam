# 보담 파이프라인 데이터 모델 설계

## 1. PostgreSQL 테이블 스키마

### 1.1 fire_incidents (화재 사고 정보)
```sql
CREATE TABLE fire_incidents (
    id VARCHAR(50) PRIMARY KEY,  -- 예: "F2025001"
    title VARCHAR(500) NOT NULL,
    location_address TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL,  -- 'dispatching', 'suppressing', 'contained', 'resolved'
    severity VARCHAR(20),  -- 'critical', 'high', 'medium', 'low'
    casualties_injured INTEGER DEFAULT 0,
    casualties_dead INTEGER DEFAULT 0,
    estimated_damage BIGINT,  -- 예상 피해액 (원)
    source_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_fire_incidents_occurred_at ON fire_incidents(occurred_at DESC);
CREATE INDEX idx_fire_incidents_status ON fire_incidents(status);
CREATE INDEX idx_fire_incidents_location ON fire_incidents USING GIST(
    ll_to_earth(latitude, longitude)
);
```

### 1.2 dispatch_events (출동 이벤트)
```sql
CREATE TABLE dispatch_events (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(50) REFERENCES fire_incidents(id) ON DELETE CASCADE,
    fire_station_id INTEGER REFERENCES fire_stations(id),
    dispatched_at TIMESTAMP WITH TIME ZONE NOT NULL,
    arrived_at TIMESTAMP WITH TIME ZONE,
    cleared_at TIMESTAMP WITH TIME ZONE,
    units_count INTEGER DEFAULT 1,  -- 출동 차량 수
    personnel_count INTEGER DEFAULT 0,  -- 출동 인원
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_dispatch_events_incident ON dispatch_events(incident_id);
CREATE INDEX idx_dispatch_events_station ON dispatch_events(fire_station_id);
CREATE INDEX idx_dispatch_events_dispatched_at ON dispatch_events(dispatched_at DESC);
```

### 1.3 news_matches (뉴스-사고 매칭)
```sql
CREATE TABLE news_matches (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(50) REFERENCES fire_incidents(id) ON DELETE CASCADE,
    news_type VARCHAR(20) NOT NULL,  -- 'naver', 'youtube'
    news_id VARCHAR(200) NOT NULL,
    title VARCHAR(500) NOT NULL,
    url TEXT NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    thumbnail_url TEXT,
    similarity_score FLOAT,  -- 유사도 점수 (0.0 ~ 1.0)
    matched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_news_matches_incident ON news_matches(incident_id);
CREATE INDEX idx_news_matches_news_id ON news_matches(news_id);
CREATE INDEX idx_news_matches_type ON news_matches(news_type);
CREATE UNIQUE INDEX idx_news_matches_unique ON news_matches(incident_id, news_type, news_id);
```

### 1.4 news_sources (뉴스 원본 데이터)
```sql
CREATE TABLE news_sources (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL,  -- 'naver', 'youtube'
    external_id VARCHAR(200) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    view_count INTEGER,
    like_count INTEGER,
    content_text TEXT,  -- 전문 (크롤링된 경우)
    embedding_vector VECTOR(1536),  -- Llama3 임베딩 (pgvector)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_news_sources_external ON news_sources(source_type, external_id);
CREATE INDEX idx_news_sources_published ON news_sources(published_at DESC);
CREATE INDEX idx_news_sources_embedding ON news_sources USING ivfflat (embedding_vector vector_cosine_ops);
```

## 2. Redis 키/값 구조

### 2.1 redis-cache (DB 0) - 캐시 레이어
```
# 최근 화재 사고 목록 (1시간 TTL)
incidents:recent:{minutes}
    Type: List
    Value: JSON array of incident objects
    TTL: 3600 seconds
    Example: ["F2025001", "F2025002", ...]

# 화재 사고 상세 (1시간 TTL)
incident:{incident_id}
    Type: String (JSON)
    Value: Full incident object with dispatch_events
    TTL: 3600 seconds
    Example: {"id": "F2025001", "title": "...", "status": "...", ...}

# 뉴스/영상 목록 (10분 TTL)
news:videos:recent
    Type: List
    Value: JSON array of video news objects
    TTL: 600 seconds

news:breaking:recent
    Type: List
    Value: JSON array of breaking news objects
    TTL: 600 seconds

# 소방서별 출동 현황 (5분 TTL)
station:{station_id}:dispatches
    Type: String (JSON)
    Value: Current dispatch status
    TTL: 300 seconds

# 통계 캐시 (30분 TTL)
stats:dashboard
    Type: String (JSON)
    Value: Dashboard statistics
    TTL: 1800 seconds
```

### 2.2 redis-queue (DB 0) - Celery Broker
```
# Celery 내부 관리 (자동)
celery:
    각종 Celery 내부 키들 (자동 관리)

# 커스텀 큐 메시지
queue:crawler:incidents
    Type: List
    Value: JSON messages from crawler
    Example: {"incident_id": "F2025001", "url": "...", "timestamp": "..."}
```

### 2.3 redis-semantic (DB 2) - Vector Store
```
# LangChain RedisVectorStore 내부 관리
doc:{hash}
    Type: Hash
    Fields: content, metadata, embedding

# 인덱스 메타데이터
idx:incidents
    Type: Index (RediSearch)
    Used for: Vector similarity search
```

## 3. 메시지 포맷 (크롤러 → 큐)

### 3.1 화재 사고 메시지
```json
{
  "type": "fire_incident",
  "incident_id": "F2025001",
  "title": "서울 중구 아파트 화재",
  "location": {
    "address": "서울특별시 중구 세종대로 110",
    "lat": 37.5665,
    "lng": 126.9780
  },
  "occurred_at": "2025-10-13T14:30:00+09:00",
  "status": "dispatching",
  "severity": "high",
  "casualties": {
    "injured": 2,
    "dead": 0
  },
  "estimated_damage": 100000000,
  "source_url": "http://localhost:8888/test_static_mock.html",
  "timestamp": "2025-10-13T14:32:00+09:00"
}
```

### 3.2 출동 이벤트 메시지
```json
{
  "type": "dispatch_event",
  "incident_id": "F2025001",
  "station_name": "서울중부소방서",
  "dispatched_at": "2025-10-13T14:31:00+09:00",
  "units_count": 3,
  "personnel_count": 12,
  "timestamp": "2025-10-13T14:32:00+09:00"
}
```

### 3.3 뉴스 매칭 요청 메시지
```json
{
  "type": "news_match_request",
  "incident_id": "F2025001",
  "search_query": "서울 중구 아파트 화재",
  "timestamp": "2025-10-13T14:35:00+09:00"
}
```

## 4. 환경 변수 설정

```env
# Redis 3종 분리
REDIS_CACHE_URL=redis://localhost:6379/0
REDIS_QUEUE_URL=redis://localhost:6379/0  # Celery broker
REDIS_SEMANTIC_URL=redis://localhost:6379/2

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# 크롤러 설정
CRAWLER_MOCK_SITE_URL=http://localhost:8888/test_static_mock.html
CRAWLER_INTERVAL_SECONDS=300  # 5분마다

# AI/임베딩
TOGETHER_AI_API_KEY=...
TOGETHER_AI_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo-Free
EMBEDDING_DIMENSION=1536
```

## 5. Alembic Migration 순서

1. `001_add_fire_incidents_table.py` - fire_incidents 테이블 생성
2. `002_add_dispatch_events_table.py` - dispatch_events 테이블 생성
3. `003_add_news_matches_table.py` - news_matches 테이블 생성
4. `004_add_news_sources_table.py` - news_sources + pgvector 설정
5. `005_add_indexes.py` - 성능 최적화 인덱스 추가

## 6. 다음 단계

이 문서를 기반으로:
1. SQLAlchemy 모델 파일 생성
2. Alembic migration 파일 생성
3. Redis 연결 설정 업데이트
4. 메시지 스키마 Pydantic 모델 생성
