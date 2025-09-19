import pytest
from httpx import AsyncClient

from src.main import app

pytestmark = pytest.mark.asyncio


async def test_ai_news_analysis_queues_job_and_returns_result() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        enqueue_payload = {
            "source": "naver_news",
            "items": [
                {
                    "title": "서울 소방서, 화재 진압 성공",
                    "url": "https://news.example.com/fire",
                    "content": "서울 강남구에서 화재 발생",
                }
            ],
        }
        enqueue_response = await client.post("/ai/news/analyze", json=enqueue_payload)
        assert enqueue_response.status_code == 202
        job_id = enqueue_response.json()["job_id"]

        result_response = await client.get(f"/ai/news/analyze/{job_id}")
        assert result_response.status_code == 200
        result_body = result_response.json()
        assert result_body.get("status") in {"pending", "completed"}
        assert "items" in result_body
