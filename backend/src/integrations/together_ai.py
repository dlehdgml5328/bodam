"""Together AI client wrapper."""

from __future__ import annotations

import json
import os
import json
from dataclasses import dataclass
from typing import Dict, List

import httpx

from src.monitoring.logging import get_logger
from src.services.ai_service import AnalysisResult, TogetherAIClient
from src.monitoring.logging import get_logger

logger = get_logger(__name__)

logger = get_logger(__name__)


@dataclass
class TogetherAISettings:
    api_key: str
    model: str = "meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo"
    base_url: str = "https://api.together.xyz"
    temperature: float = 0.1

    @classmethod
    def from_env(cls) -> "TogetherAISettings":
        api_key = os.getenv("TOGETHER_AI_API_KEY", "test_key")
        model = os.getenv("TOGETHER_AI_MODEL", cls.model)
        base_url = os.getenv("TOGETHER_AI_BASE_URL", cls.base_url)
        temperature_str = os.getenv("TOGETHER_AI_TEMPERATURE")
        temperature = cls.temperature
        if temperature_str is not None:
            try:
                temperature = float(temperature_str)
            except ValueError:
                logger.warning(
                    "[TogetherAI] Invalid TOGETHER_AI_TEMPERATURE='%s', falling back to default %.2f",
                    temperature_str,
                    cls.temperature,
                )
        return cls(api_key=api_key, model=model, base_url=base_url, temperature=temperature)


class TogetherAIHttpClient(TogetherAIClient):
    def __init__(self, settings: TogetherAISettings | None = None) -> None:
        self._settings = settings or TogetherAISettings.from_env()
        self._client = httpx.AsyncClient(
            base_url=self._settings.base_url,
            headers={"Authorization": f"Bearer {self._settings.api_key}"},
            timeout=30,
        )

    async def analyze_news(
        self,
        *,
        title: str,
        content: str,
        source: str,
    ) -> AnalysisResult:
        # In production, call Together AI inference endpoint. Here we mock the response.
        summary = content[:140] + "..." if len(content) > 140 else content
        keywords = [word for word in title.split()[:3]]
        relevance_score = 80
        embedding = [0.0] * 10
        return AnalysisResult(
            summary=summary,
            keywords=keywords,
            relevance_score=relevance_score,
            embedding=embedding,
        )

    async def evaluate_relevance(
        self,
        incident: Dict,
        news_results: List[Dict],
        video_results: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        뉴스/영상의 사고 관련성 평가 (Llama 3.3)

        Args:
            incident: 화재 출동 데이터
            news_results: 네이버 뉴스 검색 결과
            video_results: 유튜브 검색 결과

        Returns:
            Dict: {"news": [...], "videos": [...]} (관련도 높은 순 Top 3)
        """
        logger.info(f"[TogetherAI] Evaluating relevance for incident: {incident.get('id')}")

        # 프롬프트 생성
        prompt = self._build_evaluation_prompt(incident, news_results, video_results)

        try:
            response = await self._client.post(
                "/v1/chat/completions",
                json={
                    "model": self._settings.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "당신은 화재 사고와 뉴스/영상의 관련성을 정확히 평가하는 전문가입니다. JSON 형식으로만 답변하세요."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": self._settings.temperature,
                    "max_tokens": 2000
                }
            )

            response.raise_for_status()
            result = response.json()

            # 응답 파싱
            content = result["choices"][0]["message"]["content"]

            # JSON 추출 (마크다운 코드 블록 제거)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            evaluation = json.loads(content)

            # 점수 기준으로 정렬 및 Top 3 선택
            ranked_news = sorted(
                evaluation.get("news", []),
                key=lambda x: x.get("score", 0),
                reverse=True
            )[:3]

            ranked_videos = sorted(
                evaluation.get("videos", []),
                key=lambda x: x.get("score", 0),
                reverse=True
            )[:3]

            logger.info(
                f"[TogetherAI] Evaluation complete: "
                f"{len(ranked_news)} news, {len(ranked_videos)} videos"
            )

            return {
                "news": ranked_news,
                "videos": ranked_videos
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"[TogetherAI] HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"[TogetherAI] JSON parsing error: {e}")
            raise
        except Exception as e:
            logger.error(f"[TogetherAI] Unexpected error: {e}", exc_info=True)
            raise

    def _build_evaluation_prompt(
        self,
        incident: Dict,
        news_results: List[Dict],
        video_results: List[Dict]
    ) -> str:
        """평가 프롬프트 생성"""
        news_list = [{"id": i, "title": n.get("title", ""), "description": n.get("description", "")} for i, n in enumerate(news_results)]
        video_list = [{"id": i, "title": v.get("title", ""), "description": v.get("description", "")} for i, v in enumerate(video_results)]

        return f"""
다음 화재 사고 정보를 확인하세요:

**사고 정보**
- 발생일: {incident.get('occurrenceDate', '알 수 없음')}
- 위치: {incident.get('address', '알 수 없음')}
- 소방서: {incident.get('fireName', '알 수 없음')}

**뉴스 검색 결과** (총 {len(news_results)}건)
{json.dumps(news_list, ensure_ascii=False, indent=2)}

**영상 검색 결과** (총 {len(video_results)}건)
{json.dumps(video_list, ensure_ascii=False, indent=2)}

---

**작업**: 위 뉴스와 영상이 해당 화재 사고와 **실제로 관련이 있는지** 평가하세요.

**평가 기준**:
1. **지역 일치**: 사고 위치와 뉴스/영상의 지역이 일치하는가?
2. **날짜 일치**: 사고 발생일과 뉴스/영상의 보도 시점이 유사한가?
3. **내용 일치**: 제목/설명에서 화재 관련 키워드가 있는가?
4. **의미적 관련성**: 맥락상 같은 사건을 다루는가?

**점수 기준**:
- 1.0: 명백히 같은 사고 (지역+날짜+내용 모두 일치)
- 0.7~0.9: 관련 가능성 높음 (2개 이상 일치)
- 0.4~0.6: 관련 가능성 보통 (1개 일치)
- 0.0~0.3: 관련 없음

**출력 형식** (JSON만):
```json
{{{{
  "news": [
    {{{{"id": 0, "score": 0.95, "reason": "서울 강남구 화재, 날짜 일치"}}}},
    {{{{"id": 2, "score": 0.8, "reason": "지역 일치, 날짜 유사"}}}}
  ],
  "videos": [
    {{{{"id": 1, "score": 0.9, "reason": "같은 사고 영상 보도"}}}},
    {{{{"id": 0, "score": 0.7, "reason": "지역 일치, 내용 관련"}}}}
  ]
}}}}
```

**중요**: 점수가 0.6 이상인 항목만 포함하세요. JSON 형식만 출력하세요.
"""

    async def close(self) -> None:
        await self._client.aclose()


__all__ = ["TogetherAIHttpClient", "TogetherAISettings"]
