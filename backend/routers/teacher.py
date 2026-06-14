"""Science AI Lab — 교사 모드 (PIN 보호, 같은 Pi)

진행 상황 조회, 단계 제어, LLM 메시지 주입. PIN은 환경변수 TEACHER_PIN(기본 1234).
30초 무입력 자동 복귀는 프론트엔드에서 처리.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from routers.session import get_session
from services import help_signal
from services.db import get_conn

router = APIRouter(prefix="/api/teacher", tags=["teacher"])

TEACHER_PIN = os.environ.get("TEACHER_PIN", "1234")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class LoginReq(BaseModel):
    pin: str


@router.post("/login")
async def login(req: LoginReq):
    ok = req.pin == TEACHER_PIN
    if ok:
        help_signal.off()  # 교사 진입 시 도움 신호 끄기
    return {"ok": ok, "message": "교사 모드로 들어왔어요." if ok else "PIN이 달라요."}


@router.get("/{session_id}/view")
async def view(session_id: str):
    """진행 상황: 현재 단계·안전수칙 여부·막힘(stuck) 누적·도움 횟수."""
    s = get_session(session_id)
    if not s:
        return {"error": "세션을 찾을 수 없어요."}
    with get_conn() as conn:
        stuck = conn.execute(
            "SELECT COUNT(*) n FROM messages WHERE session_id=? AND "
            "(script_id LIKE '%stuck%' OR script_id LIKE '%repeat%' OR script_id='intent.deny')",
            (session_id,),
        ).fetchone()["n"]
        helps = conn.execute(
            "SELECT COALESCE(SUM(help_calls),0) n FROM experiment_runs WHERE session_id=?",
            (session_id,),
        ).fetchone()["n"]
        msgs = conn.execute("SELECT COUNT(*) n FROM messages WHERE session_id=?", (session_id,)).fetchone()["n"]
    return {
        "session_id": session_id,
        "team_name": s.get("team_name"),
        "experiment_id": s.get("experiment_id"),
        "current_step": s.get("current_step"),
        "current_mode": s.get("current_mode"),
        "safety_ritual_done": bool(s.get("safety_ritual_done")),
        "stuck_count": stuck,
        "help_calls": helps,
        "message_count": msgs,
        "status": s.get("status"),
    }


class ControlReq(BaseModel):
    session_id: str
    action: str  # pause | resume


@router.post("/control")
async def control(req: ControlReq):
    new = {"pause": "paused", "resume": "active"}.get(req.action)
    if not new:
        return {"error": "알 수 없는 동작이에요."}
    with get_conn() as conn:
        conn.execute("UPDATE sessions SET status=? WHERE id=?", (new, req.session_id))
    return {"ok": True, "status": new}


class InjectReq(BaseModel):
    session_id: str
    content: str


@router.post("/inject")
async def inject(req: InjectReq):
    """교사가 학생 화면에 메시지를 직접 주입(스크립트로 기록)."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (id, session_id, role, content, response_source, created_at) VALUES (?,?,?,?,?,?)",
            (uuid.uuid4().hex[:12], req.session_id, "teacher_injected", req.content, "scripted", _now()),
        )
    return {"ok": True, "content": req.content}
