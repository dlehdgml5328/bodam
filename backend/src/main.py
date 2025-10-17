from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    auth,
    donations,
    files,
    geo,
    groups,
    health,
    incidents,
    jobs,
    kakao,
    live,
    messages,
    news,
    payments,
    rankings,
    refunds,
    stations,
    stats,
    webpush,
)
from .api.crawler import routes as crawler
from .api.admin import refunds as admin_refunds, resources as admin_resources, search as admin_search
from .api.webhooks import toss
from .middleware.auth import AuthMiddleware
from .middleware.rate_limiter import RateLimitMiddleware
from .config.security import get_security_settings
import os

app = FastAPI(title="BoDam API")

# Get security settings
settings = get_security_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add other middleware (order matters - last added runs first)
app.add_middleware(AuthMiddleware)

# Rate limiting (활성화 여부는 환경변수로 제어)
rate_limiting_enabled = os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true"
if rate_limiting_enabled:
    redis_url = os.getenv("REDIS_CACHE_URL", "redis://localhost:6379/0")
    print(f"✅ Rate Limiting ENABLED: {redis_url}")
    app.add_middleware(RateLimitMiddleware, redis_url=redis_url)
else:
    print("⚠️  Rate Limiting DISABLED")

app.include_router(auth.router)
app.include_router(donations.router)
app.include_router(payments.router)
app.include_router(stations.router)
app.include_router(stats.router)
app.include_router(rankings.router)
app.include_router(news.router)
app.include_router(messages.router)
app.include_router(incidents.router)
app.include_router(files.router)
app.include_router(geo.router)
app.include_router(groups.router)
app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(kakao.router)
app.include_router(live.router)
app.include_router(refunds.router)
app.include_router(webpush.router)
app.include_router(admin_refunds.router)
app.include_router(admin_resources.router)
app.include_router(admin_search.router)
app.include_router(toss.router)
app.include_router(crawler.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "BoDam API"}


@app.websocket("/ws/notifications")
async def notifications_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            _message = await websocket.receive_json()
            await websocket.send_json(
                {
                    "type": "notification",
                    "payload": {"message": "알림 대기 중"},
                }
            )
    except WebSocketDisconnect:
        return
