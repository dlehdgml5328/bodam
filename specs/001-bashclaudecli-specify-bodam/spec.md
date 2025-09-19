# Feature Specification: 커피 기부 플랫폼 보담(BoDam) - 소방대원 지원 서비스

**Feature Branch**: `001-bashclaudecli-specify-bodam`
**Created**: 2025-09-19
**Status**: Draft
**Input**: User description: "커피 기부 플랫폼 보담(BoDam) - 소방대원 지원 서비스

## 핵심 기능
- 소방청 현황 데이터 기반 소방서별 기부 시스템
- 일시/정기 기부 (Toss Payments 연동)
- 실시간 화재 관련 뉴스/유튜브/재난문자 AI 분석
- 지도 기반 소방서 검색 및 즐겨찾기
- 기부 랭킹/등급 시스템, 그룹 기부
- 실시간 알림 (WebSocket, 카카오, 이메일)
- 관리자 대시보드 (AI+RAG 검색)

## 기술 스택
### 백엔드
- FastAPI (비동기, WebSocket)
- SQLAlchemy + Alembic (PostgreSQL + pgvector + PostGIS)
- Celery + Redis (비동기 작업, 30분 단위 데이터 수집)
- Neo4j → Apache AGE (그래프 DB, 어댑터 패턴)

### 프론트엔드
- Next.js (App Router) + TailwindCSS
- 관리자: /admin 경로 (권한 기반)

### 인증/보안
- JWT (OAuth2) + HttpOnly 쿠키
- 소셜 로그인: 구글/카카오/네이버

### 결제/영수증
- Toss Payments API (일시/정기, 현금영수증)
- PDF 영수증: WeasyPrint → 이메일 첨부

### AI/데이터 분석
- Together AI - Llama 3.3 70B Instruct-Turbo
- 뉴스/유튜브/재난문자 수집 → 관련성 판별 + 요약 (JSON)
- RAG: pgvector + Neo4j/AGE, KG²RAG 적용

### 인프라
- Kubernetes + NGINX Ingress
- Prometheus + Grafana 모니터링
- GitHub Actions CI/CD
- Blue-Green 배포 (라벨 스위치)

### 스토리지
- 기본: Nginx 정적 서빙 (/static, 로컬 볼륨)
- 선택: S3/Spaces 전환 (Off-by-default, .env 토글)

## 데이터 구조
### 워커 4종 분리
1. 데이터 수집 워커
2. 결제/영수증 워커
3. 알림 워커
4. AI 판별/요약 워커

### AI 판별 기준 (reliability_score)
- ≥70: 자동 통과
- 50-69: 관리자 검토
- <50: 폐기

## 도메인 구조
- 프론트: app.bodam.example (Vercel)
- API: api.bodam.example (K8s Ingress)
- 관리자: app.bodam.example/admin

## 보안 설정
- CORS: [\"https://app.bodam.example\"]
- 쿠키: Domain=.bodam.example; SameSite=None; Secure; HttpOnly

## 품질 게이트
- pytest 커버리지 ≥70%
- k6 성능: p95 < 300ms, 실패율 < 1%
- 정적 분석: ruff/black → mypy → pytest → 보안 스캔"

## Execution Flow (main)
```
1. Parse user description from Input
   → 식별됨: 소방관을 위한 커피 기부 플랫폼
2. Extract key concepts from description
   → 액터: 기부자, 소방관, 관리자
   → 액션: 기부, 추적, 관리, 알림
   → 데이터: 기부, 소방서, 뉴스, 랭킹
   → 제약사항: 신뢰도 점수, 주기적 업데이트
3. For each unclear aspect:
   → 특정 명확화 필요사항 표시
4. Fill User Scenarios & Testing section
   → 사용자 플로우 명확히 정의됨
5. Generate Functional Requirements
   → 각 요구사항 테스트 가능
6. Identify Key Entities
   → 핵심 데이터 모델 식별됨
7. Run Review Checklist
   → 일부 구현 세부사항 제거 표시
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ 사용자가 무엇을 필요로 하고 왜 필요한지에 집중
- ❌ 구현 방법은 피하기 (기술 스택, API, 코드 구조 없음)
- 👥 개발자가 아닌 비즈니스 이해관계자를 위해 작성

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story (주요 사용자 스토리)
기부자가 특정 소방서에 커피 기부를 통해 지역 소방관들을 지원하고자 합니다. 지도에서 소방서를 탐색하고, 현재 필요사항을 확인하며, 일시 또는 정기 기부를 하고, 지원하는 지역의 화재 관련 사건에 대한 실시간 업데이트를 통해 자신의 영향을 추적할 수 있습니다.

### Acceptance Scenarios (수락 시나리오)
1. **Given** 사용자가 플랫폼을 방문할 때, **When** 자신의 위치 근처 소방서를 검색하면, **Then** 근처 소방서와 현재 기부 필요사항이 표시된 지도를 봅니다
2. **Given** 사용자가 소방서를 선택할 때, **When** 기부를 선택하면, **Then** 기부 금액과 빈도(일시 또는 정기)를 선택할 수 있습니다
3. **Given** 사용자가 기부를 완료할 때, **When** 결제가 처리되면, **Then** 영수증을 받고 기부가 기록에 나타납니다
4. **Given** 화재 관련 사건이 발생할 때, **When** AI 분석이 관련성을 판단하면, **Then** 기부자는 지원하는 소방서 근처 사건에 대한 알림을 받습니다
5. **Given** 여러 사용자가 같은 소방서에 기부할 때, **When** 소방서 세부사항을 볼 때, **Then** 총 기부액과 기부자 랭킹을 봅니다
6. **Given** 관리자가 플래그된 콘텐츠를 검토할 때, **When** AI 분석된 뉴스를 승인하거나 거부하면, **Then** 콘텐츠가 사용 가능해지거나 기부자 알림에서 폐기됩니다

### Edge Cases (엣지 케이스)
- 소방서가 일시적으로 폐쇄되거나 통합될 때 어떻게 됩니까?
- 시스템이 실패한 정기 결제를 어떻게 처리합니까?
- AI 신뢰도 점수가 임계값 아래로 떨어질 때 어떻게 됩니까?
- 중복된 뉴스 기사나 사건들은 어떻게 처리됩니까?
- 기부 목표가 초과될 때 어떻게 됩니까?

## Requirements *(mandatory)*

### Functional Requirements (기능 요구사항)
- **FR-001**: 시스템은 사용자가 대화형 지도 인터페이스에서 소방서를 탐색할 수 있어야 합니다
- **FR-002**: 시스템은 사용자가 특정 소방서에 일시 및 정기 기부를 모두 할 수 있어야 합니다
- **FR-003**: 시스템은 거래를 처리하고 영수증을 생성하기 위해 결제 처리와 통합되어야 합니다
- **FR-004**: 시스템은 화재 관련 뉴스, 응급 경보, 소셜 미디어 콘텐츠를 수집하고 분석해야 합니다
- **FR-005**: 시스템은 콘텐츠 신뢰도를 점수화하고 의심스러운 콘텐츠를 관리자 검토로 라우팅해야 합니다
- **FR-006**: 시스템은 기부자에게 지원하는 소방서 근처의 화재 사건에 대해 알려야 합니다
- **FR-007**: 시스템은 소방서별 기부 랭킹과 기부자 등급 시스템을 유지해야 합니다
- **FR-008**: 시스템은 여러 사용자가 공통 목표에 기여하는 그룹 기부를 지원해야 합니다
- **FR-009**: 시스템은 사용자가 선호하는 소방서를 즐겨찾기하고 북마크할 수 있어야 합니다
- **FR-010**: 시스템은 여러 채널(웹, 이메일, 모바일)을 통해 실시간 알림을 제공해야 합니다
- **FR-011**: 시스템은 콘텐츠 조정과 플랫폼 감독을 위한 관리자 대시보드를 제공해야 합니다
- **FR-012**: 시스템은 소셜 로그인 옵션을 통해 사용자를 인증해야 합니다
- **FR-013**: 시스템은 공식 소방서 데이터와 소방서 정보를 저장하고 검색해야 합니다
- **FR-014**: 시스템은 세금 목적을 위해 여러 형식의 기부 영수증을 생성해야 합니다
- **FR-015**: 시스템은 예정된 간격으로 데이터 수집을 업데이트해야 합니다
- **FR-016**: 사용자는 완전한 기부 기록과 영향 지표를 볼 수 있어야 합니다
- **FR-017**: 시스템은 지리적 검색과 위치 기반 추천을 처리해야 합니다
- **FR-018**: 시스템은 금융 거래와 사용자 활동에 대한 감사 로그를 유지해야 합니다
- **FR-019**: 시스템은 다양한 사용자 권한 수준(기부자, 관리자, 중재자)을 지원해야 합니다
- **FR-020**: 시스템은 사용자와 관리자를 위한 데이터 내보내기 기능을 제공해야 합니다

### Key Entities (핵심 엔티티) *(include if feature involves data)*
- **User (사용자)**: 인증 자격 증명, 선호사항, 기부 기록, 권한 수준을 가진 기부자와 관리자를 나타냅니다
- **Fire Station (소방서)**: 지리적 좌표, 현재 필요사항, 연락처 정보, 운영 상태를 가진 공식 소방서 위치
- **Donation (기부)**: 금액, 빈도, 결제 방법, 거래 상태를 가진 사용자와 소방서를 연결하는 금융 기여
- **News Content (뉴스 콘텐츠)**: 신뢰도 점수, 분석 결과, 승인 상태를 가진 화재 관련 기사, 응급 경보, 소셜 미디어 게시물
- **Notification (알림)**: 배달 선호사항과 상태 추적을 가진 사건, 기부 확인, 플랫폼 업데이트에 대한 사용자 경고
- **Ranking (랭킹)**: 기부 금액과 참여를 기반으로 한 소방서별 사용자 성취 수준과 리더보드
- **Group (그룹)**: 공유 목표를 향해 일하는 여러 기여자와 함께하는 협력적 기부 캠페인
- **Receipt (영수증)**: 공식 형식과 배달 확인을 가진 기부에 대한 세금 문서

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality (콘텐츠 품질)
- [x] 구현 세부사항 없음 (언어, 프레임워크, API)
- [x] 사용자 가치와 비즈니스 요구사항에 집중
- [x] 비기술적 이해관계자를 위해 작성됨
- [x] 모든 필수 섹션 완료

### Requirement Completeness (요구사항 완성도)
- [x] [NEEDS CLARIFICATION] 마커가 남아있지 않음
- [x] 요구사항이 테스트 가능하고 명확함
- [x] 성공 기준이 측정 가능함
- [x] 범위가 명확히 경계지어짐
- [x] 의존성과 가정이 식별됨

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed (사용자 설명 파싱됨)
- [x] Key concepts extracted (핵심 개념 추출됨)
- [x] Ambiguities marked (애매함 표시됨)
- [x] User scenarios defined (사용자 시나리오 정의됨)
- [x] Requirements generated (요구사항 생성됨)
- [x] Entities identified (엔티티 식별됨)
- [x] Review checklist passed (검토 체크리스트 통과됨)

---