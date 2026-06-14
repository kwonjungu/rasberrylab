"""Science AI Lab — 응답 라우터 ⭐ (스크립트 80% + LLM 20%)

입력을 보고 '스크립트(0ms) / 룰 / LLM' 을 결정한다.
- 결정적 응답(버튼·진행·다시·안전·정상범위)은 스크립트/룰
- 자유 질문·이상값 해석만 LLM

route() 는 '결정(decision)'만 반환한다. 실제 LLM 스트리밍은 chat 라우터가 수행.
decision = {
  "source": "scripted" | "rule" | "llm" | "none",
  "content": str | None,          # 스크립트/룰일 때 즉답 내용
  "script_id": str | None,        # 어떤 스크립트가 호출됐는지(분석용)
  "system_prompt": str | None,    # source=="llm" 일 때
}
"""

from __future__ import annotations

import random
import re

from . import intent_classifier, sensor_rule_engine
from .data_loader import store
from .prompt_builder import build_system_prompt

# 세션별 '직전에 쓴 배열 인덱스' 기억 → 같은 격려 연속 방지
_last_pick: dict[str, dict[str, int]] = {}


def _render(text: str, session: dict) -> str:
    if not text:
        return text
    exp = store.experiment_by_id(session.get("experiment_id") or "")
    mapping = {
        "team_name": session.get("team_name") or "친구들",
        "step_n": session.get("current_step") or 0,
        "experiment_title": exp.title if exp else "실험",
    }
    for k, v in mapping.items():
        text = text.replace("{" + k + "}", str(v))
    return text


def _pick(session_id: str, key: str, options: list[str]) -> str:
    """배열에서 직전 것 제외하고 랜덤 선택(반복 방지)."""
    if not options:
        return ""
    if len(options) == 1:
        return options[0]
    prev = _last_pick.setdefault(session_id, {}).get(key, -1)
    idx = random.randrange(len(options))
    if idx == prev:
        idx = (idx + 1) % len(options)
    _last_pick[session_id][key] = idx
    return options[idx]


def _dialogue(*path: str):
    node = store.dialogue
    for p in path:
        if not isinstance(node, dict):
            return None
        node = node.get(p)
    return node


class ResponseRouter:
    def route(self, input_type: str, payload: dict, session: dict) -> dict:
        if input_type == "quick_reply":
            return self._quick_reply(payload, session)
        if input_type == "text":
            return self._text(payload, session)
        if input_type == "sensor":
            return self._sensor(payload, session)
        return {"source": "none", "content": None, "script_id": None}

    # ---- 빠른답변 버튼 → 100% 스크립트 ----
    def _quick_reply(self, payload: dict, session: dict) -> dict:
        button_id = payload.get("button_id", "")
        step = store.step_dict(session.get("experiment_id") or "", session.get("current_step") or 0) or {}
        replies = step.get("scripted_replies") or {}

        if button_id == "help":
            return self._scripted(_dialogue("help", "raised"), session, f"help")
        if button_id in replies:
            return self._scripted(replies[button_id], session, f"step.scripted_replies.{button_id}")
        # 기본 버튼 매핑
        fallback = {
            "done": _dialogue("transitions", "to_next_step"),
            "stuck": _dialogue("encouragement", "stuck_first"),
            "repeat": step.get("instruction_student"),
        }.get(button_id)
        if fallback:
            return self._scripted(fallback, session, f"fallback.{button_id}")
        return {"source": "none", "content": None, "script_id": None}

    # ---- 자유 텍스트 → 의도 분류 ----
    def _text(self, payload: dict, session: dict) -> dict:
        text = payload.get("text", "")
        intent = intent_classifier.classify(text)
        step = store.step_dict(session.get("experiment_id") or "", session.get("current_step") or 0) or {}
        replies = step.get("scripted_replies") or {}

        if intent == "danger":
            return self._scripted(self._danger_message(text), session, "safety.warning")
        if intent == "confirm":
            msg = replies.get("done") or _dialogue("transitions", "to_next_step")
            return self._scripted(msg, session, "intent.confirm")
        if intent == "deny":
            return self._scripted(_dialogue("encouragement", "stuck_first"), session, "intent.deny")
        if intent == "repeat":
            msg = replies.get("repeat") or step.get("instruction_student") or _dialogue("errors", "unknown")
            return self._scripted(msg, session, "intent.repeat")
        # question → LLM (RAG가 참고하도록 질문을 세션에 주입)
        session = {**session, "_last_question": text}
        return {"source": "llm", "content": None, "script_id": None, "system_prompt": build_system_prompt(session)}

    def _danger_message(self, text: str) -> str:
        kw = _dialogue("safety", "warning_keywords") or {}
        low = text.lower()
        for word, msg in kw.items():
            if word in low:
                return msg
        return "🛑 위험할 수 있어! 선생님과 함께 확인하자."

    # ---- 센서 데이터 → 룰 우선 ----
    def _sensor(self, payload: dict, session: dict) -> dict:
        step = store.step_dict(session.get("experiment_id") or "", session.get("current_step") or 0) or {}
        values = payload.get("values", {})
        hit = sensor_rule_engine.evaluate(values, step)
        if hit:
            return self._scripted(hit["scripted"], session, f"rule.{hit['sensor']}", source="rule")
        if payload.get("anomaly"):
            return {"source": "llm", "content": None, "script_id": None, "system_prompt": build_system_prompt(session)}
        if payload.get("encourage"):  # 정상 범위, 5초당 1회(호출측에서 throttle)
            opts = _dialogue("encouragement", "data_normal") or []
            return self._scripted(_pick(session.get("id", ""), "data_normal", opts), session, "encouragement.data_normal", source="rule")
        return {"source": "none", "content": None, "script_id": None}  # 무응답(조용히)

    # ---- 공통: 스크립트 결정 생성 ----
    def _scripted(self, text, session: dict, script_id: str, source: str = "scripted") -> dict:
        if isinstance(text, list):
            text = _pick(session.get("id", ""), script_id, text)
        return {"source": source, "content": _render(text or "", session), "script_id": script_id}


router = ResponseRouter()
