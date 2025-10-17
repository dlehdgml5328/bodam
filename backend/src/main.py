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
    rankings,
    refunds,
    stations,
    stats,
    webpush,
)
from .api.admin import (
    auth as admin_auth,
    chat as admin_chat,
    refund_actions as admin_refund_actions,
    refunds as admin_refunds,
    resources as admin_resources,
    search as admin_search,
)
from .api.webhooks import toss
from .middleware.auth import AuthMiddleware
from .config.security import get_security_settings

# SQLAdmin 관련 imports
from sqladmin import Admin
from .admin.config import AdminConfig
from .admin.auth import AdminAuthBackend
from .admin import register_admin_views
from .database.connection import engine

app = FastAPI(title="BoDam API")

# Get security settings
settings = get_security_settings()

# SQLAdmin 설정 (미들웨어 추가 전에 설정)
# 1. AdminConfig 인스턴스 생성 (secret_key 등 설정값 관리)
admin_config = AdminConfig()

# 2. Admin 인증 백엔드 생성
authentication_backend = AdminAuthBackend(secret_key=admin_config.secret_key)

# 3. SQLAdmin 인스턴스 생성 및 FastAPI 앱에 마운트
admin = Admin(
    app=app,
    engine=engine,
    title=admin_config.title,
    base_url="/admin",
    authentication_backend=authentication_backend,
)

# 4. Admin Views 등록 (모든 ModelView와 Llama Chat 페이지)
register_admin_views(admin)

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
# Rate limiting 일시적으로 비활성화 (개발 중)
# app.add_middleware(RateLimitMiddleware)

# 일반 API 라우터 등록
app.include_router(auth.router)
app.include_router(donations.router)
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

# Admin API 라우터 등록 (SQLAdmin 외부 API)
app.include_router(admin_auth.router)  # /admin/auth/* - Admin 로그인/로그아웃
app.include_router(admin_chat.router)  # /admin/api/chat/* - Llama Chat API
app.include_router(admin_refund_actions.router)  # /admin/api/refunds/* - 환불 처리 액션
app.include_router(admin_refunds.router)  # Admin 환불 조회
app.include_router(admin_resources.router)  # Admin 리소스 관리
app.include_router(admin_search.router)  # Admin 검색

# Webhooks
app.include_router(toss.router)


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
