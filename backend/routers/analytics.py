"""Science AI Lab — 학급 분석 대시보드 API (Phase 7)"""

from __future__ import annotations

from fastapi import APIRouter

from services.db import get_conn

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
async def summary():
    with get_conn() as conn:
        sessions = conn.execute("SELECT COUNT(*) n FROM sessions").fetchone()["n"]
        ended = conn.execute("SELECT COUNT(*) n FROM sessions WHERE status='ended'").fetchone()["n"]
        helps = conn.execute("SELECT COALESCE(SUM(help_calls),0) n FROM experiment_runs").fetchone()["n"]
        msgs = conn.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
        llm = conn.execute("SELECT COUNT(*) n FROM messages WHERE response_source='llm'").fetchone()["n"]
        scripted = conn.execute("SELECT COUNT(*) n FROM messages WHERE response_source IN ('scripted','rule')").fetchone()["n"]
        anomalies = conn.execute("SELECT COUNT(*) n FROM curation_queue").fetchone()["n"]
    total_resp = llm + scripted
    return {
        "sessions": sessions,
        "completed": ended,
        "completion_rate": round(ended / sessions * 100, 1) if sessions else 0,
        "help_calls": helps,
        "messages": msgs,
        "scripted_pct": round(scripted / total_resp * 100, 1) if total_resp else 0,
        "llm_pct": round(llm / total_resp * 100, 1) if total_resp else 0,
        "curation_items": anomalies,
    }


@router.get("/popular_experiments")
async def popular():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT experiment_id, COUNT(*) n FROM sessions WHERE experiment_id IS NOT NULL GROUP BY experiment_id ORDER BY n DESC LIMIT 10"
        ).fetchall()
    return {"experiments": [dict(r) for r in rows]}


@router.get("/learning_curve")
async def learning_curve():
    """학년별 평균 단계 도달·도움 횟수(간이)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT grade, AVG(current_step) avg_step, COUNT(*) n FROM sessions WHERE grade IS NOT NULL GROUP BY grade ORDER BY grade"
        ).fetchall()
    return {"by_grade": [dict(r) for r in rows]}
