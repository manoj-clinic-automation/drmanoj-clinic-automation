#!/bin/bash
# S243_RETIRE move — MOVE ONLY, never delete. Requires a fresh dry-run in this shell session
# (/tmp/s243_dryrun.tsv) and the argument --go. Skips HELD items. Writes MANIFEST.md5,
# WHY_SAFE.txt and UNDO.sh into the retired folder. Restarts nothing.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; . "$HERE/retire_lib.sh"
[ "${1:-}" = "--go" ] || { echo "refused: run retire_dryrun.sh first, review, then: bash retire_move.sh --go"; exit 2; }
[ -s /tmp/s243_dryrun.tsv ] || { echo "refused: no dry-run list at /tmp/s243_dryrun.tsv — run retire_dryrun.sh first"; exit 2; }
[ -n "$(find /tmp/s243_dryrun.tsv -mmin -360 2>/dev/null)" ] || { echo "refused: the dry-run list is older than 6 hours — run retire_dryrun.sh again"; exit 2; }
# the list must still match the box (nothing changed since the dry run)
enumerate > /tmp/s243_now.tsv
if ! cmp -s /tmp/s243_dryrun.tsv /tmp/s243_now.tsv; then echo "refused: the box changed since the dry run — run retire_dryrun.sh again"; diff /tmp/s243_dryrun.tsv /tmp/s243_now.tsv | head; exit 3; fi
STAMP=$(TZ=Asia/Kolkata date '+%Y-%m-%d_%H%M')
DEST="$ROOT/_retired/S243_$STAMP"
mkdir -p "$DEST" && chmod 700 "$ROOT/_retired" "$DEST"
UNDO="$DEST/UNDO.sh"; MAN="$DEST/MANIFEST.md5"; WHY="$DEST/WHY_SAFE.txt"
echo '#!/bin/bash' > "$UNDO"; echo '# puts every retired item back exactly where it was. Run: bash UNDO.sh' >> "$UNDO"
: > "$MAN"
moved=0; skipped=0
while IFS=$'\t' read -r c rel sz refs; do
  [ -n "$refs" ] && { echo "HELD  $rel"; skipped=$((skipped+1)); continue; }
  src="$ROOT/$rel"; dst="$DEST/$rel"
  mkdir -p "$(dirname "$dst")"
  if [ -f "$src" ]; then md5sum "$src" | sed "s|  $ROOT/|  |" >> "$MAN"; else find "$src" -type f -print0 | xargs -0 -r md5sum | sed "s|  $ROOT/|  |" >> "$MAN"; fi
  if mv -n "$src" "$dst"; then
    printf 'mkdir -p %q && mv -n %q %q\n' "$(dirname "$src")" "$dst" "$src" >> "$UNDO"
    echo "moved $c  $rel"; moved=$((moved+1))
  else echo "FAILED to move $rel"; fi
done < /tmp/s243_dryrun.tsv
cat > "$WHY" <<W
S243_RETIRE — $STAMP IST
What: superseded copies (.bak/.BACKUP), dated _backup_S* folders, applied patchers, walk/selftest/seed
helpers, S179/S180/S195 install residue, one-off investigation scripts, legacy import data and
salary working outputs, moved out of /root and /root/finance.
Why safe: every item was checked against every live .py/.sh/.html/.conf/.service/.timer under /root,
the root crontab and /etc/systemd — anything referenced was HELD and not moved ($skipped held).
Nothing was deleted; nothing was restarted; finance.db, logs, json, env and every live module stayed.
Undo: bash $UNDO   (moves everything back to its original path)
Delete: the owner's decision, after a full cycle — never this script.
W
echo "-- moved $moved, held $skipped, into $DEST"
echo "-- live check: clinic-finance $(systemctl is-active clinic-finance 2>/dev/null || echo n/a) · clinic-portal $(systemctl is-active clinic-portal 2>/dev/null || echo n/a)"
echo "-- undo is: bash $UNDO"
