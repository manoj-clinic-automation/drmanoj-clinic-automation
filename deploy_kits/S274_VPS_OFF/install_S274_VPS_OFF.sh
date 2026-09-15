#!/bin/bash
# =============================================================================
#  install_S274_VPS_OFF.sh  --  Club 3h, the VPS half.
#
#  Gives the four Sanjeevni server jobs the same off switch the two PCs got at
#  S259: a file whose presence stops the job and whose absence starts it again.
#
#  NOTHING IS STOPPED BY INSTALLING THIS. No cron line is touched, no service is
#  restarted, no marker is created. Every job keeps running exactly as it does
#  now -- it simply gains a way to be stopped.
#
#  Gates, in order. Any failure rolls all four files back and exits non-zero:
#    1. pin gate        -- all four must be the files this kit was built on
#    2. patch           -- all-or-nothing; each file backed up and read back
#    3. compile         -- every patched file
#    4. own selftests   -- each file's OWN --selftest must still say 0 failures;
#                          one that cannot run here says SKIPPED, never PASSED
#    5. switch proof    -- the guard is proven against a TEMPORARY folder, so
#                          the proof never creates a marker a live job reads
#    6. the folder      -- /root/finance/_off is created, EMPTY, with a README
# =============================================================================
set -u

PY=/root/wa/venv/bin/python3
DIR=/root/finance
OFF="$DIR/_off"
KIT="$(cd "$(dirname "$0")" && pwd)"
FILES="spine_cadence.py sale_attribution.py export_watch.py salts_refresh.py"

say() { echo "[S274] $*"; }

rollback() {
  for f in $FILES; do
    b=$(ls "$DIR/$f".bak_S274_* 2>/dev/null | head -1)
    if [ -n "$b" ]; then cp -f "$b" "$DIR/$f"; say "rolled back $f"; fi
  done
}

fail() { say "FAILED: $*"; rollback; say "nothing is switched off; every job runs as before."; exit 1; }

say "1/6  pin gate"
"$PY" "$KIT/patch_off_switches_s274.py" --dir "$DIR" --check || { say "the pin gate refused. Nothing changed."; exit 2; }

say "2/6  patch"
"$PY" "$KIT/patch_off_switches_s274.py" --dir "$DIR" || fail "the patcher refused"

say "3/6  compile"
for f in $FILES; do
  "$PY" -c "import py_compile;py_compile.compile('$DIR/$f',doraise=True)" || fail "$f does not compile"
  say "     ok $f"
done

say "4/6  each file's own selftest"
SKIPPED=0
for f in spine_cadence.py sale_attribution.py export_watch.py; do
  out=$(cd "$DIR" && "$PY" "$f" --selftest 2>&1 | tail -1)
  case "$out" in
    *"0 failures"*) say "     ok $f -- $out" ;;
    *failures*)     say "     $f -- $out"; fail "$f selftest reports failures" ;;
    *)              say "     SKIPPED $f -- its selftest could not run here (NOT a pass): ${out:0:90}"; SKIPPED=$((SKIPPED+1)) ;;
  esac
done
say "     salts_refresh.py has no selftest of its own -- SKIPPED, not a pass."
SKIPPED=$((SKIPPED+1))

say "5/6  the switch, proven against a temporary folder"
"$PY" "$KIT/prove_off_s274.py" "$DIR" || fail "the switch did not prove"

say "6/6  the folder"
mkdir -p "$OFF" || fail "cannot create $OFF"
cat > "$OFF/_READ_ME.txt" <<'TXT'
THE OFF SWITCHES -- Sanjeevni's server jobs
===========================================
A file in THIS folder stops a job. Delete it and the job starts again at its
next scheduled run. Nothing is unregistered and no cron line is touched.

    ALL_OFF              stops all four below
    SPINE_OFF            the item spine cadence   (every 30 min 09-23, 23:50)
    ATTRIBUTION_OFF      the discount attribution (every 30 min 09-23, 23:55)
    EXPORT_WATCH_OFF     the "did Amir export"    (23:40 and 10:45)
    SALTS_REFRESH_OFF    the salt-list refresh    (every 10 min 08-22)

A trailing .txt on any name works too.

The Marg collector and its shadow have their own, older switch, and this folder
does not affect them:   /root/marg_ingest/OFF

Turn one off:   touch /root/finance/_off/SPINE_OFF
Turn it on:     rm -f /root/finance/_off/SPINE_OFF
All off:        touch /root/finance/_off/ALL_OFF
All on:         rm -f /root/finance/_off/ALL_OFF

Or use:         bash /root/finance/sanjeevni_switch.sh status
TXT
cp -f "$KIT/sanjeevni_switch.sh" "$DIR/sanjeevni_switch.sh" && chmod +x "$DIR/sanjeevni_switch.sh"
say "     $OFF created, EMPTY -- so nothing is switched off."
say "     $DIR/sanjeevni_switch.sh installed"

say "done.  $SKIPPED check(s) SKIPPED above are not passes."
say "backups: $DIR/<file>.bak_S274_<pin>"
bash "$DIR/sanjeevni_switch.sh" status
exit 0
