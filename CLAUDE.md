# 보담(BoDam) 개발 가이드라인

Auto-generated from all feature plans. Last updated: 2025-09-19

## Active Technologies
- Python 3.11+ + FastAPI, SQLAlchemy (001-bashclaudecli-specify-bodam)
- TypeScript/Node.js 18+ + Next.js, TailwindCSS (001-bashclaudecli-specify-bodam)
- PostgreSQL + pgvector + PostGIS (001-bashclaudecli-specify-bodam)
- Celery + Redis (001-bashclaudecli-specify-bodam)

## Project Structure
```
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

infra/
├── k8s/
└── ci-cd/
```

## Commands
# Backend
cd backend && pytest --cov=src --cov-report=xml && ruff check . && mypy .

# Frontend
cd frontend && npm test && npm run lint && npm run build

# Performance testing
k6 run tests/load-test.js

## Code Style
- Python: FastAPI + SQLAlchemy 2.0 async patterns, pytest for testing
- TypeScript: Next.js App Router, TailwindCSS utilities, Jest + Playwright for testing
- Korean comments and documentation preferred
- TDD mandatory: Tests first, then implementation

## Recent Changes
- 001-bashclaudecli-specify-bodam: Added 커피 기부 플랫폼 with FastAPI + Next.js + PostgreSQL stack

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->