# BoDam Grafana 알람 설정 가이드

## 📋 설정된 알람 규칙

총 **8개**의 알람 규칙이 자동으로 프로비저닝됩니다:

### 🚀 성능 알람
1. **API 응답 속도 느림** (p95 > 300ms)
   - **심각도**: Warning ⚠️
   - **조건**: p95 응답시간이 300ms 초과 (2분 지속)
   - **설명**: API 성능 저하 감지

2. **API 응답 속도 심각** (p95 > 1초)
   - **심각도**: Critical 🔥
   - **조건**: p95 응답시간이 1초 초과 (1분 지속)
   - **설명**: 즉시 조치 필요

### 🔴 에러 알람
3. **HTTP 4xx 에러율 높음** (> 10%)
   - **심각도**: Warning ⚠️
   - **조건**: 4xx 에러율이 10% 초과 (3분 지속)
   - **설명**: 클라이언트 요청 문제

4. **HTTP 5xx 서버 에러 발생**
   - **심각도**: Critical 🚨
   - **조건**: 5xx 에러 발생 (1분 지속)
   - **설명**: 서버 내부 에러 발생

### 💳 비즈니스 로직 알람
5. **중복 기부 감지** (> 5건)
   - **심각도**: Warning 🔄
   - **조건**: 10분간 중복 기부 5건 초과 (2분 지속)
   - **설명**: Race condition 의심

### 💾 데이터베이스 알람
6. **DB 커넥션 풀 고갈 위험** (> 80%)
   - **심각도**: Warning 💾
   - **조건**: DB 커넥션 사용률 80% 초과 (2분 지속)
   - **설명**: 커넥션 부족 위험

7. **DB 데드락 발생**
   - **심각도**: Critical 🔒
   - **조건**: 데드락 발생 감지 (1분 지속)
   - **설명**: 트랜잭션 충돌

### ⚙️ 백그라운드 작업 알람
8. **Celery 작업 실패율 높음** (> 20%)
   - **심각도**: Warning ⚙️
   - **조건**: Celery 실패율 20% 초과 (3분 지속)
   - **설명**: 백그라운드 작업 문제

---

## 🔧 Slack 연동 방법

### 1. Slack Webhook URL 생성

1. Slack Workspace에서 [https://api.slack.com/apps](https://api.slack.com/apps) 접속
2. **Create New App** 클릭
3. **From scratch** 선택
4. App 이름 입력 (예: BoDam Alerts)
5. Workspace 선택
6. **Incoming Webhooks** 메뉴로 이동
7. **Activate Incoming Webhooks** 활성화
8. **Add New Webhook to Workspace** 클릭
9. 알림 받을 채널 선택 (예: #bodam-alerts)
10. **Webhook URL 복사** (예: `https://hooks.slack.com/services/T09.../B09.../xxx`)

### 2. 환경 변수 설정

`.env` 파일에 Webhook URL 추가:

```bash
SLACK_BODAM_ALERT_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. Grafana 재시작

```bash
docker compose -f docker-compose.dev.yml restart grafana
```

---

## 🧪 알람 테스트 방법

### 방법 1: Grafana UI에서 테스트

1. Grafana 접속: http://localhost:3001
2. 좌측 메뉴에서 **Alerting** 클릭
3. **Contact points** 탭 클릭
4. `slack-bodam-alerts` 찾기
5. **Test** 버튼 클릭
6. Slack 채널에서 테스트 메시지 확인

### 방법 2: 실제 조건 트리거

#### API 응답 속도 알람 테스트
```bash
# 부하 테스트로 응답 속도를 높임 (p95 > 300ms)
TEST_TOKEN="YOUR_TOKEN" \
K6_VUS=100 \
K6_DURATION=5m \
DONATION_FIRE_STATION_ID="9dc63e0c-df47-4f95-af37-cd284cf32822" \
DONATION_AMOUNT=10000 \
K6_TEST_SCRIPT="k6-donation-race.js" \
docker compose -f docker-compose.dev.yml --profile test up k6
```

#### 중복 기부 알람 테스트
```bash
# 10건의 중복 기부 메트릭 생성
for i in {1..10}; do
  curl -X POST "http://localhost:8000/observability/test/donation-duplicate?fire_station_id=test-station"
done
```

#### DB 커넥션 풀 알람 테스트
```bash
# DB 커넥션 사용률 90%로 설정
curl -X POST "http://localhost:8000/observability/test/db-pool?service=backend&in_use=9"
```

#### Celery 실패율 알람 테스트
```bash
# 20건 중 5건 실패 (25% 실패율)
for i in {1..15}; do
  curl -X POST "http://localhost:8000/observability/test/celery-task?task_name=test&status=SUCCESS"
done
for i in {1..5}; do
  curl -X POST "http://localhost:8000/observability/test/celery-task?task_name=test&status=FAILURE"
done
```

---

## 📊 Grafana에서 알람 확인

### Alert Rules 확인
1. Grafana 접속: http://localhost:3001
2. 좌측 메뉴 **Alerting** → **Alert rules** 클릭
3. **BoDam Production Alerts** 폴더에서 8개 규칙 확인

### Alert 상태 확인
- **Normal**: 정상 (초록색)
- **Pending**: 조건 충족했지만 `for` 시간 대기 중 (노란색)
- **Firing**: 알람 발동 중 (빨간색)
- **NoData**: 데이터 없음 (회색)

### Slack 알림 형식

```
🔥 BoDam Alert

Alert: API 응답 속도 느림 (p95 > 300ms)
Status: Firing

Details: 현재 p95 응답시간: 450ms. 성능 저하가 감지되었습니다.
```

---

## 🔍 문제 해결

### Slack 알림이 오지 않을 때

1. **Webhook URL 확인**
   ```bash
   # .env 파일에 올바른 URL이 있는지 확인
   grep SLACK_BODAM_ALERT_WEBHOOK .env
   ```

2. **Grafana 환경 변수 확인**
   ```bash
   docker exec bodam-grafana env | grep SLACK
   ```

3. **Contact Point 설정 확인**
   - Grafana UI → Alerting → Contact points
   - `slack-bodam-alerts`가 있는지 확인
   - Test 버튼으로 연결 테스트

4. **Alert Rule 상태 확인**
   - Alerting → Alert rules
   - 규칙이 **Normal** 상태인지 확인
   - **Pending** 또는 **Firing** 상태면 Slack으로 알림 전송됨

### 로그 확인
```bash
# Grafana 로그 확인
docker logs bodam-grafana --tail 100 | grep -i alert

# Prometheus 로그 확인
docker logs bodam-prometheus --tail 100
```

---

## 📝 알람 규칙 커스터마이징

알람 임계값을 변경하려면 `/home/donghee/bodam/infra/k8s/observability/grafana-alert-rules.yml` 파일을 수정하세요.

예시: API 응답 속도 임계값 변경

```yaml
# 300ms → 500ms로 변경
- evaluator:
    params:
      - 500  # 여기를 변경
    type: gt
```

수정 후 Grafana 재시작:
```bash
docker compose -f docker-compose.dev.yml restart grafana
```

---

## 🎯 다음 단계

1. ✅ Slack Webhook 설정
2. ✅ 알람 규칙 로드 확인
3. 🔄 알람 테스트 (Contact point Test)
4. 🔄 실제 조건 트리거 테스트
5. 📱 운영 환경 알람 채널 분리 (critical, warning)

---

**문의**: 알람 관련 문제가 있으면 Grafana 로그와 Prometheus 메트릭을 먼저 확인하세요.
