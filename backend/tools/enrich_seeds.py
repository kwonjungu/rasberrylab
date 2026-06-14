"""시드 실험 10개에 v3.1 라우팅 데이터(scripted_replies/sensor_thresholds)를 보강.

이미 필드가 있는 step(새 실험 4개)은 건드리지 않는다. 1회용 마이그레이션.
실행: .venv/bin/python -m tools.enrich_seeds
"""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "experiments.json"

# 공통 기본 빠른답변 (각 실험에 맞게 done 문구만 살짝 다름)
def replies(done, stuck, repeat_hint):
    return {
        "done": done,
        "stuck": stuck,
        "repeat": repeat_hint,
        "timer_80": "거의 다 됐어! 조금만 더 ⏳",
        "timer_end": "시간 다 됐어. 다 했으면 ✅ 눌러줘.",
    }


ENRICH = {
    "exp-3-magnet-distance": {
        "replies": replies("좋아! 🧲 자석을 조금씩 움직이며 값을 살펴보자.", "괜찮아, 센서 핀이 잘 꽂혔는지 같이 볼까?", "다시! 자석을 센서 가까이 댔다가 천천히 멀리해줘."),
        "threshold_step": 3,
        "thresholds": {"magnetic": [
            {"range": "> 650", "scripted": "자석이 가까워서 신호가 세! 🧲"},
            {"range": "350 ~ 650", "scripted": "보통 세기야."},
            {"range": "< 350", "scripted": "자석이 멀어서 신호가 약해 ✨"}]},
    },
    "exp-3-sound-clap": {
        "replies": replies("잘했어! 👏 박수 세기를 바꿔가며 값을 비교해보자.", "센서가 조용할 때 값을 먼저 확인해볼까?", "다시! 작게·보통·크게 박수를 쳐보자."),
        "threshold_step": 2,
        "thresholds": {"sound": [
            {"range": "> 600", "scripted": "소리가 커! 📢"},
            {"range": "300 ~ 600", "scripted": "보통 소리야."},
            {"range": "< 300", "scripted": "조용하네 🤫"}]},
    },
    "exp-3-ice-melt-temp": {
        "replies": replies("좋아! ❄️ 1분마다 온도를 기록해보자.", "센서 끝만 얼음물에 살짝 담갔는지 확인해줘.", "다시! 온도 센서를 얼음물에 살짝 담가줘."),
        "threshold_step": 2,
        "thresholds": {"temperature": [
            {"range": "> 5", "scripted": "아직 차가워지는 중이야 🥶"},
            {"range": "0 ~ 5", "scripted": "이제 곧 얼겠다! 👀"},
            {"range": "< 0", "scripted": "와! 얼음이 되고 있어 ❄️"}]},
    },
    "exp-4-shadow-light-block": {
        "replies": replies("잘했어! 🔦 물체로 빛을 가리며 값을 비교해보자.", "센서에 빛이 잘 닿는지 먼저 확인해볼까?", "다시! 손전등을 센서에 비춰줘."),
        "threshold_step": 2,
        "thresholds": {"light": [
            {"range": "> 700", "scripted": "아주 밝아! ☀️"},
            {"range": "300 ~ 700", "scripted": "적당한 밝기야."},
            {"range": "< 300", "scripted": "어두워졌어 🌙 그림자가 생겼나봐."}]},
    },
    "exp-4-vibration-shock": {
        "replies": replies("좋아! 📳 책상을 살살·세게 흔들어보자.", "충격 센서와 부저가 잘 연결됐는지 볼까?", "다시! 책상을 흔들어 충격을 만들어줘."),
        "threshold_step": 2,
        "thresholds": {"shock": [
            {"range": "== 1", "scripted": "💥 흔들림 감지! 지진이다!"}]},
    },
    "exp-5-insulation-compare": {
        "replies": replies("잘했어! ♨️ 재료별로 식는 속도를 비교해보자.", "물이 너무 뜨겁지 않은지 컵 바깥을 만져 확인해줘.", "다시! 따뜻한 물에 센서를 넣고 온도를 읽어줘."),
        "threshold_step": 2,
        "thresholds": {"temperature": [
            {"range": "> 35", "scripted": "아직 따뜻해 ♨️"},
            {"range": "25 ~ 35", "scripted": "조금씩 식고 있어."},
            {"range": "< 25", "scripted": "많이 식었네 🧊"}]},
    },
    "exp-6-auto-light": {
        "replies": replies("좋아! 💡 센서를 가려 어둡게 만들어보자.", "릴레이 고전압 단자엔 아무것도 연결 안 했지? 확인!", "다시! 조도 센서를 손으로 가려봐."),
        "threshold_step": 2,
        "thresholds": {"light": [
            {"range": "< 300", "scripted": "🌙 어두워졌어! 불을 켤 시간."},
            {"range": ">= 300", "scripted": "☀️ 아직 밝아. 불은 꺼둬도 돼."}]},
    },
    "exp-6-heartbeat": {
        "replies": replies("좋아! 💗 손가락을 살짝 대고 박동을 느껴보자.", "손가락을 너무 세게 누르지 말고 살짝 대줘.", "다시! 손가락을 심박 센서에 살짝 대줘."),
        "threshold_step": 2,
        "thresholds": {"heartbeat": [
            {"range": "> 120", "scripted": "심장이 빨리 뛰어! 운동했구나 🏃"},
            {"range": "60 ~ 120", "scripted": "평소 심장박동이야 💗"},
            {"range": "< 60", "scripted": "천천히 다시 측정해볼까?"}]},
    },
    "exp-6-color-mixing": {
        "replies": replies("좋아! 🌈 색을 하나씩, 그다음 섞어서 켜보자.", "RGB 핀 세 개(R·G·B)가 잘 꽂혔는지 볼까?", "다시! 빨강부터 하나씩 켜보자."),
        "threshold_step": None,
        "thresholds": {},
    },
    "exp-5-motion-ultrasonic": {
        "replies": replies("좋아! 🚗 차를 굴리며 거리 그래프를 보자.", "Echo 핀에 분압저항을 연결했는지 꼭 확인!", "다시! 차를 출발선에 놓고 굴려줘."),
        "threshold_step": 2,
        "thresholds": {"distance_cm": [
            {"range": "> 50", "scripted": "멀리 있어 🚗💨"},
            {"range": "10 ~ 50", "scripted": "점점 가까워지고 있어!"},
            {"range": "< 10", "scripted": "거의 도착! 🏁"}]},
    },
}


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    touched = 0
    for exp in data:
        cfg = ENRICH.get(exp["id"])
        if not cfg:
            continue
        for step in exp.get("steps", []):
            if not step.get("scripted_replies"):
                step["scripted_replies"] = cfg["replies"]
                touched += 1
            if cfg.get("threshold_step") == step.get("n") and not step.get("sensor_thresholds"):
                step["sensor_thresholds"] = cfg["thresholds"]
            step.setdefault("llm_trigger_examples", [])
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"보강 완료: {touched}개 step에 scripted_replies 추가")


if __name__ == "__main__":
    main()
