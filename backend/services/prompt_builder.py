"""Science AI Lab — LLM 시스템 프롬프트 조립

학년/단원/보유 센서/현재 실험·단계를 컨텍스트로 주입한다.
LLM은 '자유 질문(20%)'만 담당하므로, 안전·결정적 안내는 하지 않도록 못박는다.
"""

from __future__ import annotations

from .data_loader import store

# 학년대별 응답 길이 제한 (age_adapter와 일관)
_MAX_SENTENCES = {3: 2, 4: 2, 5: 4, 6: 4, 0: 3}


def build_system_prompt(session: dict) -> str:
    grade = session.get("grade") or 0
    exp = store.experiment_by_id(session.get("experiment_id") or "")
    max_sent = _MAX_SENTENCES.get(grade, 3)

    lines = [
        "너는 초등학생 과학 실험을 돕는 친절한 AI 선생님이야.",
        "한 모둠(4명)이 한 화면을 같이 보고 있어. 모둠 전체를 한 명처럼 대하고, 필요하면 역할(실험왕·기록왕·발표왕·안전왕)을 불러도 돼.",
        f"초등학교 {grade}학년 눈높이로, 쉬운 우리말로 말해줘." if grade else "초등학생 눈높이로 쉬운 우리말로 말해줘.",
        f"답은 최대 {max_sent}문장으로 짧고 친근하게. 이미 한 말은 반복하지 마.",
        "지시하기보다 질문으로 호기심을 끌어내. 정답을 바로 주지 말고 스스로 생각하게 도와줘.",
        "⚠️ 안전이 걱정되는 질문(불·전기·콘센트 등)에는 직접 방법을 알려주지 말고, '선생님과 함께하자'고 안내해.",
    ]

    if exp:
        sensors_ko = []
        for sid in exp.required_sensors + exp.optional_sensors + exp.required_actuators:
            s = next((x for x in store.sensors if x.id == sid), None)
            if s:
                sensors_ko.append(s.name_ko)
        lines.append("")
        lines.append(f"[지금 실험] {exp.title}")
        if exp.objectives:
            lines.append(f"[학습 목표] {' / '.join(exp.objectives)}")
        if sensors_ko:
            lines.append(f"[사용 센서] {', '.join(sensors_ko)}")
        step_n = session.get("current_step") or 0
        cur = next((s for s in exp.steps if s.n == step_n), None)
        if cur:
            lines.append(f"[현재 단계 {step_n}] {cur.instruction_student}")
            if cur.llm_coach_prompt:
                lines.append(f"[코칭 방향] {cur.llm_coach_prompt}")
        if exp.llm_system_prompt_addon:
            lines.append(f"[이 실험 특별 지침] {exp.llm_system_prompt_addon}")

    return "\n".join(lines)
