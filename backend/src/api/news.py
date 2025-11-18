"""News and media API endpoints powered by Redis feeds with mock fallback."""

from __future__ import annotations

import html
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.integrations.mock_site import MockFireNewsClient, load_local_incidents
from src.services.news_service import BreakingNewsRecord, NewsService, VideoNewsRecord

router = APIRouter(prefix="/api/news", tags=["news"])


class VideoNewsResponse(BaseModel):
    id: int
    title: str
    thumbnail: str
    duration: str
    time: str
    video_url: str | None = None
    article_url: str
    category: str
    summary: str
    views: int
    likes: int
    video_id: str

    class Config:
        populate_by_name = True
        # JSON 응답 시 카멜케이스로 변환
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
        by_alias = True


class BreakingNewsResponse(BaseModel):
    title: str
    time: str
    is_breaking: bool
    link: str

    class Config:
        populate_by_name = True
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
        by_alias = True


_UNSPLASH_IMAGES: tuple[str, ...] = (
    "photo-1501706362039-c6e80948a90d",
    "photo-1618005198919-d3d4b5a92eee",
    "photo-1464036388609-747537735eab",
    "photo-1497366754035-f200968a6e72",
    "photo-1523475472560-d2df97ec485c",
    "photo-1521033719794-41049d18b9fb",
)

_CATEGORY_BY_PROGRESS: dict[str, str] = {
    "진압완료": "현장영상",
    "진압중": "속보",
    "보상완료": "후속보도",
    "예방훈련": "훈련",
    "점검완료": "점검",
}

_CATEGORY_BY_STATUS: dict[str, str] = {
    "A": "속보",
    "B": "속보",
    "C": "브리핑",
    "D": "현장영상",
}


logger = logging.getLogger(__name__)

_client = MockFireNewsClient()
_CACHE_TTL = timedelta(minutes=5)
_incident_cache: tuple[datetime, list[dict[str, Any]]] | None = None
_news_service = NewsService()


def _format_datetime_obj(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


async def _get_fallback_incidents() -> list[dict[str, Any]]:
    global _incident_cache

    now = datetime.utcnow()
    if _incident_cache is not None:
        cached_at, cached_data = _incident_cache
        if now - cached_at < _CACHE_TTL:
            return cached_data

    incidents: list[dict[str, Any]] = []
    try:
        incidents = await _client.fetch_incidents()
        logger.debug("[NewsAPI] Retrieved %d incidents from mock site", len(incidents))
    except Exception as exc:  # pragma: no cover - network failure fallback
        logger.warning("[NewsAPI] Remote mock site fetch failed: %s", exc)

    if not incidents:
        incidents = load_local_incidents()
        if incidents:
            logger.info("[NewsAPI] Falling back to bundled mock incident data")
        else:
            logger.error("[NewsAPI] No incident data available after fallback")
            return []

    _incident_cache = (now, incidents)
    return incidents


def _format_datetime(date_str: str, time_str: str) -> str:
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return date_str
    return dt.strftime("%Y-%m-%d %H:%M")


def _choose_thumbnail(index: int) -> str:
    image_id = _UNSPLASH_IMAGES[index % len(_UNSPLASH_IMAGES)]
    return f"https://images.unsplash.com/{image_id}?auto=format&fit=crop&w=800&q=80"


def _extract_video_url(raw_url: str) -> str | None:
    if "youtube.com/watch" in raw_url:
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(raw_url)
        video_id = parse_qs(parsed.query).get("v", [None])[0]
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
    if "youtu.be/" in raw_url:
        video_id = raw_url.rstrip("/").split("/")[-1]
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
    return None


def _estimate_duration(seed: int) -> str:
    minutes = 2 + seed % 5
    seconds = seed % 60
    return f"{minutes:02}:{seconds:02}"


def _estimate_views(seed: int) -> tuple[int, int]:
    views = 5000 + (seed % 25000)
    likes = max(200, views // 6)
    return views, likes


def _build_video_news(incidents: list[dict[str, Any]], limit: int) -> list[VideoNewsResponse]:
    payload: list[VideoNewsResponse] = []
    for index, item in enumerate(incidents[:limit]):
        incident_id = item.get("id", f"incident-{index}")
        seed = sum(ord(ch) for ch in str(incident_id))
        views, likes = _estimate_views(seed)
        title = item.get("newsTitle") or f"{item.get('fireName', '소방서')} 소식"
        raw_link = str(item.get("newsLink") or "")
        payload.append(
            VideoNewsResponse(
                id=index + 1,
                title=title,
                thumbnail=_choose_thumbnail(index),
                duration=_estimate_duration(seed),
                time=_format_datetime(
                    str(item.get("occurrenceDate", "")), str(item.get("occurrenceTime", "00:00"))
                ),
                video_url=_extract_video_url(raw_link),
                article_url=raw_link,
                category=_CATEGORY_BY_PROGRESS.get(
                    str(item.get("progress", "")).strip(), _CATEGORY_BY_STATUS.get(item.get("status", ""), "브리핑")
                ),
                summary=item.get("address") or "소방 활동 현장의 최신 소식입니다.",
                views=views,
                likes=likes,
                video_id=str(incident_id),
            )
        )
    return payload


def _build_breaking_news(incidents: list[dict[str, Any]], limit: int) -> list[BreakingNewsResponse]:
    payload: list[BreakingNewsResponse] = []
    for item in incidents[:limit]:
        status_code = str(item.get("status", "")).upper()
        payload.append(
            BreakingNewsResponse(
                title=item.get("newsTitle") or f"{item.get('fireName', '소방서')} 출동 소식",
                time=_format_datetime(
                    str(item.get("occurrenceDate", "")), str(item.get("occurrenceTime", "00:00"))
                ),
                is_breaking=status_code in {"A", "B", "D"},
                link=item.get("newsLink") or "",
            )
        )
    return payload


def _map_video_record(record: VideoNewsRecord, index: int) -> VideoNewsResponse:
    metadata = record.metadata or {}
    duration = metadata.get("duration")
    if not isinstance(duration, str) or not duration.strip():
        seed = sum(ord(ch) for ch in record.id) + index
        duration = _estimate_duration(seed)

    thumbnail = record.thumbnail_url or _choose_thumbnail(index)
    views = record.views if record.views is not None else 0
    likes = record.likes if record.likes is not None else max(1, views // 6)
    category = record.category or "현장영상"

    return VideoNewsResponse(
        id=index + 1,
        title=record.title,
        thumbnail=thumbnail,
        duration=duration,
        time=_format_datetime_obj(record.occurred_at),
        video_url=record.video_url,
        article_url=record.article_url or "",
        category=category,
        summary=record.summary or "소방 활동 현장의 최신 소식입니다.",
        views=views,
        likes=likes,
        video_id=record.id,
    )


def _map_breaking_record(record: BreakingNewsRecord) -> BreakingNewsResponse:
    link = record.link or ""
    return BreakingNewsResponse(
        title=record.title,
        time=_format_datetime_obj(record.timestamp),
        is_breaking=record.is_breaking,
        link=link,
    )


async def _get_video_payload(limit: int) -> list[VideoNewsResponse]:
    # DB에서 영상만 가져오기 (실시간 주요 뉴스 섹션)
    logger.warning(f"[NewsAPI] _get_video_payload called with limit={limit}")
    try:
        logger.warning(f"[NewsAPI] Starting imports")
        from sqlalchemy import select, desc
        from src.database.connection import get_session
        from src.models.news_match import NewsMatch
        from src.models.fire_incident import FireIncident
        logger.warning(f"[NewsAPI] Imports done")

        # 필터링할 키워드 (교육, 훈련 영상 제외)
        exclude_keywords = ["예담직업전문학교", "교육", "훈련", "체험", "안전테마파크"]

        logger.warning(f"[NewsAPI] About to create session")
        from src.database.connection import SessionLocal

        video_list = []
        async with SessionLocal() as session:
            logger.warning(f"[NewsAPI] Session created")
            query = (
                select(NewsMatch, FireIncident)
                .join(FireIncident, NewsMatch.incident_id == FireIncident.id)
                .where(NewsMatch.news_type == "video")
                .order_by(desc(NewsMatch.created_at))
                .limit(limit * 2)  # 필터링 후 충분한 개수를 위해 더 많이 가져옴
            )
            logger.warning(f"[NewsAPI] Query created")

            result = await session.execute(query)
            logger.warning(f"[NewsAPI] Query executed")
            rows = result.all()
            logger.warning(f"[NewsAPI] Query returned {len(rows)} rows")
            logger.warning(f"[NewsAPI] Rows type: {type(rows)}")
            if rows:
                logger.warning(f"[NewsAPI] First row: {rows[0] if rows else None}")

            if rows:
                seen_video_ids = set()  # 중복 제거를 위한 set

                for idx, (news_match, incident) in enumerate(rows):
                    # HTML 엔티티 디코딩
                    title = html.unescape(news_match.title)

                    # 제외 키워드 필터링
                    if any(keyword in title for keyword in exclude_keywords):
                        logger.debug(f"[NewsAPI] Filtered out: {title}")
                        continue

                    # YouTube URL에서 video ID 추출
                    video_id = news_match.news_id
                    if "youtube.com/watch?v=" in news_match.url:
                        video_id = news_match.url.split("v=")[1].split("&")[0]
                    elif "youtu.be/" in news_match.url:
                        video_id = news_match.url.split("youtu.be/")[1].split("?")[0]

                    # 중복 제거: 이미 본 video_id는 스킵
                    if video_id in seen_video_ids:
                        logger.debug(f"[NewsAPI] Duplicate video_id: {video_id}")
                        continue
                    seen_video_ids.add(video_id)

                    # 썸네일 URL
                    thumbnail = news_match.thumbnail_url or f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

                    # 시간 포맷
                    published_at = news_match.published_at or news_match.created_at
                    time_str = _format_datetime_obj(published_at) if published_at else ""

                    video_list.append(VideoNewsResponse(
                        id=len(video_list) + 1,  # idx 대신 실제 추가된 개수 사용
                        title=title,
                        thumbnail=thumbnail,
                        duration="00:00",
                        time=time_str,
                        video_url=f"https://www.youtube.com/embed/{video_id}",
                        article_url=news_match.url,
                        category="화재",
                        summary=f"{incident.location_address}에서 발생한 화재 사고",
                        views=0,
                        likes=0,
                        video_id=video_id,
                    ))

                    # limit 개수만큼만 반환
                    if len(video_list) >= limit:
                        break

            logger.info(f"[NewsAPI] Loaded {len(video_list)} videos from news_matches table (filtered)")
            return video_list
    except Exception as e:
        import traceback
        logger.error(f"[NewsAPI] Failed to load from DB: {e}")
        logger.error(f"[NewsAPI] Traceback: {traceback.format_exc()}")
        # DB 조회 실패 시에도 빈 배열 반환 (Fallback 없음)
        logger.warning(f"[NewsAPI] Returning empty list (fallback)")
        return []


async def _get_breaking_payload(limit: int) -> list[BreakingNewsResponse]:
    logger.info(f"[NewsAPI] _get_breaking_payload called with limit={limit}")
    # 먼저 DB에서 실제 매칭된 뉴스 데이터 가져오기
    try:
        from sqlalchemy import select, desc
        from src.database.connection import get_session
        from src.models.news_match import NewsMatch
        from src.models.fire_incident import FireIncident

        async for session in get_session():
            query = (
                select(NewsMatch, FireIncident)
                .join(FireIncident, NewsMatch.incident_id == FireIncident.id)
                .where(NewsMatch.news_type == "news")
                .order_by(desc(NewsMatch.created_at))
                .limit(limit)
            )

            result = await session.execute(query)
            rows = result.all()
            logger.info(f"[NewsAPI] Query returned {len(rows)} rows")

            if rows:
                news_list = []
                seen_urls = set()  # 중복 제거를 위한 set (URL 기준)

                for news_match, incident in rows:
                    # 중복 제거: 같은 URL은 스킵
                    if news_match.url in seen_urls:
                        logger.debug(f"[NewsAPI] Duplicate URL: {news_match.url}")
                        continue
                    seen_urls.add(news_match.url)

                    # HTML 엔티티 디코딩
                    title = html.unescape(news_match.title)

                    # 시간 포맷
                    published_at = news_match.published_at or news_match.created_at
                    time_str = _format_datetime_obj(published_at) if published_at else ""

                    # 최근 1시간 이내면 속보
                    is_breaking = False
                    if published_at:
                        from datetime import datetime, timezone
                        time_diff = datetime.now(timezone.utc) - published_at
                        is_breaking = time_diff.total_seconds() < 3600  # 1시간

                    news_list.append(BreakingNewsResponse(
                        title=title,
                        time=time_str,
                        is_breaking=is_breaking,
                        link=news_match.url,
                    ))

                    # limit 개수만큼만 반환
                    if len(news_list) >= limit:
                        break

                logger.info(f"[NewsAPI] Loaded {len(news_list)} breaking news from news_matches table (unique)")
                return news_list
            break
    except Exception as e:
        logger.warning(f"[NewsAPI] Failed to load from DB: {e}")

    # Fallback: Redis
    redis_records = await _news_service.fetch_breaking(limit)
    if redis_records:
        return [_map_breaking_record(record) for record in redis_records[:limit]]

    # Final fallback: Mock data
    incidents = await _get_fallback_incidents()
    if not incidents:
        return []
    return _build_breaking_news(incidents, limit)


@router.get("/videos", response_model=list[VideoNewsResponse])
async def list_video_news(limit: int = Query(default=6, ge=1, le=50)) -> list[VideoNewsResponse]:
    """영상 뉴스 목록 (mock-site incidents 기반)."""
    return await _get_video_payload(limit)


@router.get("/breaking", response_model=list[BreakingNewsResponse])
async def list_breaking_news(limit: int = Query(default=15, ge=1, le=50)) -> list[BreakingNewsResponse]:
    """속보 뉴스 스트림 (mock-site incidents 기반)."""
    return await _get_breaking_payload(limit)


__all__ = ["router"]
