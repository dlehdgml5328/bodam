"""
LangGraph 노드 정의

뉴스/영상 매칭 워크플로우의 각 단계를 노드로 정의
"""
from __future__ import annotations

import copy
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, TypedDict

from src.integrations.naver_news import NaverNewsClient
from src.integrations.youtube import YouTubeClient
from src.integrations.together_ai import TogetherAIHttpClient
from src.monitoring.logging import get_logger

logger = get_logger(__name__)

_NEWS_CACHE: Dict[str, tuple[float, List[Dict]]] = {}
_VIDEO_CACHE: Dict[str, tuple[float, List[Dict]]] = {}
_CACHE_TTL = int(os.getenv('MATCH_CACHE_TTL_SECONDS', '1800'))
_EVALUATION_CACHE: Dict[str, Dict] = {}


class MatcherState(TypedDict):
    """LangGraph 상태 정의"""
    incident: Dict
    keywords: List[str]
    news_results: List[Dict]
    video_results: List[Dict]
    evaluated_news: List[Dict]
    evaluated_videos: List[Dict]
    error: str | None


async def extract_keywords_node(state: MatcherState) -> MatcherState:
    """
    1단계: 키워드 추출

    크롤링 데이터에서 검색 키워드 생성
    """
    incident = state["incident"]
    logger.info(f"[Node] extract_keywords for incident: {incident.get('id')}")

    keywords = []

    # 주소에서 지역 추출
    address = incident.get('address', '')
    address_parts = address.split()

    if len(address_parts) >= 2:
        # "서울 강남구 화재"
        keywords.append(f"{address_parts[0]} {address_parts[1]} 화재")

    # 기본 키워드
    if address_parts:
        keywords.append(f"{address_parts[0]} 화재")

    logger.info(f"[Node] Extracted keywords: {keywords}")

    state["keywords"] = keywords
    return state


async def search_news_node(state: MatcherState) -> MatcherState:
    """
    2단계: 네이버 뉴스 검색 (Tool)
    """
    keywords = state["keywords"]
    incident = state["incident"]

    if not keywords:
        logger.warning("[Node] No keywords, skipping news search")
        state["news_results"] = []
        return state

    primary_keyword = keywords[0]
    logger.info(f"[Node] Searching news with keyword: {primary_keyword}")

    try:
        now = time.time()
        cache_entry = _NEWS_CACHE.get(primary_keyword)
        if cache_entry and now - cache_entry[0] < _CACHE_TTL:
            logger.info("[Node] Using cached news results for keyword '%s'", primary_keyword)
            state["news_results"] = copy.deepcopy(cache_entry[1])
            return state

        occurrence_date = incident.get('occurrenceDate', '')
        if occurrence_date:
            try:
                incident_date = datetime.strptime(occurrence_date, '%Y-%m-%d')
                if datetime.utcnow() - incident_date > timedelta(days=5):
                    logger.info("[Node] Incident older than 5 days, skipping news search")
                    state["news_results"] = []
                    return state
            except ValueError:
                logger.debug("[Node] Unable to parse occurrence date '%s'", occurrence_date)

        naver_client = NaverNewsClient(
            client_id=os.getenv('NAVER_CLIENT_ID', 'Le3v_zRXPEpKCD8hE_ei'),
            client_secret=os.getenv('NAVER_CLIENT_SECRET', 'g3Gcw_ACuH')
        )

        if occurrence_date:
            news_results = await naver_client.search_with_date_filter(
                query=primary_keyword,
                target_date=occurrence_date,
                days_range=7,  # ±7일 범위로 확대 (신규 사고도 더 많이 포착)
                display=5  # 20 → 5로 감소 (API 호출 절감)
            )
        else:
            news_results = await naver_client.search(primary_keyword, display=5)

        logger.info(f"[Node] Found {len(news_results)} news articles")
        state["news_results"] = news_results
        _NEWS_CACHE[primary_keyword] = (now, copy.deepcopy(news_results))

    except Exception as e:
        logger.error(f"[Node] Error searching news: {e}", exc_info=True)
        state["news_results"] = []
        state["error"] = str(e)

    return state


async def search_videos_node(state: MatcherState) -> MatcherState:
    """
    3단계: 유튜브 영상 검색 (Tool)

    YouTube API 할당량 절약:
    - 모든 화재에 대해 영상 검색 (심각도 무관)
    - 검색 결과 수: 2개 (할당량 절약)
    - 검색 기간: 최근 1주일 (관련성 향상)
    """
    from datetime import datetime, timedelta

    keywords = state["keywords"]
    incident = state["incident"]

    if not keywords:
        logger.warning("[Node] No keywords, skipping video search")
        state["video_results"] = []
        return state

    severity = incident.get('severity', 'low')
    if severity not in ('medium', 'high'):
        logger.info("[Node] Severity=%s, skipping video search", severity)
        state["video_results"] = []
        return state

    occurrence_date = incident.get('occurrenceDate', '')
    if occurrence_date:
        try:
            if datetime.utcnow() - datetime.strptime(occurrence_date, '%Y-%m-%d') > timedelta(days=5):
                logger.info("[Node] Incident older than 5 days, skipping video search")
                state["video_results"] = []
                return state
        except ValueError:
            logger.debug("[Node] Unable to parse occurrence date '%s'", occurrence_date)

    primary_keyword = keywords[0]
    logger.info(f"[Node] Searching videos with keyword: {primary_keyword} (severity={severity})")

    try:
        now = time.time()
        cache_entry = _VIDEO_CACHE.get(primary_keyword)
        if cache_entry and now - cache_entry[0] < _CACHE_TTL:
            logger.info("[Node] Using cached video results for keyword '%s'", primary_keyword)
            state["video_results"] = copy.deepcopy(cache_entry[1])
            return state

        youtube_client = YouTubeClient(
            api_key=os.getenv('YOUTUBE_API_KEY', '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')
        )

        search_start = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        logger.info(f"[Node] Searching videos published after: {search_start} (7 days range)")

        video_results = youtube_client.search(
            query=f"{primary_keyword} 화재",
            max_results=2,
            order="relevance",
            video_duration="short",
            published_after=search_start
        )

        logger.info(f"[Node] Found {len(video_results)} videos")
        state["video_results"] = video_results
        _VIDEO_CACHE[primary_keyword] = (now, copy.deepcopy(video_results))

    except Exception as e:
        logger.error(f"[Node] Error searching videos: {e}", exc_info=True)
        state["video_results"] = []
        state["error"] = str(e)

    return state


async def evaluate_relevance_node(state: MatcherState) -> MatcherState:
    """
    4단계: Llama 3.3 관련성 평가

    검색 결과의 의미적 관련성을 LLM으로 평가
    """
    incident = state["incident"]
    news_results = state["news_results"]
    video_results = state["video_results"]

    logger.info(
        f"[Node] Evaluating relevance: "
        f"{len(news_results)} news, {len(video_results)} videos"
    )

    if not news_results and not video_results:
        logger.warning("[Node] No results to evaluate")
        state["evaluated_news"] = []
        state["evaluated_videos"] = []
        return state

    try:
        incident_id = incident.get('id', '')
        news_signature = tuple(sorted((item.get('url') or item.get('title', '')) for item in news_results))
        video_signature = tuple(sorted((item.get('url') or item.get('title', '')) for item in video_results))
        cache_key = f"{incident_id}:{hash(news_signature)}:{hash(video_signature)}"

        cache_entry = _EVALUATION_CACHE.get(cache_key)
        if cache_entry and time.time() - cache_entry['ts'] < _CACHE_TTL:
            logger.info("[Node] Using cached evaluation for incident %s", incident_id)
            state["evaluated_news"] = copy.deepcopy(cache_entry['news'])
            state["evaluated_videos"] = copy.deepcopy(cache_entry['videos'])
            return state

        together_client = TogetherAIHttpClient()

        evaluation = await together_client.evaluate_relevance(
            incident=incident,
            news_results=news_results,
            video_results=video_results
        )

        # Llama가 반환한 id를 실제 검색 결과와 매핑
        evaluated_news = []
        for item in evaluation["news"]:
            idx = item["id"]
            if 0 <= idx < len(news_results):
                result = news_results[idx].copy()
                result["relevance_score"] = item["score"]
                result["relevance_reason"] = item["reason"]
                evaluated_news.append(result)

        evaluated_videos = []
        for item in evaluation["videos"]:
            idx = item["id"]
            if 0 <= idx < len(video_results):
                result = video_results[idx].copy()
                result["relevance_score"] = item["score"]
                result["relevance_reason"] = item["reason"]
                evaluated_videos.append(result)

        # 각 타입별로 최고 점수 1개만 선택
        best_news = max(evaluated_news, key=lambda x: x.get("relevance_score", 0)) if evaluated_news else None
        best_video = max(evaluated_videos, key=lambda x: x.get("relevance_score", 0)) if evaluated_videos else None

        final_news = [best_news] if best_news else []
        final_videos = [best_video] if best_video else []

        # 점수 상세 로그
        if best_news:
            logger.info(f"[Node] Best news: score={best_news.get('relevance_score'):.2f}, title={best_news.get('title', '')[:50]}")
        if best_video:
            logger.info(f"[Node] Best video: score={best_video.get('relevance_score'):.2f}, title={best_video.get('title', '')[:50]}")

        logger.info(
            f"[Node] Evaluation complete: "
            f"{len(evaluated_news)} news ({len(final_news)} selected), "
            f"{len(evaluated_videos)} videos ({len(final_videos)} selected) (score >= 0.6)"
        )

        state["evaluated_news"] = final_news
        state["evaluated_videos"] = final_videos

        _EVALUATION_CACHE[cache_key] = {
            "ts": time.time(),
            "news": copy.deepcopy(final_news),
            "videos": copy.deepcopy(final_videos),
        }

        await together_client.close()

    except Exception as e:
        logger.error(f"[Node] Error in Llama evaluation: {e}", exc_info=True)
        state["evaluated_news"] = []
        state["evaluated_videos"] = []
        state["error"] = str(e)

    return state


async def save_matches_node(state: MatcherState) -> MatcherState:
    """
    5단계: DB 저장 (news_matches 테이블)
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.database.connection import get_session
    from src.models.news_match import NewsMatch
    from datetime import datetime

    incident = state["incident"]
    incident_id = incident.get('id')
    evaluated_news = state["evaluated_news"]
    evaluated_videos = state["evaluated_videos"]

    logger.info(f"[Node] Saving {len(evaluated_news)} news and {len(evaluated_videos)} videos to DB")

    try:
        # AsyncSession 생성
        async for session in get_session():
            from sqlalchemy import select
            from sqlalchemy.dialects.postgresql import insert

            # 뉴스 저장 (upsert)
            for news in evaluated_news:
                # Naver pubDate 파싱: "Thu, 02 Oct 2025 14:48:00 +0900"
                published_at = None
                if news.get('publishedAt'):
                    try:
                        published_at = datetime.strptime(
                            news['publishedAt'],
                            "%a, %d %b %Y %H:%M:%S %z"
                        )
                    except Exception as e:
                        logger.warning(f"[Node] Failed to parse news date: {e}")

                # 중복 체크 후 insert
                stmt = select(NewsMatch).where(
                    NewsMatch.incident_id == incident_id,
                    NewsMatch.news_type == 'news',
                    NewsMatch.news_id == news.get('url', '')
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if not existing:
                    news_match = NewsMatch(
                        incident_id=incident_id,
                        news_type='news',
                        news_id=news.get('url', ''),
                        title=news.get('title', ''),
                        url=news.get('url', ''),
                        published_at=published_at,
                        thumbnail_url=None,
                        similarity_score=news.get('relevance_score', 0.0)
                    )
                    session.add(news_match)

            # 비디오 저장
            for video in evaluated_videos:
                # YouTube publishedAt 파싱: "2025-10-02T14:48:00Z"
                published_at = None
                if video.get('publishedAt'):
                    try:
                        published_at = datetime.fromisoformat(
                            video['publishedAt'].replace('Z', '+00:00')
                        )
                    except Exception as e:
                        logger.warning(f"[Node] Failed to parse video date: {e}")

                # YouTube API는 'id' 키를 사용
                video_id = video.get('id', video.get('videoId', ''))

                # 중복 체크 후 insert
                stmt = select(NewsMatch).where(
                    NewsMatch.incident_id == incident_id,
                    NewsMatch.news_type == 'video',
                    NewsMatch.news_id == video_id
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if not existing:
                    video_match = NewsMatch(
                        incident_id=incident_id,
                        news_type='video',
                        news_id=video_id,
                        title=video.get('title', ''),
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        published_at=published_at,
                        thumbnail_url=video.get('thumbnail', ''),
                        similarity_score=video.get('relevance_score', 0.0)
                    )
                    session.add(video_match)

            await session.commit()
            logger.info(f"[Node] Successfully saved matches for {incident_id}")
            break  # async for 루프 탈출

    except Exception as e:
        logger.error(f"[Node] Error saving matches to DB: {e}", exc_info=True)
        state["error"] = str(e)

    return state
