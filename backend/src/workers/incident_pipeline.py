"""
화재 사고 처리 파이프라인

크롤러에서 받은 데이터를:
1. fire_incidents 테이블에 저장
2. matcher 워커를 호출하여 뉴스 매칭 시작
"""
from celery import shared_task
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import select

from src.database.connection import session_scope
from src.models.fire_incident import FireIncident
from src.monitoring.logging import get_logger

logger = get_logger(__name__)


@shared_task(name="save_and_match_incident", bind=True, max_retries=3)
def save_and_match_incident(self, incident_data: Dict[str, Any]):
    """
    화재 사고 저장 및 매칭 시작

    Args:
        incident_data: 크롤러에서 받은 사고 데이터 (기존 형식)
            {
                "id": "F2025001",
                "fireName": "강남구 논현동 상가 화재",
                "address": "서울특별시 강남구 논현동 123-45",
                "axisY": 37.5123,
                "axisX": 127.0456,
                "occurrenceDate": "2025-10-13",
                "occurrenceTime": "14:30",
                "status": "B",
                "progress": "진압중",
                "casualties": 3,
                "injured": 0,
                "damageAmount": 50000000
            }
    """
    import asyncio

    logger.info(f"[Pipeline] Processing incident {incident_data.get('id')}")

    try:
        async def _save():
            async with session_scope() as session:
                incident_id = incident_data.get('id')

                # 발생 시간 합성
                occurrence_date = incident_data.get('occurrenceDate', '')
                occurrence_time = incident_data.get('occurrenceTime', '00:00')
                occurred_at_str = f"{occurrence_date} {occurrence_time}:00"

                try:
                    occurred_at = datetime.fromisoformat(occurred_at_str.replace(' ', 'T'))
                except ValueError:
                    occurred_at = datetime.utcnow()

                # 상태 매핑
                status_map = {
                    'A': 'dispatching',  # 출동중
                    'B': 'suppressing',  # 진압중
                    'C': 'contained',    # 진압완료
                    'D': 'resolved'      # 귀소
                }
                status = status_map.get(incident_data.get('status', 'D'), 'resolved')

                # 심각도 판단 (사상자 또는 피해액 기준)
                casualties = incident_data.get('casualties', 0) + incident_data.get('injured', 0)
                damage = incident_data.get('damageAmount', 0)

                if casualties >= 10 or damage >= 1000000000:  # 10억원 이상
                    severity = 'critical'
                elif casualties >= 5 or damage >= 500000000:  # 5억원 이상
                    severity = 'high'
                elif casualties >= 1 or damage >= 100000000:  # 1억원 이상
                    severity = 'medium'
                else:
                    severity = 'low'

                # 기존 사고 확인
                stmt = select(FireIncident).where(FireIncident.id == incident_id)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # 업데이트
                    existing.status = status
                    existing.casualties_injured = incident_data.get('casualties', 0)
                    existing.casualties_dead = incident_data.get('injured', 0)  # 주의: injured가 실제로는 dead일 수 있음
                    existing.estimated_damage = incident_data.get('damageAmount')
                    existing.severity = severity
                    existing.updated_at = datetime.utcnow()

                    logger.info(f"[Pipeline] Updated incident {incident_id}")
                else:
                    # 신규 생성
                    incident = FireIncident(
                        id=incident_id,
                        title=incident_data.get('fireName', ''),
                        location_address=incident_data.get('address', ''),
                        latitude=incident_data.get('axisY'),
                        longitude=incident_data.get('axisX'),
                        occurred_at=occurred_at,
                        status=status,
                        severity=severity,
                        casualties_injured=incident_data.get('casualties', 0),
                        casualties_dead=incident_data.get('injured', 0),
                        estimated_damage=incident_data.get('damageAmount'),
                        source_url=None,
                    )

                    session.add(incident)
                    logger.info(f"[Pipeline] Created incident {incident_id}")

                # session_scope는 자동으로 commit하므로 제거
                return incident_id

        # asyncio 실행
        incident_id = asyncio.run(_save())

        # 뉴스 매칭 워커 호출
        from src.workers.matcher import match_news_and_videos
        match_news_and_videos.delay(incident_data)

        logger.info(f"[Pipeline] Successfully saved and queued matching for {incident_id}")

        return {
            "status": "success",
            "incident_id": incident_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"[Pipeline] Failed to save incident: {e}", exc_info=True)
        raise self.retry(exc=e)
