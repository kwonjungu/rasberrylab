"""Science AI Lab — 세션 API (1 Pi = 1 모둠)

세션 시작/역할분담/단계 진행/종료. 개인정보(별명)는 종료 시 NULL 처리.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
VERIFY_MODEL = os.environ.get("SCIENCE_AI_MODEL", "gemma3:1b")

from services import help_signal
from services.data_loader import store
from services.db import get_conn
from services.mode_manager import resolve_mode
from services.role_manager import ROLE_CARDS
from services.safety_ritual import build_ritual

router = APIRouter(prefix="/api/session", tags=["session"])

# 학생 화면 빠른답변 4종 (고정)
QUICK_REPLIES = [
    {"id": "done", "label": "✅ 했어요"},
    {"id": "stuck", "label": "🤔 잘몰라"},
    {"id": "repeat", "label": "🔁 다시"},
    {"id": "help", "label": "🤚 도와줘"},
]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_session(session_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        return dict(row) if row else None


class StartReq(BaseModel):
    team_name: str | None = None
    grade: int | None = None
    unit_id: str | None = None
    experiment_id: str | None = None
    class_period: str | None = None


@router.post("/start")
async def start(req: StartReq):
    sid = uuid.uuid4().hex[:12]
    with get_conn() as conn:
        # 1 Pi = 1 모둠: 이전 active 세션은 자동 종료(단일 활성 세션 보장)
        conn.execute("UPDATE sessions SET status='ended' WHERE status='active'")
        conn.execute(
            "INSERT INTO sessions (id, team_name, grade, unit_id, experiment_id, class_period, started_at, current_step, current_mode, status) "
            "VALUES (?,?,?,?,?,?,?,0,'greeting','active')",
            (sid, req.team_name, req.grade, req.unit_id, req.experiment_id, req.class_period, _now()),
        )
    return {"session_id": sid, "mode": "greeting"}


class RolesReq(BaseModel):
    session_id: str
    role_assignments: dict  # {"experiment":"지민", "record":"서연", ...}


@router.post("/roles")
async def roles(req: RolesReq):
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET role_assignments=? WHERE id=?",
            (json.dumps(req.role_assignments, ensure_ascii=False), req.session_id),
        )
    return {"ok": True}


@router.get("/{session_id}/current")
async def current(session_id: str):
    """학생 화면이 그릴 현재 상태: 모드·단계 안내문·빠른답변·타이머."""
    s = get_session(session_id)
    if not s:
        return {"error": "세션을 찾을 수 없어요."}
    mode = resolve_mode(s)
    step_n = s.get("current_step") or 0
    exp_id = s.get("experiment_id") or ""
    is_onboarding = exp_id == "onboarding-first-class"
    exp = None if is_onboarding else store.experiment_by_id(exp_id)
    ob = store.onboarding if is_onboarding else None

    title = ob.title if ob else (exp.title if exp else None)
    total = len(ob.stages) if ob else (len(exp.steps) if exp else 0)

    out = {
        "session_id": session_id,
        "mode": mode,
        "grade": s.get("grade"),
        "team_name": s.get("team_name"),
        "experiment_id": exp_id or None,
        "experiment_title": title,
        "total_steps": total,
        "step_n": step_n,
        "instruction": None,
        "duration_sec": 0,
        "safety_warnings": (exp.safety_warnings if exp else (ob.safety_rules if ob else [])),
        "quick_replies": QUICK_REPLIES,
    }

    if mode == "greeting":
        if title:
            tmpl = (store.dialogue.get("greetings", {}) or {}).get("after_role_select", "오늘은 「{experiment_title}」을(를) 할 거야. 준비됐어?")
            out["instruction"] = tmpl.replace("{team_name}", s.get("team_name") or "친구들").replace("{experiment_title}", title)
            out["quick_replies"] = [{"id": "begin", "label": "🚀 준비됐어!"}]
        else:
            out["instruction"] = (store.dialogue.get("greetings", {}) or {}).get("session_start", "안녕! 무엇을 도와줄까?")
            out["quick_replies"] = []
    elif mode == "onboarding" and ob:
        stage = next((st for st in ob.stages if st.n == step_n), None)
        if stage:
            txt = stage.llm_script or stage.title
            if stage.checkpoint_question:
                txt += f"\n\n❓ {stage.checkpoint_question}"
            out["instruction"] = txt
            out["safety_warnings"] = stage.safety_check or out["safety_warnings"]
    elif exp:
        step = next((st for st in exp.steps if st.n == step_n), None)
        if step:
            out["instruction"] = step.instruction_student
            out["duration_sec"] = step.duration_sec
            out["image_path"] = getattr(step, "image_path", None)
    if mode == "onboarding" and ob:
        stage = next((st for st in ob.stages if st.n == step_n), None)
        if stage:
            out["image_path"] = getattr(stage, "image_path", None)
    return out


@router.post("/{session_id}/step/next")
async def next_step(session_id: str):
    s = get_session(session_id)
    if not s:
        return {"error": "세션을 찾을 수 없어요."}
    nxt = (s["current_step"] or 0) + 1
    s["current_step"] = nxt
    new_mode = resolve_mode(s)  # greeting → onboarding/experiment 자동 전환
    with get_conn() as conn:
        conn.execute("UPDATE sessions SET current_step=?, current_mode=? WHERE id=?", (nxt, new_mode, session_id))
    # 단계 변경 시 자동 체크포인트(손실 0)
    try:
        from services.checkpoint import save
        save(session_id, "step_change")
    except Exception:
        pass
    return {"current_step": nxt, "mode": new_mode}


# ---------- AI 단계 채점(통과 게이트) ----------
class VerifyReq(BaseModel):
    answer: str | None = None


def _recent_readings(session_id: str, step_n: int, limit: int = 60) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT sensor_type, value, unit FROM sensor_readings "
            "WHERE session_id=? AND step_n=? ORDER BY id DESC LIMIT ?",
            (session_id, step_n, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def _summarize(readings: list[dict]) -> str:
    by: dict[str, list[float]] = {}
    for r in readings:
        v = r.get("value")
        if v is not None:
            by.setdefault(r.get("sensor_type") or "값", []).append(v)
    parts = []
    for k, vs in by.items():
        if vs:
            parts.append(f"{k}: {len(vs)}회 측정, 최소 {round(min(vs),2)}, 최대 {round(max(vs),2)}, 최근 {round(vs[0],2)}")
    return " / ".join(parts)


def _build_prompt(step: dict, data_str: str, answer: str) -> str:
    crit = []
    if step.get("objectives"):
        crit += step["objectives"]
    thr = step.get("sensor_thresholds") or {}
    for sensor, rules in thr.items():
        for rule in rules:
            crit.append(f"{sensor} {rule.get('range','')} → {rule.get('scripted','')}")
    crit_str = "\n".join(f"- {c}" for c in crit) or "- (이 단계의 안내문대로 측정/관찰을 수행)"
    return (
        "너는 초등 과학 실험을 돕는 다정한 AI 도우미야. 학생이 '다 했어요'를 눌렀어.\n"
        "아래 '실제 측정 데이터'와 '학생 설명'을 보고, 이 단계를 제대로 수행했는지 판정해.\n"
        "엄격하게 점수 매기지 말고, 데이터가 실제로 들어왔고 단계 취지에 맞으면 통과시켜. 격려가 우선이야.\n\n"
        f"[단계 안내]\n{step.get('instruction_student','')}\n\n"
        f"[성공 기준]\n{crit_str}\n\n"
        f"[실제 측정 데이터]\n{data_str or '(데이터 없음)'}\n\n"
        f"[학생 설명]\n{answer or '(설명 없음)'}\n\n"
        "반드시 아래 JSON 한 줄로만 답해. 다른 말 금지.\n"
        '{"pass": true 또는 false, "feedback": "한국어 한두 문장, 통과면 칭찬+한 줄 배운점 확인, 아니면 무엇을 더 해보면 좋을지 힌트"}'
    )


async def _ollama_judge(prompt: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": VERIFY_MODEL, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.2}},
            )
        txt = (r.json() or {}).get("response", "")
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            obj = json.loads(m.group(0))
            return {"pass": bool(obj.get("pass", True)),
                    "feedback": str(obj.get("feedback", "")).strip(), "source": "llm"}
        passed = not re.search(r"false|아니|다시|부족", txt)
        return {"pass": passed, "feedback": txt.strip()[:120], "source": "llm-text"}
    except Exception:
        # AI를 못 쓰면 학습을 막지 않는다(통과 + 안내)
        return {"pass": True, "feedback": "좋아요! 다음으로 넘어가요 👍 (AI 확인은 잠시 쉬는 중)", "source": "fallback"}


@router.post("/{session_id}/step/verify")
async def step_verify(session_id: str, req: VerifyReq = VerifyReq()):
    """핵심(데이터 수집) 단계에서 실제 센서 데이터+학생 설명을 AI가 보고 통과/재도전 판정."""
    s = get_session(session_id)
    if not s:
        return {"error": "세션을 찾을 수 없어요.", "pass": True}
    exp_id = s.get("experiment_id") or ""
    step_n = s.get("current_step") or 0
    step = store.step_dict(exp_id, step_n) if exp_id else None
    # 데이터 수집 단계가 아니면 자동 통과(준비/연결 단계는 자율)
    if not step or step.get("expected_state") != "data_collecting":
        return {"gated": False, "pass": True}
    readings = _recent_readings(session_id, step_n)
    if not readings:
        return {"gated": True, "pass": False,
                "feedback": "아직 센서 값이 안 들어왔어요. 센서로 먼저 측정해 볼까요? 📊"}
    verdict = await _ollama_judge(_build_prompt(step, _summarize(readings), req.answer or ""))
    return {"gated": True, **verdict}


@router.get("/roles/cards")
async def role_cards():
    """역할 카드 4종(실험왕·기록왕·발표왕·안전왕)."""
    return {"roles": ROLE_CARDS}


@router.get("/{session_id}/safety")
async def safety(session_id: str):
    """현재 실험의 안전수칙 복창 데이터."""
    s = get_session(session_id)
    if not s:
        return {"error": "세션을 찾을 수 없어요."}
    data = build_ritual(s.get("experiment_id") or "")
    data["done"] = bool(s.get("safety_ritual_done"))
    return data


@router.post("/{session_id}/safety/done")
async def safety_done(session_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE sessions SET safety_ritual_done=1 WHERE id=?", (session_id,))
    return {"ok": True}


@router.post("/{session_id}/help")
async def help_call(session_id: str):
    """도움요청 → GPIO 부저·LED(가능 시) + 횟수 기록."""
    sig = help_signal.trigger()
    with get_conn() as conn:
        conn.execute(
            "UPDATE experiment_runs SET help_calls = COALESCE(help_calls,0)+1 WHERE session_id=?",
            (session_id,),
        )
    msg = (store.dialogue.get("help", {}) or {}).get("raised", "선생님께 알렸어요! 🔔")
    return {"ok": True, "signal": sig, "message": msg}


@router.post("/{session_id}/end")
async def end(session_id: str):
    # PDF는 개인정보 삭제 전에 생성(모둠명·역할 포함)
    pdf_ok, pdf_err = True, None
    try:
        from services.report_pdf import generate
        generate(session_id)
    except Exception as exc:
        pdf_ok, pdf_err = False, str(exc)
    # 개인정보(별명·역할) 자동 삭제
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET ended_at=?, status='ended', team_name=NULL, role_assignments=NULL WHERE id=?",
            (_now(), session_id),
        )
    return {
        "ok": True,
        "note": "별명·역할은 개인정보 보호를 위해 삭제되었어요.",
        "pdf": f"/api/session/{session_id}/report.pdf" if pdf_ok else None,
        "pdf_error": pdf_err,
    }


@router.get("/{session_id}/report.pdf")
async def report_pdf(session_id: str):
    from pathlib import Path

    from fastapi.responses import FileResponse

    p = Path(__file__).resolve().parent.parent.parent / "db" / "reports" / f"{session_id}.pdf"
    if not p.exists():
        return {"error": "활동지가 아직 없어요. 수업을 종료하면 만들어져요."}
    return FileResponse(str(p), media_type="application/pdf", filename=f"활동지_{session_id}.pdf")
