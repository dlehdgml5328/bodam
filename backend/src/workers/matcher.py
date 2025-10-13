"""
뉴스/영상 매칭 Worker (LangGraph)

크롤링된 화재 출동 데이터를 기반으로
네이버 뉴스와 YouTube 영상을 검색하여 Llama 3.3으로 관련성 평가
"""
from celery import shared_task
from typing import Dict
from datetime import datetime
import json
from langgraph.graph import StateGraph, END
from src.workers.langgraph_nodes import (
    MatcherState,
    extract_keywords_node,
    search_news_node,
    search_videos_node,
    evaluate_relevance_node,
    save_matches_node
)
from src.cache.clients import get_cache_client
from src.monitoring.logging import get_logger

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


@shared_task
def match_news_and_videos(incident: Dict):
    """
    화재 출동 데이터에 뉴스/영상 매칭 (LangGraph)

    Args:
        incident: 화재 출동 데이터
    """
    import asyncio

    incident_id = incident.get('id')
    logger.info(f"[Matcher] Starting LangGraph match for incident: {incident_id}")

    async def _match():
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

            # Redis에 저장
            redis = await get_cache_client()

            matched_data = {
                **incident,
                "relatedNews": final_state["evaluated_news"],
                "relatedVideos": final_state["evaluated_videos"],
                "matchedAt": datetime.now().isoformat(),
                "keywords": final_state["keywords"],
                "evaluationMethod": "llama-3.3-70b"
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
                f"[Matcher] LangGraph match complete for {incident_id}: "
                f"{len(final_state['evaluated_news'])} news, "
                f"{len(final_state['evaluated_videos'])} videos"
            )

            return matched_data

        except Exception as e:
            logger.error(f"[Matcher] Error matching incident {incident_id}: {e}", exc_info=True)
            raise

    # asyncio 실행
    try:
        return asyncio.run(_match())
    except Exception as e:
        logger.error(f"[Matcher] Task failed: {e}", exc_info=True)
        raise
