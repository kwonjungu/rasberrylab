"""Science AI Lab — 체크포인트 API (Phase 5)"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services import checkpoint

router = APIRouter(prefix="/api/checkpoints", tags=["checkpoint"])


@router.get("/latest")
async def latest():
    return checkpoint.latest_pending()


class SaveReq(BaseModel):
    session_id: str
    reason: str = "manual"


@router.post("/save")
async def save(req: SaveReq):
    return checkpoint.save(req.session_id, req.reason)


@router.post("/resume/{session_id}")
async def resume(session_id: str):
    return checkpoint.resume(session_id)
