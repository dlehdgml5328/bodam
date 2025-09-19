from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .api import auth, donations, files, geo, groups, health, jobs, kakao, live, refunds, stations, webpush
from .api.admin import refunds as admin_refunds, resources as admin_resources, search as admin_search
from .api.webhooks import toss

app = FastAPI(title="BoDam API")

app.include_router(auth.router)
app.include_router(donations.router)
app.include_router(stations.router)
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
