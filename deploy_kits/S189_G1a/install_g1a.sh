#!/bin/bash
# =====================================================================
#  S189_G1a — F-130: the DESIGN is asserted, not just the ids
#
#  A page-only kit that preserves every id is invisible to an id-based
#  test. S188 shipped exactly such a kit and 464 green checks could not
#  see the one thing it changed. Until this lands, any served page can
#  silently revert its design and the whole suite stays green.
#
#  What this adds: four checks, on the REAL served routes, holding each
#  page to its RECORDED design state.
#
#  IMPORTANT — the backlog said "approvals, workbench and review". Two of
#  those three were surveyed before a line was written, and they do not
#  carry Clinic Design Language v1 AT ALL: the workbench is the S187_M1a
#  build and the review page is the untouched S179 build, both older than
#  the design language itself. Asserting v1 on them would have gone RED
#  on install. That instruction had been written without opening the
#  files -- the F-132 shape, in the record rather than in the code.
#
#  So the table declares the truth as measured, both ways:
#     /finance/entry      v1  YES  (S188_D2a)
#     /finance/approvals  v1  YES  (S187_H1b / H1c)
#     /finance/workbench  v1  NO   (S187_M1a, pre-v1)
#     /finance/review     v1  NO   (S179, pre-v1)
#  The two NOs are asserted negatively ON PURPOSE, so that rebuilding
#  either page under v1 cannot land silently either -- it has to come
#  here and flip the flag.
#
#  RISK: none at runtime. The whole change is 35 lines inside
#  def selftest(), after every route definition. Nothing the app serves
#  is touched. No page, no migration, no data.
#
#  D317 chain: SUMS -> KIT_ID -> currency gate -> DIFFERENTIAL smoke
#  BEFORE any swap -> backup -> apply -> verify -> honest red that
#  restores. bash -n'd whole (F-126).
# =====================================================================
set -u
KIT="S189_G1a"
APP=/root/finance/finance_app.py
SVC=clinic-finance
STAMP=$(date +%Y%m%d_%H%M%S)
HERE=$(cd "$(dirname "$0")" && pwd)

# the bytes this kit was BUILT ON — recovered from deploy_kits/S188_D2c by
# hash, not by filename (D188), because the repo's finance/ tree is stale.
WANT_APP=f06e139b7651329a72b08bbc5779077f
# what this kit installs
NEW_APP=16faf98caa720a662316fa235a4b35b9

say(){ printf '%s\n' "$*"; }
die(){ say ""; say "*** RED: $*"; say "*** Nothing has been changed."; exit 1; }

say "==============================================================="
say " $KIT  ·  F-130 — the design is asserted, not just the ids"
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
[ -f "$APP" ] || die "$APP not found"
GOT_APP=$(md5sum "$APP" | cut -d' ' -f1)
say "[2/7] live finance_app.py         : $GOT_APP"
if [ "$GOT_APP" != "$WANT_APP" ]; then
  say "      expected                    : $WANT_APP"
  die "the live app is not the build this kit was made on. STOP, re-pin from the box (D321(d))."
fi
say "      currency gate               : PASS"

# ---------------------------------------------------- 3. the projection
say ""
say "[3/7] THE PROJECTION -- written down BEFORE anything is measured."
say "      (a) the CURRENT app's smoke suite passes with ZERO failures."
say "      (b) the NEW app's smoke suite passes with ZERO failures."
say "      (c) the NEW suite runs EXACTLY FOUR MORE checks than the current"
say "          one -- 478 -> 482 on this box, if the box is where we left it."
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

# the new app is rehearsed from a staging directory so /root/finance is
# untouched while it runs. It reads the live store READ-ONLY: the suite copies
# the database to a throwaway and deletes it (that is its own first act).
STAGE=/tmp/${KIT}_stage_$STAMP
mkdir -p "$STAGE" || die "cannot create $STAGE"
cp "$HERE/finance_app_G1a.py" "$STAGE/finance_app.py" || die "cannot stage the new app"
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
[ "$((NEW_T - OLD_T))" -eq 4 ] || die "the new suite adds $((NEW_T - OLD_T)) checks, the projection said 4. STOP and read why."
say "      projection (a)(b)(c)        : ALL THREE HELD  (+4 checks, 0 failures)"

# ---------------------------------------------------- 6. backup, then apply
BK=/root/finance/_backup_${KIT}_${STAMP}
mkdir -p "$BK" || die "cannot create the backup folder"
cp -p "$APP" "$BK/finance_app.py" || die "backup of the app failed"
say "[6/7] backup                      : $BK"

restore(){
  cp -p "$BK/finance_app.py" "$APP"
  systemctl restart "$SVC" >/dev/null 2>&1
  sleep 2
}

cp "$HERE/finance_app_G1a.py" "$APP" || { restore; die "the app swap failed"; }
chmod 644 "$APP"

GOT_APP=$(md5sum "$APP" | cut -d' ' -f1)
if [ "$GOT_APP" != "$NEW_APP" ]; then
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
say "   finance_app.py   $NEW_APP"
say "   smoke  $OLD_P/$OLD_T  ->  $LIVE_P/$LIVE_T   (+$((LIVE_T - OLD_T)) checks, 0 failures)"
say "   backup $BK"
say ""
say " WHAT CHANGED, in one line:"
say "   Nothing you or your staff can see. The suite can now tell whether"
say "   a page still LOOKS like itself, which 464 green checks could not."
say ""
say " Pin this md5 into the KB Register as it stands (D321(d))."
say "==============================================================="
exit 0
