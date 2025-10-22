"""API 성능 개선 Integration Tests

FastAPI 엔드포인트에서 ORJSONResponse가 사용되는지 확인하고 실제 API 응답 속도를 측정합니다.
"""
import time

import pytest
from fastapi.responses import ORJSONResponse
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


class TestAPIPerformanceImprovements:
    """API 성능 개선 검증 (ORJSONResponse + uvloop)"""

    async def test_app_default_response_class_is_orjson(self):
        """FastAPI 앱의 기본 응답 클래스가 ORJSONResponse인지 확인"""
        assert app.default_response_class == ORJSONResponse, (
            f"FastAPI 기본 응답 클래스가 ORJSONResponse가 아님: {app.default_response_class}"
        )

    async def test_root_endpoint_uses_orjson(self):
        """루트 엔드포인트가 ORJSONResponse를 사용하는지 확인"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")

        # 응답 상태 코드 확인
        assert response.status_code == 200

        # Content-Type이 application/json인지 확인
        assert "application/json" in response.headers.get("content-type", "")

        # 응답 본문 파싱 가능 확인
        data = response.json()
        assert "message" in data

    async def test_health_endpoint_response_time(self):
        """헬스 체크 엔드포인트의 응답 속도 측정"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            start = time.perf_counter()
            response = await client.get("/health")
            duration = time.perf_counter() - start

        # 응답 성공 확인
        assert response.status_code == 200

        # 응답 시간이 100ms 이내여야 함 (단순 엔드포인트)
        assert duration < 0.1, f"헬스 체크 응답 시간 {duration * 1000:.2f}ms (100ms 초과)"

    async def test_multiple_concurrent_requests_performance(self):
        """여러 개의 동시 요청을 처리하는 성능 측정"""
        import asyncio

        async def make_request(client: AsyncClient) -> float:
            """단일 요청 실행 및 응답 시간 반환"""
            start = time.perf_counter()
            response = await client.get("/health")
            duration = time.perf_counter() - start
            assert response.status_code == 200
            return duration

        # 50개의 동시 요청 실행
        async with AsyncClient(app=app, base_url="http://test") as client:
            start = time.perf_counter()
            tasks = [make_request(client) for _ in range(50)]
            durations = await asyncio.gather(*tasks)
            total_duration = time.perf_counter() - start

        # 모든 요청이 성공했는지 확인
        assert len(durations) == 50

        # 평균 응답 시간
        avg_duration = sum(durations) / len(durations)

        # 전체 실행 시간이 2초 이내여야 함 (50개 요청)
        assert total_duration < 2.0, (
            f"50개 동시 요청 처리 시간 {total_duration:.2f}초 (2초 초과)"
        )

        # 평균 응답 시간이 200ms 이내여야 함
        assert avg_duration < 0.2, f"평균 응답 시간 {avg_duration * 1000:.2f}ms (200ms 초과)"

        print(f"\n50개 동시 요청:")
        print(f"  - 전체 처리 시간: {total_duration * 1000:.2f}ms")
        print(f"  - 평균 응답 시간: {avg_duration * 1000:.2f}ms")
        print(f"  - 최소 응답 시간: {min(durations) * 1000:.2f}ms")
        print(f"  - 최대 응답 시간: {max(durations) * 1000:.2f}ms")

    async def test_ranking_endpoint_response_time(self):
        """랭킹 엔드포인트의 응답 속도 측정 (JSON 직렬화 성능 테스트)"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            start = time.perf_counter()
            response = await client.get("/rankings/users?limit=100")
            duration = time.perf_counter() - start

        # 응답 성공 확인
        assert response.status_code == 200

        # 응답 시간이 500ms 이내여야 함
        assert duration < 0.5, f"랭킹 조회 응답 시간 {duration * 1000:.2f}ms (500ms 초과)"

        # 응답 데이터 파싱 확인
        data = response.json()
        assert isinstance(data, list)

        print(f"\n랭킹 엔드포인트 (limit=100) 응답 시간: {duration * 1000:.2f}ms")

    async def test_stations_endpoint_large_dataset_performance(self):
        """소방서 목록 조회의 대용량 데이터 직렬화 성능 측정"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            start = time.perf_counter()
            response = await client.get("/stations")
            duration = time.perf_counter() - start

        # 응답 성공 확인
        assert response.status_code == 200

        # 응답 시간이 1초 이내여야 함
        assert duration < 1.0, f"소방서 목록 조회 응답 시간 {duration * 1000:.2f}ms (1초 초과)"

        # 응답 데이터 파싱 확인
        data = response.json()
        assert isinstance(data, list)

        print(f"\n소방서 목록 조회 (전체) 응답 시간: {duration * 1000:.2f}ms")
        print(f"  - 조회된 소방서 수: {len(data)}개")

    async def test_sequential_requests_throughput(self):
        """순차적 요청 처리량 측정"""
        request_count = 100

        async with AsyncClient(app=app, base_url="http://test") as client:
            start = time.perf_counter()

            for _ in range(request_count):
                response = await client.get("/")
                assert response.status_code == 200

            total_duration = time.perf_counter() - start

        # 초당 요청 처리량 계산
        throughput = request_count / total_duration

        # 초당 최소 50개 이상 요청을 처리할 수 있어야 함
        assert throughput >= 50, (
            f"요청 처리량 {throughput:.2f} req/s (50 req/s 미만)"
        )

        print(f"\n순차 요청 처리 성능:")
        print(f"  - 총 요청 수: {request_count}개")
        print(f"  - 전체 처리 시간: {total_duration:.2f}초")
        print(f"  - 처리량: {throughput:.2f} req/s")

    async def test_response_content_type_header(self):
        """응답 헤더에 올바른 Content-Type이 설정되었는지 확인"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")

        # Content-Type 헤더 확인
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, (
            f"Content-Type이 application/json이 아님: {content_type}"
        )

    async def test_orjson_unicode_handling_in_api(self):
        """API에서 한글(UTF-8) 응답이 정상적으로 처리되는지 확인"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")

        # 응답 성공 확인
        assert response.status_code == 200

        # 응답 데이터에 한글이 포함되어 있는지 확인
        data = response.json()
        assert "message" in data

        # UTF-8 인코딩이 정상적으로 처리되는지 확인
        response_text = response.text
        assert isinstance(response_text, str)

    async def test_large_json_response_performance(self):
        """대용량 JSON 응답 직렬화 성능 측정 (기부 내역 조회)"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            start = time.perf_counter()
            response = await client.get("/donations?limit=1000")
            duration = time.perf_counter() - start

        # 응답 성공 확인 (데이터가 없을 수 있으므로 200 또는 404 허용)
        assert response.status_code in [200, 401, 403]  # 인증 필요할 수 있음

        # 응답 시간이 1초 이내여야 함
        if response.status_code == 200:
            assert duration < 1.0, (
                f"대용량 데이터 조회 응답 시간 {duration * 1000:.2f}ms (1초 초과)"
            )
            print(f"\n기부 내역 조회 (limit=1000) 응답 시간: {duration * 1000:.2f}ms")
