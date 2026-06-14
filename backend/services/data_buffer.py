"""Science AI Lab — 센서 데이터 메모리 버퍼

ESP·센서별 최근 60초 데이터를 deque 로 보관(그래프 즉시 응답용).
DB 영구 저장은 mqtt_client 가 sensor_readings 에 함께 기록한다.
"""

from __future__ import annotations

import threading
import time
from collections import deque

WINDOW_SEC = 60.0

_lock = threading.Lock()
# key: (esp_id, sensor) → deque[(ts, value, unit)]
_buf: dict[tuple, deque] = {}


def push(esp_id: str, sensor: str, value: float, unit: str = "", ts: float | None = None) -> None:
    ts = ts if ts is not None else time.time()
    with _lock:
        dq = _buf.setdefault((esp_id, sensor), deque(maxlen=600))
        dq.append((ts, value, unit))
        # 오래된 것 제거
        cutoff = time.time() - WINDOW_SEC
        while dq and dq[0][0] < cutoff:
            dq.popleft()


def recent(esp_id: str, seconds: float = 60.0) -> dict:
    cutoff = time.time() - seconds
    out: dict[str, list] = {}
    with _lock:
        for (eid, sensor), dq in _buf.items():
            if eid != esp_id:
                continue
            pts = [{"ts": t, "value": v, "unit": u} for (t, v, u) in dq if t >= cutoff]
            if pts:
                out[sensor] = pts
    return out


def latest(esp_id: str) -> dict:
    with _lock:
        out = {}
        for (eid, sensor), dq in _buf.items():
            if eid == eid and eid == esp_id and dq:
                t, v, u = dq[-1]
                out[sensor] = {"ts": t, "value": v, "unit": u}
        return out
