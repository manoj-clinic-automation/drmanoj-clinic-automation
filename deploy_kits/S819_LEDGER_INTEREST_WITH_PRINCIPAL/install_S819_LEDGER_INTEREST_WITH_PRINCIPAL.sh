#!/bin/bash
# =============================================================================
#  install_S819_LEDGER_INTEREST_WITH_PRINCIPAL.sh · kit S819 (session S453, 14-Nov-2026) · follows S614
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S819_LEDGER_INTEREST_WITH_PRINCIPAL/install_S819_LEDGER_INTEREST_WITH_PRINCIPAL.sh
#  DRY=1 before bash: pins, rebuild, selftest, walk and control only -- nothing changed.   --undo: the S614 file back
#  (only over this kit's own file, and only from this kit's backup).
#
#  THE OWNER'S RULING (F-1367): no interest is taken, charged or capitalised on a loan in a month unless principal
#  comes off the same loan that month. All or nothing: a month that cannot carry the whole instalment holds it
#  whole -- no interest, no penalty, the balance unchanged, the loan one month longer. A month that can carry it
#  behaves exactly as before. Untouched: the owner's skip / defer and their penalty, the advances ahead of the
#  loan, interest-free advances, every stored row.
# =============================================================================
set -u
KIT="S819_LEDGER_INTEREST_WITH_PRINCIPAL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s819_backup}"
F="${F:-/root/staff_ledger.py}"
LDIR="${LDIR:-/root/staff_ledger}"
SCSV="${SCSV:-/root/staff_master.csv}"
SVC="${SVC:-staff-ledger}"
BASE="${BASE:-http://127.0.0.1:8043}"
PIN_IN="85e2ab51a6a8e34e39cfcace20eac6be"
VER="4.3-S819-INTEREST"
W=/tmp/s819_walk
HAVE_LOCK=0
on_exit() { rm -rf "$W" /tmp/s819_rb.py /tmp/s819_pyc; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
PYTHONPYCACHEPREFIX=/tmp/s819_pyc "$PY" -m py_compile staff_ledger.py walk_s819.py edits_s819.py || stop "the kit's code does not compile"
rm -rf /tmp/s819_pyc
NEW=$(m5 staff_ledger.py)

check_up() {                      # sets OKH; never inside $( )
  OKH=0
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1
  V=0
  for i in $(seq 1 30); do
    sleep 1
    V=$(curl -s --max-time 5 "$BASE/ledger/login" | grep -c "$VER")
    [ "$V" = "1" ] && break
  done
  [ "$V" = "1" ] && OKH=1
}

put_back() {                      # the S614 file back, the service restarted -- and what was left is checked
  \cp -f "$BK/staff_ledger.py.bak_S819_$NOW" "$F"
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1
  [ "$(m5 "$F")" = "$PIN_IN" ] || echo "!! THE OLD FILE DID NOT GO BACK BYTE-EXACT ($(m5 "$F" | cut -c1-8)) -- send a photo of this screen to Claude NOW"
}

if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  b=$(ls -1t "$BK"/staff_ledger.py.bak_S819_* 2>/dev/null | head -1)
  [ "$(m5 "$F")" = "$NEW" ] || stop "the live staff_ledger.py is not this kit's file ($(m5 "$F" | cut -c1-8)) -- undo would overwrite something else"
  [ -n "$b" ] || stop "no backup of this kit is in $BK -- there is nothing to put back"
  [ "$(m5 "$b")" = "$PIN_IN" ] || stop "the backup in $BK is not the S614 file ($(m5 "$b" | cut -c1-8))"
  if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: would put back $b; nothing changed"; exit 0; fi
  \cp -f "$b" "$F" && echo "    staff_ledger.py put back ($(m5 "$F" | cut -c1-8))"
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1; sleep 4
  echo "    $SVC: $(systemctl is-active "$SVC")"
  echo "UNDONE."; exit 0
fi

echo "[1] pins"
NOW=$(m5 "$F")
if [ "$NOW" = "$NEW" ]; then echo "    ALREADY INSTALLED (staff_ledger.py ${NEW:0:8})"; exit 0; fi
[ "$NOW" = "$PIN_IN" ] || stop "staff_ledger.py is not the S614 file this kit was built on (${NOW:0:8}, expected ${PIN_IN:0:8})"
echo "    staff_ledger.py ${NOW:0:8} (v4.2-S614)"

echo "[2] rebuild from the live bytes"
"$PY" -B edits_s819.py "$F" /tmp/s819_rb.py "$KDIR/staff_ledger.py" || stop "the kit's file is not exactly the live file plus this kit's edits"

echo "[3] the file's own selftest, in a scratch folder"
rm -rf "$W"; mkdir -p "$W/st" "$W/new" "$W/old"; chmod 700 "$W"
\cp -f staff_ledger.py "$W/new/"; \cp -f "$F" "$W/old/"
( cd "$W/st" && LEDGER_DIR="$W/st/L" STAFF_CSV="$W/st/sm.csv" ATT_BASE="$W/st" STAFF_REGISTER_DB=/nonexistent NTFY_URL= timeout 600 "$PY" -B "$W/new/staff_ledger.py" --selftest > "$W/selftest.txt" 2>&1 )
grep -q "SELFTEST PASSED" "$W/selftest.txt" || { tail -5 "$W/selftest.txt"; stop "the ledger's own selftest did not pass on the new file"; }
echo "    $(grep -m1 'SELFTEST PASSED' "$W/selftest.txt" | cut -c1-60)"

echo "[4] the walk (made-up people and figures; then a scratch COPY of the live ledger -- the live one is only read)"
"$PY" -B walk_s819.py --code "$W/new" --old "$W/old" --scratch "$W/s1" --live-ledger "$LDIR" --staff-csv "$SCSV" > "$W/walk.txt" 2>&1
WK=$?; grep -E "the next close:|every person|loan shape" "$W/walk.txt" | sed 's/^  ok  /   /'; tail -2 "$W/walk.txt" | head -1 | sed 's/^/    walk: /'
[ "$WK" = 0 ] || { grep "FAIL\|RED\|Error" "$W/walk.txt" | head -8; stop "the walk is not green"; }
"$PY" -B walk_s819.py --code "$W/old" --old "$W/old" --scratch "$W/s2" > "$W/ctl.txt" 2>&1
[ $? != 0 ] && echo "    control on the live file: RED, as it must be ($(grep -c '^  FAIL' "$W/ctl.txt") checks; first: $(grep -m1 'FAIL' "$W/ctl.txt" | cut -c8-60))" \
            || stop "the control did not go red -- the walk cannot tell old from new"
rm -rf "$W"
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[5] backup -> $BK"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -f "$F" "$BK/staff_ledger.py.bak_S819_$NOW"; chmod 600 "$BK"/*
[ "$(m5 "$BK/staff_ledger.py.bak_S819_$NOW")" = "$NOW" ] || stop "the backup did not land byte-exact"
echo "    staff_ledger.py kept"

echo "[6] placed"
\cp -f staff_ledger.py "$F"
if [ "$(m5 "$F")" != "$NEW" ]; then
  put_back
  stop "staff_ledger.py did not land byte-exact" "The old file was put back and $SVC restarted."
fi
if ! PYTHONPYCACHEPREFIX=/tmp/s819_pyc "$PY" -m py_compile "$F"; then
  put_back
  stop "the placed file does not compile" "The old file was put back and $SVC restarted."
fi
echo "    staff_ledger.py ${NOW:0:8} -> ${NEW:0:8}"

echo "[7] $SVC restarted and checked"
check_up
if [ "$OKH" != 1 ]; then
  put_back
  stop "the ledger did not come back with the new version" "The old file was put back and $SVC restarted."
fi
echo "    the ledger answers, v$VER"

echo "[8] what changes"
echo "    A loan with interest: if the salary cannot carry the WHOLE instalment at the month's close, nothing is"
echo "    taken for it -- no interest, nothing added -- and the loan runs one month longer. The Statement, the Loans"
echo "    page and New entry say 'held'. A month that can carry the instalment is exactly as before."
echo "[9] pins"
echo "    $(md5sum "$F")"
echo "DONE."
