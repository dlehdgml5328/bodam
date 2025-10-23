# RAG 시스템 테스트 문서

## 개요
이 문서는 보담(BoDam) 프로젝트의 RAG 시스템을 테스트하기 위한 샘플 문서입니다.

## 시스템 구성
- 임베딩 모델: BAAI/bge-large-en-v1.5 (1024차원)
- LLM 모델: Llama-3.3-70B-Instruct-Turbo
- 벡터 데이터베이스: PostgreSQL + pgvector

## 주요 기능
1. 문서 자동 임베딩 생성
2. 시맨틱 검색
3. 하이브리드 쿼리 (SQL + RAG)
