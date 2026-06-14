"""Science AI Lab — 차시 이어하기 체크포인트 (Phase 5)

단계 변경/안전수칙/도움/주기적/종료 시 세션 상태를 저장하고,
다음 차시에 정확한 지점부터 복원한다. 손실 0이 최우선.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from . import sensor_registry
from .db import get_conn


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def save(session_id: str, reason: str = "manual") -> dict:
    with get_conn() as conn:
        s = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not s:
            return {"ok": False, "error": "세션 없음"}
        s = dict(s)
        msgs = conn.execute(
            "SELECT role, content, response_source FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 10",
            (session_id,),
        ).fetchall()
        rows = conn.execute(
            "SELECT sensor_key, value FROM sensor_readings WHERE session_id=? ORDER BY id",
            (session_id,),
        ).fetchall()

    summary: dict[str, dict] = {}
    for r in rows:
        d = summary.setdefault(r["sensor_key"], {"n": 0, "min": None, "max": None, "last": None})
        v = r["value"]
        d["n"] += 1
        d["min"] = v if d["min"] is None else min(d["min"], v)
        d["max"] = v if d["max"] is None else max(d["max"], v)
        d["last"] = v

    cp_id = uuid.uuid4().hex[:12]
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO checkpoints (id, session_id, step_n, mode, active_esp_ids, recent_messages, measurement_summary, teacher_notes, saved_at, reason) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                cp_id, session_id, s.get("current_step"), s.get("current_mode"),
                json.dumps([d["id"] for d in sensor_registry.active()], ensure_ascii=False),
                json.dumps([dict(m) for m in reversed(msgs)], ensure_ascii=False),
                json.dumps(summary, ensure_ascii=False),
                None, _now(), reason,
            ),
        )
    return {"ok": True, "checkpoint_id": cp_id, "reason": reason}


def latest_pending() -> dict:
    """미완료(active/paused) 세션의 가장 최근 체크포인트."""
    with get_conn() as conn:
        s = conn.execute(
            "SELECT * FROM sessions WHERE status IN ('active','paused') ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        if not s:
            return {"has_pending": False}
        s = dict(s)
        cp = conn.execute(
            "SELECT * FROM checkpoints WHERE session_id=? ORDER BY saved_at DESC LIMIT 1",
            (s["id"],),
        ).fetchone()
    out = {
        "has_pending": True,
        "session_id": s["id"],
        "experiment_id": s.get("experiment_id"),
        "step_n": s.get("current_step"),
    }
    if cp:
        cp = dict(cp)
        out["saved_at"] = cp.get("saved_at")
        out["reason"] = cp.get("reason")
    # 측정요약은 최신 readings로 실시간 재계산(체크포인트 이후 들어온 값 반영)
    out["measurement_summary"] = _summarize(s["id"])
    return out


def _summarize(session_id: str) -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT sensor_key, value FROM sensor_readings WHERE session_id=? ORDER BY id",
            (session_id,),
        ).fetchall()
    summary: dict[str, dict] = {}
    for r in rows:
        d = summary.setdefault(r["sensor_key"], {"n": 0, "min": None, "max": None, "last": None})
        v = r["value"]
        d["n"] += 1
        d["min"] = v if d["min"] is None else min(d["min"], v)
        d["max"] = v if d["max"] is None else max(d["max"], v)
        d["last"] = v
    return summary


def resume(session_id: str) -> dict:
    """세션을 active로 되돌리고 안전 재복창 플래그를 내린다(간소 재확인)."""
    with get_conn() as conn:
        s = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not s:
            return {"ok": False, "error": "세션 없음"}
        # 1 Pi = 1 모둠: 다른 active 정리
        conn.execute("UPDATE sessions SET status='ended' WHERE status='active' AND id<>?", (session_id,))
        conn.execute("UPDATE sessions SET status='active', safety_ritual_done=0 WHERE id=?", (session_id,))
        s = dict(s)
    return {"ok": True, "session_id": session_id, "step_n": s.get("current_step"), "resafety": True}
