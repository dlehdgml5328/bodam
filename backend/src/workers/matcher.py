"""
뉴스/영상 매칭 Worker

크롤링된 화재 출동 데이터를 기반으로
네이버 뉴스와 YouTube 영상을 검색하여 매칭
"""
from celery import shared_task
from typing import Dict, List
from datetime import datetime
from difflib import SequenceMatcher
import json
import re
from src.integrations.naver_news import NaverNewsClient
from src.integrations.youtube import YouTubeClient
from src.cache.clients import get_redis
from src.monitoring.logging import get_logger
import os

logger = get_logger(__name__)


def extract_keywords(incident: Dict) -> List[str]:
    """
    화재 출동 데이터에서 검색 키워드 추출

    Args:
        incident: 화재 출동 데이터

    Returns:
        List[str]: 검색 키워드 목록
    """
    keywords = []

    # 주소에서 지역 추출
    address = incident.get('address', '')
    address_parts = address.split()

    if len(address_parts) >= 2:
        # "서울 강남구" 형태
        keywords.append(f"{address_parts[0]} {address_parts[1]}")

    if len(address_parts) >= 3:
        # "강남구 역삼동" 형태
        keywords.append(f"{address_parts[1]} {address_parts[2]}")

    # 소방서명에서 지역 추출
    fire_name = incident.get('fireName', '')
    # "경기 수원소방서" -> "수원"
    match = re.search(r'(\w+)\s*(\w+)소방서', fire_name)
    if match:
        region = match.group(1)  # "경기"
        station = match.group(2)  # "수원"
        keywords.append(f"{station} 화재")

    # 조합 키워드 생성
    if address_parts:
        keywords.append(f"{address_parts[0] if len(address_parts) > 0 else ''} 화재")

    # 중복 제거
    keywords = list(set(keywords))

    logger.info(f"[Matcher] Extracted keywords: {keywords}")

    return keywords


def calculate_similarity(text1: str, text2: str) -> float:
    """
    문자열 유사도 계산 (0.0 ~ 1.0)

    Args:
        text1: 비교 문자열 1
        text2: 비교 문자열 2

    Returns:
        float: 유사도 점수
    """
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def rank_results(incident: Dict, results: List[Dict], result_type: str) -> List[Dict]:
    """
    검색 결과를 유사도 순으로 정렬

    Args:
        incident: 화재 출동 데이터
        results: 검색 결과 목록
        result_type: 'news' or 'video'

    Returns:
        List[Dict]: 점수가 추가된 정렬된 결과
    """
    address = incident.get('address', '')
    fire_name = incident.get('fireName', '')

    for result in results:
        title = result.get('title', '')
        description = result.get('description', '')

        # 제목과 주소의 유사도
        title_addr_sim = calculate_similarity(address, title)
        title_fire_sim = calculate_similarity(fire_name, title)

        # 설명과 주소의 유사도
        desc_sim = 0
        if description:
            desc_addr_sim = calculate_similarity(address, description)
            desc_fire_sim = calculate_similarity(fire_name, description)
            desc_sim = max(desc_addr_sim, desc_fire_sim)

        # 최종 점수 (가중 평균)
        result['score'] = max(
            title_addr_sim * 1.0,
            title_fire_sim * 0.8,
            desc_sim * 0.6
        )

    # 점수 높은 순으로 정렬
    sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)

    return sorted_results


@shared_task
async def match_news_and_videos(incident: Dict):
    """
    화재 출동 데이터에 뉴스/영상 매칭

    Args:
        incident: 화재 출동 데이터
    """
    incident_id = incident.get('id')
    logger.info(f"[Matcher] Starting match for incident: {incident_id}")

    try:
        # 1. 키워드 추출
        keywords = extract_keywords(incident)
        if not keywords:
            logger.warning(f"[Matcher] No keywords extracted for {incident_id}")
            return

        primary_keyword = keywords[0]

        # 2. 네이버 뉴스 검색
        naver_client = NaverNewsClient(
            client_id=os.getenv('NAVER_CLIENT_ID', 'Le3v_zRXPEpKCD8hE_ei'),
            client_secret=os.getenv('NAVER_CLIENT_SECRET', 'g3Gcw_ACuH')
        )

        occurrence_date = incident.get('occurrenceDate', '')
        if occurrence_date:
            news_results = await naver_client.search_with_date_filter(
                query=primary_keyword,
                target_date=occurrence_date,
                days_range=3,
                display=20
            )
        else:
            news_results = await naver_client.search(primary_keyword, display=10)

        ranked_news = rank_results(incident, news_results, 'news')[:3]  # Top 3

        logger.info(f"[Matcher] Found {len(ranked_news)} relevant news for {incident_id}")

        # 3. YouTube 영상 검색
        youtube_client = YouTubeClient(
            api_key=os.getenv('YOUTUBE_API_KEY', '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')
        )

        video_results = youtube_client.search_news_videos(
            query=primary_keyword,
            max_results=10
        )

        ranked_videos = rank_results(incident, video_results, 'video')[:3]  # Top 3

        logger.info(f"[Matcher] Found {len(ranked_videos)} relevant videos for {incident_id}")

        # 4. Redis에 저장
        redis = await get_redis()

        matched_data = {
            **incident,
            "relatedNews": ranked_news,
            "relatedVideos": ranked_videos,
            "matchedAt": datetime.now().isoformat(),
            "keywords": keywords
        }

        # 24시간 TTL로 저장
        incident_key = f"incident:{incident_id}"
        await redis.setex(
            incident_key,
            86400,  # 24시간
            json.dumps(matched_data, ensure_ascii=False)
        )

        # 최근 목록에 추가 (최대 30개 유지)
        await redis.lpush("recent_incidents", incident_id)
        await redis.ltrim("recent_incidents", 0, 29)

        logger.info(
            f"[Matcher] Successfully matched incident {incident_id}: "
            f"{len(ranked_news)} news, {len(ranked_videos)} videos"
        )

        return matched_data

    except Exception as e:
        logger.error(f"[Matcher] Error matching incident {incident_id}: {e}", exc_info=True)
        raise
