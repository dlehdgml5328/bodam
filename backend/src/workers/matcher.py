"""
뉴스/영상 매칭 Worker (LangGraph)

크롤링된 화재 출동 데이터를 기반으로
네이버 뉴스와 YouTube 영상을 검색하여 Llama 3.3으로 관련성 평가
"""
from datetime import datetime
from typing import Dict

from celery import shared_task
from langgraph.graph import END, StateGraph

from src.monitoring.logging import get_logger
from src.workers.langgraph_nodes import (
    MatcherState,
    evaluate_relevance_node,
    extract_keywords_node,
    save_matches_node,
    search_news_node,
    search_videos_node,
)

logger = get_logger(__name__)


def build_matcher_graph() -> StateGraph:
    """
    LangGraph 매칭 워크플로우 구성

    플로우:
    1. extract_keywords: 검색 키워드 생성
    2. search_news: Naver News API 호출 (Tool)
    3. search_videos: YouTube API 호출 (Tool)
    4. evaluate_relevance: Llama 3.3 관련성 평가
    5. save_matches: DB 저장 (news_matches)
    """
    workflow = StateGraph(MatcherState)

    # 노드 추가
    workflow.add_node("extract_keywords", extract_keywords_node)
    workflow.add_node("search_news", search_news_node)
    workflow.add_node("search_videos", search_videos_node)
    workflow.add_node("evaluate_relevance", evaluate_relevance_node)
    workflow.add_node("save_matches", save_matches_node)

    # 엣지 정의 (순차 실행)
    workflow.set_entry_point("extract_keywords")
    workflow.add_edge("extract_keywords", "search_news")
    workflow.add_edge("search_news", "search_videos")
    workflow.add_edge("search_videos", "evaluate_relevance")
    workflow.add_edge("evaluate_relevance", "save_matches")
    workflow.add_edge("save_matches", END)

    return workflow.compile()


async def _run_matcher(incident: Dict):
    """
    화재 출동 데이터에 뉴스/영상 매칭 (LangGraph) - 실제 async 로직

    Args:
        incident: 화재 출동 데이터
    """
    incident_id = incident.get("id")
    logger.info(f"[Matcher] Starting LangGraph match for incident: {incident_id}")

    # 발생 날짜 확인 (7일 이상 지난 화재는 건너뛰기 - 개선: 2일 → 7일)
    occurrence_date = incident.get("occurrenceDate", "")
    if occurrence_date:
        try:
            occurrence_dt = datetime.fromisoformat(occurrence_date)
            days_ago = (datetime.now() - occurrence_dt).days
            if days_ago > 7:
                logger.info(f"[Matcher] Incident {incident_id} is {days_ago} days old, skipping (max 7 days)")
                return {
                    "incident_id": incident_id,
                    "news_count": 0,
                    "video_count": 0,
                    "skipped": True,
                    "reason": "too_old"
                }
        except ValueError:
            pass  # 날짜 파싱 실패 시 계속 진행

    # 이미 매칭된 사고인지 확인 (API 호출 절감)
    try:
        from sqlalchemy import select

        from src.database.connection import get_session
        from src.models.news_match import NewsMatch

        async for session in get_session():
            stmt = select(NewsMatch).where(NewsMatch.incident_id == incident_id).limit(1)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(f"[Matcher] Incident {incident_id} already matched, skipping")
                return {
                    "incident_id": incident_id,
                    "news_count": 0,
                    "video_count": 0,
                    "skipped": True,
                    "reason": "already_matched"
                }
            break
    except Exception as e:
        logger.warning(f"[Matcher] Error checking existing match: {e}")
        # 에러 발생 시에도 매칭 진행

    try:
        # LangGraph 워크플로우 빌드
        graph = build_matcher_graph()

        # 초기 상태 설정
        initial_state: MatcherState = {
            "incident": incident,
            "keywords": [],
            "news_results": [],
            "video_results": [],
            "evaluated_news": [],
            "evaluated_videos": [],
            "error": None
        }

        # 워크플로우 실행
        final_state = await graph.ainvoke(initial_state)

        # 에러 체크
        if final_state.get("error"):
            logger.error(f"[Matcher] Workflow error: {final_state['error']}")
            # 에러 발생 시에도 부분 결과 저장

        logger.info(
            f"[Matcher] LangGraph match complete for {incident_id}: "
            f"{len(final_state['evaluated_news'])} news, "
            f"{len(final_state['evaluated_videos'])} videos"
        )

        # DB에 저장되었으므로 Redis는 스킵 (API가 DB를 먼저 확인함)
        return {
            "incident_id": incident_id,
            "news_count": len(final_state["evaluated_news"]),
            "video_count": len(final_state["evaluated_videos"])
        }

    except Exception as e:
        logger.error(f"[Matcher] Error matching incident {incident_id}: {e}", exc_info=True)
        raise


@shared_task
def match_news_and_videos(incident: Dict):
    """
    화재 출동 데이터에 뉴스/영상 매칭 (LangGraph)

    Args:
        incident: 화재 출동 데이터
    """
    import asyncio

    # 기존 event loop 사용 (Celery worker의 loop)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # 없으면 새로 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(_run_matcher(incident))
    except Exception as e:
        logger.error(f"[Matcher] Task failed: {e}", exc_info=True)
        raise


@shared_task
def retry_failed_matches(max_age_days: int = 7):
    """
    매칭 실패한 화재 사고를 재시도

    - 최근 7일 이내 발생한 화재 중
    - 뉴스/영상 매칭이 없거나 적은 사고를 재매칭
    - 6시간마다 Celery Beat로 실행

    Args:
        max_age_days: 재시도 대상 최대 경과 일수 (기본 7일)

    Returns:
        dict: 재시도 통계
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(_retry_failed_matches_async(max_age_days))
    except Exception as e:
        logger.error(f"[Matcher] Retry task failed: {e}", exc_info=True)
        raise


async def _retry_failed_matches_async(max_age_days: int) -> Dict:
    """재매칭 로직 (비동기)"""
    from datetime import timedelta

    from sqlalchemy import func, select

    from src.database.connection import session_scope
    from src.models.news_match import NewsMatch

    cutoff_date = datetime.now() - timedelta(days=max_age_days)

    logger.info(f"[Matcher] Starting retry for incidents since {cutoff_date.date()}")

    retried = 0
    skipped = 0
    failed = 0

    # 재매칭 대상 찾기: 발생일 7일 이내, 매칭이 없거나 2개 미만
    async with session_scope() as session:
        # 모든 화재 사고 조회 (간단하게 - 실제로는 incidents 테이블에서 가져와야 함)
        # 여기서는 news_matches 테이블에서 매칭 수를 확인
        stmt = (
            select(NewsMatch.incident_id, func.count(NewsMatch.id).label("match_count"))
            .where(NewsMatch.created_at >= cutoff_date)
            .group_by(NewsMatch.incident_id)
            .having(func.count(NewsMatch.id) < 2)  # 매칭이 2개 미만
        )

        result = await session.execute(stmt)
        low_match_incidents = result.all()

        logger.info(f"[Matcher] Found {len(low_match_incidents)} incidents with low matches")

        # 각 사고에 대해 재매칭 시도
        for incident_id, match_count in low_match_incidents:
            try:
                # 실제로는 incidents 테이블에서 전체 정보를 가져와야 함
                # 여기서는 간단하게 incident_id만 사용
                incident_data = {
                    "id": incident_id,
                    "occurrenceDate": (datetime.now() - timedelta(days=1)).isoformat(),  # 임시
                    # 실제로는 DB에서 조회한 전체 데이터 사용
                }

                # 기존 매칭 삭제 (재매칭을 위해)
                from sqlalchemy import delete
                delete_stmt = delete(NewsMatch).where(NewsMatch.incident_id == incident_id)
                await session.execute(delete_stmt)
                await session.commit()

                # 재매칭 실행
                logger.info(f"[Matcher] Retrying match for incident {incident_id} (current: {match_count} matches)")

                # 비동기로 매칭 실행
                result = await _run_matcher(incident_data)

                if result.get("skipped"):
                    skipped += 1
                else:
                    retried += 1
                    logger.info(
                        f"[Matcher] Retry success for {incident_id}: "
                        f"{result.get('news_count', 0)} news, {result.get('video_count', 0)} videos"
                    )

            except Exception as e:
                logger.error(f"[Matcher] Retry failed for {incident_id}: {e}", exc_info=True)
                failed += 1
                continue

    logger.info(
        f"[Matcher] Retry complete: {retried} retried, {skipped} skipped, {failed} failed"
    )

    return {
        "retried": retried,
        "skipped": skipped,
        "failed": failed,
        "total_candidates": len(low_match_incidents) if "low_match_incidents" in locals() else 0
    }
