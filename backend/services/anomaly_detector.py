"""Science AI Lab — 환각·오답 자동 분류 (Phase 7)

LLM 답변을 규칙으로 점검해 검수 큐 사유를 만든다. '알림만' — 교사 결정이 최종.
"""

from __future__ import annotations

from .data_loader import store

DANGER = ["220v", "콘센트", "감전", "직접 연결"]


def check(answer: str, grade: int | None = None) -> list[str]:
    reasons: list[str] = []
    if not answer:
        return ["빈 답변"]
    a = answer.strip()
    n = len(a)

    if n < 10:
        reasons.append("답변이 너무 짧음")
    if n > 500:
        reasons.append("답변이 너무 김")

    low = a.lower()
    for d in DANGER:
        if d in low:
            reasons.append(f"위험 표현 가능('{d}')")
            break

    # 보유하지 않은 센서/장비 언급 (sensors.json에 없는데 '센서'라 칭함) — 간단 휴리스틱
    known = {s.name_ko for s in store.sensors} | {s.id for s in store.sensors}
    # (정밀 검사는 교사 큐에서. 여기선 명백한 미보유 키워드만)
    for kw in ["카메라", "gps", "자이로", "기압센서"]:
        if kw in low:
            reasons.append(f"미보유 장비 언급 가능('{kw}')")
            break

    # 회피성 답변
    for kw in ["모르겠", "답할 수 없", "잘 모르"]:
        if kw in a:
            reasons.append("회피성 답변 가능")
            break

    return reasons
