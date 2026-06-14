"""Science AI Lab — 활성 ESP 레지스트리 (in-memory)

ESP의 info/heartbeat/data 를 받아 생존 여부를 관리한다.
15초 동안 소식 없으면 dead(😵). 챗 UI 상태 위젯에 쓰인다.
"""

from __future__ import annotations

import threading
import time

from .db import get_conn

DEAD_TIMEOUT = 15.0  # 초

_lock = threading.Lock()
_devices: dict[str, dict] = {}


def _now() -> float:
    return time.time()


def register(esp_id: str, info: dict) -> None:
    with _lock:
        d = _devices.setdefault(esp_id, {})
        d.update(
            board_type=info.get("board_type", d.get("board_type")),
            sensor_type=info.get("sensor_type") or info.get("sensor", d.get("sensor_type")),
            last_seen=_now(),
            first_seen=d.get("first_seen", _now()),
        )
    _persist(esp_id)


def heartbeat(esp_id: str, payload: dict) -> None:
    with _lock:
        d = _devices.setdefault(esp_id, {"first_seen": _now()})
        d["last_seen"] = _now()
        d["rssi"] = payload.get("rssi", d.get("rssi"))
        d["uptime_s"] = payload.get("uptime_s")
    _persist(esp_id)


def touch(esp_id: str) -> None:
    with _lock:
        d = _devices.setdefault(esp_id, {"first_seen": _now()})
        d["last_seen"] = _now()


def _status(d: dict) -> str:
    return "alive" if (_now() - d.get("last_seen", 0)) <= DEAD_TIMEOUT else "dead"


def active() -> list[dict]:
    with _lock:
        out = []
        for esp_id, d in _devices.items():
            out.append({
                "id": esp_id,
                "board_type": d.get("board_type"),
                "sensor_type": d.get("sensor_type"),
                "rssi": d.get("rssi"),
                "status": _status(d),
                "last_seen_ago": round(_now() - d.get("last_seen", _now()), 1),
            })
        return out


def _persist(esp_id: str) -> None:
    try:
        d = _devices.get(esp_id, {})
        from datetime import datetime
        now = datetime.now().isoformat(timespec="seconds")
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO esp_devices (id, board_type, sensor_type, first_seen, last_seen, rssi, status) "
                "VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET board_type=excluded.board_type, sensor_type=excluded.sensor_type, "
                "last_seen=excluded.last_seen, rssi=excluded.rssi, status=excluded.status",
                (esp_id, d.get("board_type"), d.get("sensor_type"), now, now, d.get("rssi"), _status(d)),
            )
    except Exception:
        pass
