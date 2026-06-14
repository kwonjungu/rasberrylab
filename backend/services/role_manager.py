"""Science AI Lab — 역할 카드 (모둠 4명)

수업 시작 시 4명이 역할을 고른다. LLM·스크립트가 역할을 호명한다.
별명(이름)은 세션 종료 시 NULL — 개인정보 영구저장 금지.
"""

from __future__ import annotations

ROLE_CARDS = [
    {"id": "experiment", "icon": "🔬", "name": "실험왕", "desc": "센서를 연결하고 실험을 직접 해요."},
    {"id": "record", "icon": "📝", "name": "기록왕", "desc": "데이터를 적고 발문에 답해요."},
    {"id": "present", "icon": "🎤", "name": "발표왕", "desc": "AI에게 질문하고 말로 답해요."},
    {"id": "safety", "icon": "🛡", "name": "안전왕", "desc": "안전 약속을 확인하고 도움을 요청해요."},
]

_ROLE_BY_ID = {r["id"]: r for r in ROLE_CARDS}


def call_role(role_id: str, what: str) -> str:
    """'기록왕은 지금 시간을 적어줘' 처럼 역할 호명 문구 생성."""
    r = _ROLE_BY_ID.get(role_id)
    name = r["name"] if r else "친구"
    return f"{name}은(는) {what}"


def rotation_hint() -> str:
    return "5분이 지났어! 역할을 한 칸씩 바꿔볼까? 🔄"
