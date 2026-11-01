#!/bin/bash
# =============================================================================
#  install_S682_IPD_IMPLANT_BILLS.sh · kit S682 (the parent, session S374, 01-Nov-2026) · IPD kit 4 (D804, D807; the owner's answers 07:39-07:40 IST)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s682kit && cp -rp /root/deploy/repo/deploy_kits/S682_IPD_IMPLANT_BILLS /tmp/s682kit && bash /tmp/s682kit/install_S682_IPD_IMPLANT_BILLS.sh
#  (DRY=1 before bash: every gate, the rebuild, the walk and the probe, nothing written.)
#
#  ONE whole file, pinned, REBUILT on the box from its live bytes by make_s682.py (F-472) and compared to the kit's copy:
#   /root/finance/surgery_cases.py   89a668a9 (S681, live) -> TO   the implant bills desk (/finance/surgery/implants) · the supplier's bill
#                                                                  per implant with its scan · a cheque written on its own, tied to bills
#                                                                  later · paid / confirmed · old cases settled by Dr Manoj · section 6 ·
#                                                                  the word Supplier everywhere (the addresses unchanged)
#  Data: on the first request -- columns surg_implant.estimate_p, surg_paper.implant_id, surg_cheque_alloc.implant_id; tables
#  surg_implant_bill, surg_implant_event, surg_pay_alloc. Additive only; the database is copied before placing.
#  Restarts clinic-finance only. Red after placing: the file back from its backup, the service restarted, health read.
# =============================================================================
set -u
KIT="S682_IPD_IMPLANT_BILLS"
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
FROM=89a668a98ba5cd1a7b25df9fe043d82f
CONTROL_W="walk_s682: 248 of 260 green"
PROBE_OK="PROBE OK 22 of 22"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s682_inst_$STAMP"
BAK="$LIVE.bak_S682_${FROM:0:8}"
TOOK_LOCK=0; OFF_MINE=0; PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
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
  rm -f "$FIN"/.surgery_cases.py.s682
  "$SYSTEMCTL" restart "$FSVC" || true
  local f; f=$(wait_for "http://127.0.0.1:$FIN_PORT/finance/healthz" 200)
  say "   $LIVE $(m5 "$LIVE") (expected $FROM) · finance health $f. (The added columns and tables are harmless to the old file.)"
  say "   Send a photo of this screen to Claude."
  [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_signal INT TERM HUP
allgreen() { local g t; g=$(echo "$1" | sed -n 's/^walk_s682: \([0-9]*\) of \([0-9]*\) green$/\1/p'); t=$(echo "$1" | sed -n 's/^walk_s682: \([0-9]*\) of \([0-9]*\) green$/\2/p')
            [ -n "$g" ] && [ "$g" = "$t" ] && [ "$g" -ge 329 ]; }

say "== $KIT =="
cd "$KDIR" || { say "!! the kit folder is not there"; exit 1; }
for c in md5sum awk cp mv date curl grep sed sleep find timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${SKIP_WINDOW:-0}" = 1 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || { say "!! the kit's files do not match SUMS.md5 - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! KIT_ID.txt names another kit - nothing installed"; exit 1; }
TO=$(m5 "$KDIR/surgery_cases.py")
[ "$(awk '$2=="surgery_cases.py"{print $1}' TO_PINS.md5)" = "$TO" ] || { say "!! TO_PINS.md5 and the kit's surgery_cases.py disagree - nothing installed"; exit 1; }
say "[1/8] kit files: all match SUMS.md5; TO $TO"
mkdir -p "$(dirname "$LOCK")" && mkdir "$LOCK" 2>/dev/null || { say "!! another install is running (lock $LOCK). Wait 5 minutes and run the line again"; exit 1; }
TOOK_LOCK=1; echo "$KIT $$ $STAMP" > "$LOCK/owner"
mkdir -p "$SCR/pyc" "$SCR/from" "$SCR/built" && chmod 700 "$SCR" || stop "no scratch folder"
h=$(m5 "$LIVE")
if [ "$h" = "$TO" ]; then say "ALREADY INSTALLED (the file is the kit's). Nothing written. finance health $(code "http://127.0.0.1:$FIN_PORT/finance/healthz")"; exit 0; fi
[ "$h" = "$FROM" ] || stop "$LIVE is $h -- neither its pinned live version ($FROM, S681) nor the kit's. It changed after this kit was built: tell Claude."
grep -q "S579_SURGERY_CASES begin" "$FIN/finance_app.py" || stop "the finance app does not carry the S579 mount"
\cp -p "$LIVE" "$SCR/from/surgery_cases.py"
"$APY" -B make_s682.py "$SCR/from" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "the builder refused the live file"; }
[ "$(m5 "$SCR/built/surgery_cases.py")" = "$TO" ] || stop "rebuilt from this box's live bytes, surgery_cases.py is $(m5 "$SCR/built/surgery_cases.py"), not the kit's $TO"
say "[2/8] pin: surgery_cases.py 89a668a9 (S681); rebuilt here from the live bytes ($(grep -c '^edit ok' "$SCR/make.txt") counted edits + the desk + the word pass): byte for byte the kit's copy"
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile surgery_cases.py walk_s682.py probe_s682.py make_s682.py || stop "the kit's python does not compile on $py"
done
say "[3/8] compiled on both pythons"
W1="$( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s682.py" "$KDIR/surgery_cases.py" 2>&1 | tail -1 )"
copydb "$DB" "$SCR/walk.db" || stop "no scratch copy of the database for the walk"
W2="$( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s682.py" "$KDIR/surgery_cases.py" --db "$SCR/walk.db" 2>&1 | tail -1 )"
copydb "$DB" "$SCR/walk0.db"
W0="$( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s682.py" "$LIVE" --db "$SCR/walk0.db" 2>&1 | tail -1 )"
rm -f "$SCR"/walk*.db
allgreen "$W1" || stop "the walk on a made-up database is not all green ($W1)"
allgreen "$W2" || stop "the walk on a copy of the live database is not all green ($W2)"
[ "$W0" = "$CONTROL_W" ] || stop "the control is not the expected red: the live module gave '$W0', expected '$CONTROL_W'"
say "[4/8] the walk: made-up $W1 · a copy of the live database $W2 · the live module (control) $W0"
mkdir -p "$SCR/fnew" "$SCR/fold"
for d in "$SCR/fnew" "$SCR/fold"; do
  cp -p "$FIN"/*.py "$d/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/" 2>/dev/null
  for sub in finance_ui spine vendor; do [ -d "$FIN/$sub" ] && mkdir -p "$d/$sub" && cp -rp "$FIN/$sub/." "$d/$sub/" 2>/dev/null; done
  rm -f "$d"/*.bak_* 2>/dev/null
done
\cp -p "$KDIR/surgery_cases.py" "$SCR/fnew/"
copydb "$DB" "$SCR/fnew.db" && copydb "$DB" "$SCR/fold.db" || stop "no scratch copies of the database for the probe"
Q1="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s682.py" --fin "$SCR/fnew" --db "$SCR/fnew.db" 2>&1 )"
Q0="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s682.py" --fin "$SCR/fold" --db "$SCR/fold.db" --expect-red 2>&1 )"
rm -rf /tmp/s682_probe_papers /tmp/s682_probe_none
echo "$Q1" | grep -q "^$PROBE_OK" || { echo "$Q1" | tail -24; stop "the look as manoj and shavez through the real finance app is red on copies"; }
echo "$Q0" | grep -q "^PROBE OK negative control" || { echo "$Q0" | tail -24; stop "the probe's control did not go red on the live file"; }
say "[5/8] the real finance app on copies: $(echo "$Q1" | grep '^PROBE OK') · its control: $(echo "$Q0" | grep '^PROBE OK')"
rm -rf "$SCR/fnew" "$SCR/fold" "$SCR"/*.db
f0=$(code "http://127.0.0.1:$FIN_PORT/finance/healthz")
[ "$f0" = 200 ] || stop "not healthy before the install (finance $f0)"
say "[6/8] healthy before the install: finance $f0"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the rebuild, the walk and the probe green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

[ -e "$BAK" ] && [ "$(m5 "$BAK")" != "$FROM" ] && stop "a backup $BAK is there and is not the FROM bytes - left as it is; nothing placed"
\cp -p "$LIVE" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || stop "the backup of $LIVE failed"
DBBAK="$FIN/finance.db.bak_S682_$STAMP"
copydb "$DB" "$DBBAK" || stop "the copy of the database before the change failed"
chmod 600 "$DBBAK" 2>/dev/null
if [ -e "$OFFSW" ]; then
  say "       $OFFSW was already on ($(head -c 120 "$OFFSW" 2>/dev/null)) -- left exactly as found"
else
  mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" && OFF_MINE=1 || stop "could not write $OFFSW"
fi
STG="$FIN/.surgery_cases.py.s682"
{ cat "$KDIR/surgery_cases.py" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; stop "could not stage $LIVE"; }
chmod --reference="$LIVE" "$STG" 2>/dev/null; chown --reference="$LIVE" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$LIVE" || restore "the rename of $LIVE"
[ "$(m5 "$LIVE")" = "$TO" ] || restore "the md5 read back of $LIVE"
say "[7/8] placed and read back: $LIVE at the kit's md5 (backup $(basename "$BAK"); the database copied to $(basename "$DBBAK"))"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait_for "http://127.0.0.1:$FIN_PORT/finance/healthz" 200)
c3=$(code "http://127.0.0.1:$FIN_PORT/finance/surgery/implants")
"$SYSTEMCTL" is-active --quiet "$FSVC" || restore "$FSVC is not active"
{ [ "$c1" = 200 ] && [ "$c3" = 302 ]; } || restore "finance health $c1 / the desk $c3 (302 expected without a login)"
MF=""
command -v "$JOURNALCTL" >/dev/null 2>&1 && MF="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -E "surgery_cases NOT mounted|Traceback|ImportError" | head -1)"
[ -z "$MF" ] || restore "the module did not mount: $MF"
mkdir -p "$SCR/fpl"
cp -p "$FIN"/*.py "$SCR/fpl/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/fpl/" 2>/dev/null
for sub in finance_ui spine vendor; do [ -d "$FIN/$sub" ] && mkdir -p "$SCR/fpl/$sub" && cp -rp "$FIN/$sub/." "$SCR/fpl/$sub/" 2>/dev/null; done
rm -f "$SCR/fpl"/*.bak_* 2>/dev/null
copydb "$DB" "$SCR/fpl.db" || restore "no copy of the database for the look on the placed file"
Q2="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s682.py" --fin "$SCR/fpl" --db "$SCR/fpl.db" 2>&1 )"
rm -rf /tmp/s682_probe_papers /tmp/s682_probe_none
[ "${REHEARSE_RED_AT:-}" = 8 ] && Q2="rehearsal: a forced red at [8/8]"
echo "$Q2" | grep -q "^$PROBE_OK" || { echo "$Q2" | tail -24; restore "the look as manoj and shavez on the placed file is red"; }
say "[8/8] $FSVC restarted, health $c1, /finance/surgery/implants $c3 without a login (the gate); $(echo "$Q2" | grep '^PROBE OK') on the placed file"
[ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0
release_lock
say ""
say "$KIT: DONE. The implant bills desk is the 'Implant bills' tab on IPD cases (/finance/surgery/implants): the supplier's bill"
say "with its scan, a cheque written on its own and tied to its bills later, paid and confirmed; old cases are settled by you on the"
say "supplier's page; section 6 on every case shows where each implant stands. The word is Supplier everywhere."
say "undo (one line): \\cp -p $BAK $LIVE && $SYSTEMCTL restart $FSVC"
exit 0
