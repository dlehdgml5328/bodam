# 기술 스택 연구 및 결정사항

## 1. FastAPI + SQLAlchemy + Alembic (백엔드)

### 결정사항
- **FastAPI**: 비동기 웹 프레임워크
- **SQLAlchemy 2.0**: ORM + 비동기 지원
- **Alembic**: 데이터베이스 마이그레이션

### 선택 이유
- 고성능 비동기 처리로 동시 사용자 1000명+ 지원
- 자동 API 문서 생성 (OpenAPI/Swagger)
- 타입 힌트 지원으로 개발 생산성 향상
- WebSocket 네이티브 지원 (실시간 알림)

### 대안 검토
- **Django**: 동기 처리로 성능 제약, 복잡한 설정
- **Flask**: 비동기 지원 부족, 추가 확장 필요
- **Node.js**: Python 생태계 대비 AI 라이브러리 부족

### 통합 패턴
```python
# 비동기 DB 연결
async def get_db():
    async with AsyncSession() as session:
        yield session

# WebSocket + DB 통합
@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession):
    await websocket.accept()
    # 실시간 기부 알림 처리
```

### 핵심 구현 가이드
- 비동기 뷰 함수 + 컨텍스트 매니저 사용
- 커넥션 풀링 설정 (min_size=5, max_size=20)
- 마이그레이션 자동화 (CI/CD 파이프라인)

## 2. PostgreSQL + pgvector + PostGIS

### 결정사항
- **PostgreSQL 15+**: 메인 데이터베이스
- **pgvector**: AI 벡터 유사도 검색
- **PostGIS**: 지리정보 처리

### 선택 이유
- 단일 DB에서 관계형 + 벡터 + 지리 데이터 처리
- 트랜잭션 ACID 보장 (결제 데이터 안정성)
- 복잡한 조인 쿼리 최적화 가능

### 대안 검토
- **MongoDB + 별도 벡터DB**: 데이터 일관성 문제, 복잡도 증가
- **MySQL**: pgvector, PostGIS 부재
- **Pinecone**: 벡터 전용이라 통합 쿼리 불가

### 통합 패턴
```sql
-- 소방서 근처 관련 뉴스 검색 (벡터 + 지리 결합)
SELECT n.*, f.name as station_name
FROM news_content n
JOIN fire_stations f ON ST_DWithin(n.location, f.location, 5000)
WHERE n.embedding <-> %s < 0.3
ORDER BY n.embedding <-> %s
LIMIT 10;
```

### 핵심 구현 가이드
- 벡터 인덱스 생성: `CREATE INDEX ON news_content USING ivfflat (embedding vector_cosine_ops)`
- 지리 인덱스: `CREATE INDEX ON fire_stations USING GIST (location)`
- 파티셔닝: 뉴스 데이터 월별 분할

## 3. Celery + Redis (비동기 작업)

### 결정사항
- **Celery**: 분산 작업 큐
- **Redis**: 메시지 브로커 + 캐시

### 선택 이유
- 30분 주기 데이터 수집 스케줄링
- 실시간 알림 큐 관리
- 결제 처리 백그라운드 작업

### 대안 검토
- **RQ**: 기능 제한적, 스케줄링 부족
- **APScheduler**: 단일 프로세스 제약
- **Kafka**: 과도한 복잡성

### 워커 분리 설계
```python
# 4개 워커 타입별 분리
CELERY_ROUTES = {
    'data_collector.*': {'queue': 'data_collection'},
    'payment_processor.*': {'queue': 'payments'},
    'notification_sender.*': {'queue': 'notifications'},
    'ai_analyzer.*': {'queue': 'ai_analysis'}
}
```

### 핵심 구현 가이드
- 워커별 별도 프로세스/컨테이너 실행
- Redis Streams 활용한 실시간 메시지
- 재시도 정책: 지수 백오프 + 데드레터 큐

## 4. Next.js + TailwindCSS (프론트엔드)

### 결정사항
- **Next.js 14**: App Router + React Server Components
- **TailwindCSS**: 유틸리티 CSS 프레임워크

### 선택 이유
- 서버사이드 렌더링으로 SEO 최적화
- 관리자 대시보드 라우팅 (/admin/*)
- 실시간 업데이트 (WebSocket 통합)

### 대안 검토
- **React SPA**: SEO 부족, 초기 로딩 느림
- **Vue.js**: 생태계 상대적 부족
- **Svelte**: 기업용 레퍼런스 부족

### 구조 설계
```
app/
├── (public)/
│   ├── page.tsx              # 메인 페이지
│   ├── stations/             # 소방서 목록/상세
│   └── donations/            # 기부 히스토리
└── admin/
    ├── dashboard/            # 관리자 대시보드
    ├── review-queue/         # AI 검토 대기
    └── users/                # 사용자 관리
```

### 핵심 구현 가이드
- 서버 컴포넌트 + 클라이언트 컴포넌트 하이브리드
- WebSocket 클라이언트: `useEffect` + 상태 관리
- 지도 API: Naver Maps JavaScript API v3

## 5. Toss Payments 결제 연동

### 결정사항
- **Toss Payments API**: 결제 게이트웨이
- **웹훅 처리**: 결제 상태 실시간 동기화

### 선택 이유
- 국내 최고 사용성 + 낮은 수수료
- 일시/정기결제 모두 지원
- 현금영수증 자동 발급

### 통합 패턴
```python
# 결제 승인 웹훅 처리
@app.post("/webhooks/toss/confirm")
async def toss_webhook(webhook_data: TossWebhook, db: AsyncSession):
    donation = await get_donation_by_order_id(webhook_data.orderId)
    if webhook_data.status == "DONE":
        donation.status = "completed"
        await send_receipt_email.delay(donation.id)
```

### 핵심 구현 가이드
- 웹훅 서명 검증 필수
- 멱등성 보장 (중복 처리 방지)
- PDF 영수증: WeasyPrint + HTML 템플릿

## 6. Together AI + Llama 3.3 70B

### 결정사항
- **Together AI**: API 제공업체
- **Llama 3.3 70B Instruct**: 뉴스 분석 모델

### 선택 이유
- 한국어 처리 성능 우수
- 비용 효율적 ($0.18/1M 토큰)
- 신뢰도 점수 산출 가능

### 분석 파이프라인
```python
# AI 판별 로직
async def analyze_content(content: str) -> ContentAnalysis:
    prompt = f"""
    다음 뉴스가 화재/소방 관련인지 판단하고 1-100점으로 평가:

    뉴스: {content}

    JSON 응답: {{"relevance_score": 점수, "summary": "요약", "keywords": ["키워드"]}}
    """

    response = await together_client.complete(prompt)
    analysis = json.loads(response.choices[0].message.content)

    # 점수별 처리
    if analysis["relevance_score"] >= 70:
        return "auto_approve"
    elif analysis["relevance_score"] >= 50:
        return "manual_review"
    else:
        return "reject"
```

### 핵심 구현 가이드
- 배치 처리로 API 비용 절약
- 캐싱으로 중복 분석 방지
- 프롬프트 엔지니어링 최적화

## 7. Kubernetes 배포 + 모니터링

### 결정사항
- **Kubernetes**: 컨테이너 오케스트레이션
- **NGINX Ingress**: 로드밸런싱
- **Prometheus + Grafana**: 모니터링

### 선택 이유
- Blue-Green 무중단 배포
- 자동 스케일링 (HPA)
- 서비스 간 네트워크 격리

### 배포 구조
```yaml
# Backend 배포
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bodam-backend
  labels:
    version: blue  # 또는 green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bodam-backend
      version: blue
```

### 핵심 구현 가이드
- 라벨 기반 트래픽 스위칭
- ConfigMap + Secret 분리
- Persistent Volume for static files
- 헬스체크: `/healthz`, `/readyz`

## 8. 테스트 전략

### 계층별 테스트
1. **단위 테스트**: pytest + httpx (비동기 지원)
2. **E2E 테스트**: Tavern (YAML 기반 API 시나리오)
3. **보안 테스트**: BOLA (권한 분리 검증)
4. **성능 테스트**: k6 (목표: p95 < 300ms)

### BOLA 테스트 중점 영역
```python
# 다른 사용자 기부 내역 접근 차단 테스트
def test_donation_access_control():
    user_a_token = get_auth_token("user_a")
    user_b_donation_id = create_donation("user_b")

    response = client.get(
        f"/donations/{user_b_donation_id}",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert response.status_code == 403  # Forbidden
```

### CI/CD 파이프라인
```yaml
# GitHub Actions 단계
- name: Test Pipeline
  run: |
    ruff check .
    black --check .
    mypy .
    pytest --cov=src --cov-report=xml
    coverage report --fail-under=70
```

## 9. 보안 구현 가이드

### 인증/인가
- JWT Access Token: 15분 만료
- Refresh Token: Redis 저장, 7일 만료
- HttpOnly 쿠키: XSS 방지

### API 보안
```python
# Rate Limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_requests = await redis.get(f"rate_limit:{client_ip}")
    if current_requests and int(current_requests) > 100:  # 분당 100회
        raise HTTPException(429, "Too Many Requests")
```

### 데이터 보호
- PII 마스킹 로그
- 결제 정보 암호화 저장
- SQL 인젝션 방지 (Parameterized Query)

## 최종 권장사항

1. **개발 순서**: 인증 → 결제 → 데이터 수집 → AI 분석 → 알림
2. **성능 최적화**: DB 인덱싱 → 캐싱 → CDN → 코드 최적화
3. **모니터링**: 에러율 < 0.5%, 응답시간 p95 < 300ms 유지
4. **확장성**: 컨테이너 기반 마이크로서비스로 개별 스케일링

모든 기술 결정은 실시간 처리, 확장성, 유지보수성을 고려하여 선택되었으며, 단계별 구현을 통해 복잡도를 관리할 예정입니다.