# Cluster Autoscaler 설정 가이드

DigitalOcean Kubernetes (DOKS)에서 Cluster Autoscaler를 설정하는 방법입니다.

## 사전 요구사항

1. DigitalOcean Personal Access Token
2. DigitalOcean Kubernetes Cluster ID
3. kubectl 설정 완료

## 설치 단계

### 1. DigitalOcean Secrets 생성

```bash
# DigitalOcean API Token
kubectl create secret generic digitalocean-token \
  --from-literal=token=YOUR_DIGITALOCEAN_TOKEN \
  --namespace=kube-system

# Cluster ID (DOKS 대시보드에서 확인)
kubectl create secret generic digitalocean-cluster \
  --from-literal=cluster-id=YOUR_CLUSTER_ID \
  --namespace=kube-system
```

### 2. Cluster Autoscaler 배포

```bash
# Autoscaler 리소스 배포
kubectl apply -f autoscaler-config.yaml

# 배포 상태 확인
kubectl get deployment cluster-autoscaler -n kube-system
kubectl get pods -n kube-system -l app=cluster-autoscaler
```

### 3. 로그 확인

```bash
# Autoscaler 로그 확인
kubectl logs -f deployment/cluster-autoscaler -n kube-system

# 상태 확인
kubectl describe configmap cluster-autoscaler-status -n kube-system
```

## 설정 파라미터

### 노드 스케일링 범위
- **최소 노드**: 1개
- **최대 노드**: 2개
- **노드 타입**: 2vCPU / 4GB RAM

### 스케일 다운 정책
- `--scale-down-delay-after-add=5m`: 노드 추가 후 5분 대기
- `--scale-down-unneeded-time=10m`: 10분간 미사용 시 제거
- `--scale-down-utilization-threshold=0.5`: 50% 미만 사용률일 때 제거

### Expander 전략
- `--expander=least-waste`: 리소스 낭비가 가장 적은 노드 그룹 선택

## 모니터링

### Prometheus 메트릭
Cluster Autoscaler는 `:8085/metrics` 엔드포인트에서 메트릭을 노출합니다.

```bash
# 메트릭 확인
kubectl port-forward -n kube-system deployment/cluster-autoscaler 8085:8085
curl http://localhost:8085/metrics
```

주요 메트릭:
- `cluster_autoscaler_scaled_up_nodes_total`: 스케일 업된 노드 수
- `cluster_autoscaler_scaled_down_nodes_total`: 스케일 다운된 노드 수
- `cluster_autoscaler_unschedulable_pods_count`: 스케줄링 불가능한 Pod 수

### 상태 확인

```bash
# Autoscaler 이벤트 확인
kubectl get events -n kube-system --field-selector involvedObject.name=cluster-autoscaler

# ConfigMap 상태 확인
kubectl describe configmap cluster-autoscaler-status -n kube-system
```

## 트러블슈팅

### 노드가 스케일 업되지 않는 경우

1. Pending Pod 확인
```bash
kubectl get pods --all-namespaces --field-selector=status.phase=Pending
```

2. Autoscaler 로그 확인
```bash
kubectl logs -f deployment/cluster-autoscaler -n kube-system | grep -i scale
```

3. Node Pool 설정 확인
```bash
# DigitalOcean CLI로 확인
doctl kubernetes cluster node-pool list YOUR_CLUSTER_ID
```

### 노드가 스케일 다운되지 않는 경우

1. 노드 사용률 확인
```bash
kubectl top nodes
```

2. 노드에서 실행 중인 Pod 확인
```bash
kubectl get pods --all-namespaces -o wide
```

3. PodDisruptionBudget 확인
```bash
kubectl get pdb --all-namespaces
```

## 비용 최적화

### 현재 설정 (월 비용)
- 노드 1개: $24/month (2vCPU / 4GB)
- 노드 2개 (피크 시): $48/month

### 예상 비용
- **평균 사용**: 1-1.5 노드 (~$30-36/month)
- **피크 시간**: 2 노드 (최대 $48/month)

## 참고 자료

- [Cluster Autoscaler 공식 문서](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)
- [DigitalOcean Kubernetes Autoscaling](https://docs.digitalocean.com/products/kubernetes/how-to/autoscale/)
- [Kubernetes HPA 가이드](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
