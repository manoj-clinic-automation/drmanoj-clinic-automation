#!/bin/bash
# =============================================================================
#  install_S273_BACKUP_GAP.sh
#
#  Widens the nightly code bundle so the six live files that had NO off-box
#  copy in ANY store are carried. Nothing else on the box is touched: no
#  service is restarted, no page changes, no database is opened, no Drive
#  upload happens here (the 01:35 cron does that, unchanged).
#
#  It proves the change ON THE BOX before it keeps it:
#    1. pin gate        -- refuses unless code_bundle.py is the file we built on
#    2. BEFORE build    -- runs the LIVE tool, records what it carries
#    3. patch           -- anchored, backed up, read back
#    4. AFTER build     -- runs the PATCHED tool over the same real tree
#    5. assert          -- nothing lost, the six present, the tool's own
#                         secret scan reports no new exclusion failure
#    6. rollback        -- on ANY failure the backup is restored byte-identically
#                         and the script exits non-zero
# =============================================================================
set -u

PY=/root/wa/venv/bin/python3
TARGET=/root/state_backup/code_bundle.py
KIT="$(cd "$(dirname "$0")" && pwd)"
FROM=27e42d0d970a3e475aae7b2fdcebb780
TO=ed5b483f6eb09f0e3663091a01aaa251
BAK="${TARGET}.bak_S273_27e42d0d"
WORK=/root/state_backup/_s273_work
OUT=/root/state_backup/code_nightly.tar.gz

say() { echo "[S273] $*"; }

fail() {
  say "FAILED: $*"
  if [ -f "$BAK" ]; then
    cp -f "$BAK" "$TARGET"
    now=$(md5sum "$TARGET" | cut -d' ' -f1)
    if [ "$now" = "$FROM" ]; then
      say "ROLLED BACK -- $TARGET is $FROM again, byte-identical."
    else
      say "ROLLBACK DID NOT VERIFY -- $TARGET reads $now. STOP AND SAY SO."
    fi
  else
    say "nothing had been changed yet; nothing to roll back."
  fi
  rm -rf "$WORK"
  exit 1
}

say "1/6  pin gate"
[ -x "$PY" ] || { say "FAILED: $PY not found"; exit 1; }
[ -f "$TARGET" ] || { say "FAILED: $TARGET not found"; exit 1; }
NOW=$(md5sum "$TARGET" | cut -d' ' -f1)
if [ "$NOW" = "$TO" ]; then say "ALREADY INSTALLED -- $TARGET is already $TO. Nothing to do."; exit 0; fi
if [ "$NOW" != "$FROM" ]; then say "REFUSING -- $TARGET reads $NOW, expected $FROM"; exit 2; fi
say "     ok, $TARGET is $FROM"

rm -rf "$WORK"; mkdir -p "$WORK" || { say "FAILED: cannot create $WORK"; exit 1; }

say "2/6  BEFORE build -- what the live tool carries today"
[ -f "$OUT" ] && cp -f "$OUT" "$WORK/before_bundle.tar.gz"
"$PY" "$TARGET" build > "$WORK/before.log" 2>&1 || { say "FAILED: the LIVE tool could not build. Nothing changed."; cat "$WORK/before.log" | tail -20; rm -rf "$WORK"; exit 1; }
tar tzf "$OUT" | grep -v -E '^(MANIFEST\.md5|BUNDLE_INFO\.txt|crontab\.txt)$' | sort > "$WORK/before.txt" || { say "FAILED: could not list the before bundle"; rm -rf "$WORK"; exit 1; }
say "     it carries $(wc -l < "$WORK/before.txt") files"

say "3/6  patch"
"$PY" "$KIT/patch_code_bundle_s273.py" --file "$TARGET" || fail "the patcher refused"
NOW=$(md5sum "$TARGET" | cut -d' ' -f1)
[ "$NOW" = "$TO" ] || fail "after patching, $TARGET reads $NOW, not the predicted $TO"
"$PY" -c "import py_compile,sys; py_compile.compile('$TARGET', doraise=True)" || fail "the patched file does not compile"
say "     ok, $TARGET is $TO and compiles"

say "4/6  AFTER build -- the patched tool over the same real tree"
"$PY" "$TARGET" build > "$WORK/after.log" 2>&1 || { tail -20 "$WORK/after.log"; fail "the PATCHED tool could not build"; }
tar tzf "$OUT" | grep -v -E '^(MANIFEST\.md5|BUNDLE_INFO\.txt|crontab\.txt)$' | sort > "$WORK/after.txt" || fail "could not list the after bundle"
say "     it carries $(wc -l < "$WORK/after.txt") files"

say "5/6  assert"
LOST=$(comm -23 "$WORK/before.txt" "$WORK/after.txt")
if [ -n "$LOST" ]; then echo "$LOST" | sed 's/^/       LOST: /'; fail "the patched tool drops files the live one carried"; fi
say "     nothing lost"

MISSING=0
for f in root/assetapp/asset_register.py root/shared/sarvam_ocr.py root/deploy/email_agent.py root/deploy/gen_live_pins.py root/deploy/verify_live_pins.py root/deploy/sweep_baseline.txt root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py root/finance/freshness_legs.json; do
  if grep -qx "$f" "$WORK/after.txt"; then say "     + $f"; else say "     MISSING: $f"; MISSING=$((MISSING+1)); fi
done
if [ "$MISSING" -gt 0 ]; then
  say "     NOTE: a MISSING line above means that path does not exist on this box,"
  say "     or is still being excluded. Neither is a reason to keep a half-change."
  fail "$MISSING of the named files are not in the new bundle"
fi

"$PY" -c "
import tarfile,sys
t=tarfile.open('$OUT'); n=[x for x in t.getnames()]
bad=[x for x in n if x.endswith('.env') or x.endswith('.conf') or '.db' in x.split('/')[-1] or 'config' in x.split('/')[-1]]
print('secret-shaped names in the new bundle: %d' % len(bad))
[print('   !!', b) for b in bad]
sys.exit(1 if bad else 0)
" || fail "the new bundle carries a secret-shaped name"
say "     no secret-shaped name in the new bundle"

say "6/6  done"
GAINED=$(comm -13 "$WORK/before.txt" "$WORK/after.txt" | wc -l)
say "     +$GAINED files, -0 files."
say "     backup kept at $BAK"
say "     the 01:35 cron ships the wider bundle tonight, unchanged in every other way."
rm -rf "$WORK"
exit 0
