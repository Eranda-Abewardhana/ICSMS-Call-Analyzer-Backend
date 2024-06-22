from typing import List
from fastapi import WebSocket, WebSocketDisconnect

# A list to store active WebSocket connections
active_connections: List[WebSocket] = []


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


def broadcast_message(message: str):
    for connection in active_connections:
        connection.send_text(message)
