#!/bin/bash
# =============================================================================
#  install_reconcile_aug2.sh · kit S238_RECONCILE_AUG2
#  Run by:  bash /root/deploy/vps_deploy.sh S238_RECONCILE_AUG2
#
#  REVISION 2 of the August stated record (owner, 10-Sep-2026 night): Ranjeet's,
#  Shivani's and Sukhveer's August advances come off the AUGUST salary. The
#  reconciler itself is unchanged (v1.0, 3f3457dd); it is now proven against the
#  live staff_ledger.py v3.7 (49b13f42, S238_CLOSE_GUARD).
#
#  Places the reconciler, proves it on a throw-away COPY of the real ledger, and
#  then prints the DRY RUN: every difference between the owner's stated record
#  and the ledger, and what the next close would take before and after the fix.
#  IT NEVER RUNS --apply. Writing is a separate line the owner chooses to run.
#
#  Red path: undoes only what this run did. No service is touched. The ledger
#  is never opened for writing by this script.
# =============================================================================
set -u
KIT="S238_RECONCILE_AUG2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
RDIR="${RECON_DIR:-/root/staff_ledger_reconcile}"
MODULE="${SL_MODULE:-/root/staff_ledger.py}"
PIN="${SL_PIN:-49b13f42d3a923c5bb2e34230c80e6e8}"      # staff_ledger.py v3.7 (S238_CLOSE_GUARD)
LDIR="${LEDGER_DIR:-/root/staff_ledger}"
STAMP="$(date +%Y%m%d-%H%M%S)"
FILES="ledger_reconcile.py stated_record_2026-08.txt"
PLACED=""; BAKS=""; MADE_DIR=0

fail() { echo "!! RED — $*"
  if [ -n "$PLACED" ]; then
    for f in $PLACED; do
      b="$(echo "$BAKS" | tr ' ' '\n' | grep "/$f.bak_S238_" | head -1)"
      if [ -n "$b" ] && [ -f "$b" ]; then cp -f "$b" "$RDIR/$f" && echo "   restored the previous $RDIR/$f"
      else rm -f "$RDIR/$f"; echo "   removed $RDIR/$f, which this run had created"; fi
    done
    [ "$MADE_DIR" -eq 1 ] && rmdir "$RDIR" 2>/dev/null && echo "   removed the empty $RDIR this run had created"
  else echo "   nothing was placed by this run"; fi
  echo "   the ledger was never opened for writing and cannot have changed"; exit 1; }

cd "$KDIR" || fail "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || fail "SUMS.md5 gate failed — kit corrupt"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || fail "KIT_ID.txt names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum ledger_reconcile.py | awk '{print $1}')" ] \
  || fail "KIT_ID.txt does not match ledger_reconcile.py (F-88)"
echo "-- gates green"

# The service's ExecStart is the only authority on which file runs (S237 trap).
XS="${EXECSTART_TEXT:-$(systemctl show -p ExecStart staff-ledger.service 2>/dev/null)}"
echo "$XS" | grep -q "$MODULE" || fail "staff-ledger.service does not run $MODULE — read its ExecStart before going on"
[ "$(md5sum "$MODULE" | awk '{print $1}')" = "$PIN" ] \
  || fail "$MODULE is not the pinned v3.7 ($PIN) this tool was proven against"
[ -f "$LDIR/ledger.jsonl" ] || fail "no ledger at $LDIR/ledger.jsonl"
echo "-- the service runs $MODULE, and it is the pinned file"

if [ ! -d "$RDIR" ]; then mkdir -p "$RDIR" || fail "cannot create $RDIR"; MADE_DIR=1; fi
chmod 700 "$RDIR"
for f in $FILES; do
  if [ -f "$RDIR/$f" ]; then b="$RDIR/$f.bak_S238_$STAMP"; cp -f "$RDIR/$f" "$b" || fail "backup of $f failed"; BAKS="$BAKS $b"; fi
  cp -f "$f" "$RDIR/$f" || fail "copy of $f failed"
  PLACED="$PLACED $f"
  [ "$(md5sum "$RDIR/$f" | awk '{print $1}')" = "$(md5sum "$f" | awk '{print $1}')" ] || fail "$f did not copy byte-for-byte"
  chmod 600 "$RDIR/$f"
done
"$PY" -m py_compile "$RDIR/ledger_reconcile.py" || fail "py_compile failed"
rm -rf "$RDIR/__pycache__"
M0="$(md5sum "$LDIR/ledger.jsonl" | awk '{print $1}')"
OUT="$(LEDGER_DIR="$LDIR" "$PY" "$RDIR/ledger_reconcile.py" --selftest --module "$MODULE" --ledger-dir "$LDIR" 2>&1)" \
  || fail "selftest failed: $OUT"
echo "$OUT" | grep -q " 0 failures" || fail "selftest not clean: $OUT"
[ "$(md5sum "$LDIR/ledger.jsonl" | awk '{print $1}')" = "$M0" ] || fail "the ledger changed during the selftest — STOP and report"
echo "-- $OUT   (run on a throw-away copy of the real ledger)"
echo "-- placed and verified: $RDIR"
echo ""
LEDGER_DIR="$LDIR" "$PY" "$RDIR/ledger_reconcile.py" --module "$MODULE" --ledger-dir "$LDIR"
echo ""
echo "(installer finished — nothing was written to the ledger)"
