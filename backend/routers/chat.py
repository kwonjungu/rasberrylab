"""Science AI Lab — 채팅 API (SSE, 응답 라우터 통과)

스크립트/룰 → 즉시 단일 이벤트. LLM → '생각 중' 후 토큰 스트리밍.
모든 assistant 메시지는 response_source/script_id/latency_ms 와 함께 DB 기록.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from routers.session import get_session
from services.db import get_conn
from services.response_router import router as resp_router

router = APIRouter(prefix="/api", tags=["chat"])

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# 모드별 모델: 실험/자유 채팅은 빠른 1b 우선. 품질이 필요하면 4b로 교체 가능.
MODEL_FAST = os.environ.get("SCIENCE_AI_MODEL", "gemma3:1b")


class ChatReq(BaseModel):
    session_id: str
    input_type: str = "text"   # text | quick_reply | sensor
    payload: dict = {}
    spoken_by: str | None = None


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _log(session_id, role, content, source=None, script_id=None, model=None, latency_ms=None, spoken_by=None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (id, session_id, role, content, response_source, script_id, model, latency_ms, spoken_by, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (uuid.uuid4().hex[:12], session_id, role, content, source, script_id, model, latency_ms, spoken_by, _now()),
        )


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(req: ChatReq):
    session = get_session(req.session_id) or {"id": req.session_id}

    # 사용자 입력 기록(센서는 제외)
    if req.input_type in ("text", "quick_reply"):
        user_text = req.payload.get("text") or req.payload.get("button_id") or ""
        _log(req.session_id, "user", user_text, spoken_by=req.spoken_by)
    elif req.input_type == "sensor":
        # 센서 측정값 시계열 저장 (PDF 그래프용)
        step_n = (session.get("current_step") if isinstance(session, dict) else 0) or 0
        with get_conn() as conn:
            for k, v in (req.payload.get("values") or {}).items():
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                conn.execute(
                    "INSERT INTO sensor_readings (session_id, sensor_key, value, step_n, created_at) VALUES (?,?,?,?,?)",
                    (req.session_id, k, fv, step_n, _now()),
                )

    decision = resp_router.route(req.input_type, req.payload, session)
    source = decision.get("source")

    async def gen():
        # 1) 스크립트/룰 → 즉답
        if source in ("scripted", "rule"):
            t0 = time.perf_counter()
            content = decision["content"]
            latency = int((time.perf_counter() - t0) * 1000)
            _log(req.session_id, "assistant", content, source=source, script_id=decision.get("script_id"), latency_ms=latency)
            yield _sse({"type": "message", "source": source, "content": content, "script_id": decision.get("script_id")})
            yield _sse({"type": "done"})
            return

        # 2) 무응답(센서 정상·변화없음)
        if source == "none":
            yield _sse({"type": "silent"})
            return

        # 3) LLM 스트리밍
        yield _sse({"type": "thinking"})
        system_prompt = decision.get("system_prompt") or ""
        user_text = req.payload.get("text", "")
        t0 = time.perf_counter()
        full = []
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": MODEL_FAST, "system": system_prompt, "prompt": user_text, "stream": True},
                ) as resp:
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        chunk = json.loads(line)
                        piece = chunk.get("response", "")
                        if piece:
                            full.append(piece)
                            yield _sse({"type": "token", "content": piece})
                        if chunk.get("done"):
                            break
            latency = int((time.perf_counter() - t0) * 1000)
            text = "".join(full).strip()
            _log(req.session_id, "assistant", text, source="llm", model=MODEL_FAST, latency_ms=latency)
            yield _sse({"type": "done", "source": "llm", "latency_ms": latency})
        except Exception as exc:  # LLM 실패 시 한국어 폴백
            from services.data_loader import store
            fail = (store.dialogue.get("errors", {}) or {}).get("llm_fail", "어, 잠시 멈췄어. 다시 물어볼래?")
            _log(req.session_id, "assistant", fail, source="scripted", script_id="errors.llm_fail")
            yield _sse({"type": "message", "source": "scripted", "content": fail, "error": str(exc)})
            yield _sse({"type": "done"})

    return StreamingResponse(gen(), media_type="text/event-stream")
