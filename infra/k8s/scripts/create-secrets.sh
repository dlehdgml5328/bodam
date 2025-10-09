#!/bin/bash
# K8s Secrets 생성 스크립트
# Feature: 002-cache-redis-queue

set -e

echo "Creating K8s Secrets for Redis & Celery deployment..."

# Flower Basic Auth Secret
read -p "Enter Flower password (default: admin123): " FLOWER_PASSWORD
FLOWER_PASSWORD=${FLOWER_PASSWORD:-admin123}

kubectl create secret generic flower-auth \
  --from-literal=password="${FLOWER_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Flower auth secret created"

# AWS Credentials for Redis backup (optional)
read -p "Create AWS credentials secret for Redis backup? (y/n): " CREATE_AWS
if [[ "$CREATE_AWS" == "y" ]]; then
  read -p "Enter AWS Access Key ID: " AWS_ACCESS_KEY_ID
  read -p "Enter AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY

  kubectl create secret generic aws-credentials \
    --from-literal=access-key-id="${AWS_ACCESS_KEY_ID}" \
    --from-literal=secret-access-key="${AWS_SECRET_ACCESS_KEY}" \
    --dry-run=client -o yaml | kubectl apply -f -

  echo "✅ AWS credentials secret created"
else
  echo "⏭️  Skipping AWS credentials (backup disabled)"
fi

echo ""
echo "🎉 All secrets created successfully!"
echo ""
echo "Verify with:"
echo "  kubectl get secrets | grep -E 'flower-auth|aws-credentials'"
