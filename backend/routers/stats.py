"""Science AI Lab — 라우팅 통계 (스크립트 vs LLM 비율 측정)

목표: 스크립트 70~85%, LLM 15~30%. LLM 비율이 너무 높으면 scripted_replies 보강.
"""

from __future__ import annotations

from fastapi import APIRouter

from services.db import get_conn

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/routing")
async def routing():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT response_source AS src, COUNT(*) AS n, AVG(latency_ms) AS avg_ms "
            "FROM messages WHERE role='assistant' AND response_source IS NOT NULL "
            "GROUP BY response_source"
        ).fetchall()

    by = {r["src"]: {"n": r["n"], "avg_ms": round(r["avg_ms"] or 0, 1)} for r in rows}
    scripted = by.get("scripted", {}).get("n", 0) + by.get("rule", {}).get("n", 0)
    llm = by.get("llm", {}).get("n", 0)
    total = scripted + llm

    def pct(x):
        return round(100 * x / total, 1) if total else 0.0

    return {
        "total_responses": total,
        "scripted": scripted,
        "scripted_pct": pct(scripted),
        "llm": llm,
        "llm_pct": pct(llm),
        "avg_scripted_ms": by.get("scripted", {}).get("avg_ms", 0),
        "avg_rule_ms": by.get("rule", {}).get("avg_ms", 0),
        "avg_llm_ms": by.get("llm", {}).get("avg_ms", 0),
        "by_source": by,
        "target": "스크립트 70~85% / LLM 15~30%",
        "in_target": 70 <= pct(scripted) <= 85 if total else None,
    }
