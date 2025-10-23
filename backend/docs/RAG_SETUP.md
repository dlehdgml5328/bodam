# RAG (Retrieval-Augmented Generation) 확장 가이드

## 개요

Admin LLM 채팅 서비스에 **문서 기반 질의(RAG)** 기능이 추가되었습니다. 이제 SQL 쿼리뿐만 아니라 내부 문서(PDF, Markdown, 텍스트)를 검색하여 답변을 생성할 수 있습니다.

## 주요 기능

### 1. 쿼리 모드
- **SQL 모드** (기존): 통계, 검색, 분석 쿼리 → SQL 실행
- **Document 모드** (신규): 운영 매뉴얼, 가이드 질의 → 문서 검색
- **Hybrid 모드** (신규): SQL + 문서 결합 답변

### 2. 문서 Ingestion
- PDF, Markdown, 텍스트 파일 지원
- 자동 청크 분할 (800자 단위, 100자 겹침)
- Together AI 임베딩 (768차원)
- pgvector 유사도 검색 (ivfflat 인덱스)
- 중복 방지 (파일 해시 + 수정시각 기준)

### 3. 관리 API
- 문서 목록/상세 조회
- 파일/디렉터리 수집 (Celery 태스크)
- 문서 삭제 (단일/출처별 일괄)

---

## 설치 및 설정

### 1. 의존성 설치

```bash
# pdfplumber 설치 (PDF 텍스트 추출)
cd backend
poetry add pdfplumber

# 또는 pip
pip install pdfplumber
```

### 2. 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
cd backend
alembic upgrade head

# 확인
psql -U postgres -d bodam -c "\d knowledge_documents"
```

### 3. 문서 저장 디렉터리 생성

```bash
mkdir -p data/knowledge_base/pdfs
mkdir -p data/knowledge_base/markdown
mkdir -p data/knowledge_base/text
```

---

## 사용 방법

### 1. 문서 수집 (Ingestion)

#### 단일 파일 수집

```python
from src.workers.knowledge_ingestor import ingest_file_task

# Celery 태스크로 수집
task = ingest_file_task.delay(
    file_path="data/knowledge_base/pdfs/manual.pdf",
    title="운영 매뉴얼",
)
print(f"Task ID: {task.id}")
```

#### 디렉터리 전체 수집

```python
from src.workers.knowledge_ingestor import ingest_directory_task

# 재귀적으로 모든 PDF/MD/TXT 파일 수집
task = ingest_directory_task.delay(
    directory_path="data/knowledge_base",
    recursive=True,
)
```

#### API로 수집 시작

```bash
# 단일 파일
curl -X POST http://localhost:8000/admin-api/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "path": "data/knowledge_base/pdfs/manual.pdf",
    "title": "운영 매뉴얼"
  }'

# 디렉터리
curl -X POST http://localhost:8000/admin-api/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "path": "data/knowledge_base/pdfs",
    "recursive": true
  }'
```

### 2. 문서 기반 질의 (Admin Chat)

```bash
# 문서 질의 예시
curl -X POST http://localhost:8000/admin-api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "화재 출동 절차는 어떻게 되나요?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**응답 예시**:
```json
{
  "response": "화재 출동 절차는 다음과 같습니다. [운영 매뉴얼 3장]에 따르면...",
  "sources": [
    {
      "doc_id": "...",
      "source": "data/knowledge_base/pdfs/manual.pdf",
      "title": "운영 매뉴얼",
      "section": "3장",
      "similarity": 0.89
    }
  ],
  "execution_time_ms": 1234.5,
  "cached": false,
  "query_type": "document"
}
```

### 3. 하이브리드 질의 (SQL + 문서)

```bash
# 통계 + 운영 가이드 통합 답변
curl -X POST http://localhost:8000/admin-api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "서울 지역 화재가 몇 건인지, 그리고 대응 절차는?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**응답**: SQL 결과(건수) + 문서(대응 절차)를 통합한 답변

---

## 문서 관리 API

### 문서 목록 조회

```bash
curl -X GET "http://localhost:8000/admin-api/knowledge/documents?limit=10"
```

### 문서 상세 조회

```bash
curl -X GET "http://localhost:8000/admin-api/knowledge/documents/{doc_id}"
```

### 문서 삭제

```bash
# 단일 문서 삭제
curl -X DELETE "http://localhost:8000/admin-api/knowledge/documents/{doc_id}"

# 출처별 일괄 삭제
curl -X DELETE "http://localhost:8000/admin-api/knowledge/documents?source=data/knowledge_base/pdfs/old_manual.pdf"
```

---

## 설정 커스터마이징

### LlamaChatService 설정

```python
from src.admin.llama_chat.service import LlamaChatService

service = LlamaChatService(
    embedding_model="togethercomputer/m2-bert-80M-8k-retrieval",  # 임베딩 모델
)

# RAG 설정 조정
service.rag_top_k = 5  # 검색할 문서 개수 (기본: 3)
service.rag_similarity_threshold = 0.6  # 최소 유사도 (기본: 0.7)
```

### DocumentIngestor 설정

```python
from src.workers.knowledge_ingestor import DocumentIngestor

ingestor = DocumentIngestor(
    chunk_size=1000,  # 청크 크기 (기본: 800)
    chunk_overlap=150,  # 겹침 크기 (기본: 100)
)

await ingestor.ingest_file("manual.pdf")
```

---

## 운영 가이드

### 1. 정기 문서 업데이트

Celery Beat로 주기적 수집 스케줄링:

```python
# celerybeat-schedule.py
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'ingest-knowledge-daily': {
        'task': 'knowledge.ingest_directory',
        'schedule': crontab(hour=2, minute=0),  # 매일 새벽 2시
        'args': ('data/knowledge_base', None, True),
    },
}
```

### 2. 모니터링

```bash
# Celery 태스크 로그 확인
celery -A src.workers inspect active

# 문서 개수 확인
psql -U postgres -d bodam -c "SELECT source, COUNT(*) FROM knowledge_documents GROUP BY source"

# 임베딩 상태 확인
psql -U postgres -d bodam -c "SELECT COUNT(*) FROM knowledge_documents WHERE embedding IS NULL"
```

### 3. 성능 최적화

#### pgvector 인덱스 재구성 (문서 1000개 이상일 때)

```sql
-- lists 파라미터를 문서 개수의 제곱근으로 조정
DROP INDEX IF EXISTS ix_knowledge_documents_embedding_ivfflat;

CREATE INDEX ix_knowledge_documents_embedding_ivfflat
ON knowledge_documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 200);  -- 예: 문서 40000개면 lists=200
```

---

## 문제 해결

### 1. 임베딩 생성 실패

**증상**: `embedding is None` 경고 로그

**해결**:
- Together AI API 키 확인: `TOGETHER_AI_API_KEY`
- Rate Limit 확인: `TOGETHER_AI_MIN_INTERVAL` 조정 (기본: 0.2초)

### 2. PDF 텍스트 추출 실패

**증상**: 빈 content, "pdfplumber not installed" 오류

**해결**:
```bash
pip install pdfplumber
```

이미지 기반 PDF의 경우 OCR 필요 (향후 확장):
```bash
pip install pytesseract
```

### 3. 유사도 검색 느림

**증상**: 검색 시간 > 1초

**해결**:
- pgvector ivfflat 인덱스 확인
- `lists` 파라미터 조정 (문서 개수의 제곱근)
- 임베딩 차원 확인 (768차원)

---

## 다음 단계

### 기능 확장 (선택)
1. **Markdown/HTML 청크 개선**: 헤더 기반 분할
2. **OCR 지원**: 이미지 기반 PDF 텍스트 추출
3. **메타데이터 필터링**: 날짜, 카테고리별 문서 검색
4. **문서 버전 관리**: 같은 파일의 여러 버전 추적
5. **프론트엔드 UI**: 문서 출처 카드, 다운로드 버튼

### 성능 모니터링
- Ingestion 성공률, 실패 파일 추적
- RAG 유사도 히트율, LLM 호출 latency
- 문서별 검색 빈도 분석

---

## 참고 자료

- [pgvector 문서](https://github.com/pgvector/pgvector)
- [Together AI Embedding API](https://docs.together.ai/docs/embeddings)
- [pdfplumber 가이드](https://github.com/jsvine/pdfplumber)
