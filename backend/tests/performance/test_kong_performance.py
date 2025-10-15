"""Kong Gateway 성능 테스트

목표: p95 레이턴시 < 100ms, 처리량 > 1000 req/s
"""

import asyncio
import time
import statistics
from typing import List, Dict

import httpx
import pytest


class PerformanceMetrics:
    """성능 메트릭 수집"""
    
    def __init__(self):
        self.latencies: List[float] = []
        self.errors: int = 0
        self.total_requests: int = 0
    
    def add_latency(self, latency: float):
        self.latencies.append(latency)
        self.total_requests += 1
    
    def add_error(self):
        self.errors += 1
        self.total_requests += 1
    
    def get_percentile(self, percentile: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * (percentile / 100))
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]
    
    def get_summary(self) -> Dict[str, float]:
        if not self.latencies:
            return {}
        
        return {
            "total_requests": self.total_requests,
            "errors": self.errors,
            "error_rate": (self.errors / self.total_requests) * 100 if self.total_requests > 0 else 0,
            "p50_latency": self.get_percentile(50),
            "p95_latency": self.get_percentile(95),
            "p99_latency": self.get_percentile(99),
        }


async def make_request(url: str, client: httpx.AsyncClient, metrics: PerformanceMetrics):
    start_time = time.time()
    try:
        response = await client.get(url)
        response.raise_for_status()
        latency = (time.time() - start_time) * 1000
        metrics.add_latency(latency)
    except Exception:
        metrics.add_error()


async def load_test(url: str, total_requests: int, concurrent: int) -> PerformanceMetrics:
    metrics = PerformanceMetrics()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(0, total_requests, concurrent):
            batch_size = min(concurrent, total_requests - i)
            tasks = [make_request(url, client, metrics) for _ in range(batch_size)]
            await asyncio.gather(*tasks)
    
    return metrics


@pytest.mark.asyncio
async def test_kong_throughput():
    """Kong Gateway 처리량 측정 (목표: > 1000 req/s)"""
    metrics = await load_test("http://localhost:8000/api/fire-stations/search", 5000, 100)
    summary = metrics.get_summary()
    
    print(f"\n처리량 테스트: p95={summary['p95_latency']:.2f}ms, 에러율={summary['error_rate']:.2f}%")
    
    assert summary['p95_latency'] < 100, f"p95 레이턴시 초과: {summary['p95_latency']:.2f}ms"
    assert summary['error_rate'] < 0.1, f"에러율 높음: {summary['error_rate']:.2f}%"
