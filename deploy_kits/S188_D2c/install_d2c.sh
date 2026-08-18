#!/bin/bash
# =====================================================================
#  S188_D2c — F-132: the maker's page stops showing the running unit balance,
#             and starts showing what he is actually entitled to know
#
#  "Opening cash - carried from the last filed day" was NOT one day's carry.
#  It came from v_cash_ledger, whose window is UNBOUNDED PRECEDING: a running
#  total of every day since the books began. It was the whole unit cash
#  position, in 24px bold, and it was not TRUE of his drawer -- most of that
#  money is parked with Dr Bhawna (D323).
#
#  D2a gated this route and recorded that its payload was "already correctly
#  scoped". That claim was never tested. This kit is the correction.
#
#  In its place, on the owner's ruling: what IS his to know -- money parked
#  with Dr Manoj or Dr Bhawna (a total line that opens to the two names,
#  current financial year only) and days since the last bank trip.
#
#  F-133 rides along, unfixed by code because code is not what is broken:
#  NOT ONE handover to either doctor has ever been recorded, though the entry
#  has existed on this page since S179. So a zero is rendered as an
#  INSTRUCTION, never as a fact.
#
#  D317 chain: SUMS -> KIT_ID -> currency gate -> DIFFERENTIAL smoke BEFORE any
#  swap -> backup -> apply -> verify -> honest red that restores.
#  bash -n'd whole (F-126).
# =====================================================================
set -u
KIT="S188_D2c"
APP=/root/finance/finance_app.py
PAGE=/root/finance/finance_ui/finance_entry.html
SVC=clinic-finance
STAMP=$(date +%Y%m%d_%H%M%S)
HERE=$(cd "$(dirname "$0")" && pwd)

# the bytes this kit was BUILT ON -- verified from the S187_H1a / S179 kits by
# hash, not by filename (D188). If the box does not carry these, the build is
# stale and nothing may be swapped.
WANT_APP=3a7086f851720dd161bc43c3c1fd45dd
WANT_PAGE=2c23b461bdae5a4ed6a4c4ed4708b4f9
# what this kit installs
NEW_APP=f06e139b7651329a72b08bbc5779077f
NEW_PAGE=d3844bb96a1d496e5882cfbbb695cbf4

say(){ printf '%s\n' "$*"; }
die(){ say ""; say "*** RED: $*"; say "*** Nothing has been changed."; exit 1; }

say "==============================================================="
say " $KIT  ·  F-132 (what the maker may see) + F-133"
say "==============================================================="

# ---------------------------------------------------- 1. the kit's own bytes
cd "$HERE" || die "cannot enter the kit folder"
[ -f SUMS.md5 ] || die "SUMS.md5 is missing from the kit"
if ! md5sum -c SUMS.md5 > /tmp/${KIT}_sums.txt 2>&1; then
  cat /tmp/${KIT}_sums.txt
  die "the kit's own files do not match SUMS.md5"
fi
# F-119: a WARNING line is a FAIL even when the exit code is 0
if grep -qi 'WARNING' /tmp/${KIT}_sums.txt; then
  cat /tmp/${KIT}_sums.txt
  die "md5sum printed a WARNING -- that is a fail, not a note (F-119)"
fi
say "[1/7] kit bytes verified          : $(grep -c ': OK$' /tmp/${KIT}_sums.txt) files OK"
say "      KIT_ID                      : $(cat KIT_ID.txt 2>/dev/null || echo '(none)')"

# ---------------------------------------------------- 2. currency gate
[ -f "$APP" ]  || die "$APP not found"
[ -f "$PAGE" ] || die "$PAGE not found"
GOT_APP=$(md5sum "$APP"  | cut -d' ' -f1)
GOT_PAGE=$(md5sum "$PAGE" | cut -d' ' -f1)
say "[2/7] live finance_app.py         : $GOT_APP"
say "      live finance_entry.html     : $GOT_PAGE"
if [ "$GOT_APP" != "$WANT_APP" ]; then
  say "      expected                    : $WANT_APP"
  die "the live app is not the build this kit was made on. STOP, re-pin from the box (D321(d))."
fi
if [ "$GOT_PAGE" != "$WANT_PAGE" ]; then
  say "      expected                    : $WANT_PAGE"
  die "the live entry page is not the build this kit was made on. STOP."
fi
say "      currency gate               : PASS (both files are the expected builds)"

# ---------------------------------------------------- 3. the projection
say ""
say "[3/7] THE PROJECTION -- written down BEFORE anything is measured."
say "      (a) the CURRENT app's smoke suite passes with ZERO failures."
say "      (b) the NEW app's smoke suite passes with ZERO failures."
say "      (c) the NEW suite runs MORE checks than the current one -- this kit"
say "          adds checks, it does not quietly retire any."
say "      Any of the three failing is a RED and nothing is swapped."
say ""

smoke(){                       # $1 = python file, $2 = label -> echoes "pass total"
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

# the new app is rehearsed from a staging directory so that /root/finance is
# untouched while it runs. It reads the live store READ-ONLY: the suite copies
# the database to a throwaway and deletes it (that is its own first act).
STAGE=/tmp/${KIT}_stage_$STAMP
mkdir -p "$STAGE" || die "cannot create $STAGE"
cp "$HERE/finance_app_D2c.py" "$STAGE/finance_app.py" || die "cannot stage the new app"
for f in /root/finance/*.py /root/finance/*.sql; do
  b=$(basename "$f"); [ "$b" = "finance_app.py" ] && continue
  cp "$f" "$STAGE/" 2>/dev/null
done
mkdir -p "$STAGE/finance_ui"
cp /root/finance/finance_ui/*.html "$STAGE/finance_ui/" 2>/dev/null
cp "$HERE/finance_ui/finance_entry.html.new" "$STAGE/finance_ui/finance_entry.html" || die "cannot stage the new page"

NEWOUT=$(cd "$STAGE" && FINANCE_DB=/root/finance/finance.db \
         /usr/bin/python3 finance_app.py --selftest 2>&1)
printf '%s\n' "$NEWOUT" > /tmp/${KIT}_smoke_new.txt
read -r NEW_P NEW_T <<< "$(printf '%s\n' "$NEWOUT" | sed -n 's/^SMOKE \([0-9]*\)\/\([0-9]*\) passed.*/\1 \2/p' | head -1)"
[ -n "${NEW_T:-}" ] || { tail -20 /tmp/${KIT}_smoke_new.txt; die "the NEW app's smoke suite did not report a result"; }
say "[5/7] new app smoke (staged)      : $NEW_P/$NEW_T"
[ "$NEW_P" = "$NEW_T" ] || { grep '  FAIL' /tmp/${KIT}_smoke_new.txt; die "the new app is red on the real store. NOT installing."; }
[ "$NEW_T" -gt "$OLD_T" ] || die "the new suite runs $NEW_T checks and the old ran $OLD_T -- checks were lost, not added."
say "      projection (a)(b)(c)        : ALL THREE HELD  (+$((NEW_T - OLD_T)) checks, 0 failures)"

# ---------------------------------------------------- 6. backup, then apply
BK=/root/finance/_backup_${KIT}_${STAMP}
mkdir -p "$BK/finance_ui" || die "cannot create the backup folder"
cp -p "$APP"  "$BK/finance_app.py"            || die "backup of the app failed"
cp -p "$PAGE" "$BK/finance_ui/finance_entry.html" || die "backup of the page failed"
say "[6/7] backup                      : $BK"

restore(){
  cp -p "$BK/finance_app.py" "$APP"
  cp -p "$BK/finance_ui/finance_entry.html" "$PAGE"
  systemctl restart "$SVC" >/dev/null 2>&1
  sleep 2
}

cp "$HERE/finance_app_D2c.py" "$APP"                     || { restore; die "the app swap failed"; }
cp "$HERE/finance_ui/finance_entry.html.new" "$PAGE"     || { restore; die "the page swap failed"; }
chmod 644 "$APP" "$PAGE"

GOT_APP=$(md5sum "$APP"  | cut -d' ' -f1)
GOT_PAGE=$(md5sum "$PAGE" | cut -d' ' -f1)
if [ "$GOT_APP" != "$NEW_APP" ] || [ "$GOT_PAGE" != "$NEW_PAGE" ]; then
  restore; die "what landed on disk is not what the kit shipped. Restored."
fi

systemctl restart "$SVC" || { restore; die "the service refused to restart. Restored."; }
sleep 3

# ---------------------------------------------------- 7. verify, live
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
say "   finance_app.py            $NEW_APP"
say "   finance_ui/finance_entry.html $NEW_PAGE"
say "   smoke  $OLD_P/$OLD_T  ->  $LIVE_P/$LIVE_T   (+$((LIVE_T - OLD_T)) checks, 0 failures)"
say "   backup $BK"
say ""
say " WHAT CHANGED, in one line:"
say "   Darpan no longer sees the running unit balance. He now sees what is"
say "   parked with you and Dr Bhawna (opens to the two names, this FY only)"
say "   and days since the last bank trip -- which today reads 19."
say ""
say " READ THIS: both parked figures will show ZERO, because not one"
say "   handover has ever been recorded (F-133). The page says so as an"
say "   instruction, not as a fact. That zero is also why the drawer"
say "   figure has been drifting upward."
say ""
say " Pin these two md5s into the KB Register as they stand (D321(d))."
say "==============================================================="
exit 0
