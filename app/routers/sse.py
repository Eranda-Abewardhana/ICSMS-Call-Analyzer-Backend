import asyncio
import json
import os

from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse

from app.config.config import Configurations

sse_router = APIRouter()
pendingCalls = []


async def event_generator():
    while True:
        await asyncio.sleep(10)  # Check every 10 seconds
        pendingCalls.clear()
        for filename in os.listdir(Configurations.UPLOAD_FOLDER):
            pendingCalls.append(filename.split("_")[-1].split(".")[0])
        if not pendingCalls:
            yield f"data: []\n\n"
        else:
            yield f"data: {json.dumps(pendingCalls)}\n\n"


@sse_router.get("/sse-pending-calls")
async def sse(request: Request):
    async def event_publisher():
        async for event in event_generator():
            yield event
            if await request.is_disconnected():
                break

    return StreamingResponse(event_publisher(), media_type="text/event-stream")
