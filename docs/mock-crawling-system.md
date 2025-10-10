# Mock 크롤링 시스템 구현 가이드

> **목적**: 실제 출동 데이터가 없는 상황에서 크롤링 → 매칭 → API 제공 파이프라인 구축

## 📋 목차

- [개요](#개요)
- [시스템 아키텍처](#시스템-아키텍처)
- [Mock Site 구현](#mock-site-구현)
- [Backend 크롤러 구현](#backend-크롤러-구현)
- [매칭 알고리즘](#매칭-알고리즘)
- [API 구현](#api-구현)
- [배포 및 운영](#배포-및-운영)

---

## 개요

### 문제 상황
- 실제 출동 데이터 크롤링 불가 (공공 사이트 접근 제한)
- 뉴스/영상 매칭 알고리즘 개발 필요
- 프론트엔드는 실시간 출동 현황 표시 필요

### 해결 방안
```
1. Mock 출동 데이터 30개 생성 (실제 뉴스 기반)
2. GitHub Pages로 Mock 사이트 배포 (크롤링 대상)
3. Celery로 5분마다 크롤링
4. 매칭 알고리즘으로 뉴스/영상 검색
5. Redis 캐싱 → API 제공
```

---

## 시스템 아키텍처

```
┌─────────────────┐
│  GitHub Pages   │  Mock 출동 데이터 (30개)
│  Mock Site      │  5분마다 1개씩 순환 표시
└────────┬────────┘
         │ HTTPS
         ↓ (5분마다 크롤링)
┌─────────────────┐
│  Celery Worker  │  크롤링 + 파싱
│  (Beat)         │  중복 체크
└────────┬────────┘
         ↓
┌─────────────────┐
│ Matching Engine │  키워드 추출
│                 │  Naver News API
│                 │  YouTube API
└────────┬────────┘
         ↓
┌─────────────────┐
│  Redis Cache    │  24시간 TTL
│                 │  최근 30개 유지
└────────┬────────┘
         ↓
┌─────────────────┐
│  FastAPI        │  GET /emergency-stations
│                 │  랜덤 5개 반환
└────────┬────────┘
         ↓
┌─────────────────┐
│  Frontend       │  60초마다 폴링
│  (Next.js)      │  출동 현황 표시
└─────────────────┘
```

### 데이터 흐름

**Phase 1: Mock 데이터 생성 (1회)**
```
실제 뉴스 30개 수집 (수동)
  ↓
주소/시간/소방서 추출
  ↓
Mock 출동 데이터 30개 생성 (JSON)
  ↓
GitHub Pages 배포
```

**Phase 2: 실시간 크롤링 (5분 주기)**
```
Celery Beat (5분마다)
  ↓
Mock Site 크롤링 (현재 표시된 1개)
  ↓
중복 체크 (Redis)
  ↓ (신규 데이터만)
매칭 알고리즘 실행
  ↓
Redis 저장 (24시간 TTL)
```

**Phase 3: API 제공 (실시간)**
```
Frontend 요청 (60초마다)
  ↓
Redis에서 최근 30개 조회
  ↓
랜덤 5개 선택
  ↓
JSON 응답 (뉴스/영상 포함)
```

---

## Mock Site 구현

### 1. 디렉토리 구조

```
mock-site/
├── index.html           # 메인 페이지
├── data/
│   └── incidents.json   # 30개 출동 데이터
├── js/
│   └── update.js        # 5분 순환 로직
├── css/
│   └── style.css        # 스타일
└── README.md            # 사용법
```

### 2. 출동 데이터 형식

```json
// data/incidents.json
[
  {
    "id": "20241009001",
    "union": "11",
    "status": "A",
    "fireName": "서울강남소방서",
    "address": "서울 강남구 역삼동 테헤란로 123",
    "axisX": 127.0376,
    "axisY": 37.4979,
    "occurrenceTime": "14:32",
    "casualties": 0,
    "injured": 0,
    "damageAmount": 0,
    "progress": "화재진압"
  }
  // ... 30개
]
```

### 3. 순환 표시 로직

```javascript
// js/update.js
let currentIndex = 0;

async function loadIncidents() {
  const response = await fetch('data/incidents.json');
  return await response.json();
}

function displayIncident(incident) {
  document.getElementById('current-incident').innerHTML = `
    <div class="incident" data-id="${incident.id}">
      <h2>${incident.fireName}</h2>
      <p class="address">${incident.address}</p>
      <p class="time">${incident.occurrenceTime}</p>
      <span class="status">${incident.progress}</span>
    </div>
  `;

  // 크롤링 포인트 (data-* 속성)
  document.querySelector('.incident').setAttribute('data-lat', incident.axisY);
  document.querySelector('.incident').setAttribute('data-lng', incident.axisX);
}

async function rotateIncidents() {
  const incidents = await loadIncidents();

  function showNext() {
    displayIncident(incidents[currentIndex]);
    console.log(`[${new Date().toISOString()}] Displaying incident #${currentIndex + 1}`);
    currentIndex = (currentIndex + 1) % incidents.length;
  }

  // 초기 표시
  showNext();

  // 5분(300초)마다 갱신
  setInterval(showNext, 300000);
}

rotateIncidents();
```

### 4. GitHub Pages 배포

```bash
# 1. 레포지토리 생성
gh repo create mock-fire-station-site --public

# 2. 파일 푸시
cd mock-site
git init
git add .
git commit -m "Initial mock site"
git remote add origin git@github.com:username/mock-fire-station-site.git
git push -u origin main

# 3. GitHub Pages 활성화
# Settings → Pages → Source: main branch → Save
```

**배포 URL**: `https://username.github.io/mock-fire-station-site/`

---

## Backend 크롤러 구현

### 1. 크롤링 Task

```python
# backend/src/tasks/crawler.py
import httpx
from bs4 import BeautifulSoup
from celery import shared_task
import json

MOCK_SITE_URL = "https://username.github.io/mock-fire-station-site/"

@shared_task
async def crawl_mock_site():
    """5분마다 Mock 사이트 크롤링"""

    # 1. HTML 가져오기
    async with httpx.AsyncClient() as client:
        response = await client.get(MOCK_SITE_URL)
        html = response.text

    # 2. 파싱
    soup = BeautifulSoup(html, 'html.parser')
    incident_div = soup.find('div', {'class': 'incident'})

    incident = {
        'id': incident_div.get('data-id'),
        'fireName': incident_div.find('h2').text,
        'address': incident_div.find('p', {'class': 'address'}).text,
        'occurrenceTime': incident_div.find('p', {'class': 'time'}).text,
        'axisY': float(incident_div.get('data-lat')),
        'axisX': float(incident_div.get('data-lng')),
        'progress': incident_div.find('span', {'class': 'status'}).text,
    }

    # 3. 중복 체크
    from src.cache.clients import get_redis
    redis = await get_redis()

    if await redis.exists(f"incident:{incident['id']}"):
        logger.info(f"[Crawler] Skip duplicate: {incident['id']}")
        return

    # 4. 매칭 태스크 호출
    from src.tasks.matcher import match_news_and_videos
    await match_news_and_videos.delay(incident)

    logger.info(f"[Crawler] New incident: {incident['id']}")
```

### 2. Celery Beat 스케줄

```python
# backend/src/worker.py
from celery import Celery
from celery.schedules import crontab

celery = Celery('bodam')

celery.conf.beat_schedule = {
    'crawl-mock-site-every-5min': {
        'task': 'src.tasks.crawler.crawl_mock_site',
        'schedule': 300.0,  # 5분 = 300초
    },
}

celery.conf.timezone = 'Asia/Seoul'
```

### 3. 크롤러 모니터링

```python
# backend/src/tasks/crawler.py
from prometheus_client import Counter, Histogram

crawl_total = Counter('crawl_total', 'Total crawl attempts')
crawl_success = Counter('crawl_success', 'Successful crawls')
crawl_duration = Histogram('crawl_duration_seconds', 'Crawl duration')

@shared_task
@crawl_duration.time()
async def crawl_mock_site():
    crawl_total.inc()

    try:
        # ... 크롤링 로직
        crawl_success.inc()
    except Exception as e:
        logger.error(f"[Crawler] Error: {e}")
        raise
```

---

## 매칭 알고리즘

### 1. 키워드 추출

```python
# backend/src/services/matcher.py
from typing import List, Dict
import re

def extract_keywords(incident: Dict) -> List[str]:
    """출동 데이터에서 검색 키워드 추출"""

    keywords = []

    # 주소에서 지역 추출
    address_parts = incident['address'].split()
    if len(address_parts) >= 2:
        keywords.append(f"{address_parts[0]} {address_parts[1]}")  # "서울 강남구"

    # 소방서명에서 지역 추출
    fire_station_match = re.search(r'(\w+)소방서', incident['fireName'])
    if fire_station_match:
        keywords.append(fire_station_match.group(1))  # "강남"

    # 진행 상황 추가
    keywords.append(incident['progress'])  # "화재진압"

    # 조합 키워드
    keywords.append(f"{address_parts[1] if len(address_parts) > 1 else ''} 화재")

    return keywords
```

### 2. Naver News API 연동

```python
# backend/src/integrations/naver_news.py
import httpx
from typing import List, Dict

class NaverNewsClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"

    async def search(self, query: str, display: int = 10) -> List[Dict]:
        """뉴스 검색"""
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        params = {
            "query": query,
            "display": display,
            "sort": "date"  # 최신순
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                headers=headers,
                params=params
            )
            data = response.json()

            return [
                {
                    "title": item["title"].replace("<b>", "").replace("</b>", ""),
                    "url": item["link"],
                    "description": item["description"].replace("<b>", "").replace("</b>", ""),
                    "publishedAt": item["pubDate"]
                }
                for item in data.get("items", [])
            ]
```

### 3. YouTube API 연동

```python
# backend/src/integrations/youtube.py
from googleapiclient.discovery import build
from typing import List, Dict

class YouTubeClient:
    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """영상 검색"""
        request = self.youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
            order="date",  # 최신순
            relevanceLanguage="ko"
        )

        response = request.execute()

        return [
            {
                "id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
                "publishedAt": item["snippet"]["publishedAt"]
            }
            for item in response.get("items", [])
        ]
```

### 4. 유사도 매칭

```python
# backend/src/services/matcher.py
from difflib import SequenceMatcher

def calculate_similarity(text1: str, text2: str) -> float:
    """문자열 유사도 계산 (0.0 ~ 1.0)"""
    return SequenceMatcher(None, text1, text2).ratio()

def rank_results(incident: Dict, results: List[Dict]) -> List[Dict]:
    """결과를 유사도 순으로 정렬"""
    address = incident['address']

    for result in results:
        # 제목과 주소의 유사도 계산
        title_similarity = calculate_similarity(
            address.lower(),
            result['title'].lower()
        )

        # 설명과 주소의 유사도 계산 (뉴스만)
        desc_similarity = 0
        if 'description' in result:
            desc_similarity = calculate_similarity(
                address.lower(),
                result['description'].lower()
            )

        # 최종 점수
        result['score'] = max(title_similarity, desc_similarity)

    # 점수 높은 순으로 정렬
    return sorted(results, key=lambda x: x['score'], reverse=True)
```

### 5. 통합 매칭 Task

```python
# backend/src/tasks/matcher.py
from celery import shared_task
from src.services.matcher import extract_keywords, rank_results
from src.integrations.naver_news import NaverNewsClient
from src.integrations.youtube import YouTubeClient
from src.cache.clients import get_redis
import json

@shared_task
async def match_news_and_videos(incident: Dict):
    """출동 데이터에 뉴스/영상 매칭"""

    # 1. 키워드 추출
    keywords = extract_keywords(incident)
    primary_keyword = keywords[0] if keywords else incident['address']

    # 2. 뉴스 검색
    naver = NaverNewsClient(
        client_id=settings.NAVER_CLIENT_ID,
        client_secret=settings.NAVER_CLIENT_SECRET
    )
    news_results = await naver.search(primary_keyword, display=10)
    ranked_news = rank_results(incident, news_results)[:3]  # Top 3

    # 3. 영상 검색
    youtube = YouTubeClient(api_key=settings.YOUTUBE_API_KEY)
    video_results = await youtube.search(primary_keyword, max_results=5)
    ranked_videos = rank_results(incident, video_results)[:3]  # Top 3

    # 4. Redis 저장
    redis = await get_redis()
    matched_data = {
        **incident,
        "relatedNews": ranked_news,
        "relatedVideos": ranked_videos,
        "matchedAt": datetime.now().isoformat()
    }

    # 24시간 TTL
    await redis.setex(
        f"incident:{incident['id']}",
        86400,
        json.dumps(matched_data)
    )

    # 최근 목록에 추가
    await redis.lpush("recent_incidents", incident['id'])
    await redis.ltrim("recent_incidents", 0, 29)  # 최근 30개만

    logger.info(f"[Matcher] Matched: {incident['id']} → {len(ranked_news)} news, {len(ranked_videos)} videos")
```

---

## API 구현

### 1. Emergency Stations API

```python
# backend/src/api/emergency.py
from fastapi import APIRouter, HTTPException
from typing import List
from src.cache.clients import get_redis
import json
import random

router = APIRouter(prefix="/emergency-stations", tags=["emergency"])

@router.get("", response_model=List[EmergencyStationResponse])
async def get_emergency_stations():
    """실시간 출동 현황 조회 (랜덤 5개)"""

    redis = await get_redis()

    # 1. 최근 30개 ID 조회
    incident_ids = await redis.lrange("recent_incidents", 0, 29)

    if not incident_ids:
        # Fallback 데이터
        return FALLBACK_STATIONS

    # 2. 각 ID의 상세 데이터 조회
    incidents = []
    for incident_id in incident_ids:
        data = await redis.get(f"incident:{incident_id.decode()}")
        if data:
            incidents.append(json.loads(data))

    # 3. 랜덤 5개 선택
    selected = random.sample(incidents, min(5, len(incidents)))

    # 4. 응답 형식 변환
    return [
        {
            "name": inc["fireName"],
            "location": inc["address"],
            "status": STATUS_MAP.get(inc["status"], "출동 중"),
            "priority": calculate_priority(inc),
            "time": format_time(inc["occurrenceTime"]),
            "relatedNews": inc.get("relatedNews", []),
            "relatedVideos": inc.get("relatedVideos", [])
        }
        for inc in selected
    ]

def calculate_priority(incident: Dict) -> str:
    """우선순위 계산"""
    if incident.get("casualties", 0) > 0:
        return "high"
    if incident.get("injured", 0) > 0:
        return "high"
    if incident.get("status") == "A":  # 출동
        return "medium"
    return "low"

def format_time(occurrence_time: str) -> str:
    """시간 포맷 변환 (14:32 → N분 전)"""
    from datetime import datetime, timedelta

    now = datetime.now()
    time_parts = occurrence_time.split(":")
    occurred = now.replace(hour=int(time_parts[0]), minute=int(time_parts[1]))

    diff = now - occurred
    minutes = int(diff.total_seconds() / 60)

    if minutes < 60:
        return f"{minutes}분 전"
    hours = minutes // 60
    return f"{hours}시간 전"

STATUS_MAP = {
    "A": "출동 중",
    "B": "도착",
    "C": "진압 중",
    "D": "귀소"
}
```

### 2. Response Model

```python
# backend/src/api/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class NewsItem(BaseModel):
    title: str
    url: str
    description: Optional[str]
    publishedAt: str
    score: Optional[float]

class VideoItem(BaseModel):
    id: str
    title: str
    url: str
    thumbnail: str
    publishedAt: str
    score: Optional[float]

class EmergencyStationResponse(BaseModel):
    name: str
    location: str
    status: str
    priority: str
    time: str
    relatedNews: List[NewsItem] = []
    relatedVideos: List[VideoItem] = []
```

---

## 배포 및 운영

### 1. 환경 변수 설정

```bash
# backend/.env
# Naver News API
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret

# YouTube API
YOUTUBE_API_KEY=your_api_key

# Mock Site
MOCK_SITE_URL=https://username.github.io/mock-fire-station-site/

# Redis
REDIS_CACHE_URL=redis://redis-cache-service:6379/0
```

### 2. Celery Worker 실행

```bash
# Worker 실행
celery -A src.worker worker --loglevel=info

# Beat 실행 (스케줄러)
celery -A src.worker beat --loglevel=info

# Flower 모니터링
celery -A src.worker flower --port=5555
```

### 3. K8s 배포

```yaml
# infra/k8s/celery/crawler-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-crawler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: celery-crawler
  template:
    metadata:
      labels:
        app: celery-crawler
    spec:
      containers:
      - name: worker
        image: bodam/backend:latest
        command: ["celery", "-A", "src.worker", "worker", "--loglevel=info"]
        env:
        - name: NAVER_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: naver-client-id
        - name: YOUTUBE_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: youtube-api-key
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-beat
spec:
  replicas: 1
  selector:
    matchLabels:
      app: celery-beat
  template:
    metadata:
      labels:
        app: celery-beat
    spec:
      containers:
      - name: beat
        image: bodam/backend:latest
        command: ["celery", "-A", "src.worker", "beat", "--loglevel=info"]
```

### 4. 모니터링

```python
# backend/src/monitoring/metrics.py
from prometheus_client import Counter, Gauge, Histogram

# 크롤링 메트릭
crawl_total = Counter('crawl_total', 'Total crawl attempts')
crawl_success = Counter('crawl_success', 'Successful crawls')
crawl_errors = Counter('crawl_errors', 'Crawl errors', ['error_type'])
crawl_duration = Histogram('crawl_duration_seconds', 'Crawl duration')

# 매칭 메트릭
match_total = Counter('match_total', 'Total match attempts')
match_news_found = Gauge('match_news_found', 'News items found')
match_videos_found = Gauge('match_videos_found', 'Videos found')

# API 메트릭
api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint'])
api_cache_hits = Counter('api_cache_hits', 'Cache hits')
api_cache_misses = Counter('api_cache_misses', 'Cache misses')
```

### 5. 로그 분석

```python
# backend/src/utils/logger.py
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("crawler")

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 사용 예시
logger.info("Crawled incident", extra={
    "incident_id": "20241009001",
    "news_count": 3,
    "video_count": 2,
    "duration_ms": 1234
})
```

---

## 트러블슈팅

### 1. 크롤링 실패

**증상**: Celery task가 계속 실패
**원인**: Mock Site CORS 설정, 네트워크 오류
**해결**:
```python
# Retry 설정
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
async def crawl_mock_site(self):
    try:
        # 크롤링 로직
        pass
    except Exception as exc:
        raise self.retry(exc=exc)
```

### 2. API Rate Limit

**증상**: Naver/YouTube API 할당량 초과
**원인**: 5분마다 호출 시 하루 288회
**해결**:
```python
# API 호출 전 확인
if await redis.get("api_quota_exceeded"):
    logger.warning("API quota exceeded, using cached data")
    return []

try:
    results = await naver.search(keyword)
except QuotaExceeded:
    await redis.setex("api_quota_exceeded", 3600, "1")  # 1시간 차단
    return []
```

### 3. 중복 데이터

**증상**: 같은 출동 데이터가 여러 번 처리됨
**원인**: Redis 중복 체크 실패
**해결**:
```python
# 원자적 연산 사용
async def check_and_set(redis, key, value, ttl):
    """중복 체크 + 설정을 원자적으로"""
    lua_script = """
    if redis.call("exists", KEYS[1]) == 0 then
        redis.call("setex", KEYS[1], ARGV[1], ARGV[2])
        return 1
    else
        return 0
    end
    """
    result = await redis.eval(lua_script, 1, key, ttl, value)
    return result == 1
```

---

## 성능 최적화

### 1. 병렬 처리

```python
import asyncio

@shared_task
async def match_news_and_videos(incident: Dict):
    # 뉴스/영상 검색을 병렬로
    news_task = naver.search(keyword)
    video_task = youtube.search(keyword)

    news_results, video_results = await asyncio.gather(
        news_task,
        video_task
    )
```

### 2. 배치 캐싱

```python
# 여러 출동 데이터를 한 번에 저장
async def batch_save(incidents: List[Dict]):
    pipeline = redis.pipeline()
    for inc in incidents:
        pipeline.setex(f"incident:{inc['id']}", 86400, json.dumps(inc))
    await pipeline.execute()
```

### 3. 압축

```python
import gzip
import json

# 큰 데이터는 압축해서 저장
compressed = gzip.compress(json.dumps(incident).encode())
await redis.setex(f"incident:{incident['id']}", 86400, compressed)

# 조회 시 압축 해제
data = await redis.get(f"incident:{incident['id']}")
decompressed = gzip.decompress(data).decode()
incident = json.loads(decompressed)
```

---

## 향후 개선 사항

### 1. AI 기반 매칭
- 단순 키워드 → Embedding 기반 유사도
- OpenAI/Claude API로 관련도 판단
- 벡터 DB (Pinecone, Weaviate) 활용

### 2. 실시간 알림
- WebSocket으로 신규 출동 Push
- 우선순위 높은 출동 알림
- Slack/Discord 연동

### 3. 대시보드
- Grafana 대시보드
- 크롤링 성공률, 매칭 정확도
- API 응답 시간, 캐시 히트율

---

## 참고 자료

- [Celery 공식 문서](https://docs.celeryq.dev/)
- [BeautifulSoup 문서](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Naver Search API](https://developers.naver.com/docs/serviceapi/search/news/news.md)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Redis 공식 문서](https://redis.io/docs/)

---

**작성일**: 2025-10-09
**버전**: 1.0.0
**작성자**: Claude + 동희
