# GitHub Secrets 설정 가이드

이 가이드는 CI/CD 파이프라인 실행을 위한 GitHub Secrets 설정 방법을 안내합니다.

## 설정 방법

### 웹 인터페이스
1. GitHub 레포지토리 → **Settings**
2. 좌측 메뉴 → **Secrets and variables** → **Actions**
3. **New repository secret** 클릭
4. 아래 목록의 Secret을 하나씩 추가

### GitHub CLI 사용 (추천)
```bash
# GitHub CLI 로그인
gh auth login

# Secret 추가
gh secret set SECRET_NAME
# 엔터 후 값 입력 (입력 내용은 표시되지 않음)
```

---

## 필수 Secrets 목록

### 1. DigitalOcean 관련

#### `DIGITALOCEAN_TOKEN`
- **설명**: DigitalOcean API 토큰
- **생성 방법**:
  1. [DigitalOcean 콘솔](https://cloud.digitalocean.com/account/api/tokens) 접속
  2. **Generate New Token** 클릭
  3. Token name: `bodam-ci-cd`
  4. Scopes: **Read & Write** 선택
  5. 생성된 토큰 복사 (한 번만 표시됨!)

```bash
gh secret set DIGITALOCEAN_TOKEN
# 값 입력: dop_v1_xxxxxxxxxxxxxxxxxxxxx
```

#### `DIGITALOCEAN_CLUSTER_ID_PROD`
- **설명**: Production Kubernetes 클러스터 ID
- **생성 방법**:
  ```bash
  # doctl 설치
  brew install doctl  # macOS
  # 또는
  snap install doctl  # Linux

  # 인증
  doctl auth init
  # DIGITALOCEAN_TOKEN 입력

  # 클러스터 생성 (아직 없는 경우)
  doctl kubernetes cluster create bodam-prod \
    --region sgp1 \
    --version 1.28.2-do.0 \
    --node-pool "name=pool-1;size=s-2vcpu-4gb;count=2;auto-scale=true;min-nodes=1;max-nodes=3"

  # 클러스터 ID 확인
  doctl kubernetes cluster list
  # ID 컬럼의 UUID 복사
  ```

```bash
gh secret set DIGITALOCEAN_CLUSTER_ID_PROD
# 값 입력: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### `DIGITALOCEAN_CLUSTER_ID_PREVIEW`
- **설명**: Preview/Staging Kubernetes 클러스터 ID
- **옵션**: Production과 동일한 클러스터 사용 가능 (비용 절약)

```bash
# 별도 클러스터 생성 (선택)
doctl kubernetes cluster create bodam-preview \
  --region sgp1 \
  --version 1.28.2-do.0 \
  --node-pool "name=pool-1;size=s-2vcpu-4gb;count=1;auto-scale=true;min-nodes=1;max-nodes=2"

# 또는 Production과 동일한 ID 사용
gh secret set DIGITALOCEAN_CLUSTER_ID_PREVIEW
# 값 입력: (동일한 UUID 또는 별도 클러스터 ID)
```

---

### 2. Database 관련

#### `DATABASE_URL`
- **설명**: PostgreSQL 연결 문자열
- **형식**: `postgresql+asyncpg://user:password@host:port/database`

**옵션 1: DigitalOcean Managed Database (권장)**
```bash
# DigitalOcean 콘솔에서 Database 생성
# 1. Databases → Create Database
# 2. PostgreSQL 16 선택
# 3. Region: Singapore (SGP1)
# 4. Plan: Basic ($15/month)
# 5. Connection String 복사

gh secret set DATABASE_URL
# 값 예시: postgresql+asyncpg://doadmin:AVNS_xxxxxx@db-postgresql-sgp1-xxxxx.ondigitalocean.com:25060/defaultdb?sslmode=require
```

**옵션 2: 자체 호스팅 PostgreSQL**
```bash
# Kubernetes에 PostgreSQL 배포 후
gh secret set DATABASE_URL
# 값 예시: postgresql+asyncpg://bodam:yourpassword@postgresql.bodam.svc.cluster.local:5432/bodam
```

---

### 3. Backend 관련

#### `JWT_SECRET_KEY`
- **설명**: JWT 토큰 서명 키 (32자 이상 권장)
- **생성**:
  ```bash
  # 안전한 랜덤 키 생성
  openssl rand -base64 32
  ```

```bash
gh secret set JWT_SECRET_KEY
# 값 입력: (생성된 랜덤 문자열)
```

#### `TOGETHER_AI_API_KEY`
- **설명**: Together AI API 키 (Llama 3.3 사용)
- **생성 방법**:
  1. [Together AI](https://api.together.xyz/) 회원가입
  2. Dashboard → API Keys
  3. Create New API Key

```bash
gh secret set TOGETHER_AI_API_KEY
# 값 입력: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### `ADMIN_SECRET_KEY`
- **설명**: SQLAdmin 세션 암호화 키
- **생성**:
  ```bash
  openssl rand -base64 32
  ```

```bash
gh secret set ADMIN_SECRET_KEY
# 값 입력: (생성된 랜덤 문자열)
```

---

### 4. API URL 관련

#### `PRODUCTION_API_URL`
- **설명**: Production 백엔드 API URL
- **설정 시점**: 클러스터 배포 후 LoadBalancer IP 확인 후 설정

```bash
# 배포 후 확인
kubectl get svc nginx-ingress-service -n bodam-prod
# EXTERNAL-IP 확인

gh secret set PRODUCTION_API_URL
# 값 예시: http://203.0.113.10
# 또는 도메인 설정 후: https://api.bodam.kr
```

#### `PREVIEW_API_URL`
- **설명**: Preview 환경 백엔드 API URL

```bash
gh secret set PREVIEW_API_URL
# 값 예시: http://203.0.113.20
# 또는: https://preview-api.bodam.kr
```

---

### 5. Vercel 관련 (Frontend)

#### `VERCEL_TOKEN`
- **설명**: Vercel API 토큰
- **생성 방법**:
  1. [Vercel 대시보드](https://vercel.com/account/tokens) 접속
  2. **Create Token** 클릭
  3. Scope: **Full Access** 선택
  4. 토큰 복사

```bash
gh secret set VERCEL_TOKEN
# 값 입력: xxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### `VERCEL_ORG_ID`
- **설명**: Vercel Organization/Team ID
- **확인 방법**:
  ```bash
  # Vercel CLI 설치
  npm i -g vercel

  # 로그인
  vercel login

  # 프로젝트 디렉토리에서
  cd frontend
  vercel link

  # .vercel/project.json 확인
  cat .vercel/project.json
  # "orgId" 값 복사
  ```

```bash
gh secret set VERCEL_ORG_ID
# 값 입력: team_xxxxxxxxxxxx
```

#### `VERCEL_PROJECT_ID`
- **설명**: Vercel 프로젝트 ID
- **확인 방법**:
  ```bash
  # .vercel/project.json 확인
  cat frontend/.vercel/project.json
  # "projectId" 값 복사
  ```

```bash
gh secret set VERCEL_PROJECT_ID
# 값 입력: prj_xxxxxxxxxxxx
```

#### `NEXT_PUBLIC_API_URL`
- **설명**: 프론트엔드에서 사용할 API URL (브라우저에서 접근)
- **설정**: Production API URL과 동일하거나 퍼블릭 도메인

```bash
gh secret set NEXT_PUBLIC_API_URL
# 값 입력: https://api.bodam.kr
```

---

### 6. Slack 알림 (선택사항)

#### `SLACK_WEBHOOK_URL`
- **설명**: 배포 알림을 받을 Slack Webhook URL
- **생성 방법**:
  1. Slack 워크스페이스 → Apps
  2. **Incoming Webhooks** 검색 및 추가
  3. 채널 선택 (#deployments 권장)
  4. Webhook URL 복사

```bash
gh secret set SLACK_WEBHOOK_URL
# 값 입력: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

---

### 7. Codecov (선택사항)

#### `CODECOV_TOKEN`
- **설명**: 코드 커버리지 업로드 토큰
- **생성 방법**:
  1. [Codecov](https://codecov.io/) 로그인
  2. GitHub 레포지토리 연동
  3. Settings → Repository Upload Token 복사

```bash
gh secret set CODECOV_TOKEN
# 값 입력: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## 설정 확인

모든 Secret 설정 후 확인:

```bash
# 웹에서 확인
# Repository → Settings → Secrets and variables → Actions

# CLI로 확인
gh secret list
```

**필수 Secrets 체크리스트:**
- [ ] DIGITALOCEAN_TOKEN
- [ ] DIGITALOCEAN_CLUSTER_ID_PROD
- [ ] DIGITALOCEAN_CLUSTER_ID_PREVIEW
- [ ] DATABASE_URL
- [ ] JWT_SECRET_KEY
- [ ] TOGETHER_AI_API_KEY
- [ ] ADMIN_SECRET_KEY
- [ ] PRODUCTION_API_URL (배포 후)
- [ ] PREVIEW_API_URL (배포 후)
- [ ] VERCEL_TOKEN
- [ ] VERCEL_ORG_ID
- [ ] VERCEL_PROJECT_ID
- [ ] NEXT_PUBLIC_API_URL
- [ ] SLACK_WEBHOOK_URL (선택)
- [ ] CODECOV_TOKEN (선택)

---

## 초기 설정 순서

1. **DigitalOcean 계정 생성 및 토큰 발급**
   - `DIGITALOCEAN_TOKEN` 설정

2. **Kubernetes 클러스터 생성**
   - `DIGITALOCEAN_CLUSTER_ID_PROD` 설정
   - `DIGITALOCEAN_CLUSTER_ID_PREVIEW` 설정

3. **Database 생성**
   - `DATABASE_URL` 설정

4. **암호화 키 생성**
   - `JWT_SECRET_KEY` 설정
   - `ADMIN_SECRET_KEY` 설정

5. **외부 API 키 발급**
   - `TOGETHER_AI_API_KEY` 설정

6. **Vercel 프로젝트 연동**
   - `VERCEL_TOKEN` 설정
   - `VERCEL_ORG_ID` 설정
   - `VERCEL_PROJECT_ID` 설정

7. **첫 배포 후 API URL 설정**
   - `PRODUCTION_API_URL` 설정
   - `PREVIEW_API_URL` 설정
   - `NEXT_PUBLIC_API_URL` 설정

8. **알림 설정 (선택)**
   - `SLACK_WEBHOOK_URL` 설정
   - `CODECOV_TOKEN` 설정

---

## 다음 단계

Secrets 설정 완료 후:
1. `wonuk` 또는 `donghee` 브랜치에 코드 push
2. GitHub Actions 자동 실행 확인
3. 배포 성공 시 API URL Secrets 업데이트

문제 발생 시:
- GitHub Actions 로그 확인
- Kubernetes Pod 상태 확인: `kubectl get pods -n bodam-prod`
