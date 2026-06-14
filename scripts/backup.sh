#!/bin/bash
# Science AI Lab — DB + 데이터 백업 (cron: 0 0 * * *)
set -e
ROOT="/mnt/nvme/projects/science-ai"
DATE=$(date +%Y%m%d-%H%M%S)
DEST="/mnt/nvme/backups"
mkdir -p "$DEST"
TMP="$DEST/science-ai-$DATE"
mkdir -p "$TMP"
[ -f "$ROOT/db/lab.db" ] && cp "$ROOT/db/lab.db" "$TMP/" || true
cp -r "$ROOT/backend/data" "$TMP/data"
tar -czf "$TMP.tar.gz" -C "$DEST" "science-ai-$DATE"
rm -rf "$TMP"
# 30일 지난 백업 삭제
find "$DEST" -name "science-ai-*.tar.gz" -mtime +30 -delete
echo "백업 완료: $TMP.tar.gz"
