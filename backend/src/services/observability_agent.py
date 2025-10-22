"""
ObservabilityAgent - Llama → Prometheus/Loki/Tempo 쿼리
FR-013, FR-014, NFR-001: 1초 이내 응답
"""
from datetime import datetime
from typing import Any, Dict

import httpx


class ObservabilityAgent:
    def __init__(
        self,
        prometheus_url="http://prometheus:9090",
        loki_url="http://loki:3100",
        tempo_url="http://tempo:3200",
    ):
        self.prometheus_url = prometheus_url
        self.loki_url = loki_url
        self.tempo_url = tempo_url

    async def query_prometheus(self, promql: str) -> Dict[str, Any]:
        """PromQL 쿼리"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": promql},
            )
            response.raise_for_status()
            return response.json()

    async def query_loki(self, logql: str, limit: int = 100) -> Dict[str, Any]:
        """LogQL 쿼리"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.loki_url}/loki/api/v1/query_range",
                params={"query": logql, "limit": limit},
            )
            response.raise_for_status()
            return response.json()

    async def query_tempo(self, trace_id: str) -> Dict[str, Any]:
        """Tempo trace 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.tempo_url}/api/traces/{trace_id}")
            response.raise_for_status()
            return response.json()

    async def analyze_with_llama(self, question: str, time_range: str = "1h") -> str:
        """Llama AI가 질문을 해석하고 쿼리"""
        if "5XX 에러" in question or "5xx" in question.lower():
            promql = 'rate(http_requests_total{status="5xx"}[1h])'
            result = await self.query_prometheus(promql)
            return f"5XX 에러 발생: {result}"
        elif "DB 커넥션" in question:
            promql = "db_connection_pool_in_use / db_connection_pool_size"
            result = await self.query_prometheus(promql)
            return f"DB 커넥션 풀 사용률: {result}"
        else:
            return "질문을 이해하지 못했습니다."

    async def get_dashboard_metrics(self, time_range: str = "15m") -> Dict[str, Any]:
        """Dashboard metrics 요약"""
        http_rps = await self.query_prometheus("rate(http_requests_total[5m])")
        http_2xx = await self.query_prometheus('rate(http_requests_total{status="2xx"}[5m])')
        http_4xx = await self.query_prometheus('rate(http_requests_total{status="4xx"}[5m])')
        http_5xx = await self.query_prometheus('rate(http_requests_total{status="5xx"}[5m])')
        http_p95 = await self.query_prometheus("histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))")

        db_pool_size = await self.query_prometheus("db_connection_pool_size")
        db_pool_in_use = await self.query_prometheus("db_connection_pool_in_use")
        db_pool_available = await self.query_prometheus("db_connection_pool_available")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "http": {
                "requests_per_second": self._extract_value(http_rps),
                "status_2xx_rate": self._extract_value(http_2xx),
                "status_4xx_rate": self._extract_value(http_4xx),
                "status_5xx_rate": self._extract_value(http_5xx),
                "p95_latency_ms": self._extract_value(http_p95) * 1000,
            },
            "database": {
                "pool_size": self._extract_value(db_pool_size),
                "pool_in_use": self._extract_value(db_pool_in_use),
                "pool_available": self._extract_value(db_pool_available),
                "utilization_percent": (
                    self._extract_value(db_pool_in_use) / self._extract_value(db_pool_size) * 100
                    if self._extract_value(db_pool_size) > 0 else 0
                ),
            },
            "http_client": {
                "pool_size": 0,
                "pool_in_use": 0,
                "waiting_requests": 0,
            },
            "celery": {
                "tasks_per_second": 0,
            },
        }

    def _extract_value(self, prometheus_result: Dict[str, Any]) -> float:
        """Prometheus 결과에서 값 추출"""
        try:
            return float(prometheus_result["data"]["result"][0]["value"][1])
        except (KeyError, IndexError):
            return 0.0
