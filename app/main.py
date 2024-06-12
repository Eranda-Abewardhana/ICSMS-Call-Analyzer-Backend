import os

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config.config import Configurations
from app.models.action_result import ActionResult
from app.routers.filtering import filter_router
from app.routers.operators import operator_router
from app.routers.settings import settings_router
from app.routers.analytics import analytics_router
from app.routers.call import call_router

os.makedirs(Configurations.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Configurations.SAVED_FOLDER, exist_ok=True)

app = FastAPI(title="iCSMS Call Analyzer REST API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(call_router, tags=["Call Recordings"])
app.include_router(analytics_router, tags=["Call Analytics"])
app.include_router(settings_router, tags=["Call Settings"])
app.include_router(operator_router, tags=["Call Operators"])
app.include_router(filter_router, tags=["Call Filtering"])

connected_clients: list[WebSocket] = []


@app.websocket("/ws/notify")
async def analysis_result(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    action_result = ActionResult(status=True, message="Call Recording Analysis Completed")
    try:
        while True:
            await websocket.receive_text()
            for websocket in connected_clients:
                await websocket.send_json(action_result.model_dump())
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
