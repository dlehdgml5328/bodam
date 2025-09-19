# BoDam 배포 가이드

## 사전 요구사항
- Kubernetes 클러스터 (1.27+)
- PostgreSQL 및 Redis 인프라
- GitHub Container Registry 접근 권한
- Vercel 계정 (프론트엔드)

## 백엔드 배포
1. `docker-compose`로 로컬 테스트 후 이미지를 빌드합니다.
2. `ghcr.io/bodam/backend:latest` 태그로 푸시합니다.
3. `infra/k8s/backend/deployment.yaml`과 `infra/k8s/backend/service.yaml`을 적용합니다.
4. `kubectl rollout status deployment/bodam-backend`로 배포 상태를 확인합니다.

## 프론트엔드 배포
1. `frontend/Dockerfile`을 사용해 이미지 생성 후 `ghcr.io/bodam/frontend:latest`로 푸시합니다.
2. `infra/k8s/frontend/deployment.yaml`을 적용하거나 Vercel에 연결합니다.
3. 환경 변수 `NEXT_PUBLIC_API_BASE_URL`을 API 엔드포인트로 설정합니다.

## CI/CD
- `.github/workflows/ci.yml`을 사용해 기본 테스트와 빌드를 자동화합니다.
- 프로덕션 배포는 GitHub Actions에서 수동 승인 단계를 추가해 운영합니다.

## 모니터링
- `/healthz`, `/readyz` 엔드포인트로 상태 확인
- Prometheus 스크레이프 대상에 `/metrics` 추가 (TODO: 운영 시 구현)

## 롤백 전략
- 이전 이미지 태그 기록을 유지합니다.
- `kubectl rollout undo deployment/bodam-backend`로 빠르게 롤백합니다.

