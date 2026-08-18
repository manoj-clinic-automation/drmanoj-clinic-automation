#!/bin/bash
# =====================================================================
#  S189_E1b — the expense MENU: free text demoted, identity server-resolved
#
#  OWNER RULING (S189): expense entry on Darpan's page moves from free
#  text to a category menu, and -- "Darpan draws only his salary advance
#  from the medical cash" -- the staff selector is REMOVED entirely.
#
#  F-139, found on the way: the old page's staff dropdown was hardcoded
#  fiction -- <option value="1">Darpan</option><option value="2">Someone
#  else</option> -- ids pointing at a staff_ref table that has been EMPTY
#  since S179 and that nothing in the app ever read or wrote. Surveyed on
#  the box first: ZERO rows ever carried a staff_id, so the loaded gun
#  was never fired. From this kit the SERVER resolves the identity (the
#  F-84 rule: the client does not get to name who money attributes to),
#  lazily creating the one real staff_ref row on first use, and a
#  client-sent staff id is ignored.
#
#  THE MENU (one authored source, in the app; the selftest holds the
#  served page to every label so the two copies cannot drift):
#     Medicine purchase (stock) · Shop expense · Transport / courier ·
#     My salary advance · Other (write details, required)
#  A skipped choice is REFUSED server-side -- never quietly written as an
#  uncategorised row, which is the rogue this menu exists to end. The
#  advance writes the exact string the three S184 rows already carry
#  ("Salary advance - Darpan"), so history stays one queryable value.
#
#  Checker pages untouched. Old cached pages keep working (their shape is
#  accepted; their staff ids are ignored).
#
#  E1b, NOT E1a. The first kit refused itself at its own gate on the box:
#  its selftest hunted a rehearsal day FORWARD from 1 April and landed on
#  the store's first hole -- a Sunday in early April, 135 days back --
#  where the save answers `too_old` (BACKFILL_WINDOW_DAYS=120) before the
#  expense parse the checks exist to test. All six went red, nothing was
#  swapped: the D317 chain doing its job. The failure was REPRODUCED
#  offline on a store given the box's shape (a beyond-window gap: the
#  exact six FAILs), then fixed -- the finder now searches BACKWARD from
#  today, the direction the D2/F-129 blocks already use, and every check
#  prints the server's actual error when it fails. Rehearsed green on
#  FOUR store shapes: continuous, mid-window gap, beyond-window gap,
#  custody-migrated. The page is byte-identical to E1a's; only the
#  selftest changed, so the check count stays 509.
#
#  D317 chain: SUMS -> KIT_ID -> currency gate (BOTH files) ->
#  DIFFERENTIAL smoke BEFORE any swap -> backup -> apply -> verify ->
#  honest red that restores. bash -n'd whole (F-126).
# =====================================================================
set -u
KIT="S189_E1b"
APP=/root/finance/finance_app.py
PAGE=/root/finance/finance_ui/finance_entry.html
SVC=clinic-finance
STAMP=$(date +%Y%m%d_%H%M%S)
HERE=$(cd "$(dirname "$0")" && pwd)

WANT_APP=41788368ec815b804d276df63c796575      # S189_W1b
WANT_PAGE=d3844bb96a1d496e5882cfbbb695cbf4     # S188_D2c
NEW_APP=5cb73ff83b591535053c7911026ecd8b
NEW_PAGE=1c7d2dc3179f29e9de0b9fb0d77c6fe1

say(){ printf '%s\n' "$*"; }
die(){ say ""; say "*** RED: $*"; say "*** Nothing has been changed."; exit 1; }

say "==============================================================="
say " $KIT  ·  the expense menu — free text is a choice, not a default"
say "==============================================================="

cd "$HERE" || die "cannot enter the kit folder"
[ -f SUMS.md5 ] || die "SUMS.md5 is missing from the kit"
if ! md5sum -c SUMS.md5 > /tmp/${KIT}_sums.txt 2>&1; then
  cat /tmp/${KIT}_sums.txt; die "the kit's own files do not match SUMS.md5"
fi
if grep -qi 'WARNING' /tmp/${KIT}_sums.txt; then
  cat /tmp/${KIT}_sums.txt
  die "md5sum printed a WARNING -- that is a fail, not a note (F-119)"
fi
say "[1/7] kit bytes verified          : $(grep -c ': OK$' /tmp/${KIT}_sums.txt) files OK"
say "      KIT_ID                      : $(cat KIT_ID.txt 2>/dev/null || echo '(none)')"

[ -f "$APP" ]  || die "$APP not found"
[ -f "$PAGE" ] || die "$PAGE not found"
GOT_APP=$(md5sum "$APP"  | cut -d' ' -f1)
GOT_PAGE=$(md5sum "$PAGE" | cut -d' ' -f1)
say "[2/7] live finance_app.py         : $GOT_APP"
say "      live finance_entry.html     : $GOT_PAGE"
[ "$GOT_APP" = "$WANT_APP" ] || { say "      expected app                : $WANT_APP (S189_W1b)"; \
  die "the live app is not the build this kit was made on. Re-pin from the box (D321(d))."; }
[ "$GOT_PAGE" = "$WANT_PAGE" ] || { say "      expected page               : $WANT_PAGE (S188_D2c)"; \
  die "the live entry page is not the build this kit was made on. STOP."; }
say "      currency gate               : PASS (both files)"

say ""
say "[3/7] THE PROJECTION -- written down BEFORE anything is measured."
say "      (a) the CURRENT app's smoke suite: GREEN, zero failures."
say "      (b) the NEW app + NEW page, staged: GREEN, zero failures,"
say "          and EXACTLY 21 MORE checks -- 488 -> 509 on this box."
say "      Either failing is a RED and nothing is swapped."
say ""

smoke(){
  local out
  out=$(cd /root/finance && FINANCE_DB=/root/finance/finance.db \
        /usr/bin/python3 "$1" --selftest 2>&1)
  printf '%s\n' "$out" > "/tmp/${KIT}_smoke_$2.txt"
  printf '%s\n' "$out" | sed -n 's/^SMOKE \([0-9]*\)\/\([0-9]*\) passed.*/\1 \2/p' | head -1
}

read -r OLD_P OLD_T <<< "$(smoke "$APP" old)"
[ -n "${OLD_T:-}" ] || { tail -20 /tmp/${KIT}_smoke_old.txt; die "the CURRENT app's smoke suite did not report a result"; }
say "[4/7] current app smoke           : $OLD_P/$OLD_T"
[ "$OLD_P" = "$OLD_T" ] || { grep '  FAIL' /tmp/${KIT}_smoke_old.txt; die "the box is already red BEFORE this kit. Fix that first."; }

STAGE=/tmp/${KIT}_stage_$STAMP
mkdir -p "$STAGE/finance_ui" || die "cannot create $STAGE"
cp "$HERE/finance_app_E1b.py" "$STAGE/finance_app.py" || die "cannot stage the new app"
for f in /root/finance/*.py /root/finance/*.sql; do
  b=$(basename "$f"); [ "$b" = "finance_app.py" ] && continue
  cp "$f" "$STAGE/" 2>/dev/null
done
cp /root/finance/finance_ui/*.html "$STAGE/finance_ui/" 2>/dev/null
cp "$HERE/finance_ui/finance_entry.html.new" "$STAGE/finance_ui/finance_entry.html" || die "cannot stage the new page"

NEWOUT=$(cd "$STAGE" && FINANCE_DB=/root/finance/finance.db \
         /usr/bin/python3 finance_app.py --selftest 2>&1)
printf '%s\n' "$NEWOUT" > /tmp/${KIT}_smoke_new.txt
read -r NEW_P NEW_T <<< "$(printf '%s\n' "$NEWOUT" | sed -n 's/^SMOKE \([0-9]*\)\/\([0-9]*\) passed.*/\1 \2/p' | head -1)"
[ -n "${NEW_T:-}" ] || { tail -20 /tmp/${KIT}_smoke_new.txt; die "the NEW build's smoke suite did not report a result"; }
say "[5/7] new build smoke (staged)    : $NEW_P/$NEW_T"
[ "$NEW_P" = "$NEW_T" ] || { grep '  FAIL' /tmp/${KIT}_smoke_new.txt; die "the new build is red on the real store. NOT installing."; }
[ "$NEW_T" -gt "$OLD_T" ] || die "checks were lost, not added."
[ "$((NEW_T - OLD_T))" -eq 21 ] || die "the new suite adds $((NEW_T - OLD_T)) checks, the projection said 21. STOP and read why."
say "      projection (a)(b)           : BOTH HELD  (+21 checks, 0 failures)"

BK=/root/finance/_backup_${KIT}_${STAMP}
mkdir -p "$BK/finance_ui" || die "cannot create the backup folder"
cp -p "$APP"  "$BK/finance_app.py"                || die "backup of the app failed"
cp -p "$PAGE" "$BK/finance_ui/finance_entry.html" || die "backup of the page failed"
say "[6/7] backup                      : $BK"

restore(){
  cp -p "$BK/finance_app.py" "$APP"
  cp -p "$BK/finance_ui/finance_entry.html" "$PAGE"
  systemctl restart "$SVC" >/dev/null 2>&1
  sleep 2
}

cp "$HERE/finance_app_E1b.py" "$APP"                     || { restore; die "the app swap failed"; }
cp "$HERE/finance_ui/finance_entry.html.new" "$PAGE"     || { restore; die "the page swap failed"; }
chmod 644 "$APP" "$PAGE"
GOT_APP=$(md5sum "$APP"  | cut -d' ' -f1)
GOT_PAGE=$(md5sum "$PAGE" | cut -d' ' -f1)
if [ "$GOT_APP" != "$NEW_APP" ] || [ "$GOT_PAGE" != "$NEW_PAGE" ]; then
  restore; die "what landed on disk is not what the kit shipped. Restored."
fi
systemctl restart "$SVC" || { restore; die "the service refused to restart. Restored."; }
sleep 3

HZ=$(curl -s --max-time 10 http://127.0.0.1:8106/finance/healthz)
case "$HZ" in
  *'"ok":true'*) : ;;
  *) say "      healthz said: $HZ"; restore; die "the app is not healthy after the swap. Restored." ;;
esac

read -r L_P L_T <<< "$(smoke "$APP" live)"
if [ -z "${L_T:-}" ] || [ "$L_P" != "$L_T" ]; then
  grep '  FAIL' /tmp/${KIT}_smoke_live.txt 2>/dev/null
  restore; die "the installed build is red. Restored."
fi
[ "$L_T" = "$NEW_T" ] || { restore; die "the installed suite ran $L_T checks, the rehearsal ran $NEW_T. Restored."; }

say "[7/7] installed and verified LIVE : $L_P/$L_T   backup: $BK"
say ""
say "==============================================================="
say " GREEN.  $KIT is live."
say "   finance_app.py                 $NEW_APP"
say "   finance_ui/finance_entry.html  $NEW_PAGE"
say "   smoke  $OLD_P/$OLD_T  ->  $L_P/$L_T   (+21 checks, 0 failures)"
say ""
say " WHAT CHANGED, in one line:"
say "   Darpan picks an expense category from a menu; free text now needs"
say "   a deliberate choice AND written details; a salary advance is his"
say "   own, attributed by the server, and posts to the Staff Ledger only"
say "   on your approval (the wiring itself is still D3, unbuilt)."
say ""
say " Pin these two md5s into the KB Register as they stand (D321(d))."
say "==============================================================="
exit 0
