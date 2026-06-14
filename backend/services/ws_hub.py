"""Science AI Lab — WebSocket 브로드캐스트 허브

paho-mqtt 백그라운드 스레드 등 어디서든 publish()로 이벤트를 보내면,
asyncio 루프에 등록된 모든 WebSocket 큐로 안전하게 전달한다.
(스레드 → asyncio 는 loop.call_soon_threadsafe 로 처리)
"""

from __future__ import annotations

import asyncio

_loop: asyncio.AbstractEventLoop | None = None
_queues: set[asyncio.Queue] = set()


def set_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _loop
    _loop = loop


def register() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=200)
    _queues.add(q)
    return q


def unregister(q: asyncio.Queue) -> None:
    _queues.discard(q)


def publish(event: dict) -> None:
    """어느 스레드에서든 호출 가능. 등록된 모든 WS 큐로 전달."""
    if _loop is None:
        return
    for q in list(_queues):
        try:
            _loop.call_soon_threadsafe(q.put_nowait, event)
        except Exception:
            pass
