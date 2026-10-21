#!/bin/bash
# =============================================================================
#  install_S611_LEDGER_STATEMENT.sh · kit S611 (session S331, 21-Oct-2026) · follows S609 (installed 19:39 IST)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S611_LEDGER_STATEMENT/install_S611_LEDGER_STATEMENT.sh
#  DRY=1 before bash: pins, rebuild, selftest, walk and control only -- nothing changed.   --undo: the S609 file back.
#
#  THE OWNER, 21-Oct-2026 19:57-20:16 IST: with "All months" the statement must show every month in the system,
#  non-confusing: when advances were taken and how much, which were settled, the salary cleared, the advances current;
#  the word "advance remaining"; for every staff member.  One block per month (taken · cut from salary, line by line ·
#  other items · salary: base - advances - leave/late/fines = paid, from the LOCKED salary sheet · advance remaining at
#  month end), the running month from the close's own dry run, every advance on one line, the old lines kept closed
#  under "Technical entries".  Read-only: no ledger or salary figure changes.
# =============================================================================
set -u
KIT="S611_LEDGER_STATEMENT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s611_backup}"
SRDB="${SRDB:-/root/staff_register/staff_register.db}"
F="${F:-/root/staff_ledger.py}"
LDIR="${LDIR:-/root/staff_ledger}"
SCSV="${SCSV:-/root/staff_master.csv}"
SVC="${SVC:-staff-ledger}"
BASE="${BASE:-http://127.0.0.1:8043}"
PIN_IN="2fc0542f57766207d65eb14d128ca985"
W=/tmp/s611_walk
HAVE_LOCK=0
on_exit() { rm -rf "$W" /tmp/s611_rb.py; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
PYTHONPYCACHEPREFIX=/tmp/s611_pyc "$PY" -m py_compile staff_ledger.py walk_s611.py edits_s611.py || stop "the kit's code does not compile"
rm -rf /tmp/s611_pyc
NEW=$(m5 staff_ledger.py)

check_up() {                      # sets OKH; never inside $( )
  OKH=0
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1
  V=0
  for i in $(seq 1 30); do
    sleep 1
    V=$(curl -s --max-time 5 "$BASE/ledger/login" | grep -c "4.0-S611-STATEMENT")
    [ "$V" = "1" ] && break
  done
  [ "$V" = "1" ] && OKH=1
}

if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  b=$(ls -1t "$BK"/staff_ledger.py.bak_S611_* 2>/dev/null | head -1)
  [ -n "$b" ] && \cp -f "$b" "$F" && echo "    staff_ledger.py put back ($(m5 "$F" | cut -c1-8))"
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1; sleep 4
  echo "    $SVC: $(systemctl is-active "$SVC")"
  echo "UNDONE."; exit 0
fi

echo "[1] pins"
NOW=$(m5 "$F")
if [ "$NOW" = "$NEW" ]; then echo "    ALREADY INSTALLED (staff_ledger.py ${NEW:0:8})"; exit 0; fi
[ "$NOW" = "$PIN_IN" ] || stop "staff_ledger.py is not the S609 file this kit was built on (${NOW:0:8}, expected ${PIN_IN:0:8})"
echo "    staff_ledger.py ${NOW:0:8} (v3.9-S609)"

echo "[2] rebuild from the live bytes"
"$PY" -B edits_s611.py "$F" /tmp/s611_rb.py "$KDIR/staff_ledger.py" || stop "the kit's file is not exactly the live file plus this kit's edits"

echo "[3] the file's own selftest, in a scratch folder"
rm -rf "$W"; mkdir -p "$W/st" "$W/new" "$W/old"; chmod 700 "$W"
\cp -f staff_ledger.py "$W/new/"; \cp -f "$F" "$W/old/"
( cd "$W/st" && LEDGER_DIR="$W/st/L" STAFF_CSV="$W/st/sm.csv" ATT_BASE="$W/st" STAFF_REGISTER_DB=/nonexistent NTFY_URL= timeout 600 "$PY" -B "$W/new/staff_ledger.py" --selftest > "$W/selftest.txt" 2>&1 )
grep -q "SELFTEST PASSED" "$W/selftest.txt" || { tail -5 "$W/selftest.txt"; stop "the ledger's own selftest did not pass on the new file"; }
echo "    $(grep -m1 'SELFTEST PASSED' "$W/selftest.txt" | cut -c1-60)"

echo "[4] the walk (a made-up person; then scratch COPIES of the live ledger and staff register -- the live ones are only read)"
"$PY" -B walk_s611.py --code "$W/new" --scratch "$W/s1" --live-ledger "$LDIR" --live-register "$SRDB" --staff-csv "$SCSV" > "$W/walk.txt" 2>&1
WK=$?; grep -E "^WALK|every |each month|running month" "$W/walk.txt" | sed 's/^/    /'; tail -1 "$W/walk.txt" | sed 's/^/    walk: /'
[ "$WK" = 0 ] || { grep "FAIL\|RED\|Error" "$W/walk.txt" | head -8; stop "the walk is not green"; }
"$PY" -B walk_s611.py --code "$W/old" --scratch "$W/s2" > "$W/ctl.txt" 2>&1
[ $? != 0 ] && echo "    control on the live file: RED, as it must be ($(grep -m1 'RED' "$W/ctl.txt" | cut -c1-60))" \
            || stop "the control did not go red -- the walk cannot tell old from new"
rm -rf "$W"
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[5] backup -> $BK"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -f "$F" "$BK/staff_ledger.py.bak_S611_$NOW"; chmod 600 "$BK"/*
echo "    staff_ledger.py kept"

echo "[6] placed"
\cp -f staff_ledger.py "$F"
[ "$(m5 "$F")" = "$NEW" ] || stop "staff_ledger.py did not land byte-exact" "Run the line again with --undo at the end."
echo "    staff_ledger.py ${NOW:0:8} -> ${NEW:0:8}"

echo "[7] $SVC restarted and checked"
check_up
if [ "$OKH" != 1 ]; then
  \cp -f "$BK/staff_ledger.py.bak_S611_$NOW" "$F"
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1
  stop "the ledger did not come back with the new version" "The old file was put back and $SVC restarted."
fi
echo "    the ledger answers, v4.0-S611-STATEMENT"

echo "[8] pins"
echo "    $(md5sum "$F")"
echo "DONE. Open https://followup.dr-manoj.in/ledger/statement?staff=Surendra"
