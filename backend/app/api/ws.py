"""
WebSocket route for live ambulance status updates.
"""
import asyncio
import json
import random
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])

# Connection manager for broadcast
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def send_json(self, ws: WebSocket, data: dict):
        try:
            await ws.send_json(data)
        except Exception:
            self.disconnect(ws)


manager = ConnectionManager()

AMBULANCE_STATUSES = [
    "Ambulance dispatched",
    "En route to scene",
    "Arrival in 8 minutes",
    "Arrival in 5 minutes",
    "Arrival in 2 minutes",
    "Arrived at scene",
]


@router.websocket("/ws/live/{incident_id}")
async def live_updates(websocket: WebSocket, incident_id: str):
    """Stream live ambulance status updates for a given incident."""
    await manager.connect(websocket)
    step = 0
    try:
        # Send initial status
        await manager.send_json(websocket, {
            "event": "connected",
            "incident_id": incident_id,
            "message": "Connected to RapidCare live updates",
        })

        while True:
            await asyncio.sleep(5)  # Update every 5 seconds

            if step < len(AMBULANCE_STATUSES):
                status = AMBULANCE_STATUSES[step]
                step += 1
            else:
                status = "Medical team at scene — patient being assessed"

            await manager.send_json(websocket, {
                "event": "ambulance_update",
                "incident_id": incident_id,
                "status": status,
                "step": step,
                "timestamp": asyncio.get_event_loop().time(),
                "eta_minutes": max(0, 10 - step * 2),
            })

            if step >= len(AMBULANCE_STATUSES):
                await asyncio.sleep(3)
                await manager.send_json(websocket, {
                    "event": "incident_resolved",
                    "incident_id": incident_id,
                    "message": "Patient handed over to medical team. Incident resolved.",
                })
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
