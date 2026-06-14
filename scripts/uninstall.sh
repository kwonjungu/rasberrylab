#!/bin/bash
# Science AI Lab — 서비스 제거(데이터는 보존)
set -e
sudo systemctl disable --now science-ai-backend science-ai-warmup science-ai-watchdog 2>/dev/null || true
sudo rm -f /etc/systemd/system/science-ai-*.service
sudo systemctl daemon-reload
rm -f "$HOME/Desktop/ScienceLab.desktop" "$HOME/.config/autostart/ScienceLab.desktop"
echo "제거 완료(데이터·코드는 /mnt/nvme에 보존)."
