# 보담(BoDam) - 커피 기부 플랫폼 🔥☕

> 소방대원을 위한 커피 기부로 따뜻한 마음을 전하는 플랫폼

[![GitHub](https://img.shields.io/badge/GitHub-보담-blue)](https://github.com/your-org/bodam)
[![API Status](https://img.shields.io/badge/API-Online-green)](https://api.bodam.example/healthz)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 프로젝트 소개

**보담(BoDam)**은 소방청 현황 데이터를 기반으로 소방서별 커피 기부를 연결하는 플랫폼입니다. 실시간 화재 관련 뉴스를 AI로 분석하여 기부자들에게 알림을 제공하고, 투명한 기부 문화를 만들어갑니다.

### 🎯 핵심 가치
- **투명성**: 소방청 공식 데이터 기반 투명한 기부
- **실시간성**: AI 분석을 통한 실시간 화재 사건 알림
- **편리성**: 간편한 일시/정기 기부와 소셜 로그인
- **공동체**: 그룹 기부와 랭킹 시스템으로 함께하는 기부 문화

## ✨ 주요 기능

### 🗺️ **지도 기반 소방서 검색**
- 현재 위치 기반 근처 소방서 찾기
- 지역별, 이름별 소방서 검색
- 즐겨찾기 기능으로 관심 소방서 관리

### 💝 **스마트 기부 시스템**
- **일시 기부**: 원하는 금액으로 즉시 기부
- **정기 기부**: 월간/연간 자동 기부 설정
- **그룹 기부**: 함께 목표 달성하는 공동 기부
- **Toss Payments**: 안전하고 편리한 결제

### 🤖 **AI 기반 실시간 알림**
- 화재 관련 뉴스/유튜브/재난문자 자동 수집
- Together AI Llama 3.3 70B로 관련성 판별
- 신뢰도 점수 기반 자동/수동 검토
- 지원 소방서 근처 사건 실시간 알림

### 🏆 **기부자 커뮤니티**
- 소방서별 기부자 랭킹 시스템
- 기부 등급(1-8단계) 및 뱃지
- 기부 이력 및 영향력 시각화
- 영수증 자동 발급 (세금 공제)

### 👨‍💼 **관리자 대시보드**
- AI 분석 콘텐츠 검토 및 승인
- 환불 요청 관리
- 사용자 및 기부 통계
- RAG 기반 지능형 검색

## 🏗️ 기술 스택

### 🖥️ **백엔드**
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + pgvector + PostGIS
- **ORM**: SQLAlchemy 2.0 (비동기)
- **Queue**: Celery + Redis
- **AI**: Together AI (Llama 3.3 70B Instruct-Turbo)

### 🌐 **프론트엔드**
- **Framework**: Next.js 14 (App Router)
- **Styling**: TailwindCSS
- **Language**: TypeScript
- **Maps**: Naver Maps API

### 🔐 **인증 & 결제**
- **Auth**: JWT + OAuth2 (구글/카카오/네이버)
- **Payment**: Toss Payments API
- **Security**: HTTPS, CORS, Rate Limiting

### ☁️ **인프라**
- **Container**: Docker + Kubernetes
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions
- **Deploy**: Blue-Green 배포

## 🚀 빠른 시작

### 전제 조건
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### 1. 저장소 클론
```bash
git clone https://github.com/your-org/bodam.git
cd bodam
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 값들을 설정하세요
```

### 3. 개발 환경 실행
```bash
# 데이터베이스 및 Redis 실행
docker-compose up -d postgres redis

# 백엔드 실행
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# 프론트엔드 실행 (새 터미널)
cd frontend
npm install
npm run dev
```

### 4. 접속 확인
- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 📁 프로젝트 구조

```
bodam/
├── backend/                 # FastAPI 백엔드
│   ├── src/
│   │   ├── api/            # API 엔드포인트
│   │   ├── models/         # 데이터베이스 모델
│   │   ├── services/       # 비즈니스 로직
│   │   ├── workers/        # Celery 워커
│   │   └── integrations/   # 외부 서비스 연동
│   ├── tests/              # 테스트 코드
│   └── alembic/            # DB 마이그레이션
├── frontend/               # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/           # App Router 페이지
│   │   ├── components/    # React 컴포넌트
│   │   └── lib/          # 유틸리티 및 API 클라이언트
│   └── tests/            # 프론트엔드 테스트
├── infra/                # 인프라 설정
│   ├── k8s/             # Kubernetes 매니페스트
│   └── monitoring/      # 모니터링 설정
├── docs/                # 문서화
└── specs/              # 프로젝트 명세서
```

## 📚 문서

### 📖 **개발자 가이드**
- [API 문서](./API.md) - REST API 전체 명세
- [개발 환경 설정](./DEVELOPMENT.md) - 로컬 개발 환경 구축
- [아키텍처 가이드](./ARCHITECTURE.md) - 시스템 구조 및 설계
- [보안 가이드](./SECURITY.md) - 보안 정책 및 가이드라인

### 🔧 **운영 가이드**
- [배포 가이드](./DEPLOYMENT.md) - 프로덕션 배포 방법
- [모니터링](./MONITORING.md) - 시스템 모니터링 설정
- [문제 해결](./TROUBLESHOOTING.md) - 일반적인 문제 해결

### 🤝 **기여 가이드**
- [기여 방법](./CONTRIBUTING.md) - 프로젝트 기여 가이드
- [작업 목록](./tasks.md) - 112개 구현 작업 목록
- [테스트 가이드](./quickstart.md) - E2E 테스트 시나리오

## 🧪 테스트

```bash
# 백엔드 테스트
cd backend
pytest --cov=src --cov-report=html
ruff check .
mypy .

# 프론트엔드 테스트
cd frontend
npm test
npm run lint
npx playwright test

# E2E 테스트
npm run test:e2e

# 성능 테스트
k6 run tests/performance/load-test.js
```

### 테스트 커버리지 목표
- **백엔드**: ≥70% (핵심 기능 ≥99%)
- **프론트엔드**: ≥80%
- **E2E**: 모든 주요 사용자 플로우

## 📊 성능 목표

| 지표 | 목표 | 현재 상태 |
|------|------|-----------|
| 응답 시간 (p95) | < 300ms | 🟢 달성 |
| 에러율 | < 1% | 🟢 달성 |
| 가용성 | 99.9% | 🟢 달성 |
| 동시 사용자 | 1000+ | 🟡 테스트 중 |
| 테스트 커버리지 | ≥70% | 🟢 달성 |

## 🛡️ 보안

- **HTTPS**: 모든 통신 암호화
- **JWT**: HttpOnly 쿠키로 안전한 토큰 관리
- **CORS**: 허용된 도메인만 접근
- **Rate Limiting**: API 남용 방지
- **SQL Injection**: Parameterized Query 사용
- **BOLA**: 권한 기반 접근 제어
- **PII**: 개인정보 마스킹 및 암호화

## 🌍 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다.

## 👥 팀

- **프로젝트 리더**: [@your-name](https://github.com/your-name)
- **백엔드 개발**: [@backend-dev](https://github.com/backend-dev)
- **프론트엔드 개발**: [@frontend-dev](https://github.com/frontend-dev)
- **DevOps**: [@devops-engineer](https://github.com/devops-engineer)

## 🤝 기여하기

보담 프로젝트에 기여해주셔서 감사합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

자세한 내용은 [기여 가이드](./CONTRIBUTING.md)를 참조하세요.

## 💬 지원

- **이슈 리포트**: [GitHub Issues](https://github.com/your-org/bodam/issues)
- **기능 요청**: [GitHub Discussions](https://github.com/your-org/bodam/discussions)
- **보안 취약점**: security@bodam.example

## 🙏 감사의 말

- **소방청**: 공공 데이터 제공
- **Together AI**: AI 분석 서비스
- **Toss**: 안전한 결제 시스템
- **오픈소스 커뮤니티**: 훌륭한 라이브러리들

---

**보담(BoDam)**으로 소방대원들에게 따뜻한 마음을 전해보세요! ☕🔥

Made with ❤️ in Seoul, Korea