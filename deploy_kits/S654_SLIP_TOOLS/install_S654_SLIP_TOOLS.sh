#!/bin/bash
# =============================================================================
#  install_S654_SLIP_TOOLS.sh . kit S654 (25-Oct-2026, session S354, the parent) . D789 the slip tools
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s654kit && cp -rp /root/deploy/repo/deploy_kits/S654_SLIP_TOOLS /tmp/s654kit && bash /tmp/s654kit/install_S654_SLIP_TOOLS.sh
#  (DRY=1 before bash: every gate and both walks, nothing written.)
#
#  /root/finance/slip_log.py     93103944 -> b47a5ded  5 counted edits: the previous book kept and accepted; renumber / remove
#  /root/finance/parchi_desk.py  99b7e43b -> db5fd07f  5 counted edits: No. / Hatao on the day's rows, two JSON doors
#  Data step: none by hand -- on the first page view slip_book gains prev_first_no / prev_last_no (xp 1001-1400, opd 19201-19600).
#  Restarts clinic-finance. Red after placing: both old files back byte-identically, restart.
#  Undo:  \cp -p /root/finance/slip_log.py.bak_S654 /root/finance/slip_log.py; \cp -p /root/finance/parchi_desk.py.bak_S654 /root/finance/parchi_desk.py; systemctl restart clinic-finance
# =============================================================================
set -u
KIT="S654_SLIP_TOOLS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
ROWS="$FIN/slip_log.py|slip_log.py|93103944a60cbce13ec4dde462626bf6|b47a5ded64d0c9828bb7343bc7328a6b
$FIN/parchi_desk.py|parchi_desk.py|99b7e43b95a034398962269dc6ce84fa|db5fd07f8417881fd743b6353b3fa3a2"
HAVE_LOCK=0; WN=""; WO=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$WN" ] && rm -rf "$WN" "$WO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
ALL_TO=1
while IFS='|' read -r LP KF FROM TO; do
  [ "$(m5 "$KDIR/$KF")" = "$TO" ] || stop "the kit's $KF is not the built file"
  [ "$(m5 "$LP")" = "$TO" ] || ALL_TO=0
done <<< "$ROWS"
[ "$ALL_TO" = 1 ] && { echo "ALREADY INSTALLED."; exit 0; }
while IFS='|' read -r LP KF FROM TO; do
  L=$(m5 "$LP"); [ "$L" = "$FROM" ] || stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
done <<< "$ROWS"
echo "2. the two live files are the ones this kit was built from"
WN=$(mktemp -d /tmp/s654new.XXXX); WO=$(mktemp -d /tmp/s654old.XXXX)
\cp "$KDIR/slip_log.py" "$KDIR/parchi_desk.py" "$WN/"; \cp "$FIN/slip_log.py" "$FIN/parchi_desk.py" "$WO/"
[ -f "$FIN/slip_adjust.py" ] && \cp "$FIN/slip_adjust.py" "$WN/" && \cp "$FIN/slip_adjust.py" "$WO/"
"$PY" -B -m py_compile "$WN/slip_log.py" "$WN/parchi_desk.py" || stop "a file does not compile with $PY"
R=$("$PY" -B walk_s654.py "$WN" 2>&1 | tail -1)
[ "$R" = "25 of 25 green" ] || { "$PY" -B walk_s654.py "$WN" 2>&1 | grep -E 'RED|Error' | head; stop "the walk is not green ($R)"; }
echo "3. the walk on a made-up slip book: $R"
R=$("$PY" -B walk_s654.py "$WO" --old 2>&1 | tail -1)
[ "$R" = "16 S654 check(s) red · 0 older red · 9 green" ] || { echo "$R"; stop "the control on the live files is not as expected ($R)"; }
echo "   control on the live files: $R"
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
restore() {
  while IFS='|' read -r LP KF FROM TO; do [ -f "$LP.bak_S654" ] && \cp -p "$LP.bak_S654" "$LP"; done <<< "$ROWS"
  "$SYSTEMCTL" restart "$SVC"; h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  bad=0; while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$FROM" ] || { echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S654 back by hand"; bad=1; }; done <<< "$ROWS"
  [ "$bad" = 0 ] && echo "   both old files are back byte-identically"
  echo "   after the restore: finance $h2. Send a photo of this screen to Claude."; exit 1
}
while IFS='|' read -r LP KF FROM TO; do \cp -p "$LP" "$LP.bak_S654" || stop "could not keep a backup of $LP"; done <<< "$ROWS"
while IFS='|' read -r LP KF FROM TO; do \cp "$KDIR/$KF" "$LP" && chmod --reference="$LP.bak_S654" "$LP" 2>/dev/null; done <<< "$ROWS"
ok=1; while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$TO" ] || ok=0; done <<< "$ROWS"
[ "$ok" = 1 ] || { echo "!! read-back did not match"; restore; }
echo "4. placed both files (backups *.bak_S654), read back by md5"
"$SYSTEMCTL" restart "$SVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
D=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/slips/desk/api/renumber" -X POST -H 'Content-Type: application/json' -d '{}')
if [ "$h" != 200 ] || { [ "$D" != 401 ] && [ "$D" != 403 ] && [ "$D" != 302 ]; }; then echo "!! RED after placing (finance $h; the new door signed out answered $D, not a refusal)"; restore; fi
echo "5. $SVC restarted and healthy; the new door refuses a signed-out call ($D)"
echo ""
echo "INSTALLED. On the parchi desk every saved parchi of the last 7 days carries No. and Hatao; the previous book's numbers are accepted."
