from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        # 存放所有活跃的连接
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """向所有连接的客户端发送 JSON 数据"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # 如果发送失败（比如客户端断网），暂时忽略，后续可做清理
                pass