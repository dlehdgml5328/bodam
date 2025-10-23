# RedisInsight 사용 가이드

## 🚀 빠른 시작

### 1. 브라우저에서 열기
```
http://localhost:5540
```

### 2. Redis 연결 추가

RedisInsight를 처음 열면 연결 설정 화면이 나옵니다.

#### Redis Cache (채팅 기록)
- **이름**: bodam-redis-cache
- **Host**: `bodam-redis-cache` (또는 `localhost`)
- **Port**: `6379`
- **Database**: `0`

#### Redis Queue (Celery 작업)
- **이름**: bodam-redis-queue
- **Host**: `bodam-redis-queue` (또는 `localhost`)
- **Port**: `6380`
- **Database**: `0`

#### Redis Semantic (시맨틱 캐시)
- **이름**: bodam-redis-semantic
- **Host**: `bodam-redis-semantic` (또는 `localhost`)
- **Port**: `6381`
- **Database**: `2`

## 📊 주요 기능

### 1. 채팅 기록 보기 (Redis Cache)

**연결**: bodam-redis-cache

**키 패턴 검색**:
```
chat:context:*
```

**예시**:
- `chat:context:test-rag-session` - 테스트 세션의 채팅 기록
- `chat:context:92964fd6-87d3-4f63-9462-b6c0da6a8fcf` - 실제 사용자 세션

**내용 보기**:
1. 키 클릭
2. JSON 포맷으로 대화 내용 확인
3. messages 배열에 user/assistant 메시지 저장됨

### 2. 시맨틱 캐시 보기 (Redis Semantic)

**연결**: bodam-redis-semantic

**키 패턴 검색**:
```
semantic:chat:*
```

**내용**:
- 쿼리와 응답 캐시
- 임베딩 벡터 (1024차원)
- 유사도 95% 이상일 때 재사용

### 3. Celery 작업 큐 보기 (Redis Queue)

**연결**: bodam-redis-queue

**키 패턴**:
- `celery-task-meta-*` - 작업 메타데이터
- `_kombu.*` - 메시지 큐

## 🔍 유용한 기능

### 1. Browser 탭
- **키 검색**: 패턴으로 검색 가능 (`chat:*`, `semantic:*`)
- **자동 새로고침**: 실시간 데이터 확인
- **JSON 포맷팅**: 보기 쉬운 형태로 표시

### 2. Workbench 탭 (Redis 명령어)
```redis
# 모든 채팅 세션 보기
KEYS chat:context:*

# 특정 세션 내용 보기
GET chat:context:test-rag-session

# 채팅 기록 개수
DBSIZE

# 특정 키 TTL 확인 (남은 시간)
TTL chat:context:test-rag-session

# 모든 시맨틱 캐시 보기
KEYS semantic:chat:*
```

### 3. CLI 탭
실시간 Redis 명령어 실행

### 4. Profiler 탭
Redis 명령어 모니터링 (성능 분석)

## 📈 데이터 구조 예시

### 채팅 기록 (chat:context:*)
```json
{
  "messages": [
    {
      "role": "user",
      "content": "문서 업로드는 어떻게 하나요?",
      "timestamp": "2025-10-23T05:24:03.731084"
    },
    {
      "role": "assistant",
      "content": "문서 업로드는 몇 가지 단계를...",
      "timestamp": "2025-10-23T05:24:03.731095"
    }
  ],
  "created_at": "2025-10-23T05:24:00.538425",
  "updated_at": "2025-10-23T05:24:40.955245"
}
```

### 시맨틱 캐시 (semantic:chat:*)
```json
{
  "query": "문서 업로드는 어떻게 하나요?",
  "response": "문서 업로드는...",
  "sources": [...],
  "embedding": [0.04380608, 0.05076662, ...],  // 1024차원
  "query_type": "document",
  "cached_at": "2025-10-23T05:24:03.000000"
}
```

## 🎯 실습: 채팅 기록 확인하기

1. **RedisInsight 열기**: http://localhost:5540
2. **연결 추가**: bodam-redis-cache (localhost:6379)
3. **Browser 탭** 클릭
4. **검색창**에 `chat:*` 입력
5. **키 클릭**하여 내용 확인
6. JSON 형태로 당신이 물어본 질문과 답변 확인!

## 💡 팁

- **실시간 모니터링**: Browser 탭에서 자동 새로고침 켜기
- **TTL 확인**: 키 옆에 남은 시간 표시됨
- **필터링**: 키 패턴 검색으로 원하는 데이터만 보기
- **JSON 뷰어**: 복잡한 데이터도 깔끔하게 표시

## 🛑 RedisInsight 종료

```bash
docker-compose -f docker-compose.dev.yml stop redis-insight
```

## 🔄 RedisInsight 재시작

```bash
docker-compose -f docker-compose.dev.yml start redis-insight
```

---

**포트**: http://localhost:5540
**상태 확인**: `docker ps | grep redis-insight`
