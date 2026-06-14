"""Science AI Lab — 리플레이 (Phase 5)

종료된 세션의 messages + sensor_readings 를 시간순으로 병합해
재생 이벤트 목록을 만든다. 라우터가 SSE로 배속 송출한다.
"""

from __future__ import annotations

from datetime import datetime

from .db import get_conn


def _ts(s: str | None) -> float:
    if not s:
        return 0.0
    try:
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return 0.0


def sessions(limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, experiment_id, grade, started_at, ended_at FROM sessions "
            "WHERE status='ended' ORDER BY ended_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def timeline(session_id: str) -> list[dict]:
    """messages·sensor_readings를 (상대초, 종류, 페이로드)로 병합 정렬."""
    events: list[dict] = []
    with get_conn() as conn:
        for m in conn.execute(
            "SELECT role, content, response_source, created_at FROM messages WHERE session_id=? ORDER BY id",
            (session_id,),
        ):
            events.append({"t": _ts(m["created_at"]), "kind": "message",
                           "role": m["role"], "content": m["content"], "source": m["response_source"]})
        for r in conn.execute(
            "SELECT sensor_key, value, unit, created_at FROM sensor_readings WHERE session_id=? ORDER BY id",
            (session_id,),
        ):
            events.append({"t": _ts(r["created_at"]), "kind": "data",
                           "sensor": r["sensor_key"], "value": r["value"], "unit": r["unit"]})
    if not events:
        return []
    events.sort(key=lambda e: e["t"])
    t0 = events[0]["t"]
    for e in events:
        e["offset"] = round(e["t"] - t0, 2)
        del e["t"]
    return events
