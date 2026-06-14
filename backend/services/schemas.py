"""Science AI Lab — 데이터 스키마 (Pydantic v2)

sensors / experiments / curriculum / onboarding 4개 JSON의 단일 진실 소스 검증.
모든 모델은 extra="allow" 로 두어, 데이터 진화 과정에서 필드를 더해도
기존 로딩이 깨지지 않게 한다(교사 큐레이션 친화적).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

_CFG = ConfigDict(extra="allow")


# ============================ sensors.json ============================
class Sensor(BaseModel):
    model_config = _CFG

    id: str
    name_ko: str
    name_en: str = ""
    kit_label: str = ""
    category: str
    type: Literal["input", "output"]
    voltage: str = "3.3V or 5V"
    interface: str = "digital"
    wires_required: int = 3
    pin_layout: list[str] = Field(default_factory=list)
    esp_pin_suggested: str = ""
    library: str = ""
    code_snippet_path: str = ""
    wiring_diagram_path: str = ""
    safety_level: Literal["low", "medium", "high"] = "low"
    safety_notes: list[str] = Field(default_factory=list)
    difficulty: int = 1
    first_time_friendly: bool = True
    applicable_unit_ids: list[str] = Field(default_factory=list)
    common_pitfalls: list[str] = Field(default_factory=list)
    student_hint: str = ""
    teacher_note: str = ""


# ========================== curriculum.json ==========================
class AchievementStandard(BaseModel):
    model_config = _CFG
    code: str
    text: str


class Unit(BaseModel):
    model_config = _CFG

    id: str
    title: str
    achievement_standards: list[AchievementStandard] = Field(default_factory=list)
    key_concepts: list[str] = Field(default_factory=list)
    linked_sensor_ids: list[str] = Field(default_factory=list)
    linked_experiment_ids: list[str] = Field(default_factory=list)
    # 성취기준 원문/학기 배치가 확실치 않을 때 True → 교사 확인 대상
    needs_verification: bool = False
    teacher_note: str = ""


class GradeBlock(BaseModel):
    model_config = _CFG
    grade: int
    semester: int = 0  # 0 = 학기 미확정(확인 필요)
    units: list[Unit] = Field(default_factory=list)


class Curriculum(BaseModel):
    model_config = _CFG
    version: str = "2022-revised"
    grades: list[GradeBlock] = Field(default_factory=list)


# ========================= experiments.json =========================
class ExperimentStep(BaseModel):
    model_config = _CFG
    n: int
    instruction_student: str
    duration_sec: int = 60
    image_path: str = ""
    llm_coach_prompt: str = ""
    expected_state: str = ""
    # --- v3.1 응답 라우팅(스크립트 우선) 데이터 ---
    # 버튼/의도별 0ms 즉답 (done/stuck/repeat/timer_80/timer_end 등)
    scripted_replies: dict[str, str] = Field(default_factory=dict)
    # 센서별 임계값 → 정해진 멘트 (룰 엔진이 LLM보다 먼저 처리)
    sensor_thresholds: dict[str, list] = Field(default_factory=dict)
    # 이 단계에서 LLM을 호출할 만한 자유질문 예시 (분류기 테스트용)
    llm_trigger_examples: list[str] = Field(default_factory=list)


class DataViz(BaseModel):
    model_config = _CFG
    type: str = "line_chart"
    x_axis: str = ""
    y_axis: str = ""


class Experiment(BaseModel):
    model_config = _CFG

    id: str
    title: str
    grade: int
    unit_id: str
    achievement_codes: list[str] = Field(default_factory=list)
    difficulty: int = 1
    duration_min: int = 30
    required_sensors: list[str] = Field(default_factory=list)
    optional_sensors: list[str] = Field(default_factory=list)
    required_actuators: list[str] = Field(default_factory=list)
    extra_materials: list[str] = Field(default_factory=list)
    safety_level: Literal["low", "medium", "high"] = "low"
    safety_warnings: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    hypothesis_prompt: str = ""
    steps: list[ExperimentStep] = Field(default_factory=list)
    data_visualization: Optional[DataViz] = None
    post_questions: list[str] = Field(default_factory=list)
    report_template_id: str = "report-basic"
    llm_system_prompt_addon: str = ""


# ========================== onboarding.json =========================
class OnboardingStage(BaseModel):
    model_config = _CFG
    n: int
    title: str
    duration_min: int = 5
    type: str = "intro"
    llm_script: str = ""
    student_action: str = ""
    checkpoint_question: str = ""
    expected_answer_keywords: list[str] = Field(default_factory=list)
    safety_check: list[str] = Field(default_factory=list)
    image_path: str = ""
    expected_state: str = ""


class Onboarding(BaseModel):
    model_config = _CFG
    id: str
    title: str
    duration_min: int = 45
    objectives: list[str] = Field(default_factory=list)
    stages: list[OnboardingStage] = Field(default_factory=list)
    safety_rules: list[str] = Field(default_factory=list)
