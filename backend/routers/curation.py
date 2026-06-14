"""Science AI Lab — 큐레이션 + RAG 디버그 + 프롬프트 버전 API (Phase 7)"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from services import curation, embeddings, prompt_evolver, rag, vector_store
from services.db import get_conn

router = APIRouter(prefix="/api", tags=["curation"])


@router.get("/curation/queue")
async def get_queue(status: str = "pending"):
    return {"items": curation.queue(status)}


@router.post("/curation/{cid}/approve")
async def approve(cid: str):
    return curation.approve(cid)


@router.post("/curation/{cid}/reject")
async def reject(cid: str):
    return curation.reject(cid)


class EditReq(BaseModel):
    edited_answer: str


@router.post("/curation/{cid}/edit")
async def edit(cid: str, req: EditReq):
    return curation.edit(cid, req.edited_answer)


class SearchReq(BaseModel):
    question: str
    grade: int | None = None
    unit_id: str | None = None


@router.post("/rag/search")
async def rag_search(req: SearchReq):
    return {"hits": rag.retrieve(req.question, req.grade, req.unit_id), "indexed": vector_store.count()}


@router.get("/prompt_versions")
async def prompt_versions():
    return {"versions": prompt_evolver.versions(), "active_addon": prompt_evolver.active_addon()}


@router.post("/prompt_versions/evolve")
async def evolve():
    return prompt_evolver.evolve()


@router.post("/prompt_versions/{vid}/activate")
async def activate(vid: int):
    return prompt_evolver.activate(vid)


@router.post("/index/rebuild")
async def rebuild():
    """기존 LLM Q&A를 임베딩 백필(승인 전 상태). 가짜/실데이터 모두 대상."""
    added = 0
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT m.content AS answer, m.session_id, s.grade, s.unit_id "
            "FROM messages m JOIN sessions s ON m.session_id=s.id "
            "WHERE m.role='assistant' AND m.response_source='llm' LIMIT 1000"
        ).fetchall()
    for r in rows:
        # 직전 user 질문 찾기는 단순화: 답변 자체를 인덱싱(질문 매칭은 생략)
        vec = embeddings.embed(r["answer"])
        if vec:
            vector_store.add("qa", uuid.uuid4().hex[:12], r["answer"], vec,
                             grade=r["grade"], unit_id=r["unit_id"], answer=r["answer"])
            added += 1
    return {"ok": True, "indexed": added, "total": vector_store.count()}
