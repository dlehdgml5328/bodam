# 보담(BoDam) 프로젝트 - 미구현 기능 및 개선사항 상세 분석

## 📅 작성일: 2025-10-17
## 🎯 목적: 배포 전 필수 구현사항 및 개선 포인트 파악

---

## 📊 종합 요약

### ✅ 구현 완료 (Core Features)
- ✅ NFDS 실시간 화재 사고 크롤링 (Selenium + BeautifulSoup)
- ✅ FastAPI 백엔드 + Next.js 프론트엔드
- ✅ PostgreSQL + Redis (3종 분리: Cache, Queue, Semantic)
- ✅ Celery Workers + Beat Scheduler
- ✅ AI 매칭 (Together AI + LangGraph)
- ✅ Toss Payments 결제 통합
- ✅ 기본 인증/인가 (JWT)
- ✅ Docker Compose 개발 환경

### ❌ 미구현 또는 부족 (Critical Gaps)
총 **47개 항목** 확인됨

---

## 🔴 1. 배포 & 인프라 (Critical - 10개)

### 1.1 Kubernetes 배포 미완성
- ❌ **K8s manifests 있지만 실제 배포 테스트 안 됨**
  - 위치: `/infra/k8s/*/*.yaml` (33개 파일 존재)
  - 문제: kong, nginx, backend, redis, celery 등 YAML만 작성됨
  - **필요 작업**:
    - [ ] 실제 K8s 클러스터 구축 (DigitalOcean/AWS/GCP)
    - [ ] Helm Chart로 전환 고려
    - [ ] ConfigMap/Secret 환경변수 관리
    - [ ] PersistentVolume 설정 (PostgreSQL, Redis)
    - [ ] Ingress Controller 설정 (NGINX/Kong)

### 1.2 CI/CD 파이프라인 불완전
- ⚠️ **GitHub Actions 있지만 배포 단계 없음**
  - 현재: Lint + Test만 실행
  - 부족: Docker 빌드, 이미지 푸시, K8s 배포, 롤백
  - **필요 작업**:
    - [ ] Docker 이미지 빌드 & DockerHub/ECR 푸시
    - [ ] K8s 배포 자동화 (kubectl apply / Helm)
    - [ ] Blue-Green 배포 스크립트
    - [ ] 자동 롤백 메커니즘
    - [ ] 환경별 배포 (dev, staging, prod)

### 1.3 프로덕션 환경 설정 부재
- ❌ **`.env.production` 없음**
  - 현재: `.env.example`만 존재
  - **필요 작업**:
    - [ ] 프로덕션 환경 변수 정의
    - [ ] K8s Secrets 관리
    - [ ] 외부 서비스 URL (RDS, ElastiCache 등)

### 1.4 SSL/TLS 인증서 관리
- ⚠️ **cert-manager 설정 없음**
  - CLAUDE.md에 언급만 있음
  - **필요 작업**:
    - [ ] cert-manager 설치
    - [ ] Let's Encrypt 설정
    - [ ] TLS Ingress 설정

### 1.5 도메인 & DNS 설정
- ❌ **도메인 없음**
  - **필요 작업**:
    - [ ] 도메인 구매
    - [ ] DNS A/CNAME 레코드 설정
    - [ ] Cloudflare/Route53 설정

### 1.6 로드 밸런싱
- ⚠️ **Kong Gateway 설정 있지만 미테스트**
  - **필요 작업**:
    - [ ] Kong 로컬 테스트
    - [ ] Rate Limiting 정책 설정
    - [ ] Circuit Breaker 구현

### 1.7 데이터베이스 마이그레이션 전략
- ❌ **Alembic 마이그레이션 파일 없음**
  - **필요 작업**:
    - [ ] `alembic init` 실행
    - [ ] 초기 마이그레이션 생성
    - [ ] 자동 마이그레이션 스크립트

### 1.8 백업 & 복구 전략
- ❌ **DB/Redis 백업 전략 없음**
  - Redis Queue CronJob은 있지만 실행 안 됨
  - **필요 작업**:
    - [ ] PostgreSQL 자동 백업 (pg_dump)
    - [ ] Redis AOF/RDB 백업
    - [ ] S3/DO Spaces 백업 저장
    - [ ] 복구 테스트 시나리오

### 1.9 로그 수집
- ❌ **ELK Stack / Loki 없음**
  - **필요 작업**:
    - [ ] Fluentd/Promtail 설치
    - [ ] Elasticsearch/Loki 구축
    - [ ] 로그 retention 정책

### 1.10 Secrets 관리
- ❌ **Vault / K8s Secrets 관리 부족**
  - API 키가 `.env`에 하드코딩
  - **필요 작업**:
    - [ ] HashiCorp Vault 또는 AWS Secrets Manager
    - [ ] K8s SealedSecrets

---

## 🟠 2. 모니터링 & 관측성 (High Priority - 8개)

### 2.1 APM (Application Performance Monitoring)
- ❌ **APM 도구 없음**
  - Sentry, New Relic, DataDog 등 미설치
  - **필요 작업**:
    - [ ] Sentry for error tracking
    - [ ] New Relic APM 연동
    - [ ] Transaction tracing

### 2.2 Metrics 수집
- ❌ **Prometheus + Grafana 없음**
  - `/infra/k8s/monitoring/` 디렉토리 비어있음
  - **필요 작업**:
    - [ ] Prometheus Operator 설치
    - [ ] ServiceMonitor 설정
    - [ ] Grafana 대시보드 생성
    - [ ] AlertManager 알림 설정

### 2.3 Health Check 개선
- ⚠️ **기본 `/health` 엔드포인트만 존재**
  - DB, Redis 연결 체크 없음
  - **필요 작업**:
    - [ ] `/health/live` (Liveness Probe)
    - [ ] `/health/ready` (Readiness Probe)
    - [ ] 의존성 체크 (DB, Redis, External APIs)

### 2.4 Distributed Tracing
- ❌ **OpenTelemetry / Jaeger 없음**
  - 마이크로서비스 간 추적 불가
  - **필요 작업**:
    - [ ] OpenTelemetry SDK 통합
    - [ ] Jaeger/Zipkin 설치

### 2.5 Redis Monitoring
- ⚠️ **Redis Exporter 설정 있지만 Prometheus 없음**
  - **필요 작업**:
    - [ ] redis_exporter 연동
    - [ ] 메모리 사용량, 히트율 모니터링

### 2.6 Celery Monitoring
- ❌ **Flower 설정 있지만 접근 불가**
  - `flower-deployment.yaml` 있지만 미배포
  - **필요 작업**:
    - [ ] Flower 웹 UI 노출
    - [ ] Task 성공률, 실패율 모니터링

### 2.7 Custom Metrics
- ❌ **비즈니스 메트릭 없음**
  - 크롤링 성공률, 매칭 정확도 등
  - **필요 작업**:
    - [ ] Prometheus client_python 통합
    - [ ] Custom gauges/counters 정의

### 2.8 Alerting
- ❌ **알림 설정 없음**
  - **필요 작업**:
    - [ ] Slack/Discord webhook
    - [ ] PagerDuty 통합
    - [ ] 임계값 기반 알림

---

## 🟡 3. 보안 (High Priority - 9개)

### 3.1 API Rate Limiting
- ⚠️ **코드에 있지만 비활성화됨**
  - `ENABLE_RATE_LIMITING=false` in docker-compose
  - **필요 작업**:
    - [ ] 프로덕션에서 활성화
    - [ ] Redis 기반 Sliding Window
    - [ ] IP/User별 제한

### 3.2 CORS 정책 강화
- ⚠️ **현재 `http://localhost:3000`만 허용**
  - **필요 작업**:
    - [ ] 프로덕션 도메인 추가
    - [ ] Preflight caching

### 3.3 CSRF 보호
- ⚠️ **CSRF 토큰 구현 있지만 검증 부족**
  - **필요 작업**:
    - [ ] Double Submit Cookie 검증
    - [ ] SameSite 쿠키 설정

### 3.4 SQL Injection 방지
- ✅ SQLAlchemy ORM 사용으로 기본 방어
  - 하지만 raw query 사용 시 주의 필요
  - **필요 작업**:
    - [ ] 코드 리뷰 (parameterized query 확인)

### 3.5 XSS 방어
- ⚠️ **프론트엔드 입력 검증 부족**
  - **필요 작업**:
    - [ ] DOMPurify 라이브러리 추가
    - [ ] CSP (Content Security Policy) 헤더

### 3.6 API 인증 개선
- ⚠️ **JWT 토큰 만료 시간 1440분 (24시간) 너무 김**
  - **필요 작업**:
    - [ ] Access Token 15분으로 단축
    - [ ] Refresh Token 구현

### 3.7 Password 정책
- ❌ **비밀번호 복잡도 검증 없음**
  - **필요 작업**:
    - [ ] 최소 8자, 영문+숫자+특수문자
    - [ ] Pwned Passwords API 체크

### 3.8 민감정보 마스킹
- ❌ **로그에 민감정보 노출 가능**
  - **필요 작업**:
    - [ ] 이메일, 전화번호 마스킹
    - [ ] API 키 로그 제거

### 3.9 WAF (Web Application Firewall)
- ❌ **WAF 없음**
  - **필요 작업**:
    - [ ] Cloudflare WAF
    - [ ] ModSecurity 규칙

---

## 🟢 4. 백엔드 기능 (Medium Priority - 8개)

### 4.1 Geocoding
- ❌ **소방서 위도/경도 0, 0**
  - `fire_stations` 테이블에 위치 정보 없음
  - **필요 작업**:
    - [ ] Kakao Map API / Google Geocoding
    - [ ] 주소 → 좌표 변환 스크립트
    - [ ] PostGIS 쿼리 최적화

### 4.2 소방서 상세 정보
- ❌ **전화번호 '000-0000-0000'**
  - 실제 소방서 정보 크롤링 필요
  - **필요 작업**:
    - [ ] 공공데이터포털 API 연동
    - [ ] 소방서 홈페이지 크롤링

### 4.3 뉴스/영상 매칭 개선
- ⚠️ **현재 168건 중 1건만 매칭**
  - 매칭 정확도 0.6%
  - **필요 작업**:
    - [ ] Embedding 모델 튜닝
    - [ ] 키워드 기반 검색 추가
    - [ ] 시간 범위 확대

### 4.4 재해문자 연동
- ❌ **재해문자 크롤링 없음**
  - NFDS만 크롤링 중
  - **필요 작업**:
    - [ ] 재해문자 API 연동
    - [ ] SMS 알림 발송

### 4.5 정기 기부
- ⚠️ **UI만 있고 로직 없음**
  - `regular-donation` 페이지 존재
  - **필요 작업**:
    - [ ] 정기결제 스케줄링
    - [ ] Toss Billing Key 저장

### 4.6 환불 처리
- ⚠️ **환불 API stub만 존재**
  - **필요 작업**:
    - [ ] Toss Payments 환불 API 연동
    - [ ] 환불 이력 저장

### 4.7 기부 영수증
- ❌ **PDF 영수증 생성 없음**
  - **필요 작업**:
    - [ ] WeasyPrint / ReportLab
    - [ ] 이메일 발송

### 4.8 푸시 알림
- ⚠️ **WebPush stub만 존재**
  - **필요 작업**:
    - [ ] Firebase Cloud Messaging
    - [ ] Service Worker 등록

---

## 🔵 5. 프론트엔드 기능 (Medium Priority - 6개)

### 5.1 마이페이지 미완성
- ⚠️ **`/mypage` 디렉토리만 존재**
  - 기부 내역, 영수증 다운로드 등 없음
  - **필요 작업**:
    - [ ] 기부 내역 조회
    - [ ] 정기 기부 관리
    - [ ] 회원 정보 수정

### 5.2 소방서 상세 페이지 데이터 부족
- ⚠️ **`fire-station-detail/[id]` 있지만 데이터 없음**
  - **필요 작업**:
    - [ ] 소방서 정보 채우기
    - [ ] 최근 출동 이력
    - [ ] 기부 랭킹

### 5.3 반응형 디자인 부족
- ⚠️ **모바일 최적화 부족**
  - Tailwind 사용하지만 테스트 필요
  - **필요 작업**:
    - [ ] Mobile-first 점검
    - [ ] 터치 이벤트 최적화

### 5.4 Loading States
- ⚠️ **로딩 스피너 부족**
  - **필요 작업**:
    - [ ] Skeleton UI
    - [ ] Suspense Boundaries

### 5.5 Error Boundaries
- ❌ **Error Boundary 없음**
  - **필요 작업**:
    - [ ] React Error Boundary
    - [ ] 에러 페이지 디자인

### 5.6 SEO 최적화
- ⚠️ **메타 태그 부족**
  - **필요 작업**:
    - [ ] Open Graph 태그
    - [ ] Twitter Card
    - [ ] Sitemap.xml
    - [ ] robots.txt

---

## 🟣 6. 테스트 (Medium Priority - 4개)

### 6.1 Integration Tests 부족
- ⚠️ **55개 테스트 파일 있지만 커버리지 낮음**
  - **필요 작업**:
    - [ ] API 엔드투엔드 테스트
    - [ ] Celery 작업 테스트

### 6.2 Frontend 테스트 없음
- ❌ **Jest/Playwright 설정만 있고 테스트 없음**
  - **필요 작업**:
    - [ ] 컴포넌트 단위 테스트
    - [ ] E2E 테스트 (결제 플로우)

### 6.3 Load Testing
- ⚠️ **K6 스크립트 있지만 미실행**
  - `tests/performance/*.js` 존재
  - **필요 작업**:
    - [ ] K6 부하 테스트 실행
    - [ ] 병목 지점 파악

### 6.4 Security Testing
- ❌ **보안 스캔 없음**
  - **필요 작업**:
    - [ ] OWASP ZAP
    - [ ] Snyk 취약점 스캔

---

## 🟤 7. 성능 최적화 (Low Priority - 2개)

### 7.1 CDN
- ❌ **Static Assets CDN 없음**
  - **필요 작업**:
    - [ ] Cloudflare/Cloudfront
    - [ ] 이미지 최적화

### 7.2 캐싱 전략
- ⚠️ **Redis Cache 있지만 적용 범위 좁음**
  - **필요 작업**:
    - [ ] API 응답 캐싱
    - [ ] ETag / Last-Modified 헤더

---

## 📈 우선순위별 실행 계획

### Phase 1: 배포 준비 (1-2주)
1. ✅ K8s 클러스터 구축
2. ✅ CI/CD 파이프라인 완성
3. ✅ SSL/TLS 인증서
4. ✅ 도메인 & DNS
5. ✅ DB 마이그레이션

### Phase 2: 모니터링 & 보안 (1주)
6. ✅ Prometheus + Grafana
7. ✅ Sentry 에러 트래킹
8. ✅ Rate Limiting 활성화
9. ✅ JWT Refresh Token

### Phase 3: 기능 완성 (2주)
10. ✅ Geocoding
11. ✅ 뉴스/영상 매칭 개선
12. ✅ 마이페이지 완성
13. ✅ 정기 기부

### Phase 4: 최적화 (1주)
14. ✅ Load Testing
15. ✅ CDN 설정
16. ✅ SEO 최적화

---

## 🎯 핵심 메트릭 (KPI)

배포 전 달성 목표:
- [ ] API 응답 시간 < 200ms (P95)
- [ ] 크롤링 성공률 > 95%
- [ ] 매칭 정확도 > 70%
- [ ] 테스트 커버리지 > 80%
- [ ] 보안 스캔 0 Critical Issues
- [ ] Uptime > 99.9%

---

## 📝 결론

**총 47개 개선사항** 중:
- 🔴 Critical (배포 전 필수): 18개
- 🟠 High Priority (1개월 내): 17개
- 🟡 Medium Priority (3개월 내): 10개
- 🟢 Low Priority (이후): 2개

**다음 단계**: Phase 1 (배포 준비) 부터 시작 권장

---

**작성자**: Claude Code Analysis
**최종 업데이트**: 2025-10-17
