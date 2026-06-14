#!/usr/bin/env python3
"""Science AI Lab — 첫 부팅 마법사 (설치 직후 1회)

모둠 이름·교사 PIN·학년·단원을 입력받아 .env 에 저장한다.
WiFi 비밀번호는 무작위 생성(학생 비노출, 교사 모드에서 확인).
"""

import random
import string
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"


def ask(q: str, default: str = "") -> str:
    s = input(f"{q}{f' [{default}]' if default else ''}: ").strip()
    return s or default


def main():
    print("=== Science AI Lab 첫 설정 ===")
    team = ask("모둠 이름은? (예: 다람쥐)", "다람쥐")
    pin = ask("교사 PIN 4자리?", "".join(random.choices(string.digits, k=4)))
    grade = ask("기본 학년? (3~6)", "5")
    label = ask("모둠 라벨(SSID용, 예: A)", "A")
    wifi_pw = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))

    ENV.write_text(
        f"TEAM_NAME={team}\nTEACHER_PIN={pin}\nDEFAULT_GRADE={grade}\n"
        f"TEAM_LABEL={label}\nWIFI_SSID=science-lab-{label}\nWIFI_PASSWORD={wifi_pw}\n",
        encoding="utf-8",
    )
    print("\n저장 완료 → .env")
    print(f"  모둠: {team} | 학년: {grade}")
    print(f"  교사 PIN: {pin}   ← 기록하세요")
    print(f"  WiFi: science-lab-{label} / {wifi_pw}   ← 인쇄해서 보관(학생 비노출)")
    print("\n재부팅하면 자동 시작합니다.")


if __name__ == "__main__":
    main()
