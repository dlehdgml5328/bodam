# Quickstart: Redis 분리 배포 및 Celery 운영 환경

**Feature**: 002-cache-redis-queue
**Date**: 2025-10-07

## 목표

이 가이드를 따라하면 다음을 완료할 수 있습니다:
1. K8s에 Redis Cache/Queue 인스턴스 배포
2. Celery Worker/Beat/Flower 배포
3. 비동기 작업 실행 확인
4. 모니터링 대시보드 접속

**소요 시간**: 약 30분

---

## 사전 준비

### 1. 필수 도구 설치
```bash
# kubectl 설치 확인
kubectl version --client

# K8s 클러스터 접근 확인
kubectl get nodes
```

### 2. 네임스페이스 생성
```bash
kubectl create namespace bodam
kubectl config set-context --current --namespace=bodam
```

### 3. Secrets 생성
```bash
# Flower 인증 비밀번호
kubectl create secret generic flower-auth \
  --from-literal=password=your-secure-password

# AWS credentials (백업용)
kubectl create secret generic aws-credentials \
  --from-literal=access-key-id=YOUR_AWS_KEY \
  --from-literal=secret-access-key=YOUR_AWS_SECRET
```

---

## Step 1: Redis Cache 배포

### 1.1 ConfigMap 생성
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-cache-config
data:
  redis.conf: |
    maxmemory 512mb
    maxmemory-policy allkeys-lru
    save ""
    appendonly no
EOF
```

### 1.2 Deployment 배포
```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-cache
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-cache
  template:
    metadata:
      labels:
        app: redis-cache
    spec:
      containers:
      - name: redis
        image: redis:7.2-alpine
        command: ["redis-server", "/etc/redis/redis.conf"]
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: config
          mountPath: /etc/redis
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
      volumes:
      - name: config
        configMap:
          name: redis-cache-config
EOF
```

### 1.3 Service 생성
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: redis-cache-service
spec:
  type: ClusterIP
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis-cache
EOF
```

### 1.4 확인
```bash
# Pod 상태 확인
kubectl get pods -l app=redis-cache

# 연결 테스트
kubectl run redis-test --rm -it --image=redis:7.2-alpine -- redis-cli -h redis-cache-service PING
# Expected output: PONG
```

---

## Step 2: Redis Queue 배포

### 2.1 ConfigMap 생성
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-queue-config
data:
  redis.conf: |
    maxmemory 1gb
    maxmemory-policy noeviction
    appendonly yes
    appendfsync everysec
    save 3600 1
EOF
```

### 2.2 StatefulSet 배포
```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-queue
spec:
  serviceName: redis-queue-service
  replicas: 1
  selector:
    matchLabels:
      app: redis-queue
  template:
    metadata:
      labels:
        app: redis-queue
    spec:
      containers:
      - name: redis
        image: redis:7.2-alpine
        command: ["redis-server", "/etc/redis/redis.conf"]
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: config
          mountPath: /etc/redis
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: redis-queue-config
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 5Gi
EOF
```

### 2.3 Headless Service 생성
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: redis-queue-service
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis-queue
EOF
```

### 2.4 확인
```bash
# StatefulSet 상태 확인
kubectl get statefulset redis-queue

# PVC 생성 확인
kubectl get pvc

# 연결 테스트
kubectl run redis-test --rm -it --image=redis:7.2-alpine -- redis-cli -h redis-queue-0.redis-queue-service PING
# Expected output: PONG
```

---

## Step 3: Celery Worker 배포

### 3.1 Deployment 배포
```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: worker
        image: your-registry/bodam-backend:latest
        command: ["celery", "-A", "src.worker.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
        env:
        - name: CELERY_BROKER_URL
          value: "redis://redis-queue-service:6379/0"
        - name: CELERY_RESULT_BACKEND
          value: "redis://redis-queue-service:6379/1"
        - name: DATABASE_URL
          value: "postgresql+psycopg://bodam:bodam@db:5432/bodam"
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
EOF
```

### 3.2 HPA (Horizontal Pod Autoscaler) 생성
```bash
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 180
    scaleDown:
      stabilizationWindowSeconds: 300
EOF
```

### 3.3 확인
```bash
# Pod 상태 확인
kubectl get pods -l app=celery-worker

# Worker 로그 확인
kubectl logs -l app=celery-worker --tail=50

# HPA 상태 확인
kubectl get hpa celery-worker-hpa
```

---

## Step 4: Celery Beat 배포

### 4.1 Deployment 배포
```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-beat
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: celery-beat
  template:
    metadata:
      labels:
        app: celery-beat
    spec:
      containers:
      - name: beat
        image: your-registry/bodam-backend:latest
        command: ["celery", "-A", "src.worker.celery_app", "beat", "--loglevel=info"]
        env:
        - name: CELERY_BROKER_URL
          value: "redis://redis-queue-service:6379/0"
        - name: CELERY_RESULT_BACKEND
          value: "redis://redis-queue-service:6379/1"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
EOF
```

### 4.2 확인
```bash
# Pod 상태 확인
kubectl get pods -l app=celery-beat

# Beat 로그 확인 (스케줄 실행 로그)
kubectl logs -l app=celery-beat --tail=50
```

---

## Step 5: Flower 배포

### 5.1 Deployment 배포
```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flower
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flower
  template:
    metadata:
      labels:
        app: flower
    spec:
      containers:
      - name: flower
        image: your-registry/bodam-backend:latest
        command:
        - celery
        - -A
        - src.worker.celery_app
        - flower
        - --port=5555
        - --url_prefix=/flower
        - --basic_auth=admin:\$(FLOWER_PASSWORD)
        env:
        - name: CELERY_BROKER_URL
          value: "redis://redis-queue-service:6379/0"
        - name: CELERY_RESULT_BACKEND
          value: "redis://redis-queue-service:6379/1"
        - name: FLOWER_PASSWORD
          valueFrom:
            secretKeyRef:
              name: flower-auth
              key: password
        ports:
        - containerPort: 5555
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
EOF
```

### 5.2 Service 생성
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: flower-service
spec:
  type: ClusterIP
  ports:
  - port: 5555
    targetPort: 5555
  selector:
    app: flower
EOF
```

### 5.3 Ingress 생성
```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flower-ingress
  annotations:
    nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8"
spec:
  rules:
  - host: bodam.example.com
    http:
      paths:
      - path: /flower
        pathType: Prefix
        backend:
          service:
            name: flower-service
            port:
              number: 5555
EOF
```

### 5.4 확인
```bash
# Pod 상태 확인
kubectl get pods -l app=flower

# 웹 브라우저에서 접속
# https://bodam.example.com/flower
# Username: admin, Password: (flower-auth Secret에서 설정한 값)
```

---

## Step 6: 모니터링 배포

### 6.1 Redis Exporter (Cache)
```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-cache-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-cache-exporter
  template:
    metadata:
      labels:
        app: redis-cache-exporter
    spec:
      containers:
      - name: exporter
        image: oliver006/redis_exporter:latest
        env:
        - name: REDIS_ADDR
          value: "redis://redis-cache-service:6379"
        ports:
        - containerPort: 9121
---
apiVersion: v1
kind: Service
metadata:
  name: redis-cache-exporter-service
spec:
  type: ClusterIP
  ports:
  - port: 9121
    targetPort: 9121
  selector:
    app: redis-cache-exporter
EOF
```

### 6.2 Redis Exporter (Queue)
```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-queue-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-queue-exporter
  template:
    metadata:
      labels:
        app: redis-queue-exporter
    spec:
      containers:
      - name: exporter
        image: oliver006/redis_exporter:latest
        env:
        - name: REDIS_ADDR
          value: "redis://redis-queue-service:6379"
        ports:
        - containerPort: 9121
---
apiVersion: v1
kind: Service
metadata:
  name: redis-queue-exporter-service
spec:
  type: ClusterIP
  ports:
  - port: 9121
    targetPort: 9121
  selector:
    app: redis-queue-exporter
EOF
```

### 6.3 확인
```bash
# Exporter 메트릭 확인
kubectl run curl-test --rm -it --image=curlimages/curl -- curl http://redis-cache-exporter-service:9121/metrics
```

---

## Step 7: 통합 테스트

### 7.1 Backend API 환경 변수 업데이트
```bash
# Backend Deployment 수정
kubectl set env deployment/backend \
  REDIS_CACHE_URL=redis://redis-cache-service:6379/0 \
  CELERY_BROKER_URL=redis://redis-queue-service:6379/0 \
  CELERY_RESULT_BACKEND=redis://redis-queue-service:6379/1
```

### 7.2 Celery 작업 테스트
```bash
# Backend Pod에 접속
kubectl exec -it deployment/backend -- python

# Python 인터프리터에서 실행
>>> from src.workers.payment_processor import confirm_pending_payments
>>> result = confirm_pending_payments.delay()
>>> result.get(timeout=10)
'payments-confirmed@2025-10-07T10:00:00'
```

### 7.3 Flower에서 작업 확인
1. 웹 브라우저에서 `https://bodam.example.com/flower` 접속
2. `admin` / `your-password`로 로그인
3. **Tasks** 탭에서 방금 실행한 작업 확인
4. **Workers** 탭에서 Worker 상태 확인

### 7.4 Redis 데이터 확인
```bash
# Queue Redis에 작업 결과 저장 확인
kubectl run redis-test --rm -it --image=redis:7.2-alpine -- \
  redis-cli -h redis-queue-service -n 1 KEYS "celery-task-meta-*"
```

---

## Step 8: 백업 설정

### 8.1 CronJob 생성
```bash
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: redis-queue-backup
spec:
  schedule: "0 2 * * *"  # 매일 새벽 2시
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: amazon/aws-cli:latest
            command:
            - /bin/sh
            - -c
            - |
              redis-cli -h redis-queue-service BGSAVE
              sleep 10
              kubectl cp redis-queue-0:/data/dump.rdb /tmp/dump.rdb
              aws s3 cp /tmp/dump.rdb s3://bodam-backups/redis/\$(date +%Y-%m-%d)/dump.rdb
            env:
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: secret-access-key
          restartPolicy: OnFailure
EOF
```

### 8.2 수동 백업 테스트
```bash
kubectl create job --from=cronjob/redis-queue-backup redis-backup-test
kubectl logs job/redis-backup-test
```

---

## Step 9: 최종 확인 체크리스트

```bash
# 모든 리소스 확인
kubectl get all

# Expected output:
# - redis-cache Deployment (1/1 Ready)
# - redis-queue StatefulSet (1/1 Ready)
# - celery-worker Deployment (2/2 Ready)
# - celery-beat Deployment (1/1 Ready)
# - flower Deployment (1/1 Ready)
# - redis-cache-exporter Deployment (1/1 Ready)
# - redis-queue-exporter Deployment (1/1 Ready)
```

**체크리스트**:
- [ ] Redis Cache 정상 작동 (`PING` → `PONG`)
- [ ] Redis Queue 정상 작동 + PVC 바인딩
- [ ] Celery Worker 2개 이상 실행 중
- [ ] Celery Beat 정확히 1개 실행 중
- [ ] Flower 웹 UI 접속 가능
- [ ] Backend API가 새로운 Redis 연결 성공
- [ ] Celery 작업 실행 및 결과 확인
- [ ] Prometheus 메트릭 수집 확인
- [ ] 백업 CronJob 생성 완료

---

## Troubleshooting

### 문제 1: Redis Pod가 CrashLoopBackOff
**원인**: ConfigMap 오류 또는 메모리 부족
**해결**:
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### 문제 2: Celery Worker가 작업을 처리하지 않음
**원인**: Broker URL 오류
**해결**:
```bash
kubectl logs -l app=celery-worker
# CELERY_BROKER_URL 환경 변수 확인
kubectl exec -it deployment/celery-worker -- env | grep CELERY
```

### 문제 3: Flower 접속 불가
**원인**: Ingress 설정 오류 또는 Basic Auth 실패
**해결**:
```bash
kubectl describe ingress flower-ingress
kubectl port-forward deployment/flower 5555:5555
# 로컬에서 http://localhost:5555/flower 접속
```

### 문제 4: PVC가 Pending 상태
**원인**: StorageClass 미설정
**해결**:
```bash
kubectl get storageclass
# 기본 StorageClass 설정
kubectl patch storageclass <your-storage-class> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

---

## 다음 단계

1. **Loki + Promtail 로그 수집** (별도 기능)
2. **Kong Gateway 연동** (별도 기능)
3. **OpenTelemetry 분산 트레이싱** (별도 기능)

---

## 참고 문서

- K8s 리소스 YAML: `infra/k8s/redis/`, `infra/k8s/celery/`
- 모니터링 설정: `infra/monitoring/`
- Celery 작업 코드: `backend/src/workers/`
- 환경 변수 예시: `backend/.env.example`
