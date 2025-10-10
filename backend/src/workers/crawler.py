"""
Mock 소방서 사이트 크롤러

5분마다 Mock 사이트에서 화재 출동 데이터를 크롤링하여
뉴스/영상 매칭 프로세스 시작
"""
import httpx
from bs4 import BeautifulSoup
from celery import shared_task
from datetime import datetime
import json
from typing import Dict, Optional
from src.cache.clients import get_redis
from src.monitoring.logging import get_logger

logger = get_logger(__name__)

MOCK_SITE_URL = "https://dlehdgml5328.github.io/mock-fire-station-site/"


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
async def crawl_mock_site(self):
    """
    Mock 소방서 사이트 크롤링

    Returns:
        Dict: 크롤링된 화재 출동 데이터 또는 None
    """
    logger.info(f"[Crawler] Starting crawl from {MOCK_SITE_URL}")

    try:
        # 1. Mock 사이트 HTML 가져오기
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(MOCK_SITE_URL)
            response.raise_for_status()
            html = response.text

        # 2. HTML 파싱
        soup = BeautifulSoup(html, 'html.parser')
        tbody = soup.find('tbody', {'id': 'incidents-tbody'})

        if not tbody:
            logger.warning("[Crawler] No tbody found in HTML")
            return None

        # 3. 테이블에서 최신 데이터 (첫 번째 행) 추출
        first_row = tbody.find('tr')

        if not first_row:
            logger.warning("[Crawler] No incident rows found")
            return None

        incident = parse_incident_row(first_row)

        if not incident:
            logger.warning("[Crawler] Failed to parse incident row")
            return None

        logger.info(f"[Crawler] Parsed incident: {incident['id']} - {incident['fireName']}")

        # 4. Redis 중복 체크
        redis = await get_redis()
        incident_key = f"incident:{incident['id']}"

        exists = await redis.exists(incident_key)
        if exists:
            logger.info(f"[Crawler] Skip duplicate incident: {incident['id']}")
            return None

        # 5. 매칭 태스크 호출 (비동기)
        from src.workers.matcher import match_news_and_videos
        match_news_and_videos.delay(incident)

        logger.info(f"[Crawler] New incident queued for matching: {incident['id']}")

        return incident

    except httpx.HTTPError as e:
        logger.error(f"[Crawler] HTTP error: {e}")
        raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"[Crawler] Unexpected error: {e}", exc_info=True)
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

        # 사상자 수 파싱
        casualties = 0
        injured = 0
        if casualties_text and casualties_text != '-':
            casualties = int(casualties_text.replace('명', ''))

        # 피해액 파싱
        damage_amount = 0
        if damage_text and damage_text != '-':
            damage_text_clean = damage_text.replace('만원', '').replace(',', '')
            damage_amount = int(damage_text_clean) * 10000

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
async def test_crawl():
    """크롤러 테스트용 태스크"""
    result = await crawl_mock_site()
    if result:
        logger.info(f"[Test] Crawled: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        logger.info("[Test] No new incidents")
    return result
