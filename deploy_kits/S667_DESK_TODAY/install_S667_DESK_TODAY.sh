#!/bin/bash
# =============================================================================
#  install_S667_DESK_TODAY.sh . kit S667 (27-Oct-2026, session S358, the parent) . the parchi desk follows the real day
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s667kit && cp -rp /root/deploy/repo/deploy_kits/S667_DESK_TODAY /tmp/s667kit && bash /tmp/s667kit/install_S667_DESK_TODAY.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  /root/finance/parchi_desk.py  db5fd07f -> fb405c12  5 counted edits: on "Aaj" the desk moves to the new day by itself;
#                                a save made from a stale "Aaj" is refused and the page moves to today. A chosen late day is as before.
#  A desk opened before the install (old page) saving for another day is refused: "press F5 once".
#  Data step: fix_s667_day.py moves OPD 19858 and X-ray 1420 (typed 27-Oct 11:26 on a desk left open since 26-Oct) from
#  26-Oct to 27-Oct -- only those exact rows, one audit_log row each; finance.db backed up first. Safe to run twice.
#  Restarts clinic-finance. Red after placing: the old file back byte-identically, restart (the two moved rows stay moved).
#  Undo:  \cp -p /root/finance/parchi_desk.py.bak_S667 /root/finance/parchi_desk.py && systemctl restart clinic-finance
# =============================================================================
set -u
KIT="S667_DESK_TODAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
DBF="${DBF:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LP="$FIN/parchi_desk.py"; FROM=db5fd07f8417881fd743b6353b3fa3a2; TO=fb405c1233c7f5c808aefb7e67c57a2f
WALK_OK="16 of 16 green"; CONTROL="6 S667 check(s) red · 0 older red · 10 green"
HAVE_LOCK=0; WN=""; WO=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$WN" ] && rm -rf "$WN" "$WO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/parchi_desk.py")" = "$TO" ] || stop "the kit's parchi_desk.py is not the built file"
echo "1. kit files: all match SUMS.md5"
if [ "$(m5 "$LP")" = "$TO" ]; then echo "ALREADY INSTALLED. The data step (safe to repeat):"; "$PY" -B fix_s667_day.py "$DBF" --lib "$FIN"; echo "   data step rc $?"; exit 0; fi
L=$(m5 "$LP"); [ "$L" = "$FROM" ] || stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
[ -f "$FIN/slip_log.py" ] && [ -f "$DBF" ] || stop "slip_log.py or finance.db is not where expected"
echo "2. the live file is the one this kit was built from"
WN=$(mktemp -d /tmp/s667new.XXXX); WO=$(mktemp -d /tmp/s667old.XXXX)
\cp "$KDIR/parchi_desk.py" "$WN/"; \cp "$LP" "$WO/"
"$PY" -B -m py_compile "$WN/parchi_desk.py" || stop "parchi_desk.py does not compile with $PY"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s667.py" "$WN" "$FIN" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd /tmp && "$PY" -B "$KDIR/walk_s667.py" "$WN" "$FIN" 2>&1 | grep -E 'RED|Error' | head); stop "the walk is not green ($R)"; }
echo "3. the walk on a made-up slip book (clock moved past midnight): $R"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s667.py" "$WO" "$FIN" --old 2>&1 | tail -1)
[ "$R" = "$CONTROL" ] || stop "the control on the live file is not as expected ($R)"
echo "   control on the live file: $R"
R=$("$PY" -B fix_s667_day.py "$DBF" --dry --lib "$FIN" 2>&1); RC=$?
echo "$R" | sed 's/^/   the data step, DRY on the live database: /'
[ "$RC" = 0 ] || stop "the data step's DRY run did not find the two parchis as expected (rc $RC)"
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
restore() {
  \cp -p "$LP.bak_S667" "$LP"
  "$SYSTEMCTL" restart "$SVC"; h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  [ "$(m5 "$LP")" = "$FROM" ] && echo "   the old parchi_desk.py is back byte-identically" || echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S667 back by hand"
  echo "   after the restore: finance $h2. Send a photo of this screen to Claude."; exit 1
}
STAMP=$(date +%Y%m%d_%H%M%S)
\cp -p "$LP" "$LP.bak_S667" || stop "could not keep a backup of $LP"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$DBF.bak_S667_$STAMP" \
  || stop "could not back up finance.db"
echo "4. backups: parchi_desk.py.bak_S667, finance.db.bak_S667_$STAMP"
\cp "$KDIR/parchi_desk.py" "$LP" && chmod --reference="$LP.bak_S667" "$LP" 2>/dev/null
[ "$(m5 "$LP")" = "$TO" ] || { echo "!! read-back did not match"; restore; }
echo "5. placed parchi_desk.py, read back by md5"
R=$("$PY" -B fix_s667_day.py "$DBF" --lib "$FIN" 2>&1); RC=$?
echo "$R" | sed 's/^/6. the data step: /'
[ "$RC" = 0 ] || { echo "!! the data step did not finish (rc $RC) -- the page is placed; send a photo of this screen to Claude"; }
"$SYSTEMCTL" restart "$SVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
D=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/slips/desk/api/save" -X POST -H 'Content-Type: application/json' -d '{}')
if [ "$h" != 200 ] || { [ "$D" != 401 ] && [ "$D" != 403 ] && [ "$D" != 302 ]; }; then echo "!! RED after placing (finance $h; the desk's save door signed out answered $D, not a refusal)"; restore; fi
echo "7. $SVC restarted and healthy; the desk's save door refuses a signed-out call ($D)"
echo ""
echo "$KIT: DONE. Reload the parchi desk once (F5). From now on it moves to the new day by itself; 1420 and 19858 are on today."
