"""Science AI Lab — 도움요청 물리 신호 (GPIO 부저·LED)

🤚 버튼을 누르면 부저 1초 + LED 깜빡임. GPIO를 쓸 수 없는 환경(개발 PC,
권한 없음)에서는 화면 깜빡임으로 대체하도록 available=False 를 반환한다.

Pi 5 권장 백엔드: gpiozero (+ lgpio). 부저=GPIO18, LED=GPIO23 (BCM).
"""

from __future__ import annotations

import threading

BUZZER_PIN = 18
LED_PIN = 23

_buzzer = None
_led = None
_available = False
_init_error = ""

try:  # gpiozero 가 있고 GPIO 접근이 되면 사용
    from gpiozero import LED, Buzzer  # type: ignore

    _buzzer = Buzzer(BUZZER_PIN)
    _led = LED(LED_PIN)
    _available = True
except Exception as exc:  # 라이브러리 없음/권한 없음/개발 PC
    _init_error = str(exc)
    _available = False


def is_available() -> bool:
    return _available


def _pulse():
    try:
        if _buzzer:
            _buzzer.on()
        # LED 1초 동안 5회 깜빡
        import time

        for _ in range(5):
            if _led:
                _led.toggle()
            time.sleep(0.1)
        if _buzzer:
            _buzzer.off()
        if _led:
            _led.off()
    except Exception:
        pass


def trigger() -> dict:
    """도움요청 신호 발생. GPIO 가능하면 부저·LED, 아니면 화면 대체 플래그."""
    if _available:
        threading.Thread(target=_pulse, daemon=True).start()
        return {"gpio": True, "fallback": None}
    # GPIO 불가 → 화면에서 🔔 큰 깜빡임으로 대체
    return {"gpio": False, "fallback": "screen_blink", "reason": _init_error or "GPIO 미사용 환경"}


def off() -> None:
    """교사 모드 진입 시 신호 끄기."""
    try:
        if _buzzer:
            _buzzer.off()
        if _led:
            _led.off()
    except Exception:
        pass
