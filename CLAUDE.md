# 보담(BoDam) 개발 가이드라인

Auto-generated from all feature plans. Last updated: 2025-10-15

## Active Technologies
- Python 3.11+ + FastAPI, SQLAlchemy (001-bashclaudecli-specify-bodam)
- TypeScript/Node.js 18+ + Next.js, TailwindCSS (001-bashclaudecli-specify-bodam)
- PostgreSQL + pgvector + PostGIS (001-bashclaudecli-specify-bodam)
- Celery + Redis (001-bashclaudecli-specify-bodam)
- Kong Gateway 3.x + NGINX 1.24+ (002-kong-gateway-selenium-migration)
- Selenium 4.15+ + ChromeDriver (002-kong-gateway-selenium-migration)
- Kubernetes + cert-manager (002-kong-gateway-selenium-migration)

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

# Kong Gateway (local testing)
docker run -d --name kong \
  -e "KONG_DATABASE=off" \
  -e "KONG_DECLARATIVE_CONFIG=/kong.yaml" \
  -p 8000:8000 -p 8001:8001 \
  -v $(pwd)/specs/002-kong-gateway-selenium-migration/contracts/kong-gateway-routes.yaml:/kong.yaml \
  kong:3.5-alpine

# Kong Gateway validation
docker exec kong kong config parse /kong.yaml

# Selenium crawler tests
pytest tests/integration/test_selenium_crawler.py -v

# Infrastructure deployment
kubectl apply -f infra/k8s/kong/
kubectl apply -f infra/k8s/nginx/

## Code Style
- Python: FastAPI + SQLAlchemy 2.0 async patterns, pytest for testing
- TypeScript: Next.js App Router, TailwindCSS utilities, Jest + Playwright for testing
- Korean comments and documentation preferred
- TDD mandatory: Tests first, then implementation

## Recent Changes
- 002-kong-gateway-selenium-migration: Migrated from NGINX Ingress to Kong Gateway for API routing, replaced BeautifulSoup4 with Selenium for dynamic content crawling
- 001-bashclaudecli-specify-bodam: Added 커피 기부 플랫폼 with FastAPI + Next.js + PostgreSQL stack

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->