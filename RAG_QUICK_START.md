# RAG 확장 빠른 시작 가이드

## 🎯 개요

Admin LLM 채팅에 **RAG(Retrieval-Augmented Generation)** 기능이 추가되었습니다!

### 기존 (SQL 전용)
```
질문: "서울 소방서는 몇 개?" → SQL 쿼리 → 답변: "25개"
```

### 확장 (RAG 추가)
```
질문: "화재 출동 절차는?" → 문서 검색 → 답변: "매뉴얼에 따르면..."
질문: "서울 화재 건수와 대응 절차는?" → SQL + 문서 → 하이브리드 답변
```

---

## ⚡ 빠른 설치 (3단계)

### 1. 의존성 설치

```bash
cd backend
pip install pdfplumber  # PDF 텍스트 추출용
```

### 2. 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
alembic upgrade head

# 확인
psql -U postgres -d bodam -c "\d knowledge_documents"
```

✅ `knowledge_documents` 테이블이 생성되면 성공!

### 3. 문서 디렉터리 준비

```bash
# 문서 저장 경로 생성
mkdir -p data/knowledge_base/pdfs
mkdir -p data/knowledge_base/markdown
mkdir -p data/knowledge_base/text

# 예시: 샘플 문서 추가
echo "화재 출동 절차는 다음과 같습니다..." > data/knowledge_base/text/procedure.txt
```

---

## 🚀 사용 예시

### 1. 문서 수집 (Ingestion)

#### API로 수집 (추천)

```bash
# 단일 파일 수집
curl -X POST http://localhost:8000/admin-api/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "path": "data/knowledge_base/pdfs/manual.pdf",
    "title": "운영 매뉴얼"
  }'

# 응답
{
  "status": "submitted",
  "task_id": "abc-123-def",
  "message": "파일 수집 태스크 시작: manual.pdf"
}
```

#### Python으로 수집

```python
from src.workers.knowledge_ingestor import ingest_file_task

# Celery 태스크 실행
task = ingest_file_task.delay(
    file_path="data/knowledge_base/pdfs/manual.pdf",
    title="운영 매뉴얼",
)
print(f"Task ID: {task.id}")
```

#### 진행 상태 확인

```bash
# Celery 태스크 로그
celery -A src.workers inspect active

# 수집된 문서 개수 확인
curl http://localhost:8000/admin-api/knowledge/documents?limit=10
```

---

### 2. RAG 질의 (Admin Chat)

#### 문서 기반 질의 (Document Mode)

```bash
curl -X POST http://localhost:8000/admin-api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "화재 출동 절차는 어떻게 되나요?",
    "session_id": "test-session-001"
  }'
```

**응답**:
```json
{
  "response": "화재 출동 절차는 다음과 같습니다. [운영 매뉴얼 3장]에 따르면, 1) 출동 신호 수신, 2) 장비 점검, 3) 현장 출동...",
  "sources": [
    {
      "doc_id": "uuid-...",
      "source": "data/knowledge_base/pdfs/manual.pdf",
      "title": "운영 매뉴얼",
      "section": "3장",
      "similarity": 0.92,
      "content_preview": "화재 출동 절차는..."
    }
  ],
  "execution_time_ms": 1234.5,
  "cached": false,
  "query_type": "document"
}
```

#### 하이브리드 질의 (SQL + Document)

```bash
curl -X POST http://localhost:8000/admin-api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "서울 지역 화재 건수는 몇 건이고, 대응 절차는?",
    "session_id": "test-session-001"
  }'
```

**응답**: 서울 화재 통계(SQL) + 대응 절차(문서)를 통합한 답변

---

## 📊 동작 원리

### 1. 문서 Ingestion 파이프라인

```
PDF/MD/TXT → 텍스트 추출 → 청크 분할 (800자)
  → Together AI 임베딩 (768차원) → DB 저장 (pgvector)
```

### 2. RAG 검색 흐름

```
사용자 질문 → 쿼리 분류 (SQL/Document/Hybrid)
  ↓ (Document 모드)
질문 임베딩 → pgvector 유사도 검색 (top-3)
  → LLM 컨텍스트 주입 → 답변 생성
```

### 3. 쿼리 분류 기준

| 쿼리 타입 | 예시 질문 | 처리 방식 |
|-----------|----------|-----------|
| **statistics** | "서울 소방서는 몇 개?" | SQL 쿼리 |
| **search** | "강남구 소방서 찾아줘" | SQL 쿼리 |
| **analysis** | "화재 트렌드 분석해줘" | SQL 쿼리 + LLM |
| **document** | "출동 절차는?" | 문서 검색 + LLM |
| **hybrid** | "서울 화재 건수와 절차는?" | SQL + 문서 + LLM |

---

## 🔧 설정 커스터마이징

### 환경 변수

```bash
# Together AI 설정
TOGETHER_AI_API_KEY=your-api-key
TOGETHER_AI_MIN_INTERVAL=0.2  # API 호출 간격 (초)

# DB 연결
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### 서비스 설정

```python
from src.admin.llama_chat.service import LlamaChatService

service = LlamaChatService()

# RAG 파라미터 조정
service.rag_top_k = 5  # 검색할 문서 개수 (기본: 3)
service.rag_similarity_threshold = 0.6  # 최소 유사도 (기본: 0.7)
```

---

## 📝 문서 관리 API

### 문서 목록 조회

```bash
curl -X GET "http://localhost:8000/admin-api/knowledge/documents?limit=10&source_filter=manual"
```

### 문서 상세 보기

```bash
curl -X GET "http://localhost:8000/admin-api/knowledge/documents/{doc_id}"
```

### 문서 삭제

```bash
# 단일 문서
curl -X DELETE "http://localhost:8000/admin-api/knowledge/documents/{doc_id}"

# 출처별 일괄 삭제
curl -X DELETE "http://localhost:8000/admin-api/knowledge/documents?source=old_manual.pdf"
```

---

## 🐛 문제 해결

### 1. 임베딩 생성 실패

**증상**: 로그에 "Embedding generation failed" 오류

**해결**:
```bash
# Together AI API 키 확인
echo $TOGETHER_AI_API_KEY

# Rate Limit 조정
export TOGETHER_AI_MIN_INTERVAL=0.5
```

### 2. PDF 텍스트 추출 안 됨

**증상**: PDF 파일 수집 시 빈 내용

**해결**:
```bash
# pdfplumber 설치 확인
pip install pdfplumber

# 이미지 기반 PDF는 OCR 필요 (향후 지원)
pip install pytesseract
```

### 3. 문서 검색 결과 없음

**증상**: "관련된 문서를 찾을 수 없습니다"

**체크리스트**:
- [ ] 문서가 실제로 수집되었는지 확인
  ```bash
  psql -U postgres -d bodam -c "SELECT COUNT(*) FROM knowledge_documents"
  ```
- [ ] 임베딩이 생성되었는지 확인
  ```bash
  psql -U postgres -d bodam -c "SELECT COUNT(*) FROM knowledge_documents WHERE embedding IS NOT NULL"
  ```
- [ ] 유사도 임계값 낮추기
  ```python
  service.rag_similarity_threshold = 0.5  # 기본: 0.7
  ```

---

## 🎓 다음 단계

### 추천 작업 흐름
1. **샘플 문서 수집**: 운영 매뉴얼, 절차 가이드 등 PDF/MD 파일 준비
2. **Ingestion 실행**: API 또는 Celery 태스크로 문서 수집
3. **테스트 질의**: Admin Chat에서 문서 기반 질의 테스트
4. **성능 모니터링**: 검색 속도, 유사도, LLM latency 확인
5. **정기 업데이트**: Celery Beat으로 주기적 문서 수집 스케줄링

### 상세 문서
- [전체 설정 가이드](backend/docs/RAG_SETUP.md)
- [테스트 가이드](backend/tests/unit/test_rag_pipeline.py)
- [모델 정의](backend/src/models/knowledge_document.py)
- [Ingestion 파이프라인](backend/src/workers/knowledge_ingestor.py)

---

## 📈 성능 기대치

### Semantic Cache 히트 (기존 SQL)
- 동일/유사 질문 → **< 500ms** (캐시)
- 신규 질문 → **1-3초** (LLM + SQL)

### Document RAG
- 캐시 미스 → **1.5-2.5초** (임베딩 + 검색 + LLM)
- 캐시 히트 → **< 600ms**

### Hybrid (SQL + Document)
- **2-4초** (SQL + 문서 검색 + LLM 통합)

---

## ✅ 체크리스트

구현 완료 항목:
- [x] knowledge_documents 테이블 (pgvector)
- [x] SQLAlchemy 모델 (KnowledgeDocument)
- [x] Ingestion 파이프라인 (PDF/MD/TXT 지원)
- [x] LlamaChatService RAG 확장
- [x] 문서 관리 API (CRUD)
- [x] 단위 테스트
- [x] 문서 (이 가이드 포함)

선택 확장 (향후):
- [ ] 프론트엔드 UI (출처 카드, 다운로드)
- [ ] Celery Beat 자동 수집
- [ ] OCR 지원 (이미지 PDF)
- [ ] Markdown/HTML 청크 개선
- [ ] 문서 버전 관리

---

**문의**: RAG 확장 관련 이슈는 GitHub Issues 또는 개발팀에 문의해주세요.

Happy RAG! 🚀
