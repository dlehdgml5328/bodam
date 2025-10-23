# 문서 업로드 가이드

## 지원 파일 형식
- PDF (.pdf)
- Markdown (.md)
- 텍스트 (.txt)

## 업로드 방법
1. 파일을 `backend/knowledge_docs/` 디렉토리에 저장
2. API 호출: `POST /admin-api/knowledge/ingest`
3. 시스템이 자동으로 청킹 및 임베딩 생성

## 문서 청킹 설정
- 청크 크기: 800자
- 오버랩: 100자
- 중복 제거: 파일 해시 기반

## 검색 임계값
- 최소 유사도: 0.7 (70%)
- 기본 반환 문서 수: 3개

## 예시
```bash
# 1. 문서 파일 복사
cp my_document.pdf backend/knowledge_docs/

# 2. API 호출 (자동 임베딩 생성)
curl -X POST http://localhost:8000/admin-api/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/app/knowledge_docs/my_document.pdf"}'
```
