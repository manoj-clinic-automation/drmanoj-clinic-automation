#!/bin/bash
# =============================================================================
#  install_ledger_statement.sh · kit S237_LEDGER_STATEMENT
#  Run by:  bash /root/deploy/vps_deploy.sh S237_LEDGER_STATEMENT
#
#  Places a READ-ONLY reader and then runs it, so the August statement is on
#  screen at the end of the one line. It has no --write and no --fix: it opens
#  the ledger, prints, and stops. The ledger is append-only and stays that way.
#
#  Red path: undoes only what this run did. No service is touched.
# =============================================================================
set -u
KIT="S237_LEDGER_STATEMENT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="/usr/bin/python3"
TARGET="/root/ledger_statement.py"
LED="${LEDGER_DIR:-/root/staff_ledger}/ledger.jsonl"
MONTH="${MONTH:-2026-08}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BAK=""; PLACED=0

fail() { echo "!! RED — $*"
  if [ "$PLACED" -eq 1 ]; then
    if [ -n "$BAK" ] && [ -f "$BAK" ]; then cp -f "$BAK" "$TARGET" && echo "   restored the previous $TARGET"
    else rm -f "$TARGET" 2>/dev/null; echo "   removed the $TARGET this run had just created"; fi
  else echo "   $TARGET was NOT touched by this run"; fi
  echo "   the ledger was never opened for writing and cannot have changed"; exit 1; }

cd "$KDIR" || fail "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || fail "SUMS.md5 gate failed — kit corrupt"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || fail "KIT_ID.txt names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum ledger_statement.py | awk '{print $1}')" ] \
  || fail "KIT_ID.txt does not match ledger_statement.py (F-88)"
echo "-- gates green"

if [ -f "$TARGET" ]; then BAK="${TARGET}.bak_S237_${STAMP}"; cp -f "$TARGET" "$BAK" || fail "backup failed"; fi
cp -f ledger_statement.py "$TARGET" || fail "copy to $TARGET failed"
PLACED=1
[ "$(md5sum "$TARGET" | awk '{print $1}')" = "$(md5sum ledger_statement.py | awk '{print $1}')" ] \
  || fail "the copied file does not match the kit's"
"$PY" -m py_compile "$TARGET" || fail "py_compile failed"
OUT="$("$PY" "$TARGET" --selftest)" || fail "selftest failed: $OUT"
echo "$OUT" | grep -q " 0 failures" || fail "selftest not clean: $OUT"
echo "-- $OUT"
echo "-- placed and verified: $TARGET"

[ -f "$LED" ] || fail "no ledger at $LED — set LEDGER_DIR if it lives elsewhere"
echo "-- reading $LED ($(wc -l < "$LED") lines)"
echo ""
"$PY" "$TARGET" --file "$LED" --month "$MONTH"
echo ""
echo "A spreadsheet of the open advances, if you want one:"
echo ""
echo "  $PY $TARGET --file $LED --month $MONTH --csv /root/advances_$MONTH.csv"
echo ""
echo "One person only:   $PY $TARGET --file $LED --month $MONTH --staff Darpan"
echo "Include cleared:   add --all"
