#!/bin/bash
# =============================================================================
#  install_S817_CALLS_FOLLOWUP_LINES.sh . kit S817 (13-Nov-2026, session S447, the parent) . F-1322 . the owner's rulings of
#  13-Nov on the approved mock-up (the follow-up lines)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s817kit && cp -rp /root/deploy/repo/deploy_kits/S817_CALLS_FOLLOWUP_LINES /tmp/s817kit && bash /tmp/s817kit/install_S817_CALLS_FOLLOWUP_LINES.sh
#  (DRY=1 before bash: every gate, the walks and the proof on the live stores; nothing written.)
#
#  ONE live file:  /root/portal/calls_console.py   45b03731 (S762) -> TO_MD5.txt
#      the follow-up sections of the Call Console only: in Grace and older a call counts from the day AFTER the due date; each
#      folded line "Called today N of M" / "Reached K" / "Earlier days, after the due date: x called . y reached"; only
#      patients who have not come back by D893; each patient's last answered call with the page's own player.
#  ON THE BOX before anything is written: the S817 walk green on the new page (its ten mutations red, every other reader's
#      figures the same as the live page's) and its control red on the live page; S748's and S762's walks on the new page
#      red ONLY where EXPECTED_REDS.txt names; the proof on the LIVE stores (read-only, counts only).
#  Red after placing: the file back byte-identically and clinic-portal restarted.
#  Undo:  bash /tmp/s817kit/install_S817_CALLS_FOLLOWUP_LINES.sh --undo
# =============================================================================
set -u
KIT="S817_CALLS_FOLLOWUP_LINES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
PD="${PD:-/root/portal}"; WA="${WA:-/root/wa}"; FIN="${FIN:-/root/finance}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
CDB="${CDB:-$WA/console.db}"; IDB="${IDB:-$WA/wa_inbox/inbox.db}"; FDB="${FDB:-$FIN/finance.db}"
SM="${SM:-/root/staff_master.csv}"; PU="${PU:-/root/punches.csv}"
RVDB="${RVDB:-$PD/call_review.db}"
LB="$WA/portal_console.py"
F1="$PD/calls_console.py"
FROM1=45b0373131411242839fecd940fc028c
TO1=49a3633d714060bf82cabf87e14b248c
BAK="$F1.bak_S817_${FROM1:0:8}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(phz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  local ok=1
  [ -f "$BAK" ] && \cp -p "$BAK" "$F1"
  [ "$(m5 "$F1")" = "$FROM1" ] || ok=0
  echo $ok
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the file back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   calls_console.py is back byte-identically (${FROM1:0:8})" || echo "   !! the file is NOT back -- copy $BAK over $F1 by hand"
  echo "   portal health $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 calls_console.py)" = "$TO1" ] || stop "the kit's calls_console.py is not the built one"
[ "$(awk 'NR==1{print $2}' TO_MD5.txt)" = "$TO1" ] || stop "TO_MD5.txt and the installer name different files"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK" ] || stop "no $BAK -- nothing to undo"
  [ "$(m5 "$BAK")" = "$FROM1" ] || stop "$BAK is not the file this kit kept (${FROM1:0:8})"
  L1=$(m5 "$F1")
  [ "$L1" = "$FROM1" ] && { echo "-- NOTHING TO UNDO: the live file is already the one before this kit (${FROM1:0:8}). portal health $(phz)"; exit 0; }
  [ "$L1" = "$TO1" ] || stop "the live $F1 is not this kit's any more (live ${L1:0:8}) -- a later kit sits on top; an undo here would take it away too"
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: calls_console.py is back (S762's, ${FROM1:0:8}); portal health $(wait200)" || echo "!! the file is not back -- send a photo"
  exit 0
fi
echo "[1/7] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ]; then echo "-- ALREADY INSTALLED: the live calls_console.py is the kit's (${TO1:0:8}). Nothing written. portal health $(phz)"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not S762's (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ -f "$LB" ] || stop "$LB is not there (the walks read its SCHEMA and build_fu_all, read only)"
for f in "$FIN/dx_feed.py" "$FIN/finance_patient_sync.py" "$PD/ring_outcome.py" "$PD/ring_common.py"; do [ -f "$f" ] || stop "$f is not there (the walks read it, read only)"; done
SCR=$(mktemp -d /tmp/s817.XXXX); chmod 700 "$SCR"
mkdir -p "$SCR/new" "$SCR/live"
\cp "$KDIR/calls_console.py" "$SCR/new/calls_console.py"; \cp "$F1" "$SCR/live/calls_console.py"
"$VPY" -B -c "import sys;compile(open(sys.argv[1],encoding='utf-8').read(),sys.argv[1],'exec')" "$SCR/new/calls_console.py" 2>/dev/null || stop "calls_console.py does not compile with $VPY"
echo "[2/7] the live file is S762's (${FROM1:0:8}); the new page compiles"
R=$(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s817.py" "$SCR/new" "$PD" "$LB" "$FIN" "$SCR/live" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the S817 walk is not green ($R)";; esac
R2=$(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s817.py" "$SCR/live" "$PD" "$LB" "$FIN" --control 2>&1 | tail -1)
case "$R2" in "CONTROL:"*) ;; *) stop "the control on the live page did not go red ($R2)";; esac
R3=$(cd "$SCR" && VPY="$VPY" bash "$KDIR/oldwalks_s817.sh" "$SCR/new" "$PD" "$LB" 2>&1 | tail -1)
case "$R3" in "OLD WALKS OK"*) ;; *) stop "the earlier walks on the new page are not as expected ($R3)";; esac
echo "[3/7] the walk on made-up data: $R"
echo "      on the live page: $R2"
echo "      $R3"
echo "[4/7] the proof on the LIVE stores (read-only, counts only):"
(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/proof_s817.py" "$SCR/new/calls_console.py" "$SCR/live/calls_console.py" "$PD" "$CDB" "$IDB" "$FDB" "$SM" "$PU" "$RVDB") > "$SCR/proof.txt" 2>&1
sed 's/^/      /' "$SCR/proof.txt"
tail -1 "$SCR/proof.txt" | grep -q '^PROOF CLEAN' || stop "the proof on the live stores is not clean"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ "$(m5 "$F1")" = "$FROM1" ] || stop "the live $F1 changed while the gates ran"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[5/7] the build lock taken; the doctor's auto-fix paused for the restart ($([ "$OFF_MINE" = 1 ] && echo 'by this kit' || echo 'it was already off -- left as it is'))"
\cp -p "$F1" "$BAK" || stop "could not keep a backup of $F1"
[ "$(m5 "$BAK")" = "$FROM1" ] || stop "the backup $BAK did not read back as the live file"
PLACED=1
\cp "$KDIR/calls_console.py" "$F1.s817new" && chmod --reference="$BAK" "$F1.s817new" && mv -f "$F1.s817new" "$F1" || restore "calls_console.py could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "calls_console.py read-back did not match"
echo "[6/7] placed and read back: calls_console.py ${TO1:0:8} (backup $BAK)"
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1"
c2=$(hcode "http://127.0.0.1:$PPORT/portal/console"); case "$c2" in 302|401|403|303) ;; *) restore "/portal/console answered $c2 without a login";; esac
c3=$(hcode "http://127.0.0.1:$PPORT/portal/console/api/mycard"); case "$c3" in 302|401|403|303) ;; *) restore "/portal/console/api/mycard answered $c3 without a login (the staff route must sit behind the login)";; esac
c4=$(hcode "http://127.0.0.1:$PPORT/portal/console/api/card/x"); case "$c4" in 302|401|403|303) ;; *) restore "/portal/console/api/card answered $c4 without a login";; esac
sleep "${NAP:-2}"
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null | awk '/Starting gunicorn|Listening at:/{f=1} f{print} END{if(!f)exit 9}')" || JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[7/7] $PSVC restarted at $T0: health $p1; /portal/console $c2, mycard $c3, card $c4 without a login (the gates); the journal clean"
echo ""
echo "$KIT: DONE. Your Call Console's follow-up lines now show \"Called today N of M\" in large type, count a call only from the day after the due date, list only patients who have not come back, and show when each patient was last reached."
