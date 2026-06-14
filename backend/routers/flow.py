"""Science AI Lab — 노드 흐름 API + WebSocket (Phase 5)"""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services import ws_hub
from services.data_loader import store
from services.flow_state import NODES

router = APIRouter(prefix="/api/flow", tags=["flow"])

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.environ.get("SCIENCE_AI_MODEL", "gemma3:1b")


def _tier(grade: int | None) -> str:
    return "lower" if grade and grade <= 4 else "upper"


@router.get("/topology")
async def topology():
    return {"nodes": NODES, "explanations_available": bool(store.node_explanations)}


@router.get("/explain/{node_type}")
async def explain(node_type: str, grade: int | None = None):
    node = store.node_explanations.get(node_type)
    if not node:
        return {"error": f"'{node_type}' 노드 설명이 없어요."}
    return {
        "node": node_type,
        "icon": node.get("icon"),
        "title": node.get("title"),
        "text": node.get(_tier(grade), node.get("upper", "")),
    }


@router.post("/explain/{node_type}/llm")
async def explain_llm(node_type: str, grade: int | None = None, experiment_id: str | None = None):
    node = store.node_explanations.get(node_type, {})
    exp = store.experiment_by_id(experiment_id or "")
    tier = "초등 3~4학년" if _tier(grade) == "lower" else "초등 5~6학년"
    ctx = f"지금 실험: {exp.title}." if exp else ""
    prompt = (
        f"'{node.get('title', node_type)}'이 무엇인지 {tier} 학생에게 2~3문장으로, "
        f"쉬운 비유를 들어 설명해줘. {ctx} 어려운 용어는 풀어서."
    )
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/generate",
                       json={"model": LLM_MODEL, "prompt": prompt, "stream": False}, timeout=120)
        r.raise_for_status()
        return {"node": node_type, "text": r.json().get("response", "").strip()}
    except Exception:
        return {"node": node_type, "text": node.get(_tier(grade), "조금 이따 다시 물어봐 줄래?")}


@router.websocket("/ws")
async def ws_flow(ws: WebSocket):
    await ws.accept()
    q = ws_hub.register()
    try:
        while True:
            event = await q.get()
            # flow 관련 이벤트만 전달
            if event.get("type") in ("flow", "flow_error"):
                await ws.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        ws_hub.unregister(q)
