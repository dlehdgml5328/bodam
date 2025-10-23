# Knowledge Documents 디렉토리

이 폴더는 RAG(Retrieval-Augmented Generation) 시스템을 위한 문서 저장소입니다.

## 사용 방법

### 1. 문서 추가
이 폴더에 PDF, Markdown, 또는 텍스트 파일을 추가하세요.

```bash
# 예시
cp your_document.pdf backend/knowledge_docs/
```

### 2. 임베딩 생성
API를 통해 문서를 처리하면 자동으로 임베딩이 생성됩니다.

```bash
curl -X POST http://localhost:8000/admin-api/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/app/knowledge_docs/your_document.pdf",
    "title": "문서 제목"
  }'
```

### 3. 채팅에서 사용
Admin 채팅에서 질문하면 자동으로 관련 문서를 검색하여 답변합니다.

```
질문: "문서 업로드는 어떻게 하나요?"
→ 시스템이 이 폴더의 문서를 검색하여 답변
```

## 현재 문서 목록

- `test_rag.md` - RAG 시스템 테스트 문서
- `system_architecture.md` - 보담 시스템 아키텍처
- `document_upload_guide.md` - 문서 업로드 가이드

## 기술 스펙

- **임베딩 모델**: BAAI/bge-large-en-v1.5 (1024차원)
- **벡터 DB**: PostgreSQL + pgvector
- **검색 방식**: 코사인 유사도 (threshold: 0.7)
