#!/bin/bash
# =============================================================================
#  install_S365_DAY_PANEL.sh · kit S365_DAY_PANEL (session 280, Sanjeevni, 21-Sep-2026)
#  The owner, 21-Sep: the day panel "should be simple, human readable, expandable ... which sale returns
#  were there, what were the sales". Sale -> returns -> UPI -> without cash -> CASH RECEIVED (15-Sep = 11,291)
#  -> where the cash went; every line opens to its bills, every bill to its medicines.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S365_DAY_PANEL/install_S365_DAY_PANEL.sh
#
#    /root/finance/sanjeevni_day.py NEW -- reads only.
#    /root/finance/darpan_kal.py    63c70749 (S363) -> TO: its init() also mounts the day panel.
#    /root/finance/finance_ui/finance_approvals.html 5b6ecceb (S363) -> TO -- THE PARENT'S FILE, DECLARED:
#        the day panel reads the new view; the old panel stays one tap away and is the fallback.
#    clinic-finance RESTARTED -- DECLARED. finance.db is not touched.
# =============================================================================
set -u
KIT="S365_DAY_PANEL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s365_walk_$STAMP"
declare -A FROM=( [darpan_kal.py]=63c707499efc2a370df65d3f219ce6a5 [finance_ui/finance_approvals.html]=5b6ecceb0a78ea0c9b16040f2f4a5496 )
declare -A TO=( [darpan_kal.py]=19b9c0e85bf73340df3dd006b1f5c9ce [finance_ui/finance_approvals.html]=6c668cccc9e80bec8c843599a274951d [sanjeevni_day.py]=7f6ea5837cbcc03cec2325ed7f4316c0 )
CORE=8e58691bac16fceb00602e7f8eabdaf8
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 sanjeevni_day.py)" = "${TO[sanjeevni_day.py]}" ] || { say "!! [1/7] kit sanjeevni_day.py is not its pin - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$FIN/darpan_kal.py")" = "${TO[darpan_kal.py]}" ] && [ "$(m5 "$FIN/finance_ui/finance_approvals.html")" = "${TO[finance_ui/finance_approvals.html]}" ] && [ "$(m5 "$FIN/sanjeevni_day.py")" = "${TO[sanjeevni_day.py]}" ]; then
  say "-- ALREADY INSTALLED"; exit 0; fi
for f in darpan_kal.py finance_ui/finance_approvals.html; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/7] $FIN/$f is not its pin ${FROM[$f]:0:8} - nothing installed"; exit 1; }; done
[ -e "$FIN/sanjeevni_day.py" ] && { say "!! [2/7] $FIN/sanjeevni_day.py exists already - nothing installed"; exit 1; }
[ "$(m5 "$FIN/sanjeevni_cash.py")" = "$CORE" ] || { say "!! [2/7] S363 is not live (sanjeevni_cash.py v1.1) - nothing installed"; exit 1; }
say "[2/7] live files at their pins; S363 live"
mkdir -p "$WALK/app/finance_ui" "$WALK/kit" || exit 1
cp -p apply_s365.py a_old.txt a_new.txt walk_s365.py sanjeevni_day.py "$WALK/kit/" || exit 1
for p in "$FIN"/*.py "$FIN"/*.json "$FIN"/*.sql "$FIN"/*.html "$FIN"/*.txt; do [ -f "$p" ] && cp -p "$p" "$WALK/app/"; done
cp -p "$FIN"/finance_ui/* "$WALK/app/finance_ui/" 2>/dev/null
( cd "$WALK/kit" && "$SPY" -B apply_s365.py --dir "$FIN" --out "$WALK/app" ) | sed 's/^/   /'
cp -p "$WALK/kit/sanjeevni_day.py" "$WALK/app/"
for f in darpan_kal.py finance_ui/finance_approvals.html sanjeevni_day.py; do [ "$(m5 "$WALK/app/$f")" = "${TO[$f]}" ] || { say "!! [3/7] the patch does not produce the predicted $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
( cd "$WALK/app" && "$SPY" -m py_compile darpan_kal.py sanjeevni_day.py && "$VPY" -m py_compile darpan_kal.py sanjeevni_day.py ) || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the patch produces exactly the predicted bytes; compiles on both pythons"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [4/7] could not copy the database - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
WOUT="$( cd "$WALK/kit" && timeout 600 "$SPY" -B walk_s365.py --app "$WALK/app" --db "$WALK/scratch.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S365 GREEN" || { say "!! [4/7] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/7] walk green on a scratch copy of the live database (above)"
restore() {
  say "!! RED after placing - restoring byte-identically"
  for f in darpan_kal.py finance_ui/finance_approvals.html; do [ -f "$FIN/$f.bak_S365_${FROM[$f]:0:8}" ] && \cp -p "$FIN/$f.bak_S365_${FROM[$f]:0:8}" "$FIN/$f"; done
  rm -f "$FIN/sanjeevni_day.py"
  systemctl restart clinic-finance 2>/dev/null; sleep 3
  say "   darpan_kal.py $(m5 "$FIN/darpan_kal.py") · finance_approvals.html $(m5 "$FIN/finance_ui/finance_approvals.html") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  exit 1
}
( cd "$KDIR" && "$SPY" -B apply_s365.py --dir "$FIN" ) | sed 's/^/   /'
\cp -p sanjeevni_day.py "$FIN/sanjeevni_day.py" && chmod 644 "$FIN/sanjeevni_day.py" || restore
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
for f in darpan_kal.py finance_ui/finance_approvals.html sanjeevni_day.py; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[5/7] backups .bak_S365_<from8> beside each file; placed; every md5 read back = the kit"
systemctl restart clinic-finance || restore
sleep 3
systemctl is-active --quiet clinic-finance || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
IMP="$( cd "$FIN" && "$SPY" -B -c "import sanjeevni_day, darpan_kal; print('imports', sanjeevni_day.VERSION)" 2>&1 )"
echo "$IMP" | grep -q "imports 1.0" || restore
say "[6/7] clinic-finance up, healthz $HC, the day panel module imports (the page itself is behind the login gate)"
md5sum "$FIN/darpan_kal.py" "$FIN/finance_ui/finance_approvals.html" "$FIN/sanjeevni_day.py"
say "[7/7] $KIT: DONE -- open any day on the approvals page: sale, returns, UPI, without cash, cash received, each line opens."
