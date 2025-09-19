FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install \
    fastapi>=0.110,<0.111 \
    uvicorn[standard]>=0.29,<0.30 \
    sqlalchemy>=2.0,<2.1 \
    alembic>=1.13,<1.14 \
    psycopg[binary]>=3.1,<3.2 \
    geoalchemy2>=0.14,<0.15 \
    pgvector>=0.2.5,<0.3 \
    asyncpg>=0.29,<0.30 \
    pydantic>=2.6,<2.8 \
    pydantic-settings>=2.2,<2.3 \
    celery>=5.3,<5.4 \
    redis>=5.0,<5.1 \
    httpx>=0.27,<0.28 \
    tenacity>=8.2,<8.3 \
    structlog>=23.1,<23.2 \
    prometheus-client>=0.20,<0.21

COPY src ./src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
