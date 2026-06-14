#!/bin/bash
# Science AI Lab — 전체 설치 (새 Pi 또는 갱신). 콘솔에서 실행 권장.
set -e
ROOT="/mnt/nvme/projects/science-ai"
echo "==> Science AI Lab 설치 시작"

# 1. 시스템 패키지
sudo apt update
sudo apt install -y python3-venv python3-pip mosquitto mosquitto-clients \
  hostapd dnsmasq avahi-daemon chromium fonts-noto-cjk || true

# 2. venv + 의존성
cd "$ROOT/backend"
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

# 3. GPIO(옵션) — 도움요청 부저/LED
./.venv/bin/pip install gpiozero lgpio 2>/dev/null || echo "  (gpiozero 생략 — 화면 깜빡임 폴백)"

# 4. systemd 서비스 등록
sudo cp "$ROOT"/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mosquitto ollama 2>/dev/null || true
sudo systemctl enable science-ai-backend science-ai-warmup science-ai-watchdog
sudo systemctl restart science-ai-backend

# 4-1. 워치독/런처가 비밀번호 없이 백엔드를 재시작할 수 있게 (제한적 NOPASSWD)
SUDOERS=/etc/sudoers.d/science-ai
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart science-ai-backend, /usr/bin/systemctl start science-ai-backend, /usr/bin/systemctl restart science-ai-ap, /usr/bin/systemctl start hostapd, /usr/bin/systemctl start dnsmasq" | sudo tee "$SUDOERS" >/dev/null
sudo chmod 440 "$SUDOERS"

# 5. 바탕화면 아이콘
DESK="$HOME/Desktop"; mkdir -p "$DESK"
cp "$ROOT/ScienceLab.desktop" "$DESK/"
chmod +x "$DESK/ScienceLab.desktop" "$ROOT/launcher.sh" "$ROOT"/scripts/*.sh
# 자동 실행(옵션)
mkdir -p "$HOME/.config/autostart"
cp "$ROOT/ScienceLab.desktop" "$HOME/.config/autostart/" 2>/dev/null || true

echo "==> 설치 완료. 'bash scripts/first_boot.py' 로 모둠·PIN 설정 후 재부팅하세요."
echo "    (WiFi AP는 network/README.md 참고 — 콘솔에서 별도 적용)"
