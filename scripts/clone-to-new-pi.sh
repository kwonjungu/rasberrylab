#!/bin/bash
# Science AI Lab — 새 모둠 Pi 설정. 사용: ./clone-to-new-pi.sh <모둠라벨>
set -e
ROOT="/mnt/nvme/projects/science-ai"
LABEL="${1:-X}"
sudo hostnamectl set-hostname "science-pi-$LABEL" 2>/dev/null || true
# AP SSID
[ -f /etc/hostapd/hostapd.conf ] && sudo sed -i "s/^ssid=.*/ssid=science-lab-$LABEL/" /etc/hostapd/hostapd.conf || true
# .env (모둠 라벨 + 무작위 PIN)
PIN=$(shuf -i 1000-9999 -n 1)
cat > "$ROOT/.env" <<ENV
TEAM_LABEL=$LABEL
TEACHER_PIN=$PIN
ENV
echo "==> 모둠 $LABEL 준비 완료. 교사 PIN: $PIN (반드시 기록!)"
echo "    재부팅 권장."
