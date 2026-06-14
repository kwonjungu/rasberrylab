"""Science AI Lab — 시스템 프롬프트 자동 진화 (Phase 7)

교사 큐레이션(approved/rejected)에서 좋은/피할 패턴을 모아 prompt addon 을 만들고
prompt_versions 에 버전으로 저장한다. 자동 학습이 아니라 100% 교사 큐레이션 의존.
버전 기록 → 롤백 가능.
"""

from __future__ import annotations

from datetime import datetime

from .db import get_conn


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def build_addon() -> dict:
    with get_conn() as conn:
        approved = conn.execute(
            "SELECT question, COALESCE(edited_answer, answer) a FROM curation_queue WHERE status IN ('approved','edited') ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        rejected = conn.execute(
            "SELECT reason FROM curation_queue WHERE status='rejected' ORDER BY created_at DESC LIMIT 5"
        ).fetchall()

    lines = []
    if approved:
        lines.append("[좋은 답변 예시 - 교사 승인, 자동 학습됨]")
        for r in approved:
            lines.append(f"- \"{(r['question'] or '')[:30]}\" → \"{(r['a'] or '')[:70]}\"")
    if rejected:
        lines.append("[피해야 할 패턴 - 교사가 거부함]")
        seen = set()
        for r in rejected:
            for part in (r["reason"] or "").split(";"):
                p = part.strip()
                if p and p not in seen:
                    seen.add(p)
                    lines.append(f"- {p}")

    return {"addon": "\n".join(lines), "approved_n": len(approved), "rejected_n": len(rejected)}


def evolve() -> dict:
    data = build_addon()
    if not data["addon"]:
        return {"ok": False, "reason": "큐레이션 데이터 없음"}
    with get_conn() as conn:
        cur = conn.execute("SELECT COALESCE(MAX(version),0) v FROM prompt_versions").fetchone()["v"]
        new_v = cur + 1
        conn.execute("UPDATE prompt_versions SET active=0")
        conn.execute(
            "INSERT INTO prompt_versions (version, addon, active, approved_n, rejected_n, created_at) VALUES (?,?,1,?,?,?)",
            (new_v, data["addon"], data["approved_n"], data["rejected_n"], _now()),
        )
    return {"ok": True, "version": new_v, **data}


def active_addon() -> str:
    with get_conn() as conn:
        r = conn.execute("SELECT addon FROM prompt_versions WHERE active=1 ORDER BY version DESC LIMIT 1").fetchone()
    return r["addon"] if r else ""


def versions() -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT id, version, active, approved_n, rejected_n, created_at FROM prompt_versions ORDER BY version DESC")]


def activate(version_id: int) -> dict:
    with get_conn() as conn:
        conn.execute("UPDATE prompt_versions SET active=0")
        conn.execute("UPDATE prompt_versions SET active=1 WHERE id=?", (version_id,))
    return {"ok": True, "activated": version_id}
