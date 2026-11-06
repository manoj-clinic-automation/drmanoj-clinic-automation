#!/bin/bash
# =============================================================================
#  install_S712_STAFF_FORM_SUNDAY_ARJUN.sh . kit S712 (06-Nov-2026, session S389, the parent)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s712kit && cp -rp /root/deploy/repo/deploy_kits/S712_STAFF_FORM_SUNDAY_ARJUN /tmp/s712kit && bash /tmp/s712kit/install_S712_STAFF_FORM_SUNDAY_ARJUN.sh
#  (DRY=1 before bash: every gate; nothing written.)
#
#  1. F-1125 -- the Add staff form's Sunday choice: "Works every Sunday" (with hours) / "Sunday off".
#     /root/finance/staff_easy.py    c5344291 -> da4aabd2
#     /root/finance/staff_easy.html  05c1f7b8 -> 45dd0a01
#     Restarts clinic-finance. Red after placing: both files back byte-identically, restart.
#  2. D834 -- Arjun (machine number 20): base pay 3200 -> 3500 in /root/staff_master.csv, from November.
#     One cell; every other byte proved identical; backup first (staff_master.csv.bak_S712_<time>).
#  Undo:  \cp -p /root/finance/staff_easy.py.bak_S712 /root/finance/staff_easy.py && \cp -p /root/finance/staff_easy.html.bak_S712 /root/finance/staff_easy.html && systemctl restart clinic-finance
#         (the pay: copy the newest /root/staff_master.csv.bak_S712_* back over /root/staff_master.csv)
# =============================================================================
set -u
KIT="S712_STAFF_FORM_SUNDAY_ARJUN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
ATT="${ATT:-/root}"
SM="${SM:-/root/staff_master.csv}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LPY="$FIN/staff_easy.py";   FPY=c5344291eb773610e754211fbf24db69; TPY=da4aabd20cb95b87426b8167e74c5d1c
LHT="$FIN/staff_easy.html"; FHT=05c1f7b8086bdc0ad0fb174f676a5020; THT=45dd0a010fa1b34f04b46f48988059e2
WALK_OK="12 of 12 green"; CONTROL="9 S712 check(s) red . 3 green"
HAVE_LOCK=0; WN=""; WO=""; PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$WN" ] && rm -rf "$WN" "$WO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }
door() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/staff/easy/api/health"; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting both files back"
  \cp -p "$LPY.bak_S712" "$LPY"; \cp -p "$LHT.bak_S712" "$LHT"
  "$SYSTEMCTL" restart "$SVC"; h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  [ "$(m5 "$LPY")" = "$FPY" ] && [ "$(m5 "$LHT")" = "$FHT" ] && echo "   both files are back byte-identically" || echo "   !! copy $LPY.bak_S712 and $LHT.bak_S712 back by hand"
  echo "   after the restore: finance $h2. Arjun's pay was NOT touched. Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/staff_easy.py")" = "$TPY" ] && [ "$(m5 "$KDIR/staff_easy.html")" = "$THT" ] || stop "the kit's staff_easy files are not the built ones"
echo "1. kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
# the same staff list for the form, the attendance report and the salary
"$SYSTEMCTL" show "$SVC" -p Environment 2>/dev/null | grep -q 'ATT_STAFF_MASTER=' && stop "$SVC sets its own ATT_STAFF_MASTER -- not the file this kit changes"
for EF in $("$SYSTEMCTL" show "$SVC" -p EnvironmentFiles --value 2>/dev/null | sed -E 's/ *\([^)]*\)//g'); do
  [ -f "${EF#-}" ] && grep -q 'ATT_STAFF_MASTER' "${EF#-}" && stop "$SVC's environment file ${EF#-} sets ATT_STAFF_MASTER -- not the file this kit changes"
done
CM=$(cd "$ATT" && "$PY" -B -c "import att_config as c; print(c.STAFF_MASTER)" 2>/dev/null)
[ "$CM" = "$SM" ] || stop "att_config.STAFF_MASTER is '$CM', not $SM"
echo "2. the form, the attendance report and the salary all read $SM"
PYL=$(m5 "$LPY"); HTL=$(m5 "$LHT")
if [ "$PYL" = "$TPY" ] && [ "$HTL" = "$THT" ]; then
  echo "-- the form is ALREADY INSTALLED. The pay step (safe to repeat):"
  DA=""; [ "${DRY:-0}" = 1 ] && DA="--dry"
  R=$("$PY" -B "$KDIR/set_base_s712.py" "$SM" $DA 2>&1); RC=$?
  echo "$R" | sed 's/^/   /'
  [ "$RC" = 0 ] || { echo "!! the pay step stopped (rc $RC); Arjun's pay is as it was. Send a photo of this screen to Claude."; exit 1; }
  exit 0
fi
[ "$PYL" = "$FPY" ] || stop "the live $LPY changed since this kit was built (live ${PYL:0:8}, kit expects ${FPY:0:8})"
[ "$HTL" = "$FHT" ] || stop "the live $LHT changed since this kit was built (live ${HTL:0:8}, kit expects ${FHT:0:8})"
echo "3. the live files are the ones this kit was built from"
WN=$(mktemp -d /tmp/s712new.XXXX); WO=$(mktemp -d /tmp/s712old.XXXX)
\cp "$KDIR/staff_easy.py" "$KDIR/staff_easy.html" "$WN/"; \cp "$LPY" "$LHT" "$WO/"
"$PY" -B -m py_compile "$WN/staff_easy.py" || stop "staff_easy.py does not compile with $PY"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s712.py" "$WN" "$FIN" "$ATT" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd /tmp && "$PY" -B "$KDIR/walk_s712.py" "$WN" "$FIN" "$ATT" 2>&1 | grep -E 'RED|Error' | head); stop "the walk is not green ($R)"; }
echo "4. the walk on a made-up root (the real attendance readers): $R"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s712.py" "$WO" "$FIN" "$ATT" 2>&1 | tail -1)
[ "$R" = "$CONTROL" ] || stop "the control on the live files is not as expected ($R)"
echo "   control on the live files: $R"
R=$("$PY" -B "$KDIR/set_base_s712.py" "$SM" --dry 2>&1); RC=$?
echo "$R" | sed 's/^/   the pay step, DRY on the live list: /'
[ "$RC" = 0 ] || stop "the pay step's DRY run did not find Arjun as read on 06-Nov (rc $RC)"
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
[ "$(m5 "$LPY")" = "$FPY" ] && [ "$(m5 "$LHT")" = "$FHT" ] || stop "a live staff_easy file changed while this kit was checking -- run the line again"
\cp -p "$LPY" "$LPY.bak_S712" && \cp -p "$LHT" "$LHT.bak_S712" || stop "could not keep backups of the two files"
echo "5. backups: staff_easy.py.bak_S712, staff_easy.html.bak_S712"
PLACED=1
for P in "$LPY:staff_easy.py" "$LHT:staff_easy.html"; do
  L=${P%%:*}; K=${P##*:}
  \cp "$KDIR/$K" "$L.s712new" && chmod --reference="$L.bak_S712" "$L.s712new" && chown --reference="$L.bak_S712" "$L.s712new" && mv -f "$L.s712new" "$L" || restore "$K could not be placed"
done
[ "$(m5 "$LPY")" = "$TPY" ] && [ "$(m5 "$LHT")" = "$THT" ] || restore "read-back did not match"
echo "6. placed staff_easy.py (${TPY:0:8}) and staff_easy.html (${THT:0:8}), read back by md5"
"$SYSTEMCTL" restart "$SVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
D=$(door)
if [ "$h" != 200 ] || { [ "$D" != 401 ] && [ "$D" != 403 ] && [ "$D" != 302 ]; }; then restore "finance $h; the form's door signed out answered $D, not a refusal"; fi
PLACED=0
echo "7. $SVC restarted and healthy; the form's door refuses a signed-out call ($D)"
R=$("$PY" -B "$KDIR/set_base_s712.py" "$SM" 2>&1); RC=$?
echo "$R" | sed 's/^/8. the pay step: /'
[ "$RC" = 0 ] || { echo "!! the pay step did not finish (rc $RC) -- the form is placed; Arjun's pay is unchanged. Send a photo of this screen to Claude."; exit 1; }
echo ""
echo "$KIT: DONE. The Add staff form now offers Works every Sunday / Sunday off. Arjun is on Rs 3,500 from November."
