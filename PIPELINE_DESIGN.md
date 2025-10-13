# 보담 파이프라인 설계

## 전체 아키텍처

```
┌─────────────────┐
│  Mock Site      │ (GitHub Pages or localhost:8888)
│  (HTML/JS)      │
└────────┬────────┘
         │ HTTP GET
         ▼
┌─────────────────┐
│  Crawler        │ (Celery Beat Scheduled Task)
│  (BS4 Parser)   │
└────────┬────────┘
         │ JSON Message
         ▼
┌─────────────────┐
│ Redis Queue     │ (redis-queue DB 0)
│ (Celery Broker) │
└────────┬────────┘
         │ Pop Message
         ▼
┌─────────────────┐
│  Worker         │ (Celery Worker)
│  - Save to DB   │
│  - Trigger News │
│  - Update Cache │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌──────────────┐
│  PostgreSQL     │  │ Redis Cache  │
│  (fire_incidents│  │ (incidents:* │
│   dispatch_     │  │  news:*      │
│   events,       │  │  stats:*)    │
│   news_matches) │  │              │
└─────────────────┘  └──────────────┘
         │
         │ News Search Trigger
         ▼
┌─────────────────┐
│  News Matcher   │ (Celery Worker)
│  - Naver News   │
│  - YouTube API  │
│  - Together AI  │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌──────────────┐
│  PostgreSQL     │  │Redis Semantic│
│  (news_sources, │  │ (Vector DB)  │
│   news_matches) │  │ Llama3 embed │
└─────────────────┘  └──────────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │
│  /incidents     │
│  /news          │
│  /stats         │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Next.js        │
│  Frontend       │
└─────────────────┘
```

## 1. 크롤러 (Crawler)

### 1.1 역할
- Mock Site (또는 실제 소방청 API)에서 화재 사고 정보 수집
- 5분마다 자동 실행 (Celery Beat)
- 새로운 사고 발견 시 큐에 메시지 전송

### 1.2 구현 위치
`backend/src/workers/crawler.py`

### 1.3 동작 흐름
```python
@celery_app.task(name="crawl_fire_incidents")
def crawl_fire_incidents():
    """
    1. Mock Site HTTP 요청
    2. BeautifulSoup으로 HTML 파싱
    3. 각 incident 데이터 추출
    4. FireIncidentMessage 생성
    5. Redis Queue에 push
    """
    url = os.getenv("CRAWLER_MOCK_SITE_URL")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    for row in soup.select('#incidents-tbody tr'):
        incident_data = extract_incident_data(row)
        message = FireIncidentMessage(**incident_data)

        # Queue에 메시지 전송
        process_incident.delay(message.model_dump_json())
```

### 1.4 설정
```python
# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    'crawl-fire-incidents-every-5-min': {
        'task': 'crawl_fire_incidents',
        'schedule': crontab(minute='*/5'),  # 5분마다
    },
}
```

## 2. 큐 시스템 (Queue System)

### 2.1 Redis Queue (DB 0)
- Celery Broker로 사용
- 메시지 포맷: JSON string
- 작업 우선순위 지원

### 2.2 메시지 종류
1. **fire_incident** - 화재 사고 정보
2. **dispatch_event** - 출동 이벤트
3. **news_match_request** - 뉴스 매칭 요청

### 2.3 큐 구조
```
celery:default (priority 5) - 일반 작업
celery:critical (priority 9) - 긴급 작업
celery:batch (priority 1) - 배치 작업
```

## 3. 워커 (Worker)

### 3.1 Incident Processor Worker
**파일:** `backend/src/workers/incident_processor.py`

```python
@celery_app.task(name="process_incident", bind=True, max_retries=3)
def process_incident(self, message_json: str):
    """
    1. JSON 메시지 파싱
    2. PostgreSQL에 fire_incidents 저장 (upsert)
    3. Redis Cache 업데이트
    4. 뉴스 매칭 작업 트리거
    5. 통계 캐시 무효화
    """
    try:
        message = FireIncidentMessage.model_validate_json(message_json)

        # DB 저장
        async with get_db_session() as session:
            incident = await save_incident(session, message)

        # 캐시 업데이트
        await update_incident_cache(message.incident_id, incident)

        # 뉴스 매칭 트리거
        match_news_for_incident.delay(message.incident_id, message.title)

        return {"status": "success", "incident_id": message.incident_id}

    except Exception as e:
        logger.error(f"Failed to process incident: {e}")
        self.retry(exc=e, countdown=60)  # 1분 후 재시도
```

### 3.2 Dispatch Event Worker
**파일:** `backend/src/workers/dispatch_processor.py`

```python
@celery_app.task(name="process_dispatch_event")
def process_dispatch_event(message_json: str):
    """
    1. 출동 이벤트 메시지 파싱
    2. fire_station 이름으로 ID 조회
    3. dispatch_events 테이블에 저장
    4. 소방서 상태 캐시 업데이트
    """
    message = DispatchEventMessage.model_validate_json(message_json)

    async with get_db_session() as session:
        station = await get_station_by_name(session, message.station_name)
        await save_dispatch_event(session, message, station.id)

    await update_station_cache(station.id)
```

## 4. 뉴스 매칭 파이프라인

### 4.1 News Matcher Worker
**파일:** `backend/src/workers/news_matcher.py`

```python
@celery_app.task(name="match_news_for_incident")
def match_news_for_incident(incident_id: str, search_query: str):
    """
    1. Naver News API 검색
    2. YouTube API 검색
    3. Together AI로 관련도 평가
    4. 임베딩 생성 및 Redis Semantic에 저장
    5. news_matches 테이블에 저장
    """
    # Naver News 검색
    naver_results = search_naver_news(search_query, limit=10)

    # YouTube 검색
    youtube_results = search_youtube(search_query, limit=5)

    # Together AI로 관련도 평가
    for news in naver_results:
        relevance_score = evaluate_relevance(incident_id, news)
        if relevance_score > 0.7:  # 70% 이상만 저장
            await save_news_match(incident_id, news, relevance_score)
            await save_to_vector_store(news)

    # 캐시 업데이트
    await update_news_cache()
```

### 4.2 AI/시맨틱 검색
```python
async def evaluate_relevance(incident_id: str, news: dict) -> float:
    """Together AI로 뉴스와 사고의 관련도 평가"""
    prompt = f"""
    화재 사고: {incident_title}
    뉴스 제목: {news['title']}
    뉴스 내용: {news['description']}

    이 뉴스가 화재 사고와 관련이 있나요? (0.0 ~ 1.0)
    """

    response = await together_ai_client.evaluate(prompt)
    return float(response.score)

async def save_to_vector_store(news: dict):
    """Redis Semantic Vector Store에 임베딩 저장"""
    embedding = await generate_embedding(news['content'])

    await redis_semantic.hset(
        f"doc:{news['id']}",
        mapping={
            "content": news['content'],
            "title": news['title'],
            "embedding": embedding.tobytes()
        }
    )
```

## 5. 캐시 전략

### 5.1 Cache Warming (주기적 캐시 갱신)
**파일:** `backend/src/workers/cache_warmer.py`

```python
@celery_app.task(name="warm_incident_cache")
def warm_incident_cache():
    """
    1. 최근 1시간 incidents 조회
    2. Redis Cache에 저장 (TTL 3600초)
    3. 실행 주기: 5분마다
    """
    async with get_db_session() as session:
        recent_incidents = await get_recent_incidents(session, hours=1)

    for incident in recent_incidents:
        await redis_cache.setex(
            f"incident:{incident.id}",
            3600,  # 1시간 TTL
            json.dumps(incident.to_dict())
        )

@celery_app.task(name="warm_news_cache")
def warm_news_cache():
    """
    1. 최근 영상 뉴스 조회
    2. 최근 속보 조회
    3. Redis Cache에 저장 (TTL 600초)
    4. 실행 주기: 2분마다
    """
    async with get_db_session() as session:
        videos = await get_recent_video_news(session, limit=20)
        breaking = await get_recent_breaking_news(session, limit=30)

    await redis_cache.setex(
        "news:videos:recent",
        600,  # 10분 TTL
        json.dumps([v.to_dict() for v in videos])
    )

    await redis_cache.setex(
        "news:breaking:recent",
        600,
        json.dumps([b.to_dict() for b in breaking])
    )
```

### 5.2 Cache Invalidation
```python
async def invalidate_stats_cache():
    """통계 캐시 무효화 (새 기부/사고 발생 시)"""
    await redis_cache.delete("stats:dashboard")

async def invalidate_incident_cache(incident_id: str):
    """특정 사고 캐시 무효화 (상태 변경 시)"""
    await redis_cache.delete(f"incident:{incident_id}")
```

## 6. 에러 처리 및 재시도

### 6.1 재시도 전략
```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1분 후 재시도
    autoretry_for=(RequestException, TimeoutError),
    retry_backoff=True,  # 지수 백오프
    retry_jitter=True    # 랜덤 지터
)
def resilient_task(self, ...):
    try:
        # 작업 수행
        pass
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise self.retry(exc=e)
```

### 6.2 Dead Letter Queue
```python
# 최대 재시도 후 실패한 작업 처리
@celery_app.task(name="handle_failed_task")
def handle_failed_task(task_id: str, exception: str):
    """
    1. 실패한 작업 로그 저장
    2. Slack/이메일 알림
    3. 수동 검토 큐에 추가
    """
    logger.critical(f"Task {task_id} permanently failed: {exception}")
    # TODO: Send alert to admin
```

## 7. 모니터링

### 7.1 Celery Flower
- URL: http://localhost:5555
- 워커 상태, 작업 성공/실패율 모니터링

### 7.2 로그 전략
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "incident_processed",
    incident_id=incident.id,
    status=incident.status,
    processing_time_ms=elapsed_time
)
```

### 7.3 메트릭
- Prometheus + Grafana 연동
- 주요 메트릭:
  - 크롤러 실행 주기 준수율
  - 큐 대기 시간
  - 작업 처리 속도
  - 에러율

## 8. Celery Beat 스케줄

```python
celery_app.conf.beat_schedule = {
    # 크롤러
    'crawl-fire-incidents': {
        'task': 'crawl_fire_incidents',
        'schedule': crontab(minute='*/5'),  # 5분마다
    },

    # 캐시 갱신
    'warm-incident-cache': {
        'task': 'warm_incident_cache',
        'schedule': crontab(minute='*/5'),
    },
    'warm-news-cache': {
        'task': 'warm_news_cache',
        'schedule': crontab(minute='*/2'),
    },
    'warm-stats-cache': {
        'task': 'warm_stats_cache',
        'schedule': crontab(minute='*/30'),  # 30분마다
    },
}
```

## 9. 다음 단계

이 설계를 바탕으로:
1. **인프라 구체화** - docker-compose 작성
2. **워커 구현** - 각 워커 파일 작성
3. **크롤러 구현** - BS4 파싱 로직
4. **API 연동** - FastAPI 엔드포인트
5. **테스트** - 전체 파이프라인 통합 테스트
