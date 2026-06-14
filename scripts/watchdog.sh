#!/bin/bash
# Science AI Lab — 워치독: 5분마다 헬스체크, 3회 연속 실패 시 백엔드 재시작
ENDPOINT="http://localhost:8000"
LOGDIR="/mnt/nvme/projects/science-ai/logs"
LOG="$LOGDIR/watchdog.log"
mkdir -p "$LOGDIR"
fails=0

log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }
log "watchdog 시작"

while true; do
  if curl -sf --max-time 10 "$ENDPOINT/health" >/dev/null; then
    fails=0
  else
    fails=$((fails + 1))
    log "헬스체크 실패 ($fails/3)"
    if [ "$fails" -ge 3 ]; then
      log "→ 백엔드 재시작"
      sudo systemctl restart science-ai-backend 2>/dev/null || true
      fails=0
    fi
  fi
  sleep 300
done
