"""Science AI Lab — RAG 검색 (Phase 7)

학생 자유 질문 → 과거 승인 사례 top-3 → LLM 시스템 프롬프트 컨텍스트.
스크립트·룰이 우선이므로 question 의도일 때만 호출(response_router에서 결정).
"""

from __future__ import annotations

from . import embeddings, vector_store


def retrieve(question: str, grade=None, unit_id=None, top_k: int = 3) -> list[dict]:
    vec = embeddings.embed(question)
    if not vec:
        return []
    hits = vector_store.search(vec, top_k=top_k, grade=grade, unit_id=unit_id)
    # 유사도가 너무 낮으면 버림(관련 없는 과거 사례 주입 방지)
    return [h for h in hits if h["raw_sim"] >= 0.5]


def context_block(question: str, grade=None, unit_id=None) -> str:
    hits = retrieve(question, grade, unit_id)
    if not hits:
        return ""
    lines = ["[참고: 과거 비슷한 질문에 좋았던 답변 예시]"]
    for h in hits:
        if h.get("answer"):
            lines.append(f"- 질문 \"{h['content'][:40]}\" → \"{h['answer'][:80]}\"")
    return "\n".join(lines) if len(lines) > 1 else ""
