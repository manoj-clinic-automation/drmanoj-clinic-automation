#!/bin/bash
# =============================================================================
#  install_S355_DAY_TRUTH.sh · kit S355_DAY_TRUTH (session 275, Sanjeevni, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S355_DAY_TRUTH/install_S355_DAY_TRUTH.sh
#
#  An autofiled pharmacy day follows the bank: the D354 autofile froze each day's UPI at the moment
#  Marg's report arrived (the bank statement lands hours later), so nine September days carry UPI 0
#  and cash overstated -- the approval section could not be trusted.
#    /root/finance/day_resync.py   NEW (TO below) -- unapproved, autofiled, never-corrected days:
#                                  UPI = the bank statement, cash = net - UPI, one audit row, the
#                                  upi_vs_statement exception re-judged by finance_upi.reconcile_upi
#    CRONTAB: one root line, every 30 min 07-23, tagged # S355_DAY_TRUTH -- DECLARED TO THE PARENT
#    finance.db: the day_line rows of those days change (backup taken first, sqlite backup API)
#  No parent file changed, no restart, no screen.  Honours /root/finance/_off/ALL_OFF.
# =============================================================================
set -u
KIT="S355_DAY_TRUTH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
DB="$FIN/finance.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s355_walk_$STAMP"
DR_TO=d154e08ebfde0099df1c13dbfebffacd
CRON_LINE='*/30 7-23 * * * flock -n /tmp/day_resync.lock /root/wa/venv/bin/python3 -B /root/finance/day_resync.py >> /root/finance/day_resync.log 2>&1 # S355_DAY_TRUTH'
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 day_resync.py)" = "$DR_TO" ] || { say "!! [1/8] kit day_resync.py is not its pin - nothing installed"; exit 1; }
say "[1/8] kit gates green"
if [ "$(m5 "$FIN/day_resync.py")" = "$DR_TO" ]; then say "-- ALREADY INSTALLED"; crontab -l 2>/dev/null | grep -q "# S355_DAY_TRUTH" && say "   cron line present" || say "   !! cron line ABSENT"; exit 0; fi
[ -e "$FIN/day_resync.py" ] && { say "!! [2/8] $FIN/day_resync.py exists and is not this kit's - nothing installed"; exit 1; }
[ -s "$DB" ] && [ -f "$FIN/finance_upi.py" ] || { say "!! [2/8] no finance.db or finance_upi.py at $FIN - nothing installed"; exit 1; }
say "[2/8] finance.db and finance_upi.py are there; no earlier copy of this file"
mkdir -p "$WALK/compile" || exit 1
cp -p day_resync.py selftest_s355.py "$WALK/compile/" && ( cd "$WALK/compile" && "$SPY" -m py_compile day_resync.py selftest_s355.py && "$VPY" -m py_compile day_resync.py selftest_s355.py ) \
  || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green on both pythons (on copies)"
SOUT="$( cd "$WALK/compile" && "$VPY" -B selftest_s355.py --finance-dir "$FIN" --python "$VPY" 2>&1 )"
echo "$SOUT" | grep -E '^  FAIL|selftest:' | sed 's/^/   /'
echo "$SOUT" | grep -q "^selftest: 20/20" || { say "!! [4/8] selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] selftest 20/20 on a scratch database in the live shape, with this box's finance_upi"
DOUT="$( cd "$WALK/compile" && "$VPY" -B day_resync.py --db "$DB" --dry-run --no-reconcile 2>&1 )"
echo "$DOUT" | sed 's/^/   /'
echo "$DOUT" | grep -q "unapproved autofiled day" || { say "!! [5/8] the dry run did not read the live database - nothing installed"; rm -rf "$WALK"; exit 1; }
echo "$DOUT" | grep -q "SHAPE" && { say "!! [5/8] a day has an unexpected line shape - nothing installed, read the line above"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[5/8] dry run against the live database read (nothing written)"
BAK="$FIN/finance.db.bak_S355_$STAMP"
"$VPY" - "$DB" "$BAK" <<'EOF' || { say "!! [6/8] database backup failed - nothing installed"; exit 1; }
import sqlite3, sys
src = sqlite3.connect(sys.argv[1]); dst = sqlite3.connect(sys.argv[2])
src.backup(dst); dst.close(); src.close()
EOF
[ -s "$BAK" ] || { say "!! [6/8] backup empty - nothing installed"; exit 1; }
say "[6/8] finance.db backed up (sqlite backup API): $BAK"
CBAK="$FIN/crontab.bak_S355_$STAMP"
crontab -l > "$CBAK" 2>/dev/null || : > "$CBAK"
restore() {
  say "!! RED after placing - restoring"
  rm -f "$FIN/day_resync.py"; crontab "$CBAK" 2>/dev/null || true
  say "   day_resync.py removed · crontab restored from $CBAK · the database backup is $BAK (rows already resynced carry their audit row; nothing else changed)"
  exit 1
}
\cp -p day_resync.py "$FIN/day_resync.py" && [ "$(m5 "$FIN/day_resync.py")" = "$DR_TO" ] || restore
if ! crontab -l 2>/dev/null | grep -q "# S355_DAY_TRUTH"; then { crontab -l 2>/dev/null; echo "$CRON_LINE"; } | crontab - || restore; fi
crontab -l 2>/dev/null | grep -q "# S355_DAY_TRUTH" || restore
say "[7/8] placed $DR_TO; cron */30 7-23 (# S355_DAY_TRUTH); crontab backup $CBAK"
ROUT="$( cd "$FIN" && flock -w 60 /tmp/day_resync.lock "$VPY" -B day_resync.py 2>&1 )"
echo "$ROUT" | sed 's/^/   /'
echo "$ROUT" | grep -q "^summary:" || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
say "[8/8] first resync run (above); the app answers healthz $HC (no restart was needed)"
md5sum "$FIN/day_resync.py"
say "$KIT: DONE -- every unapproved autofiled day now follows the bank, re-checked every 30 minutes; the approval section reads the corrected cash at its next refresh."
