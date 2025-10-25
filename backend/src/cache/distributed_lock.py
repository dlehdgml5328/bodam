"""분산 락(Distributed Lock) - Redis 기반 동시성 제어

Redis의 SET NX (SET if Not eXists) 명령을 사용하여
여러 서버/프로세스 간 동시 실행을 방지합니다.

사용 예시:
    async with acquire_lock("donation:user123:station456", timeout=5):
        # 중복 실행 방지가 필요한 코드
        await create_donation(...)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .clients import get_cache_client

logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """분산 락 획득 실패 예외"""
    pass


@asynccontextmanager
async def acquire_lock(
    key: str,
    timeout: int = 5,
    retry: bool = False,
) -> AsyncGenerator[bool, None]:
    """
    Redis 분산 락 획득 (Context Manager)

    Args:
        key: 락 키 (예: "donation:user123:station456")
        timeout: 락 유효 시간 (초) - 이 시간 후 자동 해제
        retry: True면 Lock 획득 실패 시 예외 대신 False 반환

    Raises:
        LockAcquisitionError: 락 획득 실패 (retry=False일 때)

    Usage:
        async with acquire_lock("my_key", timeout=5):
            # Critical section
            await do_something()
    """
    redis = await get_cache_client()
    lock_acquired = False

    try:
        # Redis SET NX EX: key가 없으면 설정하고 True, 이미 있으면 False
        lock_acquired = await redis.set(
            f"lock:{key}",
            "1",
            ex=timeout,  # 만료 시간 (초)
            nx=True,     # Not eXists - key가 없을 때만 설정
        )

        if not lock_acquired:
            if retry:
                logger.warning(f"Lock acquisition failed (already locked): {key}")
                yield False
                return
            else:
                raise LockAcquisitionError(f"Failed to acquire lock: {key}")

        logger.debug(f"Lock acquired: {key} (timeout={timeout}s)")
        yield True

    finally:
        # 락 해제
        if lock_acquired:
            await redis.delete(f"lock:{key}")
            logger.debug(f"Lock released: {key}")


async def try_acquire_lock(key: str, timeout: int = 5) -> bool:
    """
    락 획득 시도 (non-blocking)

    Args:
        key: 락 키
        timeout: 락 유효 시간 (초)

    Returns:
        True: 락 획득 성공
        False: 락 획득 실패 (이미 다른 프로세스가 사용 중)
    """
    redis = await get_cache_client()
    lock_acquired = await redis.set(
        f"lock:{key}",
        "1",
        ex=timeout,
        nx=True,
    )
    return bool(lock_acquired)


__all__ = ["acquire_lock", "try_acquire_lock", "LockAcquisitionError"]
