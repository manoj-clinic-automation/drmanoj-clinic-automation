#!/bin/bash
# =====================================================================
#  S189_W1a — F-137: "Where the cash is" reads CUSTODY, not MOVEMENTS
#
#  THE FINDING. S188 built /finance/api/where-is-the-cash on cash_movement
#  and reasoned, in the endpoint's own docstring, that the drawer read over
#  two lakh because "the money left the room and never left the books."
#  That is wrong, and it was about to cost real money.
#
#  v_day_cash computes  cash_out_p = SUM(cash_movement WHERE direction='out').
#  So EVERY movement row is subtracted from cash in hand, whatever the party.
#  Recording the doctors' holdings there -- the only way to make the card
#  speak, as built -- would have taken cash in hand from Rs 2,05,198 to about
#  Rs 30,000 and destroyed the agreement the 17 Aug 2026 PHYSICAL COUNT
#  established: drawer 0, owner 18,963, Dr Bhawna 1,56,235, total 1,75,198.
#
#  OWNER RULING (S189): cash held by either doctor IS cash in hand, merely
#  located elsewhere. So custody is LOCATION and lives in cash_custody_event,
#  which no view in the cash ledger reads. S186 built that table and then
#  wrote the facts into a sentence in cash_count.explanation instead.
#
#  WHAT CHANGES. The endpoint reads cash_custody_event; places (drawer,
#  counter, bank) are never shown as parked WITH anybody; and the payload now
#  carries the physical count the position rests on. The page is NOT touched
#  -- the additions are additive keys, so finance_entry.html needs no change.
#
#  SIX NEW CHECKS prove both halves of the finding as one sequence: a custody
#  event moves the CARD and not the ledger; a cash_movement moves the LEDGER
#  and not the card. If those two ever swap again, the suite goes red.
#
#  RISK: this changes what one maker-facing API returns. It changes no page,
#  no money, no table. Until S189_C1a runs, the card keeps reading zero --
#  which is what it reads today.
#
#  D317 chain: SUMS -> KIT_ID -> currency gate -> DIFFERENTIAL smoke BEFORE
#  any swap -> backup -> apply -> verify -> honest red that restores.
#  bash -n'd whole (F-126).
# =====================================================================
set -u
KIT="S189_W1a"
APP=/root/finance/finance_app.py
SVC=clinic-finance
STAMP=$(date +%Y%m%d_%H%M%S)
HERE=$(cd "$(dirname "$0")" && pwd)

WANT_APP=16faf98caa720a662316fa235a4b35b9      # the S189_G1a build
NEW_APP=583092c015c37d97fc240d09637b5ea7

say(){ printf '%s\n' "$*"; }
die(){ say ""; say "*** RED: $*"; say "*** Nothing has been changed."; exit 1; }

say "==============================================================="
say " $KIT  ·  F-137 — custody is location, movement is quantity"
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

[ -f "$APP" ] || die "$APP not found"
GOT_APP=$(md5sum "$APP" | cut -d' ' -f1)
say "[2/7] live finance_app.py         : $GOT_APP"
if [ "$GOT_APP" != "$WANT_APP" ]; then
  say "      expected                    : $WANT_APP  (the S189_G1a build)"
  die "the live app is not the build this kit was made on. Install S189_G1a first, or re-pin from the box (D321(d))."
fi
say "      currency gate               : PASS"

say ""
say "[3/7] THE PROJECTION -- written down BEFORE anything is measured."
say "      (a) the CURRENT app's smoke suite passes with ZERO failures."
say "      (b) the NEW app's smoke suite passes with ZERO failures."
say "      (c) the NEW suite runs EXACTLY SIX MORE checks -- 482 -> 488."
say "      Any of the three failing is a RED and nothing is swapped."
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
mkdir -p "$STAGE" || die "cannot create $STAGE"
cp "$HERE/finance_app_W1a.py" "$STAGE/finance_app.py" || die "cannot stage the new app"
for f in /root/finance/*.py /root/finance/*.sql; do
  b=$(basename "$f"); [ "$b" = "finance_app.py" ] && continue
  cp "$f" "$STAGE/" 2>/dev/null
done
mkdir -p "$STAGE/finance_ui"
cp /root/finance/finance_ui/*.html "$STAGE/finance_ui/" 2>/dev/null

NEWOUT=$(cd "$STAGE" && FINANCE_DB=/root/finance/finance.db \
         /usr/bin/python3 finance_app.py --selftest 2>&1)
printf '%s\n' "$NEWOUT" > /tmp/${KIT}_smoke_new.txt
read -r NEW_P NEW_T <<< "$(printf '%s\n' "$NEWOUT" | sed -n 's/^SMOKE \([0-9]*\)\/\([0-9]*\) passed.*/\1 \2/p' | head -1)"
[ -n "${NEW_T:-}" ] || { tail -20 /tmp/${KIT}_smoke_new.txt; die "the NEW app's smoke suite did not report a result"; }
say "[5/7] new app smoke (staged)      : $NEW_P/$NEW_T"
[ "$NEW_P" = "$NEW_T" ] || { grep '  FAIL' /tmp/${KIT}_smoke_new.txt; die "the new app is red on the real store. NOT installing."; }
[ "$NEW_T" -gt "$OLD_T" ] || die "the new suite runs $NEW_T checks and the old ran $OLD_T -- checks were lost, not added."
[ "$((NEW_T - OLD_T))" -eq 6 ] || die "the new suite adds $((NEW_T - OLD_T)) checks, the projection said 6. STOP and read why."
say "      projection (a)(b)(c)        : ALL THREE HELD  (+6 checks, 0 failures)"

BK=/root/finance/_backup_${KIT}_${STAMP}
mkdir -p "$BK" || die "cannot create the backup folder"
cp -p "$APP" "$BK/finance_app.py" || die "backup of the app failed"
say "[6/7] backup                      : $BK"

restore(){
  cp -p "$BK/finance_app.py" "$APP"
  systemctl restart "$SVC" >/dev/null 2>&1
  sleep 2
}

cp "$HERE/finance_app_W1a.py" "$APP" || { restore; die "the app swap failed"; }
chmod 644 "$APP"
GOT_APP=$(md5sum "$APP" | cut -d' ' -f1)
if [ "$GOT_APP" != "$NEW_APP" ]; then
  restore; die "what landed on disk is not what the kit shipped. Restored."
fi
systemctl restart "$SVC" || { restore; die "the service refused to restart. Restored."; }
sleep 3

HZ=$(curl -s --max-time 10 http://127.0.0.1:8106/finance/healthz)
case "$HZ" in
  *'"ok":true'*) : ;;
  *) say "      healthz said: $HZ"; restore; die "the app is not healthy after the swap. Restored." ;;
esac

read -r LIVE_P LIVE_T <<< "$(smoke "$APP" live)"
if [ -z "${LIVE_T:-}" ] || [ "$LIVE_P" != "$LIVE_T" ]; then
  grep '  FAIL' /tmp/${KIT}_smoke_live.txt 2>/dev/null
  restore; die "the installed app is red. Restored."
fi
if [ "$LIVE_T" != "$NEW_T" ]; then
  restore; die "the installed suite ran $LIVE_T checks, the rehearsal ran $NEW_T. Restored."
fi

say "[7/7] installed and verified LIVE : $LIVE_P/$LIVE_T"
say ""
say "==============================================================="
say " GREEN.  $KIT is live."
say "   finance_app.py   $NEW_APP"
say "   smoke  $OLD_P/$OLD_T  ->  $LIVE_P/$LIVE_T   (+$((LIVE_T - OLD_T)) checks, 0 failures)"
say "   backup $BK"
say ""
say " WHAT CHANGED, in one line:"
say "   Darpan's card now asks the custody table where the cash is."
say "   It will still read ZERO until S189_C1a records the count --"
say "   that is correct, and it is the next kit."
say ""
say " Pin this md5 into the KB Register as it stands (D321(d))."
say "==============================================================="
exit 0
