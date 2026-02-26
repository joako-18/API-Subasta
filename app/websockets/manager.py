import json
from collections import defaultdict
from decimal import Decimal

from fastapi import WebSocket


class ConnectionManager:
    """
    Gestiona las conexiones WebSocket agrupadas por producto_id.
    Permite broadcast en tiempo real cuando se registra una nueva puja (HU-04).
    """

    def __init__(self):
        # { producto_id: [WebSocket, ...] }
        self._rooms: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, producto_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms[producto_id].append(websocket)

    def disconnect(self, producto_id: int, websocket: WebSocket) -> None:
        room = self._rooms.get(producto_id, [])
        if websocket in room:
            room.remove(websocket)

    async def broadcast(self, producto_id: int, data: dict) -> None:
        """Envía un mensaje JSON a todos los clientes en la sala del producto."""
        dead: list[WebSocket] = []
        message = json.dumps(data, default=str)
        for ws in self._rooms.get(producto_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(producto_id, ws)


manager = ConnectionManager()
