# -*- coding: utf-8 -*-
"""Science AI Lab — 삽화 에셋 생성기 (외부 자문 보강)
data/*.json 이 참조하지만 실제로는 없던 SVG 들을 frontend/assets 아래에 실제 생성한다.
 - steps/      : 실험 단계 삽화 34종 (이모지 장면 카드)
 - onboarding/ : 온보딩 삽화 2종
 - wiring/     : 센서 배선 카드 42종 (빵판 다이어그램)
모두 480x320, UI 팔레트(파랑/초록/주황)에 맞춘 부드러운 플랫 스타일.
"""
from __future__ import annotations
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # ScienceLab/
ASSETS = ROOT / "frontend" / "assets"

# 부드러운 파스텔 배경(테마군별)
BG = {
    "blue":   ("#eaf2ff", "#d6e4ff"),
    "green":  ("#e8f9ee", "#cdeed7"),
    "amber":  ("#fff4e2", "#ffe3bd"),
    "pink":   ("#ffeef4", "#ffd6e4"),
    "purple": ("#f1edff", "#ddd2ff"),
    "cyan":   ("#e6fbff", "#c9f1f7"),
}

def scene(primary: str, accents: list[str], caption: str, theme: str = "blue") -> str:
    c1, c2 = BG[theme]
    acc = ""
    # 보조 이모지: 큰 이모지 우상단/좌하단에 배치
    pos = [(360, 110, 56), (110, 250, 52)]
    for i, e in enumerate(accents[:2]):
        x, y, s = pos[i]
        acc += f'<text x="{x}" y="{y}" font-size="{s}" text-anchor="middle">{e}</text>\n  '
    cap = html.escape(caption)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 320" width="480" height="320" role="img" aria-label="{cap}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <filter id="sh" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#1f2a44" flood-opacity="0.14"/>
    </filter>
  </defs>
  <rect x="6" y="6" width="468" height="308" rx="28" fill="url(#bg)" stroke="#ffffff" stroke-width="4"/>
  <circle cx="70" cy="64" r="26" fill="#ffffff" opacity="0.5"/>
  <circle cx="420" cy="250" r="34" fill="#ffffff" opacity="0.45"/>
  <text x="240" y="196" font-size="150" text-anchor="middle" filter="url(#sh)">{primary}</text>
  {acc}
  <rect x="40" y="250" width="400" height="46" rx="23" fill="#ffffff" opacity="0.92"/>
  <text x="240" y="281" font-size="24" font-weight="700" text-anchor="middle"
        font-family="'Noto Sans KR','Malgun Gothic',sans-serif" fill="#1f2a44">{cap}</text>
</svg>'''

# ---------------- 단계 삽화 ----------------
STEPS = {
  "linear-hall-plug":   ("🔌", ["🧲"], "센서를 빵판에 꽂아요", "blue"),
  "magnet-1cm":         ("🧲", ["📏"], "자석을 1cm 가까이 대요", "blue"),
  "magnet-far":         ("🧲", ["↔️"], "자석을 멀리 떨어뜨려요", "blue"),
  "sound-quiet":        ("🤫", ["🔈"], "조용할 때 소리를 재요", "cyan"),
  "sound-clap":         ("👏", ["🔊"], "박수로 큰 소리를 내요", "cyan"),
  "ice-sensor":         ("🌡️", ["🧊"], "얼음에 온도센서를 넣어요", "cyan"),
  "ice-melt":           ("🧊", ["💧"], "얼음이 녹는 걸 지켜봐요", "cyan"),
  "light-bright":       ("💡", ["☀️"], "밝은 빛을 측정해요", "amber"),
  "light-block":        ("🌑", ["✋"], "빛을 손으로 가려요", "purple"),
  "shock-buzzer":       ("🔔", ["⚡"], "충격센서와 부저를 연결", "amber"),
  "shake-table":        ("🫨", ["🌋"], "책상을 흔들어 보아요", "amber"),
  "warm-water":         ("♨️", ["🥤"], "따뜻한 물을 담아요", "pink"),
  "insulation":         ("🧣", ["🥤"], "컵을 감싸 보온해요", "pink"),
  "ultrasonic-setup":   ("📡", ["📦"], "초음파 센서를 설치해요", "blue"),
  "car-roll":           ("🚗", ["⬇️"], "자동차를 굴려요", "green"),
  "calc-speed":         ("🧮", ["⏱️"], "거리와 시간으로 속도 계산", "green"),
  "auto-light-wire":    ("💡", ["🔌"], "자동 전등 회로를 연결", "amber"),
  "cover-sensor":       ("✋", ["📦"], "센서를 가려 보아요", "purple"),
  "heartbeat-rest":     ("❤️", ["😌"], "쉴 때 심장박동을 재요", "pink"),
  "heartbeat-exercise": ("🏃", ["❤️"], "운동 뒤 심장박동을 재요", "pink"),
  "rgb-red":            ("🔴", ["💡"], "빨강 빛을 켜 보아요", "pink"),
  "rgb-mix":            ("🌈", ["💡"], "빛의 색을 섞어 보아요", "purple"),
  "rc-build":           ("🏎️", ["🔧"], "RC카를 조립해요", "green"),
  "rc-run":             ("🏎️", ["💨"], "RC카를 달려요", "green"),
  "rc-crash":           ("💥", ["🏎️"], "충돌 충격을 측정해요", "amber"),
  "door-build":         ("🚪", ["🔧"], "자동문을 만들어요", "blue"),
  "door-open":          ("🚪", ["🚶"], "문이 스스로 열려요", "blue"),
  "self-driving-build": ("🤖", ["🚗"], "자율주행차를 조립해요", "purple"),
  "follow-line":        ("🛣️", ["🤖"], "검은 선을 따라가요", "purple"),
  "avoid-obstacle":     ("🚧", ["🤖"], "장애물을 피해요", "purple"),
  "soil-sensor":        ("🌱", ["🪴"], "흙 수분 센서를 꽂아요", "green"),
  "auto-water":         ("💧", ["🌱"], "자동으로 물을 줘요", "green"),
  # 화면 흐름 보조(혹시 모를 참조)
  "warm-cup":           ("☕", ["🌡️"], "따뜻한 컵을 준비해요", "pink"),
}

ONBOARDING = {
  "breadboard-power":   ("🔋", ["🟢"], "빵판에 전원을 연결해요", "green"),
  "dht11-connect":      ("🌡️", ["🔌"], "온습도 센서를 연결해요", "blue"),
}

# ---------------- 센서 배선 카드 ----------------
# 색상 팔레트(센서 칩 색)
WIRE_COLOR = {"blue": "#3b82f6", "green": "#22c55e", "amber": "#f59e0b", "red": "#ef4444", "purple": "#8b5cf6"}

WIRING = {
  "dht11": ("DHT11", "온습도", "green"),
  "ds18b20": ("DS18B20", "방수 온도", "blue"),
  "analog_temp": ("Analog Temp", "아날로그 온도", "blue"),
  "temp_basic": ("Thermistor", "기본 온도", "blue"),
  "photoresistor": ("LDR", "빛 센서", "amber"),
  "light_blocking": ("Light Block", "빛 차단", "purple"),
  "laser": ("Laser", "레이저", "red"),
  "flame": ("Flame", "불꽃", "red"),
  "ir_emission": ("IR TX", "적외선 송신", "purple"),
  "ir_receiver": ("IR RX", "적외선 수신", "purple"),
  "avoid_ir": ("Avoid IR", "장애물 감지", "purple"),
  "tracking": ("Tracking", "라인 추적", "purple"),
  "hc_sr04": ("HC-SR04", "초음파 거리", "blue"),
  "linear_hall": ("Linear Hall", "자기장 세기", "blue"),
  "hall_magnetic": ("Hall", "자기 감지", "blue"),
  "analog_hall": ("Analog Hall", "아날로그 자기", "blue"),
  "reed_switch": ("Reed", "리드 스위치", "blue"),
  "mini_reed": ("Mini Reed", "미니 리드", "blue"),
  "big_sound": ("Big Sound", "큰 소리", "amber"),
  "small_sound": ("Small Sound", "작은 소리", "amber"),
  "passive_buzzer": ("Passive Buzzer", "수동 부저", "amber"),
  "active_buzzer": ("Active Buzzer", "능동 부저", "amber"),
  "tap": ("Tap", "두드림", "amber"),
  "touch": ("Touch", "터치", "green"),
  "button": ("Button", "버튼", "green"),
  "tilt": ("Tilt", "기울기", "amber"),
  "ball_switch": ("Ball Switch", "구슬 스위치", "amber"),
  "shock": ("Shock", "충격", "amber"),
  "vibration": ("Vibration", "진동", "amber"),
  "rotary_encoder": ("Encoder", "회전 엔코더", "green"),
  "joystick": ("Joystick", "조이스틱", "green"),
  "relay": ("Relay", "릴레이", "red"),
  "dc_motor": ("DC Motor", "DC 모터", "green"),
  "rgb_led": ("RGB LED", "RGB 발광", "purple"),
  "smd_rgb": ("SMD RGB", "SMD 발광", "purple"),
  "seven_color_flash": ("7-Color", "무지개 LED", "purple"),
  "two_color_led": ("2-Color LED", "두색 발광", "purple"),
  "two_color_led_small": ("2-Color S", "두색 소형", "purple"),
  "light_cup": ("Light Cup", "광 컵", "amber"),
  "soil_moisture": ("Soil", "토양 수분", "green"),
  "heartbeat": ("Heartbeat", "심박", "red"),
}

def wiring_card(chip: str, ko: str, theme: str) -> str:
    col = WIRE_COLOR[theme]
    chip = html.escape(chip); ko = html.escape(ko)
    # 빵판 구멍
    holes = ""
    for r in range(4):
        for c in range(12):
            holes += f'<circle cx="{70+c*28}" cy="{150+r*22}" r="3.2" fill="#cbd5e1"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 320" width="480" height="320" role="img" aria-label="{ko} 배선">
  <rect x="6" y="6" width="468" height="308" rx="28" fill="#f7faff" stroke="#e2e8f0" stroke-width="4"/>
  <rect x="36" y="26" width="408" height="48" rx="14" fill="{col}"/>
  <text x="58" y="57" font-size="24" font-weight="800" fill="#fff"
        font-family="'Noto Sans KR','Malgun Gothic',sans-serif">{ko}</text>
  <text x="426" y="56" font-size="16" fill="#ffffff" opacity="0.9" text-anchor="end"
        font-family="monospace">{chip}</text>
  <!-- 센서 모듈 -->
  <rect x="60" y="96" width="150" height="64" rx="12" fill="{col}" opacity="0.92"/>
  <text x="135" y="135" font-size="18" font-weight="700" fill="#fff" text-anchor="middle"
        font-family="monospace">{chip}</text>
  <!-- 점퍼선 3개(빨강/검정/노랑) -->
  <path d="M210 112 C 280 100, 300 150, 360 150" stroke="#ef4444" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M210 130 C 280 140, 300 172, 360 172" stroke="#111827" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M210 148 C 280 180, 300 196, 360 194" stroke="#f59e0b" stroke-width="5" fill="none" stroke-linecap="round"/>
  <!-- 빵판 -->
  <rect x="52" y="186" width="376" height="104" rx="14" fill="#eef2f9" stroke="#dbe3ef" stroke-width="3"/>
  {holes}
  <text x="240" y="306" font-size="13" fill="#94a3b8" text-anchor="middle"
        font-family="'Noto Sans KR',sans-serif">빨강=VCC · 검정=GND · 노랑=신호</text>
</svg>'''


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main():
    n = 0
    for name, (p, a, cap, th) in STEPS.items():
        write(ASSETS / "steps" / f"{name}.svg", scene(p, a, cap, th)); n += 1
    for name, (p, a, cap, th) in ONBOARDING.items():
        write(ASSETS / "onboarding" / f"{name}.svg", scene(p, a, cap, th)); n += 1
    for name, (chip, ko, th) in WIRING.items():
        write(ASSETS / "wiring" / f"{name}.svg", wiring_card(chip, ko, th)); n += 1
    print(f"생성 완료: {n}개 SVG → {ASSETS}")


if __name__ == "__main__":
    main()
