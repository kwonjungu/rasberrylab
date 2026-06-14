#!/bin/bash
# Science AI Lab — 백업 복원. 사용: ./restore.sh <백업.tar.gz>
set -e
ROOT="/mnt/nvme/projects/science-ai"
ARCHIVE="$1"
[ -f "$ARCHIVE" ] || { echo "사용: $0 <백업.tar.gz>"; exit 1; }
TMP=$(mktemp -d)
tar -xzf "$ARCHIVE" -C "$TMP"
SUB=$(ls "$TMP")
[ -f "$TMP/$SUB/lab.db" ] && cp "$TMP/$SUB/lab.db" "$ROOT/db/" && echo "lab.db 복원"
[ -d "$TMP/$SUB/data" ] && cp -r "$TMP/$SUB/data/." "$ROOT/backend/data/" && echo "data 복원"
rm -rf "$TMP"
sudo systemctl restart science-ai-backend 2>/dev/null || true
echo "복원 완료"
