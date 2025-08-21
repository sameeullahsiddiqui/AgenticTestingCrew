# backend/socket_manager.py

import asyncio
from typing import Set
from fastapi import WebSocket


class SocketManager:
    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def register(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)
        await self.broadcast(f"✅ New client connected. Total clients: {len(self.connections)}")

    async def unregister(self, websocket: WebSocket):
        self.connections.discard(websocket)
        await self.broadcast(f"❌ Client disconnected. Total clients: {len(self.connections)}")

    async def broadcast(self, message: str, source: str = "System"):
        if not self.connections:
            return

        payload = {
            "source": source,
            "message": message
        }

        # Send message to all connected clients
        coros = [conn.send_json(payload) for conn in self.connections]
        await asyncio.gather(*coros, return_exceptions=True)
