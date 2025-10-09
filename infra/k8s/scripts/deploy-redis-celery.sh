#!/bin/bash
# Deploy Redis cache/queue and Celery resources for feature 002-cache-redis-queue.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
INFRA_DIR="$ROOT_DIR/infra"

echo "==> Ensuring secrets exist"
"$INFRA_DIR/k8s/scripts/create-secrets.sh"

echo "==> Deploying Redis cache"
kubectl apply -f "$INFRA_DIR/k8s/redis/cache/"

echo "==> Deploying Redis queue"
kubectl apply -f "$INFRA_DIR/k8s/redis/queue/"

echo "==> Deploying Celery resources"
kubectl apply -f "$INFRA_DIR/k8s/celery/"

echo "==> Applying Celery alerting rules"
kubectl apply -f "$INFRA_DIR/monitoring/alertmanager-celery-rules.yaml"

echo "==> Restarting backend deployment"
kubectl rollout restart deployment/bodam-backend
