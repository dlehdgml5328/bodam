"""
Mock 소방서 사이트 크롤러

5분마다 Mock 사이트에서 화재 출동 데이터를 크롤링하여
fire_incidents 테이블에 저장하고 뉴스/영상 매칭 프로세스 시작
"""
import httpx
from bs4 import BeautifulSoup
from celery import shared_task
from datetime import datetime
import json
from typing import Dict, Optional
import os
from src.cache.clients import get_cache_client
from src.monitoring.logging import get_logger

logger = get_logger(__name__)

MOCK_SITE_URL = os.getenv("CRAWLER_MOCK_SITE_URL", "http://localhost:8888/test_static_mock.html")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def crawl_mock_site(self):
    """
    Mock 소방서 사이트 크롤링

    GitHub Pages의 JSON 파일을 직접 가져와서 처리

    Returns:
        Dict: 크롤링된 화재 출동 데이터 또는 None
    """
    import asyncio

    logger.info(f"[Crawler] Starting crawl from {MOCK_SITE_URL}")

    async def _crawl():
        try:
            # 1. JSON 데이터 가져오기 (GitHub Pages)
            json_url = MOCK_SITE_URL.rstrip('/') + '/data/incidents.json'

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(json_url)
                response.raise_for_status()
                incidents_data = response.json()

            if not incidents_data or len(incidents_data) == 0:
                logger.warning("[Crawler] No incidents in JSON data")
                return None

            # 2. 첫 번째 사고 데이터 가져오기 (최신 데이터)
            first_incident = incidents_data[0]

            logger.info(f"[Crawler] Parsed incident: {first_incident['id']} - {first_incident['fireName']}")

            # 3. 데이터 포맷 변환 (JSON -> pipeline 포맷)
            incident = {
                'id': first_incident['id'],
                'fireName': first_incident['fireName'],
                'address': first_incident['address'],
                'axisY': first_incident['axisY'],
                'axisX': first_incident['axisX'],
                'occurrenceDate': first_incident['occurrenceDate'],
                'occurrenceTime': first_incident['occurrenceTime'],
                'status': first_incident['status'],
                'progress': first_incident['progress'],
                'casualties': first_incident['casualties'],
                'injured': first_incident['injured'],
                'damageAmount': first_incident['damageAmount'],
                'crawledAt': datetime.now().isoformat()
            }

            # 4. Redis 중복 체크 (선택사항 - DB에서도 중복 체크하므로)
            redis = await get_cache_client()
            incident_key = f"incident:{incident['id']}"

            exists = await redis.exists(incident_key)
            if exists:
                logger.info(f"[Crawler] Incident {incident['id']} already in cache, updating...")

            # 5. DB 저장 + 매칭 파이프라인 시작
            # incident_pipeline 워커를 통해 DB 저장 및 뉴스 매칭 시작
            from src.workers.incident_pipeline import save_and_match_incident
            save_and_match_incident.delay(incident)

            logger.info(f"[Crawler] Incident {incident['id']} queued for processing")

            return incident

        except httpx.HTTPError as e:
            logger.error(f"[Crawler] HTTP error: {e}")
            raise

        except Exception as e:
            logger.error(f"[Crawler] Unexpected error: {e}", exc_info=True)
            raise

    try:
        return asyncio.run(_crawl())
    except Exception as e:
        logger.error(f"[Crawler] Task failed: {e}")
        raise self.retry(exc=e)


def parse_incident_row(row) -> Optional[Dict]:
    """
    테이블 행에서 화재 출동 데이터 추출

    Args:
        row: BeautifulSoup Tag (tr 요소)

    Returns:
        Dict: 파싱된 출동 데이터
    """
    try:
        # data-* 속성 추출
        incident_id = row.get('data-id')
        lat = row.get('data-lat')
        lng = row.get('data-lng')
        date = row.get('data-date')

        # td 요소들 추출
        cells = row.find_all('td')

        if len(cells) < 7:
            logger.warning(f"[Parser] Insufficient cells: {len(cells)}")
            return None

        fire_name = cells[0].text.strip()
        occurrence_datetime = cells[1].text.strip()  # "2025-10-10 13:00"
        address = cells[2].text.strip()
        status_badge = cells[3].find('span', {'class': 'status-badge'})
        status_text = status_badge.text.strip() if status_badge else ''
        progress = cells[4].text.strip()
        casualties_text = cells[5].text.strip()
        damage_text = cells[6].text.strip()

        # 날짜/시간 분리
        if ' ' in occurrence_datetime:
            occurrence_date, occurrence_time = occurrence_datetime.split(' ', 1)
        else:
            occurrence_date = date if date else ''
            occurrence_time = occurrence_datetime

        # 상태 코드 매핑
        status_map = {
            '출동중': 'A',
            '도착': 'B',
            '진압완료': 'C',
            '귀소': 'D'
        }
        status_code = status_map.get(status_text, 'D')

        # 사상자 수 파싱 (예: "부상 2명")
        casualties = 0
        injured = 0
        if casualties_text and casualties_text != '-':
            # "부상 2명", "사망 1명" 등의 형식 처리
            import re
            numbers = re.findall(r'\d+', casualties_text)
            if numbers:
                casualties = int(numbers[0])

        # 피해액 파싱 (예: "1억원", "5000만원")
        damage_amount = 0
        if damage_text and damage_text != '-':
            import re
            # "1억원" -> 100000000, "5000만원" -> 50000000
            if '억' in damage_text:
                numbers = re.findall(r'(\d+)억', damage_text)
                if numbers:
                    damage_amount = int(numbers[0]) * 100000000
            elif '만원' in damage_text:
                numbers = re.findall(r'(\d+)만원', damage_text)
                if numbers:
                    damage_amount = int(numbers[0]) * 10000

        incident = {
            'id': incident_id,
            'fireName': fire_name,
            'address': address,
            'axisY': float(lat) if lat else 0.0,
            'axisX': float(lng) if lng else 0.0,
            'occurrenceDate': occurrence_date,
            'occurrenceTime': occurrence_time,
            'status': status_code,
            'progress': progress,
            'casualties': casualties,
            'injured': injured,
            'damageAmount': damage_amount,
            'crawledAt': datetime.now().isoformat()
        }

        return incident

    except Exception as e:
        logger.error(f"[Parser] Error parsing row: {e}", exc_info=True)
        return None


@shared_task
def test_crawl():
    """크롤러 테스트용 태스크"""
    result = crawl_mock_site(None)
    if result:
        logger.info(f"[Test] Crawled: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        logger.info("[Test] No new incidents")
    return result
