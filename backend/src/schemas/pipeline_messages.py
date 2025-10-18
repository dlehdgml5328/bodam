"""
파이프라인 메시지 스키마 (크롤러 → 큐 → 워커)
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class LocationData(BaseModel):
    """위치 정보"""
    address: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class CasualtyData(BaseModel):
    """인명 피해 정보"""
    injured: int = 0
    dead: int = 0


class FireIncidentMessage(BaseModel):
    """화재 사고 메시지"""
    type: Literal["fire_incident"] = "fire_incident"
    incident_id: str = Field(..., description="사고 ID (예: F2025001)")
    title: str = Field(..., description="사고 제목")
    location: LocationData
    occurred_at: datetime = Field(..., description="발생 시각")
    status: Literal["dispatching", "suppressing", "contained", "resolved"] = "dispatching"
    severity: Optional[Literal["critical", "high", "medium", "low"]] = None
    casualties: Optional[CasualtyData] = None
    estimated_damage: Optional[int] = Field(None, description="예상 피해액 (원)")
    source_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="메시지 생성 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "fire_incident",
                "incident_id": "F2025001",
                "title": "서울 중구 아파트 화재",
                "location": {
                    "address": "서울특별시 중구 세종대로 110",
                    "lat": 37.5665,
                    "lng": 126.9780
                },
                "occurred_at": "2025-10-13T14:30:00+09:00",
                "status": "dispatching",
                "severity": "high",
                "casualties": {
                    "injured": 2,
                    "dead": 0
                },
                "estimated_damage": 100000000,
                "source_url": "http://localhost:8888/test_static_mock.html",
                "timestamp": "2025-10-13T14:32:00+09:00"
            }
        }


class DispatchEventMessage(BaseModel):
    """출동 이벤트 메시지"""
    type: Literal["dispatch_event"] = "dispatch_event"
    incident_id: str = Field(..., description="사고 ID")
    station_name: str = Field(..., description="소방서 이름")
    dispatched_at: datetime = Field(..., description="출동 시각")
    units_count: int = Field(1, description="출동 차량 수")
    personnel_count: int = Field(0, description="출동 인원")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "dispatch_event",
                "incident_id": "F2025001",
                "station_name": "서울중부소방서",
                "dispatched_at": "2025-10-13T14:31:00+09:00",
                "units_count": 3,
                "personnel_count": 12,
                "timestamp": "2025-10-13T14:32:00+09:00"
            }
        }


class NewsMatchRequestMessage(BaseModel):
    """뉴스 매칭 요청 메시지"""
    type: Literal["news_match_request"] = "news_match_request"
    incident_id: str = Field(..., description="사고 ID")
    search_query: str = Field(..., description="검색 쿼리")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "news_match_request",
                "incident_id": "F2025001",
                "search_query": "서울 중구 아파트 화재",
                "timestamp": "2025-10-13T14:35:00+09:00"
            }
        }


# Union type for all message types
PipelineMessage = FireIncidentMessage | DispatchEventMessage | NewsMatchRequestMessage
