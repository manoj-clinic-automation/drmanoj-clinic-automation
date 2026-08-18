#!/bin/bash
# =====================================================================
#  S190_E2 — D330: three categories · a DERIVED advance ceiling ·
#             COMPULSORY per-expense evidence · the re-save wipe closed
#
#  THE CONTRACT: claude/S190_Expense_Menu_Redesign_D330.md (signed S190,
#  supersedes D329). One kit, not three -- the owner's "minimum steps"
#  ruling; the E2a->E2b->E2c order survives INSIDE it (identity first,
#  then the ceiling, then evidence), they simply land together.
#
#  WHAT THIS CHANGES, in plain words:
#   1. Darpan's expense menu is now THREE choices: My salary advance ·
#      Home expenses (personal / COD delivery) · Other expenses. Home and
#      Other both require written details. The retired heads (medicine
#      purchase / shop / transport) are gone -- petty spends live on the
#      manual book (owner ruling; a digital petty book is PARKED).
#   2. The advance is CAPPED: percentage of base salary, floored to
#      Rs 100, DERIVED from two settings (advance.base_p Rs 20,000 ·
#      advance.pct 75 -> Rs 15,000/calendar month). Nothing stores the
#      rupee figure (F-136). The page shows month-to-date beside the
#      ceiling BEFORE he types; the server refuses anything over it with
#      both figures in the message. Above the ceiling = the staff
#      pipeline, never the drawer.
#   3. Home/Other expenses CANNOT BE FILED without a bill attached to
#      the row -- no escape hatch (owner ruling). He photographs the
#      bill when he pays; when filing next day the shared scan widget
#      offers camera AND gallery (verified on this box: the widget's
#      input carries no capture attribute). Evidence gates FILE, never
#      Save. Salary advances need no bill.
#   4. THE DRAFT-RESAVE WIPE IS CLOSED: the page now refills expenses,
#      cash movements and non-cash bills when a day is opened, and every
#      expense row carries a stable uid (new day_expense.expense_uid) so
#      its attached bill survives the save's delete-and-reinsert. The
#      cash-movement row also gained the reference field the server
#      always accepted but the page never offered.
#   5. The CLINIC entry gets the same two expense categories + the same
#      compulsory evidence. NO salary-advance path there, deliberately.
#   6. Home expenses total separately as the PROPRIETOR'S DRAWINGS on
#      the tile and the month grid, both units (owner ruling, S190).
#
#  SCHEMA: two lazily-added columns on day_expense (expense_uid,
#  category_kind -- category_fixed carries a CHECK allowing only
#  NULL/'salary_advance', found by the offline rehearsal, left exactly
#  as the schema wanted it) and one lazily-created table
#  expense_attachment keyed (day_entry_id, expense_uid). No migration
#  file: the DDL is authoritative in code (the day_mirror_reveal
#  pattern). All additive; nothing existing is altered or dropped.
#
#  REHEARSED OFFLINE ON FOUR STORE SHAPES (F-140): the live shape
#  (Sundays absent, 14/15 Aug drafts, 17 Aug unfiled) · the month
#  already AT its ceiling (the post-sitting world -- this rehearsal
#  caught two legacy checks that would have gone red on live and they
#  were made delta-disciplined) · a beyond-window hole (the E1a killer)
#  · a double run on one store (lazy-DDL idempotency). All four:
#  542/542.
#
#  THE PROJECTION, written before measuring: 509 -> 542 on this box,
#  +33 exactly (-2 menu labels, +3 in the E1a block, +23 D330 medical,
#  +8 D330 clinic, +1 clinic-day finder added during rehearsal and
#  counted honestly here rather than smoothed over).
#
#  D317 chain: SUMS -> KIT_ID -> currency gate (THREE files) ->
#  differential smoke BEFORE any swap -> backup -> apply -> verify ->
#  honest red that restores. bash -n'd whole (F-126).
# =====================================================================
set -u
KIT="S190_E2"
APP=/root/finance/finance_app.py
PAGE=/root/finance/finance_ui/finance_entry.html
CPAGE=/root/finance/finance_ui/finance_entry_clinic.html
SVC=clinic-finance
STAMP=$(date +%Y%m%d_%H%M%S)
HERE=$(cd "$(dirname "$0")" && pwd)

WANT_APP=5cb73ff83b591535053c7911026ecd8b       # S189_E1b
WANT_PAGE=1c7d2dc3179f29e9de0b9fb0d77c6fe1      # S189_E1b
WANT_CPAGE=0c64fda2005ea3cd6692aeb8fd3dc728     # S182_C2a — VERIFIED ON THE BOX
# (kit v2: the first kit carried 0c64fda2eb26... here, a full hash written
#  from a truncated record prefix -- the F-109/F-116 shape, in this file.
#  The gate refused it against the true live value, which is the chain
#  working. The PAYLOAD was always built on the live 0c64fda2005e... bytes;
#  only this constant was wrong. Transcribed now from the owner's own
#  md5sum run on the box, S190.)
NEW_APP=02062855ccd97056c2be64ce04d606cb
NEW_PAGE=f819bdf95de14fc331428cf6bea4c37e
NEW_CPAGE=1c930a3ec71873ce774770dab524ba0e

say(){ printf '%s\n' "$*"; }
die(){ say ""; say "*** RED: $*"; say "*** Nothing has been changed."; exit 1; }

say "==============================================================="
say " $KIT · D330: the menu, the ceiling, the evidence, the refill"
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

[ -f "$APP" ]   || die "$APP not found"
[ -f "$PAGE" ]  || die "$PAGE not found"
[ -f "$CPAGE" ] || die "$CPAGE not found"
GOT_APP=$(md5sum "$APP"   | cut -d' ' -f1)
GOT_PAGE=$(md5sum "$PAGE" | cut -d' ' -f1)
GOT_CPAGE=$(md5sum "$CPAGE" | cut -d' ' -f1)
say "[2/7] live finance_app.py         : $GOT_APP"
say "      live finance_entry.html     : $GOT_PAGE"
say "      live finance_entry_clinic   : $GOT_CPAGE"
[ "$GOT_APP" = "$WANT_APP" ] || { say "      expected app                : $WANT_APP (S189_E1b)"; \
  die "the live app is not the build this kit was made on. Re-pin from the box (D321(d))."; }
[ "$GOT_PAGE" = "$WANT_PAGE" ] || { say "      expected page               : $WANT_PAGE (S189_E1b)"; \
  die "the live entry page is not the build this kit was made on. STOP."; }
[ "$GOT_CPAGE" = "$WANT_CPAGE" ] || { say "      expected clinic page        : $WANT_CPAGE (S182_C2a)"; \
  die "the live clinic page is not the build this kit was made on. STOP."; }
say "      currency gate               : PASS (all three files)"

say ""
say "[3/7] THE PROJECTION -- written down BEFORE anything is measured."
say "      (a) the CURRENT app's smoke suite: GREEN, zero failures."
say "      (b) the NEW app + BOTH new pages, staged: GREEN, zero"
say "          failures, and EXACTLY 33 MORE checks -- 509 -> 542."
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
cp "$HERE/finance_app_E2.py" "$STAGE/finance_app.py" || die "cannot stage the new app"
for f in /root/finance/*.py /root/finance/*.sql; do
  b=$(basename "$f"); [ "$b" = "finance_app.py" ] && continue
  cp "$f" "$STAGE/" 2>/dev/null
done
cp /root/finance/finance_ui/*.html "$STAGE/finance_ui/" 2>/dev/null
cp "$HERE/finance_ui/finance_entry.html.new" "$STAGE/finance_ui/finance_entry.html" || die "cannot stage the new page"
cp "$HERE/finance_ui/finance_entry_clinic.html.new" "$STAGE/finance_ui/finance_entry_clinic.html" || die "cannot stage the new clinic page"

NEWOUT=$(cd "$STAGE" && FINANCE_DB=/root/finance/finance.db \
         /usr/bin/python3 finance_app.py --selftest 2>&1)
printf '%s\n' "$NEWOUT" > /tmp/${KIT}_smoke_new.txt
read -r NEW_P NEW_T <<< "$(printf '%s\n' "$NEWOUT" | sed -n 's/^SMOKE \([0-9]*\)\/\([0-9]*\) passed.*/\1 \2/p' | head -1)"
[ -n "${NEW_T:-}" ] || { tail -20 /tmp/${KIT}_smoke_new.txt; die "the NEW build's smoke suite did not report a result"; }
say "[5/7] new build smoke (staged)    : $NEW_P/$NEW_T"
[ "$NEW_P" = "$NEW_T" ] || { grep '  FAIL' /tmp/${KIT}_smoke_new.txt; die "the new build is red on the real store. NOT installing."; }
[ "$NEW_T" -gt "$OLD_T" ] || die "checks were lost, not added."
[ "$((NEW_T - OLD_T))" -eq 33 ] || die "the new suite adds $((NEW_T - OLD_T)) checks, the projection said 33. STOP and read why."
say "      projection (a)(b)           : BOTH HELD  (+33 checks, 0 failures)"

BK=/root/finance/_backup_${KIT}_${STAMP}
mkdir -p "$BK/finance_ui" || die "cannot create the backup folder"
cp -p "$APP"   "$BK/finance_app.py"                        || die "backup of the app failed"
cp -p "$PAGE"  "$BK/finance_ui/finance_entry.html"         || die "backup of the page failed"
cp -p "$CPAGE" "$BK/finance_ui/finance_entry_clinic.html"  || die "backup of the clinic page failed"
say "[6/7] backup                      : $BK"

restore(){
  cp -p "$BK/finance_app.py" "$APP"
  cp -p "$BK/finance_ui/finance_entry.html" "$PAGE"
  cp -p "$BK/finance_ui/finance_entry_clinic.html" "$CPAGE"
  systemctl restart "$SVC" >/dev/null 2>&1
  sleep 2
}

cp "$HERE/finance_app_E2.py" "$APP"                              || { restore; die "the app swap failed"; }
cp "$HERE/finance_ui/finance_entry.html.new" "$PAGE"             || { restore; die "the page swap failed"; }
cp "$HERE/finance_ui/finance_entry_clinic.html.new" "$CPAGE"     || { restore; die "the clinic page swap failed"; }
chmod 644 "$APP" "$PAGE" "$CPAGE"
GOT_APP=$(md5sum "$APP"   | cut -d' ' -f1)
GOT_PAGE=$(md5sum "$PAGE" | cut -d' ' -f1)
GOT_CPAGE=$(md5sum "$CPAGE" | cut -d' ' -f1)
if [ "$GOT_APP" != "$NEW_APP" ] || [ "$GOT_PAGE" != "$NEW_PAGE" ] || [ "$GOT_CPAGE" != "$NEW_CPAGE" ]; then
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
say "   finance_app.py                       $NEW_APP"
say "   finance_ui/finance_entry.html        $NEW_PAGE"
say "   finance_ui/finance_entry_clinic.html $NEW_CPAGE"
say "   smoke  $OLD_P/$OLD_T  ->  $L_P/$L_T   (+33 checks, 0 failures)"
say ""
say " WHAT CHANGED, in one line each:"
say "   The menu is three choices; the advance shows its month total and"
say "   refuses past the derived ceiling (Rs 15,000 for Darpan); a home"
say "   or other expense cannot be FILED without its bill attached (he"
say "   photographs when paying, uploads when filing); re-opening a day"
say "   now brings back everything it holds, so a re-save loses nothing;"
say "   the clinic page gets the same two categories and the same rule."
say ""
say " Pin these three md5s into the KB Register as they stand (D321(d))."
say "==============================================================="
exit 0
