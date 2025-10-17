"""
Llama AI 채팅 서비스 - Knowledge Graph & Semantic Cache 통합

Together AI Llama 3.3을 사용하여 자연어로 데이터베이스를 쿼리하고
대화형으로 분석 결과를 제공하는 서비스
"""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import numpy as np
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.clients import get_cache_client, get_semantic_client
from src.database.connection import get_session
from src.integrations.graph import GraphClient
from src.integrations.together_ai import TogetherAIHttpClient
from src.monitoring.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ChatResponse:
    """채팅 응답 데이터"""
    response: str
    sources: List[Dict[str, Any]]
    execution_time_ms: float
    cached: bool
    sql_query: Optional[str] = None
    query_type: Optional[str] = None


@dataclass
class ChatContext:
    """대화 컨텍스트"""
    messages: List[Dict[str, str]]
    session_id: str
    created_at: datetime
    updated_at: datetime


class LlamaChatService:
    """
    Llama AI 채팅 서비스

    주요 기능:
    - 자연어 → SQL 변환 (SELECT만 허용)
    - Knowledge Graph 쿼리 실행
    - Semantic Cache 통합 (코사인 유사도 > 0.95)
    - 대화 컨텍스트 관리 (최대 20개 메시지)
    """

    # SQL Injection 방지를 위한 위험 키워드
    DANGEROUS_SQL_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
        "TRUNCATE", "REPLACE", "EXEC", "EXECUTE", "--", "/*", "*/",
        ";--", "xp_", "sp_"
    ]

    # 쿼리 타입
    QUERY_TYPE_STATS = "statistics"
    QUERY_TYPE_SEARCH = "search"
    QUERY_TYPE_ANALYSIS = "analysis"

    def __init__(
        self,
        together_ai_client: Optional[TogetherAIHttpClient] = None,
        graph_client: Optional[GraphClient] = None,
        cache_client: Optional[redis.Redis] = None,
        semantic_client: Optional[redis.Redis] = None,
        embedding_model: str = "togethercomputer/m2-bert-80M-8k-retrieval",
    ):
        self.together_ai = together_ai_client or TogetherAIHttpClient()
        self.graph_client = graph_client or GraphClient()
        self.cache_client = cache_client
        self.semantic_client = semantic_client
        self.embedding_model = embedding_model

        # 대화 컨텍스트 설정
        self.max_context_messages = 20
        self.context_ttl_seconds = 1800  # 30분

        # Semantic cache 설정
        self.cache_similarity_threshold = 0.95
        self.cache_ttl_seconds = 300  # 5분

    async def _init_clients(self):
        """Redis 클라이언트 초기화"""
        if self.cache_client is None:
            self.cache_client = await get_cache_client()
        if self.semantic_client is None:
            self.semantic_client = await get_semantic_client()
        if self.graph_client._pool is None:
            await self.graph_client.connect()

    async def query(
        self,
        user_query: str,
        session_id: str,
        max_results: int = 10,
        explain: bool = False
    ) -> ChatResponse:
        """
        사용자 쿼리 처리

        Args:
            user_query: 사용자의 자연어 질문
            session_id: 세션 ID
            max_results: 최대 결과 개수
            explain: SQL 쿼리 노출 여부

        Returns:
            ChatResponse: 채팅 응답
        """
        start_time = time.time()
        await self._init_clients()

        logger.info(f"[LlamaChat] Query received: session={session_id}, query={user_query[:50]}...")

        # 1. Semantic cache 확인
        cached_response = await self._check_semantic_cache(user_query)
        if cached_response:
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"[LlamaChat] Cache hit! Time: {execution_time:.2f}ms")
            return ChatResponse(
                response=cached_response["response"],
                sources=cached_response["sources"],
                execution_time_ms=execution_time,
                cached=True,
                sql_query=cached_response.get("sql_query") if explain else None,
                query_type=cached_response.get("query_type")
            )

        # 2. 대화 컨텍스트 로드
        context = await self._load_context(session_id)

        # 3. 쿼리 분류 및 SQL 생성
        query_type = await self._classify_query(user_query, context)
        sql_query = await self._generate_sql(user_query, query_type, context)

        # 4. SQL 안전성 검증
        if not self._is_safe_sql(sql_query):
            logger.warning(f"[LlamaChat] Unsafe SQL detected: {sql_query}")
            return ChatResponse(
                response="죄송합니다. 해당 질문은 보안상 처리할 수 없습니다.",
                sources=[],
                execution_time_ms=(time.time() - start_time) * 1000,
                cached=False
            )

        # 5. Knowledge Graph 쿼리 실행
        try:
            results = await self._execute_query(sql_query, max_results)
        except Exception as e:
            logger.error(f"[LlamaChat] Query execution failed: {e}", exc_info=True)
            return ChatResponse(
                response=f"죄송합니다. 쿼리 실행 중 오류가 발생했습니다: {str(e)}",
                sources=[],
                execution_time_ms=(time.time() - start_time) * 1000,
                cached=False
            )

        # 6. 결과를 자연어로 변환
        natural_response = await self._format_response(
            user_query=user_query,
            query_type=query_type,
            results=results,
            context=context
        )

        # 7. Semantic cache 저장
        await self._save_semantic_cache(
            query=user_query,
            response=natural_response,
            sources=results,
            sql_query=sql_query,
            query_type=query_type
        )

        # 8. 대화 컨텍스트 업데이트
        await self._update_context(session_id, user_query, natural_response, context)

        execution_time = (time.time() - start_time) * 1000
        logger.info(f"[LlamaChat] Query completed: time={execution_time:.2f}ms, results={len(results)}")

        return ChatResponse(
            response=natural_response,
            sources=results,
            execution_time_ms=execution_time,
            cached=False,
            sql_query=sql_query if explain else None,
            query_type=query_type
        )

    async def _check_semantic_cache(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Semantic cache 확인 (코사인 유사도 > 0.95)

        Args:
            query: 사용자 쿼리

        Returns:
            캐시된 응답 또는 None
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = await self._generate_embedding(query)

            # Redis에서 유사한 쿼리 검색
            pattern = "semantic:chat:*"
            async for key in self.semantic_client.scan_iter(match=pattern):
                cached_data = await self.semantic_client.get(key)
                if not cached_data:
                    continue

                cached = json.loads(cached_data)
                cached_embedding = np.array(cached["embedding"])

                # 코사인 유사도 계산
                similarity = self._cosine_similarity(query_embedding, cached_embedding)

                if similarity >= self.cache_similarity_threshold:
                    logger.info(f"[LlamaChat] Semantic cache hit! similarity={similarity:.4f}")
                    return {
                        "response": cached["response"],
                        "sources": cached["sources"],
                        "sql_query": cached.get("sql_query"),
                        "query_type": cached.get("query_type")
                    }

            return None

        except Exception as e:
            logger.error(f"[LlamaChat] Semantic cache check failed: {e}", exc_info=True)
            return None

    async def _save_semantic_cache(
        self,
        query: str,
        response: str,
        sources: List[Dict],
        sql_query: str,
        query_type: str
    ):
        """
        Semantic cache 저장

        Args:
            query: 사용자 쿼리
            response: 응답
            sources: 데이터 소스
            sql_query: SQL 쿼리
            query_type: 쿼리 타입
        """
        try:
            embedding = await self._generate_embedding(query)

            cache_key = f"semantic:chat:{uuid.uuid4()}"
            cache_data = json.dumps({
                "query": query,
                "response": response,
                "sources": sources,
                "sql_query": sql_query,
                "query_type": query_type,
                "embedding": embedding.tolist(),
                "cached_at": datetime.utcnow().isoformat()
            })

            await self.semantic_client.setex(
                cache_key,
                self.cache_ttl_seconds,
                cache_data
            )

            logger.debug(f"[LlamaChat] Semantic cache saved: key={cache_key}")

        except Exception as e:
            logger.error(f"[LlamaChat] Semantic cache save failed: {e}", exc_info=True)

    async def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Together AI 임베딩 생성 (768차원)

        Args:
            text: 텍스트

        Returns:
            임베딩 벡터
        """
        try:
            response = await self.together_ai._client.post(
                "/v1/embeddings",
                json={
                    "model": self.embedding_model,
                    "input": text
                }
            )
            response.raise_for_status()
            result = response.json()

            embedding = result["data"][0]["embedding"]
            return np.array(embedding)

        except Exception as e:
            logger.error(f"[LlamaChat] Embedding generation failed: {e}", exc_info=True)
            # Fallback: 랜덤 임베딩 (개발용)
            return np.random.rand(768)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        코사인 유사도 계산

        Args:
            a: 벡터 A
            b: 벡터 B

        Returns:
            코사인 유사도 (0~1)
        """
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    async def _load_context(self, session_id: str) -> ChatContext:
        """
        대화 컨텍스트 로드

        Args:
            session_id: 세션 ID

        Returns:
            대화 컨텍스트
        """
        try:
            key = f"chat:context:{session_id}"
            data = await self.cache_client.get(key)

            if data:
                context_data = json.loads(data)
                return ChatContext(
                    messages=context_data["messages"],
                    session_id=session_id,
                    created_at=datetime.fromisoformat(context_data["created_at"]),
                    updated_at=datetime.fromisoformat(context_data["updated_at"])
                )

            # 새 컨텍스트 생성
            return ChatContext(
                messages=[],
                session_id=session_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"[LlamaChat] Context load failed: {e}", exc_info=True)
            return ChatContext(
                messages=[],
                session_id=session_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

    async def _update_context(
        self,
        session_id: str,
        user_query: str,
        assistant_response: str,
        context: ChatContext
    ):
        """
        대화 컨텍스트 업데이트

        Args:
            session_id: 세션 ID
            user_query: 사용자 쿼리
            assistant_response: 어시스턴트 응답
            context: 기존 컨텍스트
        """
        try:
            # 새 메시지 추가
            context.messages.append({
                "role": "user",
                "content": user_query,
                "timestamp": datetime.utcnow().isoformat()
            })
            context.messages.append({
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.utcnow().isoformat()
            })

            # 최대 메시지 개수 제한 (최신 20개만 유지)
            if len(context.messages) > self.max_context_messages:
                context.messages = context.messages[-self.max_context_messages:]

            context.updated_at = datetime.utcnow()

            # Redis에 저장
            key = f"chat:context:{session_id}"
            data = json.dumps({
                "messages": context.messages,
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat()
            })

            await self.cache_client.setex(
                key,
                self.context_ttl_seconds,
                data
            )

            logger.debug(f"[LlamaChat] Context updated: session={session_id}, messages={len(context.messages)}")

        except Exception as e:
            logger.error(f"[LlamaChat] Context update failed: {e}", exc_info=True)

    async def _classify_query(self, query: str, context: ChatContext) -> str:
        """
        쿼리 분류 (통계/검색/분석)

        Args:
            query: 사용자 쿼리
            context: 대화 컨텍스트

        Returns:
            쿼리 타입 (statistics/search/analysis)
        """
        try:
            # 컨텍스트 메시지 포함 (최근 4개)
            context_messages = context.messages[-4:] if context.messages else []

            prompt = f"""
다음 사용자 질문을 분류하세요.

**질문**: {query}

**최근 대화**:
{json.dumps(context_messages, ensure_ascii=False, indent=2)}

**분류 기준**:
1. **statistics** (통계): 개수, 합계, 평균, 최댓값, 최솟값 등 집계 정보
2. **search** (검색): 특정 조건의 레코드 찾기 (예: 특정 지역의 소방서)
3. **analysis** (분석): 관계 탐색, 트렌드 분석, 복잡한 패턴 발견

**출력**: JSON 형식으로만 답변하세요.
```json
{{"type": "statistics|search|analysis", "reason": "분류 이유"}}
```
"""

            response = await self.together_ai._client.post(
                "/v1/chat/completions",
                json={
                    "model": self.together_ai._settings.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "당신은 자연어 쿼리를 분류하는 전문가입니다. JSON 형식으로만 답변하세요."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200
                }
            )

            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # JSON 추출
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            classification = json.loads(content)
            query_type = classification.get("type", self.QUERY_TYPE_SEARCH)

            logger.info(f"[LlamaChat] Query classified: type={query_type}")
            return query_type

        except Exception as e:
            logger.error(f"[LlamaChat] Query classification failed: {e}", exc_info=True)
            return self.QUERY_TYPE_SEARCH

    async def _generate_sql(
        self,
        query: str,
        query_type: str,
        context: ChatContext
    ) -> str:
        """
        자연어 → SQL 변환

        Args:
            query: 사용자 쿼리
            query_type: 쿼리 타입
            context: 대화 컨텍스트

        Returns:
            SQL 쿼리 (SELECT만)
        """
        try:
            schema_info = """
**데이터베이스 스키마**:

1. **fire_stations** (소방서)
   - id (UUID)
   - name (소방서명)
   - address (주소)
   - region (시/도)
   - district (시/군/구)
   - status (active/closed/merged)
   - total_received (총 후원금액)
   - donor_count (후원자 수)
   - last_incident_at (마지막 화재 일시)

2. **fire_incidents** (화재 사고)
   - id (String, 예: F2025001)
   - title (사고명)
   - location_address (발생 위치)
   - occurred_at (발생 일시)
   - status (dispatching/suppressing/contained/resolved)
   - severity (critical/high/medium/low)
   - casualties_injured (부상자 수)
   - casualties_dead (사망자 수)
   - estimated_damage (예상 피해액)

3. **donations** (후원)
   - id (UUID)
   - user_id (후원자 ID)
   - fire_station_id (소방서 ID)
   - amount (후원 금액)
   - type (one_time/recurring)
   - status (pending/completed/failed/refunded)
   - created_at (후원 일시)
   - completed_at (완료 일시)
"""

            # 컨텍스트 메시지 포함
            context_messages = context.messages[-4:] if context.messages else []

            prompt = f"""
다음 자연어 질문을 PostgreSQL SELECT 쿼리로 변환하세요.

**질문**: {query}
**쿼리 타입**: {query_type}

**최근 대화**:
{json.dumps(context_messages, ensure_ascii=False, indent=2)}

{schema_info}

**중요 규칙**:
1. SELECT 문만 사용 (INSERT, UPDATE, DELETE, DROP 등 금지)
2. 보안을 위해 파라미터화된 쿼리 사용
3. JOIN은 필요한 경우만 사용
4. LIMIT는 기본 10, 최대 100
5. WHERE 조건은 명확하게 작성
6. 날짜 비교는 timestamp with time zone 타입 고려
7. 금액은 Numeric(12, 2) 타입

**출력**: SQL 쿼리만 출력하세요 (설명 없이).
"""

            response = await self.together_ai._client.post(
                "/v1/chat/completions",
                json={
                    "model": self.together_ai._settings.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "당신은 PostgreSQL 전문가입니다. 자연어를 안전한 SELECT 쿼리로만 변환하세요."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500
                }
            )

            response.raise_for_status()
            result = response.json()
            sql = result["choices"][0]["message"]["content"].strip()

            # 코드 블록 제거
            if "```sql" in sql:
                sql = sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql:
                sql = sql.split("```")[1].split("```")[0].strip()

            # 세미콜론 제거
            sql = sql.rstrip(";")

            logger.info(f"[LlamaChat] SQL generated: {sql[:100]}...")
            return sql

        except Exception as e:
            logger.error(f"[LlamaChat] SQL generation failed: {e}", exc_info=True)
            raise

    def _is_safe_sql(self, sql: str) -> bool:
        """
        SQL Injection 방지 검증

        Args:
            sql: SQL 쿼리

        Returns:
            안전 여부
        """
        # 대소문자 구분 없이 검사
        sql_upper = sql.upper()

        # SELECT로 시작하는지 확인
        if not sql_upper.strip().startswith("SELECT"):
            logger.warning(f"[LlamaChat] SQL must start with SELECT: {sql[:50]}")
            return False

        # 위험 키워드 검사
        for keyword in self.DANGEROUS_SQL_KEYWORDS:
            if keyword in sql_upper:
                logger.warning(f"[LlamaChat] Dangerous keyword found: {keyword}")
                return False

        return True

    async def _execute_query(self, sql: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Knowledge Graph 쿼리 실행

        Args:
            sql: SQL 쿼리
            max_results: 최대 결과 개수

        Returns:
            쿼리 결과
        """
        try:
            # LIMIT 추가
            if "LIMIT" not in sql.upper():
                sql = f"{sql} LIMIT {max_results}"

            # GraphClient 사용하여 쿼리 실행
            records = await self.graph_client.query(sql)

            # asyncpg.Record → dict 변환
            results = []
            for record in records:
                row = {}
                for key in record.keys():
                    value = record[key]
                    # datetime, UUID 등 JSON 직렬화 가능하게 변환
                    if isinstance(value, datetime):
                        row[key] = value.isoformat()
                    elif isinstance(value, uuid.UUID):
                        row[key] = str(value)
                    else:
                        row[key] = value
                results.append(row)

            logger.info(f"[LlamaChat] Query executed: rows={len(results)}")
            return results

        except Exception as e:
            logger.error(f"[LlamaChat] Query execution failed: {e}", exc_info=True)
            raise

    async def _format_response(
        self,
        user_query: str,
        query_type: str,
        results: List[Dict[str, Any]],
        context: ChatContext
    ) -> str:
        """
        쿼리 결과를 자연어로 변환

        Args:
            user_query: 사용자 쿼리
            query_type: 쿼리 타입
            results: 쿼리 결과
            context: 대화 컨텍스트

        Returns:
            자연어 응답
        """
        try:
            if not results:
                return "죄송합니다. 해당 조건에 맞는 데이터를 찾을 수 없습니다."

            # 컨텍스트 메시지 포함
            context_messages = context.messages[-2:] if context.messages else []

            prompt = f"""
다음 데이터베이스 쿼리 결과를 자연스러운 한국어로 설명하세요.

**사용자 질문**: {user_query}
**쿼리 타입**: {query_type}

**최근 대화**:
{json.dumps(context_messages, ensure_ascii=False, indent=2)}

**쿼리 결과** (총 {len(results)}건):
{json.dumps(results[:10], ensure_ascii=False, indent=2)}

**작성 가이드**:
1. 핵심 정보를 먼저 설명
2. 구체적인 숫자와 단위 포함 (예: 5개, 10,000원)
3. 필요시 표 형식으로 요약
4. 친근하고 전문적인 톤
5. 2-3 문단으로 정리

**출력**: 자연어 설명만 작성하세요 (JSON이나 코드 블록 없이).
"""

            response = await self.together_ai._client.post(
                "/v1/chat/completions",
                json={
                    "model": self.together_ai._settings.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "당신은 데이터 분석 전문가입니다. 쿼리 결과를 쉽고 명확하게 설명하세요."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            )

            response.raise_for_status()
            result = response.json()
            natural_response = result["choices"][0]["message"]["content"].strip()

            logger.debug(f"[LlamaChat] Response formatted: {len(natural_response)} chars")
            return natural_response

        except Exception as e:
            logger.error(f"[LlamaChat] Response formatting failed: {e}", exc_info=True)
            # Fallback: 간단한 응답
            return f"조회 결과 {len(results)}건을 찾았습니다."

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        대화 기록 조회

        Args:
            session_id: 세션 ID

        Returns:
            대화 메시지 목록
        """
        await self._init_clients()
        context = await self._load_context(session_id)
        return context.messages

    async def clear_history(self, session_id: str):
        """
        대화 기록 초기화

        Args:
            session_id: 세션 ID
        """
        await self._init_clients()
        key = f"chat:context:{session_id}"
        await self.cache_client.delete(key)
        logger.info(f"[LlamaChat] History cleared: session={session_id}")

    async def create_session(self) -> str:
        """
        새 세션 생성

        Returns:
            세션 ID
        """
        session_id = str(uuid.uuid4())
        logger.info(f"[LlamaChat] Session created: {session_id}")
        return session_id

    async def delete_session(self, session_id: str):
        """
        세션 삭제

        Args:
            session_id: 세션 ID
        """
        await self._init_clients()
        key = f"chat:context:{session_id}"
        await self.cache_client.delete(key)
        logger.info(f"[LlamaChat] Session deleted: {session_id}")

    async def close(self):
        """리소스 정리"""
        if self.together_ai:
            await self.together_ai.close()
        if self.graph_client:
            await self.graph_client.close()


__all__ = ["LlamaChatService", "ChatResponse", "ChatContext"]
