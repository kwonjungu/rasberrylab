"""Science AI Lab — 데이터 로더 + 무결성 검증

4개 JSON을 부팅 시 메모리에 로드하고 Pydantic으로 스키마를 검증한다.
또한 상호참조(실험→센서, 실험→단원, 단원→센서)를 점검해
'사람이 직접 편집하는 데이터'에서 흔한 오타·누락을 한국어로 알려준다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .schemas import Curriculum, Experiment, Onboarding, Sensor

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class DataStore:
    """로드된 데이터 + 검증 결과를 담는 단일 저장소."""

    def __init__(self) -> None:
        self.sensors: list[Sensor] = []
        self.experiments: list[Experiment] = []
        self.curriculum: Curriculum | None = None
        self.onboarding: Onboarding | None = None
        self.dialogue: dict = {}  # dialogue_templates.json (전역 스크립트)
        self.node_explanations: dict = {}  # node_explanations.json (Phase 5)
        # 로드/검증 중 발생한 문제들 (한국어 메시지)
        self.errors: list[str] = []
        self.warnings: list[str] = []

    # ---------- 조회 도우미: 실험/스텝 ----------
    def experiment_by_id(self, exp_id: str) -> Experiment | None:
        for e in self.experiments:
            if e.id == exp_id:
                return e
        return None

    def step_dict(self, exp_id: str, step_n: int) -> dict | None:
        exp = self.experiment_by_id(exp_id)
        if not exp:
            return None
        for s in exp.steps:
            if s.n == step_n:
                return s.model_dump()
        return None

    # ---------- 로드 ----------
    def _read_json(self, name: str) -> Any:
        path = DATA_DIR / name
        if not path.exists():
            self.errors.append(f"❌ {name} 파일이 없어요: {path}")
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.errors.append(
                f"❌ {name} 의 JSON 형식이 잘못됐어요 (줄 {exc.lineno}, 칸 {exc.colno}): {exc.msg}"
            )
            return None

    def load(self) -> "DataStore":
        self.errors.clear()
        self.warnings.clear()

        # sensors
        raw = self._read_json("sensors.json")
        if isinstance(raw, list):
            for i, item in enumerate(raw):
                try:
                    self.sensors.append(Sensor(**item))
                except ValidationError as e:
                    self.errors.append(f"❌ sensors.json {i}번째 항목 오류: {_fmt(e)}")

        # curriculum
        raw = self._read_json("curriculum.json")
        if isinstance(raw, dict):
            try:
                self.curriculum = Curriculum(**raw)
            except ValidationError as e:
                self.errors.append(f"❌ curriculum.json 오류: {_fmt(e)}")

        # experiments
        raw = self._read_json("experiments.json")
        if isinstance(raw, list):
            for i, item in enumerate(raw):
                try:
                    self.experiments.append(Experiment(**item))
                except ValidationError as e:
                    self.errors.append(f"❌ experiments.json {i}번째 항목 오류: {_fmt(e)}")

        # onboarding
        raw = self._read_json("onboarding.json")
        if isinstance(raw, dict):
            try:
                self.onboarding = Onboarding(**raw)
            except ValidationError as e:
                self.errors.append(f"❌ onboarding.json 오류: {_fmt(e)}")

        # dialogue_templates (전역 스크립트) — 선택적
        raw = self._read_json("dialogue_templates.json")
        if isinstance(raw, dict):
            self.dialogue = raw

        # node_explanations (노드 설명) — 선택적
        raw = self._read_json("node_explanations.json")
        if isinstance(raw, dict):
            self.node_explanations = raw

        self._cross_validate()
        return self

    # ---------- 상호참조 검증 ----------
    def _cross_validate(self) -> None:
        sensor_ids = {s.id for s in self.sensors}
        unit_ids = set(self.unit_index().keys())

        # 실험이 참조하는 센서/액추에이터/단원이 실제 존재하는가
        for exp in self.experiments:
            for sid in exp.required_sensors + exp.optional_sensors + exp.required_actuators:
                if sid not in sensor_ids:
                    self.errors.append(
                        f"❌ 실험 '{exp.id}' 가 없는 센서 '{sid}' 를 참조해요. sensors.json 확인 필요."
                    )
            if exp.unit_id not in unit_ids:
                self.errors.append(
                    f"❌ 실험 '{exp.id}' 의 단원 '{exp.unit_id}' 가 curriculum.json 에 없어요."
                )

        # 단원이 참조하는 센서/실험 존재 여부
        exp_ids = {e.id for e in self.experiments}
        for uid, unit in self.unit_index().items():
            for sid in unit.linked_sensor_ids:
                if sid not in sensor_ids:
                    self.warnings.append(
                        f"⚠️ 단원 '{uid}' 가 없는 센서 '{sid}' 를 가리켜요."
                    )
            for eid in unit.linked_experiment_ids:
                if eid not in exp_ids:
                    self.warnings.append(
                        f"⚠️ 단원 '{uid}' 가 아직 없는 실험 '{eid}' 를 가리켜요(작성 예정일 수 있음)."
                    )

    # ---------- 조회 도우미 ----------
    def unit_index(self) -> dict[str, Any]:
        idx: dict[str, Any] = {}
        if self.curriculum:
            for gb in self.curriculum.grades:
                for u in gb.units:
                    idx[u.id] = u
        return idx

    def unused_sensors(self) -> list[str]:
        used: set[str] = set()
        for e in self.experiments:
            used.update(e.required_sensors + e.optional_sensors + e.required_actuators)
        for u in self.unit_index().values():
            used.update(u.linked_sensor_ids)
        return sorted(s.id for s in self.sensors if s.id not in used)

    def units_without_experiments(self) -> list[str]:
        covered = {e.unit_id for e in self.experiments}
        return sorted(uid for uid in self.unit_index() if uid not in covered)

    def experiments_per_grade(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for e in self.experiments:
            out[e.grade] = out.get(e.grade, 0) + 1
        return dict(sorted(out.items()))

    def report(self) -> dict[str, Any]:
        """/api/data/validate 용 무결성 리포트."""
        return {
            "ok": len(self.errors) == 0,
            "counts": {
                "sensors": len(self.sensors),
                "experiments": len(self.experiments),
                "units": len(self.unit_index()),
                "onboarding_stages": len(self.onboarding.stages) if self.onboarding else 0,
            },
            "experiments_per_grade": self.experiments_per_grade(),
            "unused_sensors": self.unused_sensors(),
            "units_without_experiments": self.units_without_experiments(),
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _fmt(e: ValidationError) -> str:
    parts = []
    for err in e.errors():
        loc = ".".join(str(x) for x in err["loc"])
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


# 모듈 전역 단일 인스턴스 (FastAPI 부팅 시 load 호출)
store = DataStore()
