#!/bin/bash
# undo_s879.sh -- kit S879_DARPAN_ENTRIES_TRANSIT: the three backups back, clinic-finance restarted.
# Run only when the three files are still at S879's TO pins. A day already re-decided on Darpan's page keeps its stored figure
# until it is opened again (the old file then reads the day without the owner's entries, as before).
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FIN_PORT="${FIN_PORT:-8106}"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
declare -A FROM=( [finance/darpan_kal.py]=d27ed062f73e3becbd23b5a9136f7ba0 [finance/darpan_kal.html]=b7d2d61e946454d940f6836e5677f294 [finance/purchase_app.py]=c15bc1c5806bb4a7aabd261b6cd580f9 )
ATFROM=1; for f in "${!FROM[@]}"; do [ "$(m5 "$ROOT/$f")" = "${FROM[$f]}" ] || ATFROM=0; done
[ "$ATFROM" = 1 ] && { echo "-- S879 is NOT installed (the files are at their FROM pins) - nothing to undo."; exit 0; }
for f in "${!FROM[@]}"; do
  [ "$(m5 "$ROOT/$f")" = "$(to_of "$f")" ] || { echo "!! $f is not at S879's TO pin - a later change sits on it. Nothing undone. Tell Claude."; exit 1; }
  b="$ROOT/$f.bak_S879_${FROM[$f]:0:8}"; [ "$(m5 "$b")" = "${FROM[$f]}" ] || { echo "!! the backup $b is missing or not at its pin - nothing undone. Tell Claude."; exit 1; }
done
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - run it again in five minutes."; exit 3; }
echo "undo_s879 $(date '+%F %T')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for f in "${!FROM[@]}"; do \cp -p "$ROOT/$f.bak_S879_${FROM[$f]:0:8}" "$ROOT/$f" || { echo "!! the undo could not write $f - send a photo of this screen to Claude."; exit 1; }; done
"$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done
echo "S879 UNDONE: the three files at their FROM pins; $FSVC restarted, finance healthz $h."
[ "$h" = 200 ] || { echo "!! finance healthz $h after the undo - send a photo of this screen to Claude."; exit 1; }
