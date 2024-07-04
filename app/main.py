import asyncio
import json
import os
from typing import List

import redis
import uvicorn
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect

from app.config.config import Configurations
from app.routers.filtering import filter_router
from app.routers.operators import operator_router
from app.routers.settings import settings_router
from app.routers.analytics import analytics_router
from app.routers.call import call_router
from app.routers.sendmail import email_router
from app.utils.auth import get_current_user
from app.routers.notification import notification_router
from app.utils.websockets import ConnectionManager

os.makedirs(Configurations.UPLOAD_FOLDER, exist_ok=True)

app = FastAPI(title="ICSMS Call Analyzer REST API", dependencies=[Depends(get_current_user)])
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

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
app.include_router(email_router, tags=["Email Notifications"])
app.include_router(notification_router, tags=["Notifications"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/notify")
async def analysis_result(websocket: WebSocket):
    await manager.connect(websocket)
    await manager.send_message("From WebSocket Server")
    print(websocket)
    try:
        while True:
            received_msg = await websocket.receive_text()
            print(received_msg)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(e)


async def redis_listener():
    pubsub = redis_client.pubsub()
    pubsub.subscribe("task_notifications")
    print("Redis channel subscribed")
    while True:
        try:
            # Get the message from redis channel
            message = pubsub.get_message(ignore_subscribe_messages=True)

            if message is not None:
                # Send the notification to all connected clients
                await manager.send_message("From Redis Server")
        except Exception as e:
            print(f"Error in redis_listener: {e}")
        await asyncio.sleep(0.01)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
