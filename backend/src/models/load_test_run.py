"""
LoadTestRun model - K6 부하 테스트 결과 저장
FR-017, FR-019: 부하 테스트 이력 및 성능 분석
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from src.models.base import Base


class LoadTestRun(Base):
    __tablename__ = "load_test_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(100), nullable=False, unique=True, index=True)
    scenario_name = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    target_vu = Column(Integer, nullable=False)
    stages_config = Column(JSONB, nullable=True)
    total_requests = Column(Integer, nullable=True)
    failed_requests = Column(Integer, nullable=True)
    requests_per_second = Column(Float, nullable=True)
    latency_p50 = Column(Float, nullable=True)
    latency_p95 = Column(Float, nullable=True)
    latency_p99 = Column(Float, nullable=True)
    latency_avg = Column(Float, nullable=True)
    latency_min = Column(Float, nullable=True)
    latency_max = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="running")
    passed_thresholds = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    results_json = Column(JSONB, nullable=True)
    executor = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=True)
    prometheus_start = Column(Integer, nullable=True)
    prometheus_end = Column(Integer, nullable=True)
