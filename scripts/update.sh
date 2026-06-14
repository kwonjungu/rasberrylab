#!/bin/bash
# Science AI Lab — 코드 갱신 (git pull + 의존성 + 재시작)
set -e
ROOT="/mnt/nvme/projects/science-ai"
cd "$ROOT"
./scripts/backup.sh
git pull --ff-only
./backend/.venv/bin/pip install -r backend/requirements.txt
sudo systemctl restart science-ai-backend
echo "업데이트 완료"
