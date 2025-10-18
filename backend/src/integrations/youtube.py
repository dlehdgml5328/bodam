"""
YouTube Data API v3 클라이언트

화재 출동 데이터에 매칭되는 영상 검색
"""
from typing import Dict, List

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.monitoring.logging import get_logger

logger = get_logger(__name__)


class YouTubeClient:
    """YouTube Data API v3 - 영상 검색"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Google API 키
        """
        self.api_key = api_key
        self.youtube = build("youtube", "v3", developerKey=api_key)

    def search(
        self,
        query: str,
        max_results: int = 5,
        order: str = "date",
        video_duration: str = "any",
        published_after: str = None
    ) -> List[Dict]:
        """
        영상 검색

        Args:
            query: 검색 키워드
            max_results: 검색 결과 개수 (최대 50)
            order: 정렬 옵션 (date, relevance, viewCount, rating)
            video_duration: 영상 길이 (any, short, medium, long)
            published_after: 이 날짜 이후 발행된 영상만 검색 (RFC 3339 format: 2025-01-01T00:00:00Z)

        Returns:
            List[Dict]: 영상 검색 결과
        """
        try:
            search_params = {
                "q": query,
                "part": "snippet",
                "type": "video",
                "maxResults": min(max_results, 50),
                "order": order,
                "relevanceLanguage": "ko",
                "videoDuration": video_duration
            }

            if published_after:
                search_params["publishedAfter"] = published_after

            request = self.youtube.search().list(**search_params)

            response = request.execute()
            items = response.get("items", [])

            logger.info(f"[YouTube] Found {len(items)} results for '{query}'")

            return [
                {
                    "id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
                    "thumbnailHigh": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                    "description": item["snippet"]["description"],
                    "publishedAt": item["snippet"]["publishedAt"],
                    "channelTitle": item["snippet"]["channelTitle"]
                }
                for item in items
            ]

        except HttpError as e:
            logger.error(f"[YouTube] HTTP error: {e.resp.status} - {e.content}")
            return []

        except Exception as e:
            logger.error(f"[YouTube] Search error: {e}", exc_info=True)
            return []

    def search_news_videos(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        뉴스 영상 검색 (짧은 영상 위주)

        Args:
            query: 검색 키워드
            max_results: 검색 결과 개수

        Returns:
            List[Dict]: 뉴스 영상 검색 결과
        """
        # 뉴스 키워드 추가
        news_query = f"{query} 뉴스"

        return self.search(
            query=news_query,
            max_results=max_results,
            order="relevance",  # 관련도순
            video_duration="short"  # 4분 이하
        )
