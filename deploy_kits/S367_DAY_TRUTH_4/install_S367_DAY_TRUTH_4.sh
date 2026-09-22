#!/bin/bash
# =============================================================================
#  install_S367_DAY_TRUTH_4.sh · kit S367_DAY_TRUTH_4 (session 281, Sanjeevni, 22-Sep-2026)
#  F-613 / the owner's ruling D602: a day filed automatically from Marg now FOLLOWS Marg's later export
#  until it is approved; the day panel says HOW each day was filed (which export, what time, nobody typed
#  it) and whether a pool deposit is confirmed by the Yes Bank statement; 04-Sep is corrected visibly
#  to Marg's 18 bills (23,875 -- bill A003396, 200 cash).
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S367_DAY_TRUTH_4/install_S367_DAY_TRUTH_4.sh
#
#    /root/finance/sanjeevni_day.py  7f6ea583 (S365) -> TO   reads only
#    /root/finance/day_resync.py     a4e53adc (S357) -> TO   + pass 0 (Marg), same cron line
#    finance.db: ONE row changed (04-Sep's cash line 11,066 -> 11,266) + one audit_log row, after a backup
#    clinic-finance RESTARTED -- DECLARED. No parent file is touched.
# =============================================================================
set -u
KIT="S367_DAY_TRUTH_4"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s367_walk_$STAMP"
declare -A FROM=( [sanjeevni_day.py]=7f6ea5837cbcc03cec2325ed7f4316c0 [day_resync.py]=a4e53adc201904bc48a15b592ddd9ebe )
declare -A TO=( [sanjeevni_day.py]=5d16eff5b6e2f0fd561e22d91e4794ab [day_resync.py]=ddbb12eb7835b29d44804105432e19a7 )
CORE=8e58691bac16fceb00602e7f8eabdaf8
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in sanjeevni_day.py day_resync.py; do [ "$(m5 $f)" = "${TO[$f]}" ] || { say "!! [1/7] kit $f is not its pin - nothing installed"; exit 1; }; done
say "[1/7] kit gates green"
if [ "$(m5 "$FIN/sanjeevni_day.py")" = "${TO[sanjeevni_day.py]}" ] && [ "$(m5 "$FIN/day_resync.py")" = "${TO[day_resync.py]}" ]; then
  say "-- files ALREADY INSTALLED; the correction:"; ( cd "$FIN" && "$SPY" -B "$KDIR/correct_0904.py" --db "$FIN/finance.db" ); exit 0; fi
for f in sanjeevni_day.py day_resync.py; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/7] $FIN/$f is not its pin ${FROM[$f]:0:8} - nothing installed"; exit 1; }; done
[ "$(m5 "$FIN/sanjeevni_cash.py")" = "$CORE" ] || { say "!! [2/7] sanjeevni_cash.py is not v1.1 (S363) - nothing installed"; exit 1; }
say "[2/7] live files at their pins"
mkdir -p "$WALK/app/finance_ui" "$WALK/kit" || exit 1
cp -p correct_0904.py walk_s367.py "$WALK/kit/" || exit 1
for p in "$FIN"/*.py "$FIN"/*.json "$FIN"/*.sql "$FIN"/*.html "$FIN"/*.txt; do [ -f "$p" ] && cp -p "$p" "$WALK/app/"; done
cp -p "$FIN"/finance_ui/* "$WALK/app/finance_ui/" 2>/dev/null
cp -p sanjeevni_day.py day_resync.py "$WALK/app/"
( cd "$WALK/app" && "$SPY" -m py_compile sanjeevni_day.py day_resync.py && "$VPY" -m py_compile sanjeevni_day.py day_resync.py ) || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] compiles on both pythons"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [4/7] could not copy the database - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
WOUT="$( cd "$WALK/kit" && timeout 600 "$SPY" -B walk_s367.py --app "$WALK/app" --db "$WALK/scratch.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S367 GREEN" || { say "!! [4/7] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/7] walk green on a scratch copy of the live database (above)"
restore() {
  say "!! RED after placing - restoring byte-identically"
  for f in sanjeevni_day.py day_resync.py; do [ -f "$FIN/$f.bak_S367_${FROM[$f]:0:8}" ] && \cp -p "$FIN/$f.bak_S367_${FROM[$f]:0:8}" "$FIN/$f"; done
  systemctl restart clinic-finance 2>/dev/null; sleep 3
  say "   sanjeevni_day.py $(m5 "$FIN/sanjeevni_day.py") · day_resync.py $(m5 "$FIN/day_resync.py") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  say "   the database backup of this run: $FIN/finance.db.bak_S367_$STAMP (04-Sep's correction, if made, stays -- it is the owner's ruling)"
  exit 1
}
"$SPY" - "$FIN/finance.db" "$FIN/finance.db.bak_S367_$STAMP" <<'PYEOF' || { say "!! [5/7] database backup failed - nothing installed"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
for f in sanjeevni_day.py day_resync.py; do \cp -p "$FIN/$f" "$FIN/$f.bak_S367_${FROM[$f]:0:8}" || restore; \cp -p "$f" "$FIN/$f" && chmod 644 "$FIN/$f" || restore; done
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
for f in sanjeevni_day.py day_resync.py; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[5/7] database backed up (finance.db.bak_S367_$STAMP); .bak_S367_<from8> beside each file; placed; every md5 read back = the kit"
COUT="$( "$SPY" -B correct_0904.py --db "$FIN/finance.db" 2>&1 )"; echo "   $COUT"
echo "$COUT" | grep -qE "^(DONE|ALREADY)" || restore
systemctl restart clinic-finance || restore
sleep 3
systemctl is-active --quiet clinic-finance || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
IMP="$( cd "$FIN" && "$SPY" -B -c "import sanjeevni_day; print('imports', sanjeevni_day.VERSION)" 2>&1 )"
echo "$IMP" | grep -q "imports 1.1" || restore
say "[6/7] 04-Sep corrected under D602; clinic-finance up, healthz $HC, the day panel v1.1 imports"
( cd "$FIN" && "$VPY" -B day_resync.py --dry-run --no-reconcile 2>&1 | head -4 | sed 's/^/   /' )
md5sum "$FIN/sanjeevni_day.py" "$FIN/day_resync.py"
say "[7/7] $KIT: DONE -- open 04-Sep on the approvals page: 23,875, filed automatically from Marg, corrected under D602, nothing needs you."
