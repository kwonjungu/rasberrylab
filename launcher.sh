#!/bin/bash
# Science AI Lab — 학생 런처 (바탕화면 아이콘 → 키오스크)
ENDPOINT="http://localhost:8000"
LOGDIR="/mnt/nvme/projects/science-ai/logs"
LOG="$LOGDIR/launcher.log"
mkdir -p "$LOGDIR"
log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }

# 1. 백엔드 살아있나 (없으면 systemd로 재시작 시도)
if ! curl -sf "$ENDPOINT/health" >/dev/null; then
  log "백엔드 미응답 → 재시작 시도"
  sudo systemctl restart science-ai-backend 2>/dev/null || true
  for i in $(seq 1 30); do
    sleep 1
    curl -sf "$ENDPOINT/health" >/dev/null && break
  done
fi

# 2. Ollama 워밍 (백그라운드)
curl -s "$ENDPOINT/api/ollama/test?prompt=안녕" >/dev/null 2>&1 &

# 3. 미완료 세션 있으면 ?resume=1
RESUME=""
if curl -sf "$ENDPOINT/api/checkpoints/latest" 2>/dev/null | grep -q '"has_pending": true'; then
  RESUME="?resume=1"
fi

# 4. Chromium 키오스크 (브라우저 실행 파일 자동 탐색)
BROWSER="$(command -v chromium-browser || command -v chromium || echo chromium-browser)"
log "키오스크 실행: $BROWSER ${ENDPOINT}${RESUME}"
exec "$BROWSER" \
  --kiosk \
  --app="${ENDPOINT}${RESUME}" \
  --no-first-run \
  --disable-features=Translate \
  --disable-pinch \
  --overscroll-history-navigation=0 \
  --autoplay-policy=no-user-gesture-required \
  --start-maximized
