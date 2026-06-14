"""Science AI Lab — 안전수칙 복창 흐름

실험 시작 직전 자동 트리거. 안전수칙(experiments.json의 safety_warnings)을
큰 글씨로 보여주고, 모두 ✅(복창) 해야 실험이 시작된다.
안전 메시지는 LLM을 거치지 않고 항상 스크립트(토씨까지 동일).
"""

from __future__ import annotations

from .data_loader import store


def build_ritual(experiment_id: str) -> dict:
    exp = store.experiment_by_id(experiment_id or "")
    intro = (store.dialogue.get("safety", {}) or {}).get("before_experiment", "실험 시작 전, 안전 약속을 다같이 외쳐보자!")
    call = (store.dialogue.get("safety", {}) or {}).get("ritual_call", "다같이 따라 읽어요. 첫째!")
    rules = list(exp.safety_warnings) if exp else []
    if not rules:
        rules = ["센서 갈아끼울 땐 USB 먼저 빼기", "보드가 뜨거우면 즉시 USB 빼고 선생님 부르기"]
    return {
        "intro": intro,
        "call": call,
        "rules": rules,
        "required": True,
        "safety_level": exp.safety_level if exp else "low",
    }
