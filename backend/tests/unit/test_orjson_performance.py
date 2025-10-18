"""orjson 성능 Unit Tests

orjson의 JSON 직렬화 성능을 표준 json 라이브러리와 비교합니다.
"""
import json
import time
from typing import Any, Dict, List

import orjson
import pytest


class TestOrjsonPerformance:
    """orjson JSON 직렬화 성능 벤치마크"""

    @pytest.fixture
    def small_dataset(self) -> Dict[str, Any]:
        """작은 데이터셋 (단일 객체)"""
        return {
            "id": 12345,
            "name": "홍길동",
            "email": "hong@example.com",
            "created_at": "2025-01-15T10:30:00Z",
            "is_active": True,
            "balance": 50000.75,
        }

    @pytest.fixture
    def large_dataset(self) -> List[Dict[str, Any]]:
        """큰 데이터셋 (1만 건의 기부 내역)"""
        return [
            {
                "id": i,
                "user_id": f"user_{i % 1000}",
                "fire_station_id": f"station_{i % 100}",
                "amount": 10000 + (i % 50000),
                "status": "completed" if i % 2 == 0 else "pending",
                "type": "one_time" if i % 3 == 0 else "subscription",
                "created_at": f"2025-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z",
                "message": f"소방관님들 응원합니다! #{i}",
                "receipt_issued": i % 4 == 0,
                "payment_method": ["card", "transfer", "kakao_pay"][i % 3],
            }
            for i in range(10000)
        ]

    def test_orjson_small_dataset_serialization(self, small_dataset: Dict[str, Any]):
        """작은 데이터셋에 대한 orjson 직렬화 성능"""
        # orjson 직렬화
        start = time.perf_counter()
        for _ in range(1000):
            orjson.dumps(small_dataset)
        orjson_duration = time.perf_counter() - start

        # 표준 json 직렬화
        start = time.perf_counter()
        for _ in range(1000):
            json.dumps(small_dataset)
        json_duration = time.perf_counter() - start

        # orjson이 더 빠르거나 비슷해야 함
        assert orjson_duration <= json_duration * 1.2  # 20% 오차 허용

    def test_orjson_large_dataset_serialization(self, large_dataset: List[Dict[str, Any]]):
        """큰 데이터셋(1만 건)에 대한 orjson 직렬화 성능"""
        # orjson 직렬화 (10회 반복)
        start = time.perf_counter()
        for _ in range(10):
            orjson.dumps(large_dataset)
        orjson_duration = time.perf_counter() - start

        # 표준 json 직렬화 (10회 반복)
        start = time.perf_counter()
        for _ in range(10):
            json.dumps(large_dataset)
        json_duration = time.perf_counter() - start

        # orjson이 더 빠르거나 비슷해야 함 (큰 데이터셋에서는 일반적으로 2-3배 빠름)
        assert (
            orjson_duration < json_duration
        ), f"orjson ({orjson_duration:.4f}s)이 표준 json ({json_duration:.4f}s)보다 느림"

        # 성능 개선 비율 출력 (디버깅용)
        speedup = json_duration / orjson_duration
        print(f"\n1만 건 데이터셋 직렬화 성능: orjson이 표준 json보다 {speedup:.2f}배 빠름")

    def test_orjson_deserialization_performance(self, large_dataset: List[Dict[str, Any]]):
        """큰 데이터셋에 대한 orjson 역직렬화 성능"""
        # JSON 문자열 생성 (표준 json 사용)
        json_str = json.dumps(large_dataset)
        orjson_bytes = orjson.dumps(large_dataset)

        # orjson 역직렬화 (10회 반복)
        start = time.perf_counter()
        for _ in range(10):
            orjson.loads(orjson_bytes)
        orjson_duration = time.perf_counter() - start

        # 표준 json 역직렬화 (10회 반복)
        start = time.perf_counter()
        for _ in range(10):
            json.loads(json_str)
        json_duration = time.perf_counter() - start

        # orjson이 더 빠르거나 비슷해야 함
        assert (
            orjson_duration < json_duration
        ), f"orjson 역직렬화 ({orjson_duration:.4f}s)가 표준 json ({json_duration:.4f}s)보다 느림"

        # 성능 개선 비율 출력 (디버깅용)
        speedup = json_duration / orjson_duration
        print(f"\n1만 건 데이터셋 역직렬화 성능: orjson이 표준 json보다 {speedup:.2f}배 빠름")

    def test_orjson_utf8_handling(self):
        """orjson의 UTF-8 한글 처리 성능"""
        korean_data = {
            "title": "소방서 기부 캠페인",
            "description": "우리 지역 소방관님들을 응원합니다! 🚒",
            "stations": [
                {"name": "서울중앙소방서", "location": "서울시 중구"},
                {"name": "강남소방서", "location": "서울시 강남구"},
                {"name": "부산중부소방서", "location": "부산시 중구"},
            ],
        }

        # orjson 직렬화 (1000회 반복)
        start = time.perf_counter()
        for _ in range(1000):
            orjson.dumps(korean_data)
        orjson_duration = time.perf_counter() - start

        # 표준 json 직렬화 (ensure_ascii=False로 UTF-8 처리)
        start = time.perf_counter()
        for _ in range(1000):
            json.dumps(korean_data, ensure_ascii=False)
        json_duration = time.perf_counter() - start

        # orjson이 더 빠르거나 비슷해야 함
        assert orjson_duration <= json_duration * 1.2  # 20% 오차 허용

    def test_orjson_output_format(self, small_dataset: Dict[str, Any]):
        """orjson이 bytes를 반환하는지 확인"""
        result = orjson.dumps(small_dataset)

        # orjson은 bytes를 반환
        assert isinstance(result, bytes)

        # UTF-8로 디코딩 가능해야 함
        decoded = result.decode("utf-8")
        assert isinstance(decoded, str)

        # 디코딩된 결과가 표준 json과 동일한지 확인 (파싱 후 비교)
        orjson_parsed = orjson.loads(result)
        json_parsed = json.loads(decoded)
        assert orjson_parsed == json_parsed

    def test_orjson_single_serialization_speed(self, large_dataset: List[Dict[str, Any]]):
        """단일 직렬화 작업의 절대 속도 측정"""
        # 1만 건 데이터를 1회 직렬화하는 시간 측정
        start = time.perf_counter()
        orjson.dumps(large_dataset)
        duration = time.perf_counter() - start

        # 1만 건 데이터를 100ms 이내에 직렬화할 수 있어야 함
        assert duration < 0.1, f"1만 건 직렬화에 {duration:.4f}초 소요 (100ms 초과)"

        print(f"\n1만 건 데이터 직렬화: {duration * 1000:.2f}ms")
