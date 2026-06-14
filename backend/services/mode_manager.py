"""Science AI Lab — 모드 관리자 (5가지 모드)

| 모드        | 트리거            | 기본 모델            |
| greeting    | 세션 시작          | 스크립트 우선         |
| onboarding  | 첫 사용·교사 선택   | 스크립트 90%+1b       |
| free_chat   | 자유 질문          | gemma3:1b            |
| experiment  | 실험 진행          | 스크립트 90%+4b       |
| live_data   | MQTT 수신 중       | 룰+1b                |
"""

from __future__ import annotations

MODES = {
    "greeting":   {"label": "인사",   "model": "gemma3:1b", "script_first": True},
    "onboarding": {"label": "첫 수업", "model": "gemma3:1b", "script_first": True},
    "free_chat":  {"label": "자유 대화", "model": "gemma3:1b", "script_first": False},
    "experiment": {"label": "실험 중", "model": "gemma3:1b", "script_first": True},
    "live_data":  {"label": "실시간 데이터", "model": "gemma3:1b", "script_first": True},
}


ONBOARDING_ID = "onboarding-first-class"


def resolve_mode(session: dict) -> str:
    """세션 상태로 현재 모드를 정한다."""
    if not session:
        return "greeting"
    step = session.get("current_step") or 0
    exp_id = session.get("experiment_id")
    if step <= 0:
        return "greeting"
    if exp_id == ONBOARDING_ID:
        return "onboarding"
    if not exp_id:
        return "free_chat"
    return "experiment"
