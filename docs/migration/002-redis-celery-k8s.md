# 002: Redis & Celery Kubernetes Migration

This document captures the rollout plan for migrating BoDam backend services from the shared Redis instance in docker-compose to dedicated Redis cache/queue clusters and managed Celery workloads on Kubernetes.

## Overview

- **Feature ID**: 002-cache-redis-queue
- **Date**: 2025-10-07
- **Goals**:
  - Split Redis responsibilities into cache (stateless) vs. queue (persistent) clusters.
  - Deploy dedicated Celery worker/beat/Flower workloads on Kubernetes.
  - Enable daily Redis queue backups to S3 and alerting for Celery incidents.

## Prerequisites

1. Kubernetes cluster with Prometheus Operator (ServiceMonitor) and NGINX Ingress installed.
2. Container registry containing `ghcr.io/bodam/backend:latest` image.
3. AWS S3 bucket (`bodam-redis-backups`) and credentials with write access.
4. `kubectl` configured with admin access to the target namespace.

## Migration Steps

### 1. Prepare secrets

```bash
cd infra/k8s/scripts
./create-secrets.sh        # Flower password + optional AWS credentials
```

- `flower-auth` secret stores the Basic Auth password for Flower.
- `aws-credentials` secret stores backup credentials (only if backups enabled).

### 2. Deploy infrastructure

A helper script encapsulates the required `kubectl apply` sequence:

```bash
cd infra/k8s/scripts
./deploy-redis-celery.sh
```

This performs the following:

1. Apply Redis cache manifests (`infra/k8s/redis/cache/`).
2. Apply Redis queue manifests (`infra/k8s/redis/queue/`).
3. Apply Celery worker/beat/Flower manifests (`infra/k8s/celery/`).
4. Apply Alertmanager rules (`infra/monitoring/alertmanager-celery-rules.yaml`).
5. Restart backend deployment to pick up new environment variables.

**Verification checklist**

- `kubectl get pods -l app=redis-cache` → 1 pod `Running`.
- `kubectl get pods -l app=redis-queue` → 1 pod `Running`, PVC `Bound`.
- `kubectl get pods -l app=celery-worker` → ≥2 pods `Running`.
- `kubectl get pods -l app=celery-beat` → exactly 1 pod `Running`.
- `kubectl get pods -l app=flower` → 1 pod `Running`.
- `kubectl port-forward service/flower-service 5555` and verify `/flower/api/workers` returns workers list.

### 3. Update backend code / configuration

- Backend deployment now uses `REDIS_CACHE_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND`.
- `backend/src/worker.py` reads Redis endpoints from environment.
- `backend/src/events/event_bus.py` now reads the cache URL via `REDIS_CACHE_URL`.

### 4. Run integration tests

Once cluster resources are in place:

```bash
venv/bin/pytest backend/tests/integration/test_redis_*.py backend/tests/integration/test_celery_*.py -v
```

All tests should pass after the Kubernetes resources are healthy and DNS routes resolve.

### 5. Retire docker-compose Redis

After verification:

```bash
docker compose stop redis
```

Confirm backend API continues to operate using the Kubernetes Redis endpoints.

### 6. Rollback plan

If issues arise:

1. Revert `infra/k8s/backend/deployment.yaml` to use `REDIS_URL` and the legacy Redis endpoint.
2. Scale down Kubernetes Redis/Celery deployments.
3. Restart backend: `kubectl rollout restart deployment/bodam-backend`.
4. Bring docker-compose Redis back online (`docker compose up -d redis`).

## Alerting

PrometheusRule `celery-alerts` triggers:

- **CeleryWorkerDown** (severity=critical) when the worker deployment has no available replicas for 5 minutes.
- **CeleryTaskQueueTooLong** (severity=warning) when the default queue backlog exceeds 1000 tasks for 10 minutes.
- Alerts route to Slack channel `#ops-celery`.

## Outstanding Items

- Configure TLS for Flower ingress via the cluster-wide certificate manager.
- Create a dedicated IAM role for Redis backup uploads.
- Integrate queue depth dashboards into Grafana.

## References

- Specs: `specs/002-cache-redis-queue/*`
- K8s manifests: `infra/k8s/redis/`, `infra/k8s/celery/`
- Alert rules: `infra/monitoring/alertmanager-celery-rules.yaml`
- Tests: `backend/tests/integration/test_redis_*.py`, `backend/tests/integration/test_celery_*.py`
