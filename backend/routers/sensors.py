"""Science AI Lab — 실시간 센서 API + WebSocket (Phase 4)"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from services import data_buffer, mqtt_client, sensor_registry, ws_hub
from services.db import get_conn

router = APIRouter(tags=["sensors"])


@router.get("/api/sensors/active")
async def active():
    return {"devices": sensor_registry.active()}


@router.get("/api/sensors/{esp_id}/recent")
async def recent(esp_id: str, seconds: float = 60.0):
    return {"esp_id": esp_id, "data": data_buffer.recent(esp_id, seconds)}


@router.get("/api/sensors/{esp_id}/history")
async def history(esp_id: str, limit: int = 500):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT sensor_key, value, unit, ts FROM sensor_readings WHERE esp_id=? ORDER BY id DESC LIMIT ?",
            (esp_id, limit),
        ).fetchall()
    return {"esp_id": esp_id, "rows": [dict(r) for r in reversed(rows)]}


class CommandReq(BaseModel):
    cmd: str
    payload: dict = {}


@router.post("/api/sensors/{esp_id}/command")
async def command(esp_id: str, req: CommandReq):
    ok = mqtt_client.publish_command(esp_id, req.cmd, req.payload)
    return {"ok": ok, "esp_id": esp_id, "cmd": req.cmd}


@router.websocket("/ws/sensors")
async def ws_sensors(ws: WebSocket):
    await ws.accept()
    q = ws_hub.register()
    try:
        # 접속 즉시 현재 활성 ESP 한 번 보냄
        await ws.send_json({"type": "snapshot", "devices": sensor_registry.active()})
        while True:
            event = await q.get()
            await ws.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        ws_hub.unregister(q)
