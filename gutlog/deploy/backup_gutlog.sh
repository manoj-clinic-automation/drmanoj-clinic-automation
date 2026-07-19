#!/usr/bin/env bash
# Daily GutLog backup. Snapshots the SQLite DB consistently, copies the
# session-key sidecar, and tars the uploads vault. Keeps 30 days.
#
# Install (root):
#   cp deploy/backup_gutlog.sh /root/gutlog/backup_gutlog.sh
#   chmod +x /root/gutlog/backup_gutlog.sh
#   crontab -e   ->   0 1 * * * /root/gutlog/backup_gutlog.sh >> /var/log/gutlog_backup.log 2>&1
set -euo pipefail
SRC=/root/gutlog
DEST=/root/backups/gutlog
STAMP=$(date +%F)
mkdir -p "$DEST"
sqlite3 "$SRC/health3.db" ".backup '$DEST/health3_$STAMP.db'"
cp -f "$SRC/health3.db.secret" "$DEST/health3.db.secret" 2>/dev/null || true
tar -czf "$DEST/uploads_$STAMP.tar.gz" -C "$SRC" uploads 2>/dev/null || true
find "$DEST" -name 'health3_*.db'      -mtime +30 -delete
find "$DEST" -name 'uploads_*.tar.gz'  -mtime +30 -delete
echo "GutLog backup complete: $STAMP"
