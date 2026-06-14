"""Science AI Lab — 리플레이 API (Phase 5)

종료된 세션을 SSE로 배속 재생. 교사 도구.
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services import replay

router = APIRouter(prefix="/api/replay", tags=["replay"])


@router.get("/sessions")
async def sessions():
    return {"sessions": replay.sessions()}


@router.get("/{session_id}/stream")
async def stream(session_id: str, speed: float = 2.0, max_gap: float = 2.0):
    """offset 간격을 speed로 나눠 SSE 송출. 간격은 max_gap로 상한(빈 구간 점프)."""
    events = replay.timeline(session_id)

    async def gen():
        if not events:
            yield f"data: {json.dumps({'type':'empty'})}\n\n"
            return
        yield f"data: {json.dumps({'type':'start','total':len(events)}, ensure_ascii=False)}\n\n"
        prev = 0.0
        for e in events:
            gap = min(max(e["offset"] - prev, 0), max_gap) / max(speed, 0.1)
            if gap > 0:
                await asyncio.sleep(gap)
            prev = e["offset"]
            yield f"data: {json.dumps(e, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type':'end'})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
