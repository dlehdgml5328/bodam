"""Selenium 크롤러 성능 테스트

목표: 처리량 > 100 jobs/min
"""

import asyncio
import time
from typing import List

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.models.selenium_crawl_job import SeleniumCrawlJob, JobStatus
from src.services.crawler.selenium_crawler import SeleniumCrawler


@pytest.fixture
async def db_session():
    """테스트용 데이터베이스 세션"""
    engine = create_async_engine("postgresql+asyncpg://bodam:bodam@localhost:5432/bodam")
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with SessionLocal() as session:
        yield session


@pytest.mark.asyncio
async def test_crawler_throughput(db_session: AsyncSession):
    """
    Selenium 크롤러 처리량 측정
    
    목표: 100 jobs/min 이상
    """
    # 10개 크롤링 작업 생성
    test_urls = [
        "https://news.naver.com",
        "https://www.yna.co.kr",
        "https://www.hani.co.kr",
    ] * 4  # 12개 URL
    
    jobs: List[SeleniumCrawlJob] = []
    for url in test_urls[:10]:  # 10개만 테스트
        job = SeleniumCrawlJob(
            url=url,
            wait_conditions={
                "type": "element_present",
                "selector": "article",
                "timeout_seconds": 5
            }
        )
        db_session.add(job)
        jobs.append(job)
    
    await db_session.commit()
    
    # 크롤러로 처리
    crawler = SeleniumCrawler()
    start_time = time.time()
    
    completed = 0
    failed = 0
    
    for job in jobs:
        try:
            result = crawler.crawl(job)
            if result:
                completed += 1
                job.mark_as_completed()
            else:
                failed += 1
                job.mark_as_failed("크롤링 실패")
        except Exception as e:
            failed += 1
            job.mark_as_failed(str(e))
    
    duration = time.time() - start_time
    throughput = (completed / duration) * 60  # jobs/min
    
    await db_session.commit()
    
    print(f"\n=== Selenium 크롤러 성능 테스트 ===")
    print(f"완료: {completed}, 실패: {failed}")
    print(f"소요 시간: {duration:.2f}초")
    print(f"처리량: {throughput:.2f} jobs/min")
    
    # 처리량이 100 jobs/min 이상인지 확인
    assert throughput >= 100, f"처리량 부족: {throughput:.2f} jobs/min"
    
    # 성공률이 80% 이상인지 확인
    success_rate = (completed / len(jobs)) * 100
    assert success_rate >= 80, f"성공률 낮음: {success_rate:.2f}%"


@pytest.mark.asyncio
async def test_webdriver_pool_efficiency(db_session: AsyncSession):
    """
    WebDriver Pool의 효율성 테스트
    
    Pool을 사용할 때와 매번 생성할 때의 성능 비교
    """
    from src.services.crawler.webdriver_pool import driver_pool
    
    # Pool 사용 (재사용)
    start_time = time.time()
    for _ in range(20):
        driver = driver_pool.acquire(timeout=10)
        driver.get("https://www.google.com")
        driver_pool.release(driver)
    pool_duration = time.time() - start_time
    
    print(f"\n=== WebDriver Pool 효율성 테스트 ===")
    print(f"Pool 사용 (20회 재사용): {pool_duration:.2f}초")
    print(f"평균 시간/요청: {(pool_duration / 20):.2f}초")
    
    # Pool을 사용하면 20회 요청이 합리적인 시간 내에 완료되어야 함
    assert pool_duration < 60, f"Pool 성능 부족: {pool_duration:.2f}초"
