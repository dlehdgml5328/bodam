"""재시도 정책

tenacity를 사용하여 HTTP 요청 재시도 로직을 구현합니다.
"""
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from src.config import settings

# 재시도 가능한 예외 타입
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.NetworkError,
)


def is_excluded_domain(url: str) -> bool:
    """재시도 제외 도메인인지 확인

    Args:
        url: 요청 URL

    Returns:
        bool: 재시도 제외 도메인이면 True
    """
    excluded = settings.retry_excluded_domains.split(",")
    return any(domain.strip() in url for domain in excluded)


async def fetch_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs: Any,
) -> httpx.Response:
    """재시도 정책이 적용된 HTTP 요청

    Args:
        client: httpx.AsyncClient 인스턴스
        method: HTTP 메서드 (GET, POST, PUT, DELETE 등)
        url: 요청 URL
        **kwargs: httpx.request()에 전달할 추가 인자

    Returns:
        httpx.Response: HTTP 응답

    Raises:
        httpx.ConnectTimeout: 재시도 후에도 연결 실패
        httpx.ReadTimeout: 재시도 후에도 읽기 실패
        httpx.NetworkError: 재시도 후에도 네트워크 오류
        httpx.HTTPStatusError: HTTP 4xx/5xx 에러 (재시도 안 함)

    Examples:
        >>> async with get_client("general") as client:
        ...     response = await fetch_with_retry(client, "GET", "https://api.example.com/data")
    """
    # 재시도 제외 도메인 확인
    if is_excluded_domain(url):
        # 재시도 없이 바로 요청
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    # 멱등성 체크 (POST는 idempotency-key 필요)
    if method.upper() == "POST":
        headers = kwargs.get("headers", {})
        if "idempotency-key" not in {k.lower() for k in headers.keys()}:
            # 멱등성 키 없으면 재시도 안 함
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response

    # 재시도 정책 적용
    @retry(
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_fixed(settings.retry_interval),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
    )
    async def _request_with_retry():
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    return await _request_with_retry()


__all__ = ["fetch_with_retry", "is_excluded_domain"]
