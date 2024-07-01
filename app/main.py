import asyncio
import json
import os

import redis
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect

from app.config.config import Configurations
from app.routers.filtering import filter_router
from app.routers.operators import operator_router
from app.routers.settings import settings_router
from app.routers.analytics import analytics_router
from app.routers.call import call_router
from app.routers.sendmail import email_router
from app.utils.websockets import ConnectionManager

os.makedirs(Configurations.UPLOAD_FOLDER, exist_ok=True)

app = FastAPI(title="ICSMS Call Analyzer REST API")
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

manager = ConnectionManager()


@app.websocket("/ws/notify")
async def analysis_result(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
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
                await manager.send_message(message['data'])
        except Exception as e:
            print(f"Error in redis_listener: {e}")
        await asyncio.sleep(0.01)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
