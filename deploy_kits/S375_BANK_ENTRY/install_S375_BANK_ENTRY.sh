#!/bin/bash
# =============================================================================
#  install_S375_BANK_ENTRY.sh · kit S375_BANK_ENTRY (session 281, Sanjeevni, 22-Sep-2026)
#  D604: the owner records a CASH DEPOSIT (the doctors' pool -> Yes Bank) and a TRANSFER (ICICI Sanjeevni ->
#  Yes Bank Sanjeevni, or either account -> its own HUF savings) himself, on the approvals page. A transfer is
#  never income and never touches a sale, a day or the cash calculation; money to an HUF savings account leaves
#  the pharmacy's picture. ICICI's position is worked out from the settlement files, never typed.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S375_BANK_ENTRY/install_S375_BANK_ENTRY.sh
#
#    /root/finance/sanjeevni_approvals.py           e601d398 (S368) -> TO
#    /root/finance/finance_ui/finance_approvals.html c6641ef6 (S368) -> TO -- THE PARENT'S FILE, DECLARED
#    finance.db: ONE NEW TABLE, bank_transfer, created empty on first use. No existing table is altered.
#    clinic-finance RESTARTED -- DECLARED.
# =============================================================================
set -u
KIT="S375_BANK_ENTRY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s375_walk_$STAMP"
declare -A FROM=( [sanjeevni_approvals.py]=e601d398b8dbc126fc64c0171b1e2e66 [finance_ui/finance_approvals.html]=c6641ef673a6aec7ee08160fdbaf074e )
declare -A TO=( [sanjeevni_approvals.py]=4f98cb378a9beee6771c3df11cc3d606 [finance_ui/finance_approvals.html]=19c877e57a65e54740af86690fedc90a )
CORE=8e58691bac16fceb00602e7f8eabdaf8
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$FIN/sanjeevni_approvals.py")" = "${TO[sanjeevni_approvals.py]}" ] && [ "$(m5 "$FIN/finance_ui/finance_approvals.html")" = "${TO[finance_ui/finance_approvals.html]}" ]; then
  say "-- ALREADY INSTALLED"; exit 0; fi
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/7] $FIN/$f is not its pin ${FROM[$f]:0:8} - nothing installed"; exit 1; }; done
[ "$(m5 "$FIN/sanjeevni_cash.py")" = "$CORE" ] || { say "!! [2/7] sanjeevni_cash.py is not v1.1 (S363) - nothing installed"; exit 1; }
say "[2/7] live files at their pins; the one calculation is S363"
mkdir -p "$WALK/app/finance_ui" "$WALK/kit" || exit 1
cp -p apply_s375.py walk_s375.py "$WALK/kit/" || exit 1
for p in "$FIN"/*.py "$FIN"/*.json "$FIN"/*.sql "$FIN"/*.html "$FIN"/*.txt; do [ -f "$p" ] && cp -p "$p" "$WALK/app/"; done
cp -p "$FIN"/finance_ui/* "$WALK/app/finance_ui/" 2>/dev/null
( cd "$WALK/kit" && "$SPY" -B apply_s375.py --dir "$FIN" --out "$WALK/app" ) | sed 's/^/   /'
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do
  [ "$(m5 "$WALK/app/$f")" = "${TO[$f]}" ] || { say "!! [3/7] the patch does not produce the predicted $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
( cd "$WALK/app" && "$SPY" -m py_compile sanjeevni_approvals.py && "$VPY" -m py_compile sanjeevni_approvals.py ) || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the patch produces exactly the predicted bytes; compiles on both pythons"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [4/7] could not copy the database - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
WOUT="$( cd "$WALK/kit" && timeout 600 "$SPY" -B walk_s375.py --app "$WALK/app" --db "$WALK/scratch.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S375 GREEN" || { say "!! [4/7] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/7] walk green on a scratch copy of the live database (above) -- every entry there, then removed again"
restore() {
  say "!! RED after placing - restoring byte-identically"
  for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do [ -f "$FIN/$f.bak_S375_${FROM[$f]:0:8}" ] && \cp -p "$FIN/$f.bak_S375_${FROM[$f]:0:8}" "$FIN/$f"; done
  systemctl restart clinic-finance 2>/dev/null; sleep 3
  say "   sanjeevni_approvals.py $(m5 "$FIN/sanjeevni_approvals.py") · finance_approvals.html $(m5 "$FIN/finance_ui/finance_approvals.html") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  exit 1
}
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do \cp -p "$FIN/$f" "$FIN/$f.bak_S375_${FROM[$f]:0:8}" || restore; done
( cd "$KDIR" && "$SPY" -B apply_s375.py --dir "$FIN" ) | sed 's/^/   /'
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[5/7] backups .bak_S375_<from8> beside each file; placed; every md5 read back = the kit"
systemctl restart clinic-finance || restore
sleep 3
systemctl is-active --quiet clinic-finance || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
IMP="$( cd "$FIN" && "$SPY" -B -c "import sanjeevni_approvals; print('imports', sanjeevni_approvals.VERSION)" 2>&1 )"
echo "$IMP" | grep -q "imports 1.1" || restore
say "[6/7] clinic-finance up, healthz $HC, the bank door is v1.1"
md5sum "$FIN/sanjeevni_approvals.py" "$FIN/finance_ui/finance_approvals.html"
say "[7/7] $KIT: DONE -- open the approvals page, Bank: 'Record a cash deposit' and 'Record a transfer' are yours."
