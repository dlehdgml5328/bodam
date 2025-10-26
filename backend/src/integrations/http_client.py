"""HTTP 클라이언트 팩토리

httpx AsyncClient를 연결 풀 설정과 함께 생성합니다.
"""
from typing import Literal

import httpx

from src.config import settings


def get_client(api_type: Literal["general", "payment"] = "general") -> httpx.AsyncClient:
    """API 타입에 맞는 httpx AsyncClient 반환

    Args:
        api_type: "general" (일반 API) 또는 "payment" (결제 API)

    Returns:
        httpx.AsyncClient: 연결 풀과 타임아웃이 설정된 클라이언트

    Examples:
        >>> async with get_client("general") as client:
        ...     response = await client.get("https://api.example.com/data")

        >>> async with get_client("payment") as client:
        ...     response = await client.post("https://api.tosspayments.com/v1/payments")
    """
    # 연결 풀 설정
    limits = httpx.Limits(
        max_connections=settings.http_max_connections,
        max_keepalive_connections=settings.http_max_keepalive_connections,
        keepalive_expiry=settings.http_keepalive_expiry,
    )

    # 타임아웃 설정 (API 타입에 따라 다름)
    if api_type == "payment":
        timeout = httpx.Timeout(
            connect=settings.http_payment_connect_timeout,
            read=settings.http_payment_read_timeout,
            write=settings.http_payment_read_timeout,  # 결제 API는 read와 동일
            pool=settings.http_pool_timeout,
        )
    else:  # general
        timeout = httpx.Timeout(
            connect=settings.http_connect_timeout,
            read=settings.http_read_timeout,
            write=settings.http_write_timeout,
            pool=settings.http_pool_timeout,
        )

    # AsyncClient 생성
    return httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        http2=True,  # HTTP/2 지원
    )


__all__ = ["get_client"]
