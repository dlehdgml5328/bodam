"""
Llama observability query API
FR-013, FR-014, NFR-001: 1초 이내 응답
"""
import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.observability_agent import ObservabilityAgent

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


class ObservabilityQueryRequest(BaseModel):
    query: str
    time_range: str = "15m"
    language: str = "ko"
    include_traces: bool = False


class ObservabilityQueryResponse(BaseModel):
    query_type: str
    generated_query: str
    result: dict
    response_time_ms: int
    data_source: str
    related_traces: Optional[List[str]] = None


@router.post("/query", response_model=ObservabilityQueryResponse)
async def query_observability(request: ObservabilityQueryRequest):
    """FR-013, FR-014, NFR-001: Llama 쿼리 (1초 이내)"""
    start = time.time()

    agent = ObservabilityAgent()
    answer = await agent.analyze_with_llama(request.query, request.time_range)

    response_time_ms = int((time.time() - start) * 1000)

    if response_time_ms > 1000:
        raise HTTPException(status_code=500, detail="Query exceeded 1 second timeout")

    return ObservabilityQueryResponse(
        query_type="combined",
        generated_query="",
        result={"summary": answer, "data": []},
        response_time_ms=response_time_ms,
        data_source="local_prometheus",
    )


@router.get("/metrics/dashboard")
async def get_dashboard_metrics(time_range: str = "15m"):
    """Dashboard metrics 요약"""
    agent = ObservabilityAgent()
    return await agent.get_dashboard_metrics(time_range)


@router.get("/trace/{trace_id}")
async def get_trace(trace_id: str):
    """Trace 조회"""
    agent = ObservabilityAgent()
    try:
        trace = await agent.query_tempo(trace_id)
        return trace
    except Exception as e:
        raise HTTPException(status_code=404, detail="Trace not found") from e
