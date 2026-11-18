#!/bin/bash
# undo_s876.sh -- kit S876_HUB_RECORD_INLINE: the two backups back, the new patient_events.py out, clinic-finance restarted.
# Run only when the three files are still at S876's TO pins (a later kit on them is undone first). Nothing in any table changes.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FIN_PORT="${FIN_PORT:-8106}"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
B1="$ROOT/finance/sanjeevni_day.py.bak_S876_db30da9f"; B2="$ROOT/finance/finance_ui/finance_approvals.html.bak_S876_254c0bbf"
N="$ROOT/finance/patient_events.py"
if [ "$(m5 "$ROOT/finance/sanjeevni_day.py")" = db30da9f33ee8319b3c8c15f1d39fb12 ] && [ "$(m5 "$ROOT/finance/finance_ui/finance_approvals.html")" = 254c0bbf47b18a539437a11dec831b0a ] && [ ! -e "$N" ]; then
  echo "-- S876 is NOT installed (the files are at their FROM pins) - nothing to undo."; exit 0; fi
for f in finance/sanjeevni_day.py finance/finance_ui/finance_approvals.html finance/patient_events.py; do
  [ "$(m5 "$ROOT/$f")" = "$(to_of "$f")" ] || { echo "!! $f is not at S876's TO pin - a later change sits on it. Nothing undone. Tell Claude."; exit 1; }; done
[ -f "$B1" ] && [ "$(m5 "$B1")" = db30da9f33ee8319b3c8c15f1d39fb12 ] && [ -f "$B2" ] && [ "$(m5 "$B2")" = 254c0bbf47b18a539437a11dec831b0a ] \
  || { echo "!! a backup is missing or not at its pin - nothing undone. Tell Claude."; exit 1; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - run it again in five minutes."; exit 3; }
echo "undo_s876 $(date '+%F %T')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
\cp -p "$B1" "$ROOT/finance/sanjeevni_day.py" && \cp -p "$B2" "$ROOT/finance/finance_ui/finance_approvals.html" && rm -f "$N" \
  || { echo "!! the undo could not write a file - send a photo of this screen to Claude."; exit 1; }
"$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done
echo "S876 UNDONE: sanjeevni_day.py $(m5 "$ROOT/finance/sanjeevni_day.py" | cut -c1-8), finance_approvals.html $(m5 "$ROOT/finance/finance_ui/finance_approvals.html" | cut -c1-8), patient_events.py removed; $FSVC restarted, finance healthz $h."
[ "$h" = 200 ] || { echo "!! finance healthz $h after the undo - send a photo of this screen to Claude."; exit 1; }
