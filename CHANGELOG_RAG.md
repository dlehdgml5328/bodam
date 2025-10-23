# RAG 시스템 구축 완료 - 2025-10-23

## 🎯 구현 내용

Admin LLM 챗봇에 RAG (Retrieval-Augmented Generation) 기능을 추가하여 내부 문서 기반 질의응답이 가능하도록 구현했습니다.

## ✨ 주요 기능

### 1. 문서 기반 검색 시스템
- **지원 파일 형식**: PDF, Markdown, 텍스트
- **자동 청킹**: 800자 단위, 100자 오버랩
- **벡터 검색**: pgvector + ivfflat 인덱스
- **유사도 임계값**: 70% 이상

### 2. 임베딩 모델 변경
- **기존**: `togethercomputer/m2-bert-80M-8k-retrieval` (768차원) - 503 에러
- **신규**: `BAAI/bge-large-en-v1.5` (1024차원) - 정상 작동

### 3. 자동 임베딩 생성 API
- **엔드포인트**: `POST /admin-api/knowledge/embed-all`
- **기능**: knowledge_docs 폴더의 모든 문서 자동 임베딩
- **중복 방지**: 파일 해시 기반 중복 체크

## 📂 변경된 파일

### Backend

**새로 추가된 파일:**
- `backend/alembic/versions/015_update_embedding_dimension.py` - DB 마이그레이션 (768→1024)
- `backend/knowledge_docs/` - 문서 저장 폴더 (로컬과 동기화)
  - `README.md` - 폴더 사용 가이드
  - `사용법.md` - 임베딩 생성 가이드
  - `test_rag.md` - RAG 테스트 문서
  - `system_architecture.md` - 시스템 아키텍처
  - `document_upload_guide.md` - 문서 업로드 가이드

**수정된 파일:**
- `backend/src/models/knowledge_document.py` - Vector 차원 768→1024
- `backend/src/admin/llama_chat/service.py` - 임베딩 모델 변경, session_scope 수정
- `backend/src/workers/knowledge_ingestor.py` - 임베딩 모델 변경
- `backend/src/api/admin/knowledge.py` - `embed-all` 엔드포인트 추가
- `backend/.env` - `TOGETHER_AI_MODEL` 추가
- `.env` - `TOGETHER_AI_MODEL` 추가
- `docker-compose.dev.yml` - knowledge_docs 볼륨 마운트 추가, 모델 환경변수 수정

## 🔧 기술 스택

### AI/ML
- **LLM**: meta-llama/Llama-3.3-70B-Instruct-Turbo (Together AI)
- **임베딩**: BAAI/bge-large-en-v1.5 (1024차원)
- **벡터 DB**: PostgreSQL 16 + pgvector
- **인덱스**: ivfflat (lists=100)

### 검색 설정
- **청크 크기**: 800자
- **청크 오버랩**: 100자
- **유사도 임계값**: 0.7 (70%)
- **기본 반환 개수**: 3개

## 📊 성능

### 검색 정확도 테스트
```
질문: "문서 업로드는 어떻게 하나요?"
→ 유사도: 71.6% ✅
→ 쿼리 타입: document (RAG)

질문: "PDF 파일도 업로드할 수 있어?"
→ 유사도: 80.9% ✅
→ 쿼리 타입: document (RAG)

질문: "LLM 모델이 뭐야?"
→ 유사도: 73.4% ✅
→ 쿼리 타입: document (RAG)
```

### 응답 시간
- 평균: ~4초
- 캐시 히트: <500ms

## 🚀 사용 방법

### 1. 문서 추가
```bash
# 파일을 backend/knowledge_docs/에 복사
cp your_document.pdf backend/knowledge_docs/
```

### 2. 임베딩 생성 (버튼 클릭)

**Swagger UI 사용 (가장 쉬움):**
1. http://localhost:8000/docs 열기
2. `/admin-api/knowledge/embed-all` 찾기
3. "Try it out" → "Execute" 클릭

**또는 curl:**
```bash
curl -X POST http://localhost:8000/admin-api/knowledge/embed-all
```

### 3. 채팅에서 사용
Admin 채팅에서 질문하면 자동으로 문서를 검색하여 답변합니다!

## 🔄 마이그레이션

데이터베이스 마이그레이션이 자동으로 실행됩니다:
```bash
docker-compose -f docker-compose.dev.yml up backend
# 자동으로 alembic upgrade 실행됨
```

## 📝 향후 개선 사항

- [ ] 파일 업로드 UI 추가
- [ ] 문서 관리 대시보드
- [ ] 실시간 파일 감지 자동 임베딩
- [ ] 다국어 임베딩 모델 지원
- [ ] 문서 버전 관리

## 🐛 알려진 이슈

- 없음 (현재 안정적으로 작동)

## 👥 기여자

- [@donghee] - RAG 시스템 구현, 임베딩 모델 변경, API 추가

---

**생성일**: 2025-10-23
**버전**: 1.0.0
**상태**: ✅ 완료
