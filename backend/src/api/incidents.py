"""
화재 사고 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from src.database.connection import get_session
from src.models.fire_incident import FireIncident, IncidentNewsMatch, IncidentVideoMatch

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("/", response_model=List[dict])
async def get_incidents(
    limit: int = Query(default=20, le=500),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    """
    화재 사고 목록 조회

    Args:
        limit: 페이지 크기 (최대 500)
        offset: 오프셋
        status: 상태 필터 (dispatching, suppressing, contained, resolved)
        severity: 심각도 필터 (critical, high, medium, low)
    """
    query = (
        select(FireIncident)
        .options(
            selectinload(FireIncident.news_matches),
            selectinload(FireIncident.video_matches)
        )
        .order_by(desc(FireIncident.occurred_at))
    )

    # 필터 적용
    if status:
        query = query.where(FireIncident.status == status)
    if severity:
        query = query.where(FireIncident.severity == severity)

    # 페이징
    query = query.limit(limit).offset(offset)

    result = await session.execute(query)
    incidents = result.scalars().all()

    return [
        {
            "id": incident.id,
            "title": incident.title,
            "location_address": incident.location_address,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "occurred_at": incident.occurred_at.isoformat() if incident.occurred_at else None,
            "status": incident.status,
            "severity": incident.severity,
            "casualties_injured": incident.casualties_injured,
            "casualties_dead": incident.casualties_dead,
            "estimated_damage": incident.estimated_damage,
            "source_url": incident.source_url,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
            "news_count": len(incident.news_matches) if incident.news_matches else 0,
            "video_count": len(incident.video_matches) if incident.video_matches else 0,
            "videos": [
                {
                    "title": match.video_title,
                    "url": match.video_url,
                    "thumbnail": match.thumbnail_url,
                    "published_at": match.published_at.isoformat() if match.published_at else None
                }
                for match in (incident.video_matches or [])
            ][:3]  # 최대 3개만
        }
        for incident in incidents
    ]


@router.get("/{incident_id}", response_model=dict)
async def get_incident(
    incident_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    화재 사고 상세 정보 조회

    Args:
        incident_id: 사고 ID (예: F2025001)
    """
    result = await session.execute(
        select(FireIncident).where(FireIncident.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return {
        "id": incident.id,
        "title": incident.title,
        "location_address": incident.location_address,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "occurred_at": incident.occurred_at.isoformat() if incident.occurred_at else None,
        "status": incident.status,
        "severity": incident.severity,
        "casualties_injured": incident.casualties_injured,
        "casualties_dead": incident.casualties_dead,
        "estimated_damage": incident.estimated_damage,
        "source_url": incident.source_url,
        "created_at": incident.created_at.isoformat() if incident.created_at else None,
        "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
    }
