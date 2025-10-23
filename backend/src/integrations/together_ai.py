"""Together AI client wrapper."""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import anyio
from together import Together

from src.monitoring.logging import get_logger
from src.services.ai_service import AnalysisResult, TogetherAIClient

logger = get_logger(__name__)


@dataclass
class TogetherAISettings:
    api_key: str
    model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
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


_RATE_LIMIT_LOCK = asyncio.Lock()
_LAST_REQUEST_TS = 0.0
_MIN_INTERVAL = float(os.getenv("TOGETHER_AI_MIN_INTERVAL", "0.2"))
_MAX_RETRIES = int(os.getenv("TOGETHER_AI_MAX_RETRIES", "3"))


async def _acquire_rate_limit() -> None:
    """Ensure Together API requests respect the minimum interval."""
    global _LAST_REQUEST_TS
    async with _RATE_LIMIT_LOCK:
        now = time.time()
        delta = now - _LAST_REQUEST_TS
        if delta < _MIN_INTERVAL:
            await asyncio.sleep(_MIN_INTERVAL - delta)
        _LAST_REQUEST_TS = time.time()


class TogetherAIHttpClient(TogetherAIClient):
    def __init__(self, settings: TogetherAISettings | None = None) -> None:
        self._settings = settings or TogetherAISettings.from_env()
        os.environ.setdefault("TOGETHER_API_KEY", self._settings.api_key)
        self._client = Together(api_key=self._settings.api_key)

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

        attempt = 0
        while True:
            try:
                await _acquire_rate_limit()
                result = await anyio.to_thread.run_sync(
                    lambda: self._client.chat.completions.create(
                        model=self._settings.model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "당신은 화재 사고와 뉴스/영상의 관련성을 정확히 평가하는 전문가입니다. "
                                    "JSON 형식으로만 답변하세요."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=self._settings.temperature,
                        max_tokens=2000,
                    )
                )

                choice = result.choices[0]
                message = getattr(choice, "message", None)
                if isinstance(choice, dict):
                    message = choice.get("message")

                content = ""
                if isinstance(message, dict):
                    content = message.get("content", "")
                elif message is not None:
                    content = getattr(message, "content", "")

                # JSON 추출 (마크다운 코드 블록 제거)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```", 1)[1].split("```")[0].strip()

                evaluation = json.loads(content) if content else {"news": [], "videos": []}

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
                    "[TogetherAI] Evaluation complete: %d news, %d videos",
                    len(ranked_news),
                    len(ranked_videos),
                )

                return {
                    "news": ranked_news,
                    "videos": ranked_videos
                }

            except json.JSONDecodeError as e:
                logger.error(f"[TogetherAI] JSON parsing error: {e}")
                raise
            except Exception as e:
                attempt += 1
                message = str(e)
                if attempt < _MAX_RETRIES and ("429" in message or "Too Many Requests" in message):
                    backoff = min(5.0, 0.5 * attempt)
                    logger.warning(
                        "[TogetherAI] Rate limit encountered (attempt %d/%d). Backing off %.1fs",
                        attempt,
                        _MAX_RETRIES,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue

                logger.error(f"[TogetherAI] Unexpected error: {e}", exc_info=True)
                raise

    async def chat_completion(
        self,
        *,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> tuple[str, Any]:
        """
        Wrapper around Together chat completions.

        Returns:
            content: 첫 번째 선택지의 메시지 콘텐츠
            raw_result: Together SDK가 반환한 원본 객체
        """
        payload: dict[str, Any] = {
            "model": self._settings.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self._settings.temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if kwargs:
            payload.update(kwargs)

        await _acquire_rate_limit()
        result = await anyio.to_thread.run_sync(lambda: self._client.chat.completions.create(**payload))

        choice = result.choices[0]
        message = getattr(choice, "message", None)
        if isinstance(choice, dict):
            message = choice.get("message")

        content = ""
        if isinstance(message, dict):
            content = message.get("content", "")
        elif message is not None:
            content = getattr(message, "content", "")

        return content, result

    async def create_embedding(
        self,
        *,
        model: str,
        input: Any,
        **kwargs: Any,
    ) -> tuple[list[float], Any]:
        """
        Wrapper around Together embedding endpoint.

        Returns:
            embedding: 첫 번째 결과의 임베딩 벡터
            raw_result: Together SDK가 반환한 원본 객체
        """
        payload: dict[str, Any] = {
            "model": model,
            "input": input,
        }
        if kwargs:
            payload.update(kwargs)

        await _acquire_rate_limit()
        result = await anyio.to_thread.run_sync(lambda: self._client.embeddings.create(**payload))

        data = getattr(result, "data", None)
        if data is None and isinstance(result, dict):
            data = result.get("data")

        embedding: list[float] = []
        if data:
            first = data[0]
            if isinstance(first, dict):
                embedding = first.get("embedding", [])
            else:
                embedding = getattr(first, "embedding", [])

        return embedding, result

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
        close_fn = getattr(self._client, "close", None)
        if callable(close_fn):
            await anyio.to_thread.run_sync(close_fn)


__all__ = ["TogetherAIHttpClient", "TogetherAISettings"]
