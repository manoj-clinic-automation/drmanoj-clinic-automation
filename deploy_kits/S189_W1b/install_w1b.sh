#!/bin/bash
# =====================================================================
#  S189_W1b — F-138: the F-137 checks assert DELTAS, not the store's state
#
#  WHAT HAPPENED. S189_C1a ran perfectly -- precheck green, migration
#  applied, verify green, cash in hand untouched -- and then the final
#  smoke re-run went RED on three checks and the installer restored the
#  books. An honest red, doing its job. But the fault was in the CHECKS:
#
#     "parked with Dr Manoj must be Rs 0.00"
#     "custody inside this year must be exactly Rs 12,345.00"
#
#  True on a store with no custody rows. False the moment C1a legitimately
#  recorded the real counted position -- Dr Manoj genuinely holds
#  Rs 18,963 now, so 18,963 + 12,345 is not 12,345. The F-106/F-125
#  family: a state-asserting test, broken by the first real datum. Worse:
#  ONE of the four F-137 checks had already been converted to a delta for
#  exactly this reason, naming F-106 in its own comment -- and its three
#  neighbours were left absolute. That is F-138.
#
#  WHAT THIS KIT CHANGES. The three checks now measure the DELTA their own
#  inserts produce, against whatever position the store already holds.
#  Nothing outside the selftest moves. Same check count: 488 -> 488,
#  because checks were CORRECTED, not added.
#
#  HOW A COUNT-EQUAL KIT PROVES ITSELF (the F-130 problem, met honestly):
#  a count cannot show this change, so this installer REPRODUCES THE
#  FAILURE instead. It applies the C1a migration to a THROWAWAY COPY of
#  the live store and requires:
#     - the CURRENT app on that copy: RED, every FAIL naming F-137
#     - the NEW app on that copy:     GREEN, all 488
#     - the NEW app on the live store: GREEN, all 488
#  The exact red you saw is recreated and then shown fixed, before any
#  swap. If the reproduction does not reproduce, nothing is installed.
#
#  D317 chain throughout. bash -n'd whole (F-126).
# =====================================================================
set -u
KIT="S189_W1b"
APP=/root/finance/finance_app.py
DB=/root/finance/finance.db
SVC=clinic-finance
STAMP=$(date +%Y%m%d_%H%M%S)
HERE=$(cd "$(dirname "$0")" && pwd)

WANT_APP=583092c015c37d97fc240d09637b5ea7      # the S189_W1a build
NEW_APP=41788368ec815b804d276df63c796575
MIG_SQL="$HERE/../S189_C1a/finance_migration_S189_custody.sql"
MIG_MD5=7180e0f1149f194e99cb91cd2a7e5bb1       # D188: the bytes, not the name

say(){ printf '%s\n' "$*"; }
die(){ say ""; say "*** RED: $*"; say "*** Nothing has been changed."; exit 1; }

say "==============================================================="
say " $KIT  ·  F-138 — a check measures its own delta, not the store"
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
say "[1/8] kit bytes verified          : $(grep -c ': OK$' /tmp/${KIT}_sums.txt) files OK"
say "      KIT_ID                      : $(cat KIT_ID.txt 2>/dev/null || echo '(none)')"

[ -f "$APP" ] || die "$APP not found"
[ -f "$DB" ]  || die "$DB not found"
GOT_APP=$(md5sum "$APP" | cut -d' ' -f1)
say "[2/8] live finance_app.py         : $GOT_APP"
if [ "$GOT_APP" != "$WANT_APP" ]; then
  say "      expected                    : $WANT_APP  (the S189_W1a build)"
  die "the live app is not the build this kit was made on. Re-pin from the box (D321(d))."
fi
[ -f "$MIG_SQL" ] || die "cannot find the C1a migration beside this kit ($MIG_SQL)"
GOT_MIG=$(md5sum "$MIG_SQL" | cut -d' ' -f1)
[ "$GOT_MIG" = "$MIG_MD5" ] || die "the C1a migration hashes to $GOT_MIG, expected $MIG_MD5 -- refusing to rehearse with unknown bytes (D188)"
if /usr/bin/python3 -c "import sqlite3,sys;c=sqlite3.connect('file:$DB?mode=ro',uri=True);sys.exit(0 if c.execute(\"SELECT COUNT(*) FROM setting WHERE key='migration.S189_custody'\").fetchone()[0] else 1)"; then
  die "the S189_custody marker is already on the live store -- C1a is applied. That is not the state this kit was rehearsed against; stop and read the record first."
fi
say "      currency gate               : PASS (app is W1a; C1a not applied, as expected)"

say ""
say "[3/8] THE PROJECTION -- written down BEFORE anything is measured."
say "      (a) the CURRENT app on the live store: GREEN, 488/488."
say "      (b) the CURRENT app on a MIGRATED COPY of the live store: RED,"
say "          and every FAIL line names F-137 -- the exact red you saw."
say "      (c) the NEW app on that same migrated copy: GREEN, 488/488."
say "      (d) the NEW app on the live store: GREEN, 488/488. Same count"
say "          as (a) -- checks corrected, not added; (b)->(c) is the proof."
say "      Any of the four failing is a RED and nothing is swapped."
say ""

smoke_db(){                    # $1 = python file, $2 = db, $3 = label
  local out
  out=$(cd /root/finance && FINANCE_DB="$2" /usr/bin/python3 "$1" --selftest 2>&1)
  printf '%s\n' "$out" > "/tmp/${KIT}_smoke_$3.txt"
  printf '%s\n' "$out" | sed -n 's/^SMOKE \([0-9]*\)\/\([0-9]*\) passed.*/\1 \2/p' | head -1
}

read -r A_P A_T <<< "$(smoke_db "$APP" "$DB" old_live)"
[ -n "${A_T:-}" ] || { tail -20 /tmp/${KIT}_smoke_old_live.txt; die "the CURRENT app's smoke suite did not report a result"; }
say "[4/8] (a) current app, live store : $A_P/$A_T"
[ "$A_P" = "$A_T" ] || { grep '  FAIL' /tmp/${KIT}_smoke_old_live.txt; die "the box is already red BEFORE this kit. Fix that first."; }

COPY=/tmp/${KIT}_migrated_copy_$STAMP.db
cp -f "$DB" "$COPY" || die "cannot copy the store for the reproduction"
/usr/bin/python3 -c "import sqlite3;c=sqlite3.connect('$COPY');c.execute('PRAGMA foreign_keys=ON');c.executescript(open('$MIG_SQL').read());c.commit();c.close()" \
  || die "could not apply the C1a migration to the throwaway copy"

read -r B_P B_T <<< "$(smoke_db "$APP" "$COPY" old_migrated)"
[ -n "${B_T:-}" ] || { tail -20 /tmp/${KIT}_smoke_old_migrated.txt; die "the reproduction run did not report a result"; }
say "[5/8] (b) current app, migrated   : $B_P/$B_T   (RED is the point)"
[ "$B_P" != "$B_T" ] || die "the reproduction did NOT reproduce -- the current app is green on a migrated copy. The premise of this kit is wrong; stop and investigate."
NON137=$(grep '^  FAIL' /tmp/${KIT}_smoke_old_migrated.txt | grep -vc 'F-137' || true)
if [ "${NON137:-0}" -ne 0 ]; then
  grep '^  FAIL' /tmp/${KIT}_smoke_old_migrated.txt
  die "the migrated copy fails checks OUTSIDE F-137 -- that is a different fault than the one this kit fixes. Stop."
fi
say "      every FAIL names F-137      : CONFIRMED -- the exact red, recreated"

STAGE=/tmp/${KIT}_stage_$STAMP
mkdir -p "$STAGE" || die "cannot create $STAGE"
cp "$HERE/finance_app_W1b.py" "$STAGE/finance_app.py" || die "cannot stage the new app"
for f in /root/finance/*.py /root/finance/*.sql; do
  b=$(basename "$f"); [ "$b" = "finance_app.py" ] && continue
  cp "$f" "$STAGE/" 2>/dev/null
done
mkdir -p "$STAGE/finance_ui"
cp /root/finance/finance_ui/*.html "$STAGE/finance_ui/" 2>/dev/null

read -r C_P C_T <<< "$( (cd "$STAGE" && FINANCE_DB="$COPY" /usr/bin/python3 finance_app.py --selftest 2>&1) | tee /tmp/${KIT}_smoke_new_migrated.txt | sed -n 's/^SMOKE \([0-9]*\)\/\([0-9]*\) passed.*/\1 \2/p' | head -1)"
[ -n "${C_T:-}" ] || { tail -20 /tmp/${KIT}_smoke_new_migrated.txt; die "the NEW app's migrated-copy run did not report a result"; }
say "[6/8] (c) new app, migrated       : $C_P/$C_T"
[ "$C_P" = "$C_T" ] || { grep '  FAIL' /tmp/${KIT}_smoke_new_migrated.txt; die "the new app is red on the migrated copy -- the fix does not fix. NOT installing."; }

read -r D_P D_T <<< "$( (cd "$STAGE" && FINANCE_DB="$DB" /usr/bin/python3 finance_app.py --selftest 2>&1) | tee /tmp/${KIT}_smoke_new_live.txt | sed -n 's/^SMOKE \([0-9]*\)\/\([0-9]*\) passed.*/\1 \2/p' | head -1)"
[ -n "${D_T:-}" ] || { tail -20 /tmp/${KIT}_smoke_new_live.txt; die "the NEW app's live-store run did not report a result"; }
say "[7/8] (d) new app, live store     : $D_P/$D_T"
[ "$D_P" = "$D_T" ] || { grep '  FAIL' /tmp/${KIT}_smoke_new_live.txt; die "the new app is red on the live store. NOT installing."; }
[ "$D_T" = "$A_T" ] || die "the new suite runs $D_T checks and the old ran $A_T -- this kit corrects checks, it must not change the count. STOP and read why."
rm -f "$COPY"
say "      projection (a)(b)(c)(d)     : ALL FOUR HELD"

BK=/root/finance/_backup_${KIT}_${STAMP}
mkdir -p "$BK" || die "cannot create the backup folder"
cp -p "$APP" "$BK/finance_app.py" || die "backup of the app failed"

restore(){
  cp -p "$BK/finance_app.py" "$APP"
  systemctl restart "$SVC" >/dev/null 2>&1
  sleep 2
}

cp "$HERE/finance_app_W1b.py" "$APP" || { restore; die "the app swap failed"; }
chmod 644 "$APP"
GOT_APP=$(md5sum "$APP" | cut -d' ' -f1)
[ "$GOT_APP" = "$NEW_APP" ] || { restore; die "what landed on disk is not what the kit shipped. Restored."; }
systemctl restart "$SVC" || { restore; die "the service refused to restart. Restored."; }
sleep 3

HZ=$(curl -s --max-time 10 http://127.0.0.1:8106/finance/healthz)
case "$HZ" in
  *'"ok":true'*) : ;;
  *) say "      healthz said: $HZ"; restore; die "the app is not healthy after the swap. Restored." ;;
esac

read -r L_P L_T <<< "$(smoke_db "$APP" "$DB" live)"
if [ -z "${L_T:-}" ] || [ "$L_P" != "$L_T" ]; then
  grep '  FAIL' /tmp/${KIT}_smoke_live.txt 2>/dev/null
  restore; die "the installed app is red. Restored."
fi

say "[8/8] installed and verified LIVE : $L_P/$L_T   backup: $BK"
say ""
say "==============================================================="
say " GREEN.  $KIT is live."
say "   finance_app.py   $NEW_APP"
say ""
say " WHAT CHANGED, in one line:"
say "   The three checks that refused your books yesterday now measure"
say "   their own footprint instead of demanding an empty store."
say ""
say " NOW RUN C1a AGAIN -- it will pass this time:"
say "   bash $HERE/../S189_C1a/install_c1a.sh"
say ""
say " Pin this md5 into the KB Register as it stands (D321(d))."
say "==============================================================="
exit 0
