# 보담(BoDam) 시스템 아키텍처

## 데이터베이스
- PostgreSQL 16 (pgvector + PostGIS 확장)
- Redis 3종 분리
  - Cache Redis: LRU 정책
  - Queue Redis: Celery 브로커
  - Semantic Redis: 벡터 저장소

## 백엔드 스택
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 (async ORM)
- Celery (백그라운드 작업)
- Together AI (LLM 및 임베딩)

## 프론트엔드
- Next.js (TypeScript)
- TailwindCSS

## AI/ML
- LLM: meta-llama/Llama-3.3-70B-Instruct-Turbo
- 임베딩: BAAI/bge-large-en-v1.5 (1024차원)
- 벡터 검색: pgvector (ivfflat 인덱스)
