"""Science AI Lab — 익명화 (Phase 7)

영구 저장(임베딩·요약) 전에 학생 식별 정보를 제거한다.
별명·이름 호칭을 일반 호칭으로 치환. IP/MAC/음성/사진은 애초에 저장하지 않음.
"""

from __future__ import annotations

import re

# 역할 호칭은 유지(교육 맥락), 실제 이름만 제거 대상
_NAME_HINT = re.compile(r"[가-힣]{2,4}(이|가|은|는|아|야|님)?\s")


def scrub(text: str, names: list[str] | None = None) -> str:
    """알려진 별명 목록을 '친구'로 치환. 그 외 텍스트는 보존."""
    if not text:
        return text
    out = text
    for n in names or []:
        if n:
            out = out.replace(n, "친구")
    return out
