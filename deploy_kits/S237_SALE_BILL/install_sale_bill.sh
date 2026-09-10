#!/bin/bash
# =============================================================================
#  install_sale_bill.sh · kit S237_SALE_BILL — keep the sale bill's money row
#
#  Run by:  bash /root/deploy/vps_deploy.sh S237_SALE_BILL
#
#  Green path: md5 gate -> kit identity (F-88) -> back up any existing copy ->
#              place the file -> md5-verify the copy landed -> py_compile ->
#              selftest must be clean -> find where the exports live on this
#              machine -> READ them and print what would be kept.
#
#  IT WRITES NOTHING TO THE DATABASE. Not one row. The table is created and
#  filled only when the owner runs the one line printed at the end, so the
#  numbers are seen before anything is stored.
#
#  Red path  : anything fails -> the previous file is restored (or the new one
#              removed if this run created it), and we exit non-zero. The red
#              path undoes ONLY what this run did -- earned at S237, where a
#              first draft deleted a working file it had never written.
#              No service is stopped, started or restarted at any point.
# =============================================================================
set -u
KIT="S237_SALE_BILL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="/usr/bin/python3"                      # the finance app is system python
FIN="${FINANCE_DIR:-/root/finance}"
TARGET="$FIN/sale_bill.py"
DB="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BAK=""; PLACED=0

fail() { echo "!! RED — $*"
  if [ "$PLACED" -eq 1 ]; then
    if [ -n "$BAK" ] && [ -f "$BAK" ]; then cp -f "$BAK" "$TARGET" && echo "   restored the previous $TARGET"
    else rm -f "$TARGET" 2>/dev/null; echo "   removed the $TARGET this run had just created"; fi
  else
    echo "   $TARGET was NOT touched by this run"
  fi
  echo "   nothing is installed, NO DATABASE ROW WAS WRITTEN, no service was touched"; exit 1; }

cd "$KDIR" || fail "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || fail "SUMS.md5 gate failed — kit corrupt"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || fail "KIT_ID.txt names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum sale_bill.py | awk '{print $1}')" ] \
  || fail "KIT_ID.txt does not match sale_bill.py (F-88)"
echo "-- gates green: SUMS.md5 and KIT_ID.txt agree"

[ -d "$FIN" ] || fail "$FIN does not exist — is this the finance box?"
if [ -f "$TARGET" ]; then BAK="${TARGET}.bak_S237_${STAMP}"; cp -f "$TARGET" "$BAK" \
  || fail "could not back up the existing $TARGET"; echo "-- backed up the previous copy to $BAK"; fi

cp -f sale_bill.py "$TARGET" || fail "copy to $TARGET failed"
PLACED=1
[ "$(md5sum "$TARGET" | awk '{print $1}')" = "$(md5sum sale_bill.py | awk '{print $1}')" ] \
  || fail "the copied file does not match the kit's — the write did not land"
echo "-- copied and md5-verified: $TARGET"

"$PY" -m py_compile "$TARGET" || fail "py_compile failed on $TARGET"
echo "-- py_compile clean (using $PY)"
OUT="$("$PY" "$TARGET" --selftest)" || fail "selftest reported failures: $OUT"
echo "$OUT" | grep -q " 0 failures" || fail "selftest did not report 0 failures: $OUT"
echo "-- $OUT"

echo ""
echo "================ WHERE ARE THE EXPORTS ON THIS MACHINE? ================"
LOC="$("$PY" "$TARGET" --locate 2>&1)"; echo "$LOC"
ROOT="$(echo "$LOC" | sed -n 's/^   -> use: --scan //p' | head -1)"
echo "======================================================================="

if [ -n "$ROOT" ]; then
  echo ""
  echo "=========== WHAT IT WOULD KEEP — read only, NOTHING WRITTEN ==========="
  "$PY" "$TARGET" --scan "$ROOT" --marg-dir "$FIN" 2>&1 | tail -22
  echo "======================================================================="
  echo ""
  echo "$KIT INSTALLED — file in place, gates green, DATABASE UNTOUCHED."
  echo ""
  echo "If those numbers look right, keep them with this one line:"
  echo ""
  echo "  $PY $TARGET --scan $ROOT --marg-dir $FIN --write $DB"
  echo ""
else
  echo ""
  echo "$KIT INSTALLED — file in place, gates green, DATABASE UNTOUCHED."
  echo ""
  echo "!! The exports are not under any of the folders it knows about."
  echo "   Nothing is wrong with the install. Tell Claude what --locate printed"
  echo "   above and it will name the right folder."
  echo ""
fi
