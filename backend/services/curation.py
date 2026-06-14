"""Science AI Lab — 교사 큐레이션 큐 (Phase 7)

LLM 답변을 검수 큐에 적재하고, 교사 승인/거부/수정을 처리한다.
승인 → 임베딩 인덱싱(approved 가중치). 거부 → 프롬프트 진화의 '피해야 할' 자료.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from . import anomaly_detector, embeddings, vector_store
from .db import get_conn


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def enqueue(message_id: str, session_id: str, question: str, answer: str, grade=None) -> dict | None:
    """이상 징후가 있을 때만 큐에 적재(전수 적재는 과부하)."""
    reasons = anomaly_detector.check(answer, grade)
    if not reasons:
        return None
    cid = uuid.uuid4().hex[:12]
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO curation_queue (id, message_id, session_id, question, answer, grade, reason, status, created_at) "
            "VALUES (?,?,?,?,?,?,?, 'pending', ?)",
            (cid, message_id, session_id, question, answer, grade, "; ".join(reasons), _now()),
        )
        conn.execute(
            "INSERT INTO anomaly_log (message_id, reason, detail, ts) VALUES (?,?,?,?)",
            (message_id, "; ".join(reasons), answer[:120], _now()),
        )
    return {"id": cid, "reasons": reasons}


def queue(status: str = "pending", limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM curation_queue WHERE status=? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def _index_qa(question: str, answer: str, grade, status: str):
    vec = embeddings.embed(question)
    if vec:
        vector_store.add("qa", uuid.uuid4().hex[:12], question, vec,
                         grade=grade, answer=answer, curated_status=status)


def approve(cid: str) -> dict:
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM curation_queue WHERE id=?", (cid,)).fetchone()
        if not r:
            return {"ok": False, "error": "항목 없음"}
        r = dict(r)
        conn.execute("UPDATE curation_queue SET status='approved' WHERE id=?", (cid,))
    _index_qa(r["question"] or "", r["answer"] or "", r["grade"], "approved")
    return {"ok": True, "status": "approved"}


def reject(cid: str) -> dict:
    with get_conn() as conn:
        conn.execute("UPDATE curation_queue SET status='rejected' WHERE id=?", (cid,))
    return {"ok": True, "status": "rejected"}


def edit(cid: str, edited_answer: str) -> dict:
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM curation_queue WHERE id=?", (cid,)).fetchone()
        if not r:
            return {"ok": False, "error": "항목 없음"}
        r = dict(r)
        conn.execute("UPDATE curation_queue SET status='edited', edited_answer=? WHERE id=?", (edited_answer, cid))
    _index_qa(r["question"] or "", edited_answer, r["grade"], "approved")
    return {"ok": True, "status": "edited"}
