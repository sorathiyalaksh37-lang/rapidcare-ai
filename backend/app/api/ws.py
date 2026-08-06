"""
WebSocket Routes — Enhanced (Task 4 Upgrade)
=============================================
Two WebSocket endpoints:
  1. /ws/live/{incident_id}         — Ambulance status stream (original, enhanced)
  2. /ws/hospitals/availability     — Live hospital capacity broadcast (Task 4)

ConnectionManager supports room-based subscriptions:
  - ambulance_rooms: incident_id → [WebSocket]
  - availability_room: [WebSocket] broadcasting to all subscribers
"""
import asyncio
import json
import logging
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


# ── Connection Manager ────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.ambulance_rooms: dict[str, list[WebSocket]] = {}  # incident_id → connections
        self.availability_subscribers: list[WebSocket] = []

    async def connect_ambulance(self, ws: WebSocket, incident_id: str):
        await ws.accept()
        self.ambulance_rooms.setdefault(incident_id, []).append(ws)
        logger.info("WS connected: ambulance room %s (total=%d)",
                    incident_id, len(self.ambulance_rooms[incident_id]))

    def disconnect_ambulance(self, ws: WebSocket, incident_id: str):
        room = self.ambulance_rooms.get(incident_id, [])
        if ws in room:
            room.remove(ws)
        if not room and incident_id in self.ambulance_rooms:
            del self.ambulance_rooms[incident_id]

    async def connect_availability(self, ws: WebSocket):
        await ws.accept()
        self.availability_subscribers.append(ws)
        logger.info("WS connected: availability (total=%d)", len(self.availability_subscribers))

    def disconnect_availability(self, ws: WebSocket):
        if ws in self.availability_subscribers:
            self.availability_subscribers.remove(ws)

    async def send_to_room(self, incident_id: str, data: dict):
        dead = []
        for ws in self.ambulance_rooms.get(incident_id, []):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_ambulance(ws, incident_id)

    async def broadcast_availability(self, data: dict):
        dead = []
        for ws in self.availability_subscribers:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_availability(ws)

    @property
    def active_connections(self) -> int:
        return (
            sum(len(v) for v in self.ambulance_rooms.values()) +
            len(self.availability_subscribers)
        )


manager = ConnectionManager()

AMBULANCE_STATUSES = [
    ("Ambulance dispatched", "dispatched"),
    ("En route to scene", "en_route"),
    ("Arrival in 8 minutes", "approaching"),
    ("Arrival in 5 minutes", "approaching"),
    ("Arrival in 2 minutes", "arriving"),
    ("Arrived at scene", "arrived"),
]


# ── Ambulance Status WebSocket ────────────────────────────────────────────────

@router.websocket("/ws/live/{incident_id}")
async def live_updates(websocket: WebSocket, incident_id: str):
    """Stream live ambulance status updates for a given incident."""
    await manager.connect_ambulance(websocket, incident_id)
    step = 0
    try:
        await websocket.send_json({
            "event": "connected",
            "incident_id": incident_id,
            "message": "Connected to RapidCare live updates",
            "timestamp": time.time(),
        })

        while True:
            await asyncio.sleep(5)

            if step < len(AMBULANCE_STATUSES):
                status_msg, status_code = AMBULANCE_STATUSES[step]
                step += 1
            else:
                status_msg, status_code = "Medical team at scene — patient being assessed", "on_scene"

            eta_minutes = max(0, 10 - step * 2)
            await websocket.send_json({
                "event": "ambulance_update",
                "incident_id": incident_id,
                "status": status_msg,
                "status_code": status_code,
                "step": step,
                "total_steps": len(AMBULANCE_STATUSES),
                "eta_minutes": eta_minutes,
                "timestamp": time.time(),
                "progress_pct": round(step / len(AMBULANCE_STATUSES) * 100),
            })

            if step >= len(AMBULANCE_STATUSES):
                await asyncio.sleep(3)
                await websocket.send_json({
                    "event": "incident_resolved",
                    "incident_id": incident_id,
                    "message": "Patient handed over to medical team. Incident resolved.",
                    "timestamp": time.time(),
                })
                break

    except WebSocketDisconnect:
        manager.disconnect_ambulance(websocket, incident_id)
        logger.info("WS disconnected: ambulance room %s", incident_id)


# ── Hospital Availability WebSocket ───────────────────────────────────────────

@router.websocket("/ws/hospitals/availability")
async def availability_stream(websocket: WebSocket):
    """
    Stream real-time hospital availability updates every 5 seconds.
    Sends availability data for a rotating set of hospitals.
    Clients can also send: {"subscribe": "hospital_id"} to filter.
    """
    await manager.connect_availability(websocket)
    subscribed_hospitals: set[str] = set()

    try:
        await websocket.send_json({
            "event": "connected",
            "message": "Subscribed to hospital availability stream",
            "update_interval_sec": 5,
            "timestamp": time.time(),
        })

        # Listen for client messages (subscriptions) + send updates concurrently
        async def listen_client():
            while True:
                try:
                    msg = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    data = json.loads(msg)
                    if "subscribe" in data:
                        subscribed_hospitals.add(data["subscribe"])
                    elif "unsubscribe" in data:
                        subscribed_hospitals.discard(data["unsubscribe"])
                except asyncio.TimeoutError:
                    pass
                except Exception:
                    break

        async def send_updates():
            from app.services.availability_service import get_bulk_availability
            update_cycle = 0
            while True:
                await asyncio.sleep(5)
                try:
                    # Send targeted or summary updates
                    if subscribed_hospitals:
                        hospital_ids = list(subscribed_hospitals)
                        avail_data = await get_bulk_availability(hospital_ids)
                        await websocket.send_json({
                            "event": "availability_update",
                            "hospitals": avail_data,
                            "update_cycle": update_cycle,
                            "timestamp": time.time(),
                        })
                    else:
                        # Send summary stats when no specific hospitals subscribed
                        from app.services.availability_service import get_availability_summary
                        summary = await get_availability_summary()
                        await websocket.send_json({
                            "event": "availability_summary",
                            "summary": summary,
                            "update_cycle": update_cycle,
                            "timestamp": time.time(),
                        })
                    update_cycle += 1
                except Exception as exc:
                    logger.debug("Availability send error: %s", exc)
                    break

        await asyncio.gather(listen_client(), send_updates())

    except WebSocketDisconnect:
        manager.disconnect_availability(websocket)
        logger.info("WS disconnected: availability subscriber")


# ── Stats endpoint ────────────────────────────────────────────────────────────

@router.get("/ws/stats")
async def ws_stats():
    """Return current WebSocket connection counts."""
    return {
        "active_connections": manager.active_connections,
        "ambulance_rooms": len(manager.ambulance_rooms),
        "availability_subscribers": len(manager.availability_subscribers),
    }
