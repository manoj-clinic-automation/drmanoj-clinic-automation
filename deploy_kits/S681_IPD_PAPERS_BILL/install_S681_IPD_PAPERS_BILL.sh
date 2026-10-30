#!/bin/bash
# =============================================================================
#  install_S681_IPD_PAPERS_BILL.sh · kit S681 (the parent, session S370, 30-Oct-2026) · IPD kits 2 + 3 (D804; the owner 13:47 / 13:52)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s681kit && cp -rp /root/deploy/repo/deploy_kits/S681_IPD_PAPERS_BILL /tmp/s681kit && bash /tmp/s681kit/install_S681_IPD_PAPERS_BILL.sh
#  (DRY=1 before bash: every gate, the walk and the probe, nothing written.)
#
#  ONE whole file, pinned:
#   /root/finance/surgery_cases.py   ed91e2af (S680, live) -> TO   papers as thumbnails + four new kinds · each implant's payment step
#                                                                  · assistants (pay his alone) · the hospital bill and his share both
#                                                                  ways (the statement's four heads x 50% · his formula per payer)
#  Data: on the first request -- one column (surg_implant.pay_status), two tables (surg_assistant, surg_bill), one setting
#  (ipd.hospital_share_pct, 50 until changed). Additive only; the database is copied before placing.
#  Restarts clinic-finance only. Red after placing: the file back from its backup, the service restarted, health read.
# =============================================================================
set -u
KIT="S681_IPD_PAPERS_BILL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"
FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
LIVE="$FIN/surgery_cases.py"
FROM=ed91e2af9696e204e5c51780522a0205
CONTROL_W="walk_s681: 204 of 207 green"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s681_inst_$STAMP"
BAK="$LIVE.bak_S681_${FROM:0:8}"
TOOK_LOCK=0; OFF_MINE=0; PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
code() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
wait_for() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(code "$1"); [ "$h" = "$2" ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; release_lock; }
trap on_exit EXIT
stop() { say "!! STOPPED: $1"; say "   Nothing was changed. Send a photo of this screen to Claude."; [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; exit 1; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the file back"
  [ -f "$BAK" ] && \cp -p "$BAK" "$LIVE"
  rm -f "$FIN"/.surgery_cases.py.s681
  "$SYSTEMCTL" restart "$FSVC" || true
  local f; f=$(wait_for "http://127.0.0.1:$FIN_PORT/finance/healthz" 200)
  say "   $LIVE $(m5 "$LIVE") (expected $FROM) · finance health $f. (The added column and tables are harmless to the old file.)"
  say "   Send a photo of this screen to Claude."
  [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_signal INT TERM HUP
allgreen() { local g t; g=$(echo "$1" | sed -n 's/^walk_s681: \([0-9]*\) of \([0-9]*\) green$/\1/p'); t=$(echo "$1" | sed -n 's/^walk_s681: \([0-9]*\) of \([0-9]*\) green$/\2/p')
            [ -n "$g" ] && [ "$g" = "$t" ] && [ "$g" -ge 252 ]; }

say "== $KIT =="
cd "$KDIR" || { say "!! the kit folder is not there"; exit 1; }
for c in md5sum awk cp mv date curl grep sed sleep find timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || { say "!! the kit's files do not match SUMS.md5 - nothing installed"; exit 1; }
TO=$(m5 "$KDIR/surgery_cases.py")
say "[1/8] kit files: all match SUMS.md5"
mkdir -p "$(dirname "$LOCK")" && mkdir "$LOCK" 2>/dev/null || { say "!! another install is running (lock $LOCK). Wait 5 minutes and run the line again"; exit 1; }
TOOK_LOCK=1; echo "$KIT $STAMP" > "$LOCK/owner"
mkdir -p "$SCR" || stop "no scratch folder"
h=$(m5 "$LIVE")
if [ "$h" = "$TO" ]; then say "ALREADY INSTALLED (the file is the kit's). Nothing written."; exit 0; fi
[ "$h" = "$FROM" ] || stop "$LIVE is $h -- neither its pinned live version ($FROM, S680) nor the kit's"
grep -q "S579_SURGERY_CASES begin" "$FIN/finance_app.py" || stop "the finance app does not carry the S579 mount"
say "[2/8] pin: surgery_cases.py ed91e2af (S680); the S579 mount present"
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile surgery_cases.py walk_s681.py probe_s681.py || stop "the kit's python does not compile on $py"
done
say "[3/8] compiled on both pythons"
W1="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s681.py" "$KDIR/surgery_cases.py" 2>&1 | tail -1 )"
copydb "$DB" "$SCR/walk.db" || stop "no scratch copy of the database for the walk"
W2="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s681.py" "$KDIR/surgery_cases.py" --db "$SCR/walk.db" 2>&1 | tail -1 )"
copydb "$DB" "$SCR/walk0.db"
W0="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s681.py" "$LIVE" --db "$SCR/walk0.db" 2>&1 | tail -1 )"
rm -f "$SCR"/walk*.db
allgreen "$W1" || stop "the walk on a made-up database is not all green ($W1)"
allgreen "$W2" || stop "the walk on a copy of the live database is not all green ($W2)"
[ "$W0" = "$CONTROL_W" ] || stop "the control is not the expected red: the live module gave '$W0', expected '$CONTROL_W'"
say "[4/8] the walk: made-up $W1 · a copy of the live database $W2 · the live module (control) $W0"
mkdir -p "$SCR/fnew" "$SCR/fold"
for d in "$SCR/fnew" "$SCR/fold"; do
  cp -p "$FIN"/*.py "$d/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/" 2>/dev/null
  for sub in finance_ui spine vendor; do [ -d "$FIN/$sub" ] && mkdir -p "$d/$sub" && cp -rp "$FIN/$sub/." "$d/$sub/" 2>/dev/null; done
done
\cp -p "$KDIR/surgery_cases.py" "$SCR/fnew/"
copydb "$DB" "$SCR/fnew.db" && copydb "$DB" "$SCR/fold.db" || stop "no scratch copies of the database for the probe"
Q1="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s681.py" --fin "$SCR/fnew" --db "$SCR/fnew.db" 2>&1 )"
Q0="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s681.py" --fin "$SCR/fold" --db "$SCR/fold.db" --expect-red 2>&1 )"
echo "$Q1" | grep -q "^PROBE OK 17 of 17" || { echo "$Q1" | tail -18; stop "the look as manoj and shavez through the real finance app is red on copies"; }
echo "$Q0" | grep -q "^PROBE OK negative control" || { echo "$Q0" | tail -18; stop "the probe's control did not go red on the live file"; }
say "[5/8] the real finance app on copies: $(echo "$Q1" | grep '^PROBE OK') · its control: $(echo "$Q0" | grep '^PROBE OK')"
rm -rf "$SCR/fnew" "$SCR/fold" "$SCR"/*.db
f0=$(code "http://127.0.0.1:$FIN_PORT/finance/healthz")
[ "$f0" = 200 ] || stop "not healthy before the install (finance $f0)"
say "[6/8] healthy before the install: finance $f0"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the probe green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

\cp -p "$LIVE" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || stop "the backup of $LIVE failed"
DBBAK="$FIN/finance.db.bak_S681_$STAMP"
copydb "$DB" "$DBBAK" || stop "the copy of the database before the change failed"
if [ -e "$OFFSW" ]; then
  say "       $OFFSW was already on ($(head -c 120 "$OFFSW" 2>/dev/null)) -- left exactly as found"
else
  mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" && OFF_MINE=1 || stop "could not write $OFFSW"
fi
STG="$FIN/.surgery_cases.py.s681"
{ cat "$KDIR/surgery_cases.py" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; stop "could not stage $LIVE"; }
chmod --reference="$LIVE" "$STG" 2>/dev/null; chown --reference="$LIVE" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$LIVE" || restore "the rename of $LIVE"
[ "$(m5 "$LIVE")" = "$TO" ] || restore "the md5 read back of $LIVE"
say "[7/8] placed and read back: $LIVE at the kit's md5 (backup $(basename "$BAK"); the database copied to $(basename "$DBBAK"))"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait_for "http://127.0.0.1:$FIN_PORT/finance/healthz" 200)
c3=$(code "http://127.0.0.1:$FIN_PORT/finance/surgery")
"$SYSTEMCTL" is-active --quiet "$FSVC" || restore "$FSVC is not active"
{ [ "$c1" = 200 ] && [ "$c3" = 302 ]; } || restore "finance health $c1 / IPD cases page $c3 (302 expected without a login)"
MF=""
command -v "$JOURNALCTL" >/dev/null 2>&1 && MF="$("$JOURNALCTL" -u "$FSVC" --since "-3 min" --no-pager 2>/dev/null | grep -E "surgery_cases NOT mounted" | head -1)"
[ -z "$MF" ] || restore "the module did not mount: $MF"
mkdir -p "$SCR/fpl"
cp -p "$FIN"/*.py "$SCR/fpl/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/fpl/" 2>/dev/null
for sub in finance_ui spine vendor; do [ -d "$FIN/$sub" ] && mkdir -p "$SCR/fpl/$sub" && cp -rp "$FIN/$sub/." "$SCR/fpl/$sub/" 2>/dev/null; done
copydb "$DB" "$SCR/fpl.db" || restore "no copy of the database for the look on the placed file"
Q2="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s681.py" --fin "$SCR/fpl" --db "$SCR/fpl.db" 2>&1 )"
echo "$Q2" | grep -q "^PROBE OK 17 of 17" || { echo "$Q2" | tail -18; restore "the look as manoj and shavez on the placed file is red"; }
say "[8/8] $FSVC restarted, health $c1, /finance/surgery $c3 without a login (the gate); $(echo "$Q2" | grep '^PROBE OK') on the placed file"
[ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"
release_lock
say ""
say "INSTALLED. IPD cases kits 2 + 3: papers as thumbnails (FIR copy, previous hospital, LAMA, DOPR added; Delete asks why),"
say "each implant's own payment step, the technician and the assisting doctor (their pay yours alone), and the hospital bill with"
say "your share worked out two ways -- the hospital statement's (50% of visit + misc + bed + surgery) and your own formula."
say "undo (one line): \\cp -p $BAK $LIVE && $SYSTEMCTL restart $FSVC"
exit 0
