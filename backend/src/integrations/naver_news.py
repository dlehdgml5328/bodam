"""
네이버 뉴스 검색 API 클라이언트

화재 출동 데이터에 매칭되는 뉴스 기사 검색
"""
from datetime import datetime, timedelta
from typing import Dict, List

import httpx

from src.monitoring.logging import get_logger

logger = get_logger(__name__)


class NaverNewsClient:
    """네이버 검색 API - 뉴스 검색"""

    BASE_URL = "https://openapi.naver.com/v1/search/news.json"

    def __init__(self, client_id: str, client_secret: str):
        """
        Args:
            client_id: 네이버 API 클라이언트 ID
            client_secret: 네이버 API 클라이언트 Secret
        """
        self.client_id = client_id
        self.client_secret = client_secret

    async def search(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date"
    ) -> List[Dict]:
        """
        뉴스 검색

        Args:
            query: 검색 키워드
            display: 검색 결과 개수 (최대 100)
            start: 검색 시작 위치 (최대 1000)
            sort: 정렬 옵션 (date: 날짜순, sim: 정확도순)

        Returns:
            List[Dict]: 뉴스 검색 결과
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

        params = {
            "query": query,
            "display": min(display, 100),
            "start": min(start, 1000),
            "sort": sort
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                items = data.get("items", [])
                logger.info(f"[NaverNews] Found {len(items)} results for '{query}'")

                return [
                    {
                        "title": self._clean_html(item["title"]),
                        "url": item["link"],
                        "description": self._clean_html(item["description"]),
                        "publishedAt": item["pubDate"]
                    }
                    for item in items
                ]

        except httpx.HTTPStatusError as e:
            logger.error(f"[NaverNews] HTTP error: {e.response.status_code}")
            return []

        except Exception as e:
            logger.error(f"[NaverNews] Search error: {e}", exc_info=True)
            return []

    async def search_with_date_filter(
        self,
        query: str,
        target_date: str,
        days_range: int = 3,
        display: int = 20
    ) -> List[Dict]:
        """
        날짜 필터링이 적용된 뉴스 검색

        Args:
            query: 검색 키워드
            target_date: 목표 날짜 (YYYY-MM-DD)
            days_range: 목표 날짜 전후 범위 (±N일)
            display: 검색 결과 개수

        Returns:
            List[Dict]: 필터링된 뉴스 검색 결과
        """
        # 전체 검색 먼저 수행
        all_results = await self.search(query, display=display, sort="date")

        if not all_results:
            return []

        # 날짜 필터링
        target = datetime.strptime(target_date, "%Y-%m-%d")
        min_date = target - timedelta(days=days_range)
        max_date = target + timedelta(days=days_range)

        filtered = []
        for result in all_results:
            try:
                # pubDate 형식: "Mon, 10 Oct 2025 13:00:00 +0900"
                pub_date_str = result["publishedAt"]
                pub_date = datetime.strptime(
                    pub_date_str,
                    "%a, %d %b %Y %H:%M:%S %z"
                )
                pub_date_naive = pub_date.replace(tzinfo=None)

                if min_date <= pub_date_naive <= max_date:
                    result["matchedDate"] = True
                    filtered.append(result)

            except Exception as e:
                logger.warning(f"[NaverNews] Date parse error: {e}")
                continue

        logger.info(
            f"[NaverNews] Filtered {len(filtered)}/{len(all_results)} "
            f"results within ±{days_range} days of {target_date}"
        )

        return filtered

    @staticmethod
    def _clean_html(text: str) -> str:
        """HTML 태그 제거"""
        return (
            text.replace("<b>", "")
            .replace("</b>", "")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )
