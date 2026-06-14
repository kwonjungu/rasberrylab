"""Science AI Lab — 의도 분류기 (간단 버전, 머신러닝 없음)

정규식 + 키워드 사전으로 학생의 자유 텍스트를 5개 의도로 분류한다.
미분류는 무조건 'question' → LLM 폴백. (확실한 것만 스크립트로 처리)

의도:
- confirm  : 긍정/진행 ("응", "네", "다음")    → 스크립트
- deny     : 부정 ("아니", "싫어")             → 스크립트
- repeat   : 다시/모름 ("다시", "몰라")         → 스크립트
- danger   : 위험 키워드 ("불", "콘센트")        → 스크립트(강한 경고)
- question : 그 외 전부 (의문사 포함)           → LLM
"""

from __future__ import annotations

import re

Intent = str  # "confirm" | "deny" | "repeat" | "danger" | "question"

# 위험 키워드는 최우선 (안전 관련은 LLM 절대 불신)
DANGER_WORDS = ["불", "촛불", "콘센트", "감전", "220v", "220볼트", "전기충격", "타는 냄새", "연기"]

CONFIRM_EXACT = {"응", "네", "넹", "예", "옙", "다음", "ㅇㅇ", "ok", "오케이", "고고", "좋아", "했어", "했어요", "완료"}
DENY_EXACT = {"아니", "아니요", "아니오", "no", "싫어", "안 했어", "못했어", "안돼"}

REPEAT_PATTERNS = [r"다시", r"모르", r"몰라", r"뭐라고", r"못\s*들었", r"한\s*번\s*더", r"다신"]
QUESTION_WORDS = ["왜", "어떻게", "무엇", "뭐", "뭔", "어디", "언제", "누가", "어느", "얼마", "몇", "?", "까", "을까", "ㄹ까"]


def classify(text: str) -> Intent:
    if text is None:
        return "question"
    t = text.strip().lower()
    if not t:
        return "question"

    # 1순위: 위험 키워드
    for w in DANGER_WORDS:
        if w in t:
            return "danger"

    # 2순위: 정확 일치 긍정/부정 (짧은 발화)
    norm = t.rstrip("!.~ ")
    if norm in CONFIRM_EXACT:
        return "confirm"
    if norm in DENY_EXACT:
        return "deny"

    # 3순위: 다시/모름
    for p in REPEAT_PATTERNS:
        if re.search(p, t):
            return "repeat"

    # 4순위: 의문사/물음표 → 질문(LLM)
    for w in QUESTION_WORDS:
        if w in t:
            return "question"

    # 짧은 긍정형(부분 포함) 보정: "응 다음", "네 했어요"
    if any(t.startswith(c) for c in ("응", "네", "예", "다음", "좋아", "했")):
        return "confirm"

    # 미분류 → LLM
    return "question"


# ----- 내장 단위 테스트 (python -m services.intent_classifier 로 실행) -----
TEST_CASES = [
    ("응", "confirm"),
    ("네 다음으로 갈래요", "confirm"),
    ("아니요", "deny"),
    ("다시 알려줘", "repeat"),
    ("잘 모르겠어요", "repeat"),
    ("불이 났어요", "danger"),
    ("콘센트 만져도 돼요?", "danger"),
    ("왜 자석이 약해져요?", "question"),
    ("이거 어떻게 해요", "question"),
    ("자기장이 뭐예요?", "question"),
]


def _run_tests() -> int:
    fails = 0
    for text, expected in TEST_CASES:
        got = classify(text)
        ok = got == expected
        if not ok:
            fails += 1
        print(f"[{'OK ' if ok else 'FAIL'}] {text!r:30} → {got:9} (기대: {expected})")
    print(f"\n결과: {len(TEST_CASES) - fails}/{len(TEST_CASES)} 통과")
    return fails


if __name__ == "__main__":
    import sys

    sys.exit(1 if _run_tests() else 0)
