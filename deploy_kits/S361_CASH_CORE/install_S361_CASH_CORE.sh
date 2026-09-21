#!/bin/bash
# =============================================================================
#  install_S361_CASH_CORE.sh · kit S361_CASH_CORE (session 280, Sanjeevni, 21-Sep-2026)
#  Part 1 of S280_CASH_ARCHITECTURE_AND_MONTH_TABLE -- the ONE cash calculation.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S361_CASH_CORE/install_S361_CASH_CORE.sh
#
#    /root/finance/sanjeevni_cash.py  NEW -- the one calculation: where every rupee of the counter's cash is,
#        from the counted position of 17-Aug, reading BOTH handover registers and counting each once;
#        and the owner's month table (sale · UPI · cash · home · procedure · paid elsewhere · cash income).
#    finance.db -- FOUR NEW TABLES, nothing existing touched: cash_anchor (the 17-Aug count), cash_handover_cover
#        (which days each August handover paid for), cash_bill_ruling (20-Aug bill 2777, paid at the clinic
#        counter -- the owner's ruling of 21-Sep), cash_period_close (the Rs 7 of 17-31 Aug, rounding).
#        Written in ONE transaction that commits only if the proof is green; backed up first.
#  Nothing imports the new module yet, so NO SCREEN CHANGES and NO SERVICE IS RESTARTED. Part 2 moves
#  every cash screen onto it. No parent file is touched.
# =============================================================================
set -u
KIT="S361_CASH_CORE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s361_walk_$STAMP"
TO=a92801a7c362ce2d368a6bff4ad7bd6e
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 sanjeevni_cash.py)" = "$TO" ] || { say "!! [1/7] kit sanjeevni_cash.py is not its pin - nothing installed"; exit 1; }
say "[1/7] kit gates green"
[ -s "$FIN/finance.db" ] || { say "!! [2/7] $FIN/finance.db missing - nothing installed"; exit 1; }
if [ -e "$FIN/sanjeevni_cash.py" ]; then
  if [ "$(m5 "$FIN/sanjeevni_cash.py")" = "$TO" ] && ( cd "$FIN" && "$SPY" -B sanjeevni_cash.py report --db "$FIN/finance.db" >/dev/null 2>&1 ); then
    say "-- ALREADY INSTALLED (module at its pin, proof green on the live database)"; exit 0; fi
  say "!! [2/7] $FIN/sanjeevni_cash.py exists and is not this kit's installed state - nothing installed"; exit 1
fi
say "[2/7] no sanjeevni_cash.py yet; finance.db present"
mkdir -p "$WALK" && cp -p sanjeevni_cash.py selftest_s361.py "$WALK/" || exit 1
( cd "$WALK" && "$SPY" -m py_compile sanjeevni_cash.py selftest_s361.py && "$VPY" -m py_compile sanjeevni_cash.py selftest_s361.py ) \
  || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
SOUT="$( cd "$WALK" && "$SPY" -B selftest_s361.py "$WALK/sanjeevni_cash.py" 2>&1 )"
echo "$SOUT" | grep -E 'FAILED|selftest_s361:' | sed 's/^/   /'
echo "$SOUT" | grep -q "^SELFTEST_S361 GREEN" || { say "!! [3/7] selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/7] compiles on both pythons; selftest green (August proof + seven deliberate failures)"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [4/7] could not copy the database for the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()
PYEOF
WOUT="$( cd "$WALK" && "$SPY" -B sanjeevni_cash.py seed --db "$WALK/scratch.db" --who S361walk 2>&1; cd "$WALK" && "$SPY" -B sanjeevni_cash.py report --db "$WALK/scratch.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^PROOF GREEN" || { say "!! [4/7] the walk on a copy of the live database is red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/7] walk green on a scratch copy of the live database (above: the proof, the positions, the month table)"
"$SPY" - "$FIN/finance.db" "$FIN/finance.db.bak_S361_$STAMP" <<'PYEOF' || { say "!! [5/7] database backup failed - nothing placed"; exit 1; }
import sqlite3, sys
s = sqlite3.connect(sys.argv[1]); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()
PYEOF
say "[5/7] backup: $FIN/finance.db.bak_S361_$STAMP"
\cp -p sanjeevni_cash.py "$FIN/sanjeevni_cash.py" && chmod 644 "$FIN/sanjeevni_cash.py" && [ "$(m5 "$FIN/sanjeevni_cash.py")" = "$TO" ] \
  || { say "!! [6/7] placing the module failed - removed, database untouched"; rm -f "$FIN/sanjeevni_cash.py"; exit 1; }
SEED="$( cd "$FIN" && "$SPY" -B sanjeevni_cash.py seed --db "$FIN/finance.db" --who "S361 (owner's rulings of 21-Sep)" 2>&1 )"
echo "$SEED" | sed 's/^/   /'
echo "$SEED" | grep -q "^SEEDED" || { say "!! [6/7] the seed refused on the live database (it writes nothing when it refuses) - module removed"; rm -f "$FIN/sanjeevni_cash.py"; exit 1; }
say "[6/7] placed /root/finance/sanjeevni_cash.py (md5 read back = the kit) and seeded August in one transaction"
ROUT="$( cd "$FIN" && "$SPY" -B sanjeevni_cash.py report --db "$FIN/finance.db" 2>&1 )"
echo "$ROUT" | grep -E '^  (ok|FAIL)|position at' | sed 's/^/   /'
if ! echo "$ROUT" | grep -q "^PROOF GREEN"; then
  say "!! [7/7] RED on the live database after the seed - undoing: the four new tables dropped, the module removed"
  "$SPY" - "$FIN/finance.db" <<'PYEOF'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
for t in ("cash_anchor", "cash_handover_cover", "cash_bill_ruling", "cash_period_close"):
    c.execute("DROP TABLE IF EXISTS %s" % t)
c.commit(); print("   dropped the four S361 tables; nothing else was ever written")
PYEOF
  rm -f "$FIN/sanjeevni_cash.py"; exit 1
fi
say "[7/7] the proof reads GREEN on the live database, read-only"
md5sum "$FIN/sanjeevni_cash.py"
say "$KIT: DONE -- one cash calculation in place and August proven (drawer 7 · Dr Bhawna 2,98,155 · Dr Manoj 79,703 on 31-Aug). No screen changed yet; part 2 moves every cash screen onto it."
