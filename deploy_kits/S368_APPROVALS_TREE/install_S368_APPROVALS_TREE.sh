#!/bin/bash
# =============================================================================
#  install_S368_APPROVALS_TREE.sh · kit S368_APPROVALS_TREE (session 281, Sanjeevni, 22-Sep-2026)
#  D591 finished, D603: the approvals page is ONE TREE -- Needs you (in words) · Days · Cash · Bank · Returns ·
#  Month · Checks (the audit material, collapsed, on the same page). The old page is kept byte for byte at
#  /finance/approvals/old. Every rupee from sanjeevni_cash; every sentence from sanjeevni_approvals.py.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S368_APPROVALS_TREE/install_S368_APPROVALS_TREE.sh
#
#    /root/finance/sanjeevni_approvals.py   NEW -- reads only
#    /root/finance/darpan_kal.py            19b9c0e8 (S365) -> TO: its init() also mounts the door (apply_s368.py)
#    /root/finance/finance_ui/finance_approvals.html  6c668ccc (S365) -> TO -- THE PARENT'S FILE, DECLARED
#    /root/finance/finance_ui/finance_approvals_old.html  NEW = the 6c668ccc bytes (the fallback page)
#    clinic-finance RESTARTED -- DECLARED. finance.db is not touched.
# =============================================================================
set -u
KIT="S368_APPROVALS_TREE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s368_walk_$STAMP"
OLD_HTML=6c668cccc9e80bec8c843599a274951d
declare -A FROM=( [darpan_kal.py]=19b9c0e85bf73340df3dd006b1f5c9ce [finance_ui/finance_approvals.html]=$OLD_HTML )
declare -A TO=( [darpan_kal.py]=1958ee7c620d890f10a609473b2a8f1d [finance_ui/finance_approvals.html]=c6641ef673a6aec7ee08160fdbaf074e [sanjeevni_approvals.py]=e601d398b8dbc126fc64c0171b1e2e66 )
CORE=8e58691bac16fceb00602e7f8eabdaf8; DAY=5d16eff5b6e2f0fd561e22d91e4794ab
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 sanjeevni_approvals.py)" = "${TO[sanjeevni_approvals.py]}" ] || { say "!! [1/7] kit sanjeevni_approvals.py is not its pin - nothing installed"; exit 1; }
[ "$(m5 finance_approvals.html)" = "${TO[finance_ui/finance_approvals.html]}" ] || { say "!! [1/7] kit finance_approvals.html is not its pin - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$FIN/darpan_kal.py")" = "${TO[darpan_kal.py]}" ] && [ "$(m5 "$FIN/finance_ui/finance_approvals.html")" = "${TO[finance_ui/finance_approvals.html]}" ] && [ "$(m5 "$FIN/sanjeevni_approvals.py")" = "${TO[sanjeevni_approvals.py]}" ]; then
  say "-- ALREADY INSTALLED"; exit 0; fi
for f in darpan_kal.py finance_ui/finance_approvals.html; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/7] $FIN/$f is not its pin ${FROM[$f]:0:8} - nothing installed"; exit 1; }; done
[ -e "$FIN/sanjeevni_approvals.py" ] && { say "!! [2/7] $FIN/sanjeevni_approvals.py exists already - nothing installed"; exit 1; }
[ -e "$FIN/finance_ui/finance_approvals_old.html" ] && { say "!! [2/7] finance_approvals_old.html exists already - nothing installed"; exit 1; }
[ "$(m5 "$FIN/sanjeevni_cash.py")" = "$CORE" ] || { say "!! [2/7] sanjeevni_cash.py is not v1.1 (S363) - nothing installed"; exit 1; }
[ "$(m5 "$FIN/sanjeevni_day.py")" = "$DAY" ] || { say "!! [2/7] sanjeevni_day.py is not v1.1 (S367) - nothing installed"; exit 1; }
say "[2/7] live files at their pins; S363 and S367 live"
mkdir -p "$WALK/app/finance_ui" "$WALK/kit" || exit 1
cp -p apply_s368.py build_page.py walk_s368.py sanjeevni_approvals.py finance_approvals.html "$WALK/kit/" || exit 1
for p in "$FIN"/*.py "$FIN"/*.json "$FIN"/*.sql "$FIN"/*.html "$FIN"/*.txt; do [ -f "$p" ] && cp -p "$p" "$WALK/app/"; done
cp -p "$FIN"/finance_ui/* "$WALK/app/finance_ui/" 2>/dev/null
( cd "$WALK/kit" && "$SPY" -B apply_s368.py --dir "$FIN" --out "$WALK/app" ) | sed 's/^/   /'
( cd "$WALK/kit" && "$SPY" -B build_page.py --src "$FIN/finance_ui/finance_approvals.html" --out "$WALK/app/finance_ui/finance_approvals.html" ) | sed 's/^/   /'
cp -p "$FIN/finance_ui/finance_approvals.html" "$WALK/app/finance_ui/finance_approvals_old.html"
cp -p "$WALK/kit/sanjeevni_approvals.py" "$WALK/app/"
[ "$(m5 "$WALK/app/darpan_kal.py")" = "${TO[darpan_kal.py]}" ] || { say "!! [3/7] the patch does not produce the predicted darpan_kal.py - nothing installed"; rm -rf "$WALK"; exit 1; }
[ "$(m5 "$WALK/app/finance_ui/finance_approvals.html")" = "${TO[finance_ui/finance_approvals.html]}" ] || { say "!! [3/7] build_page.py over the live page does not produce the kit's page - nothing installed"; rm -rf "$WALK"; exit 1; }
( cd "$WALK/app" && "$SPY" -m py_compile darpan_kal.py sanjeevni_approvals.py && "$VPY" -m py_compile darpan_kal.py sanjeevni_approvals.py ) || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the patch and the page build produce exactly the predicted bytes; compiles on both pythons"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [4/7] could not copy the database - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
WOUT="$( cd "$WALK/kit" && timeout 600 "$SPY" -B walk_s368.py --app "$WALK/app" --db "$WALK/scratch.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S368 GREEN" || { say "!! [4/7] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/7] walk green on a scratch copy of the live database (above)"
restore() {
  say "!! RED after placing - restoring byte-identically"
  for f in darpan_kal.py finance_ui/finance_approvals.html; do [ -f "$FIN/$f.bak_S368_${FROM[$f]:0:8}" ] && \cp -p "$FIN/$f.bak_S368_${FROM[$f]:0:8}" "$FIN/$f"; done
  rm -f "$FIN/sanjeevni_approvals.py" "$FIN/finance_ui/finance_approvals_old.html"
  systemctl restart clinic-finance 2>/dev/null; sleep 3
  say "   darpan_kal.py $(m5 "$FIN/darpan_kal.py") · finance_approvals.html $(m5 "$FIN/finance_ui/finance_approvals.html") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  exit 1
}
for f in darpan_kal.py finance_ui/finance_approvals.html; do \cp -p "$FIN/$f" "$FIN/$f.bak_S368_${FROM[$f]:0:8}" || restore; done
\cp -p "$FIN/finance_ui/finance_approvals.html" "$FIN/finance_ui/finance_approvals_old.html" || restore
( cd "$KDIR" && "$SPY" -B apply_s368.py --dir "$FIN" ) | sed 's/^/   /'
\cp -p finance_approvals.html "$FIN/finance_ui/finance_approvals.html" || restore
\cp -p sanjeevni_approvals.py "$FIN/sanjeevni_approvals.py" && chmod 644 "$FIN/sanjeevni_approvals.py" || restore
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
for f in darpan_kal.py finance_ui/finance_approvals.html sanjeevni_approvals.py; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
[ "$(m5 "$FIN/finance_ui/finance_approvals_old.html")" = "$OLD_HTML" ] || restore
say "[5/7] backups .bak_S368_<from8> beside each file; the old page kept as finance_approvals_old.html; placed; every md5 read back = the kit"
systemctl restart clinic-finance || restore
sleep 3
systemctl is-active --quiet clinic-finance || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
IMP="$( cd "$FIN" && "$SPY" -B -c "import sanjeevni_approvals, darpan_kal; print('imports', sanjeevni_approvals.VERSION)" 2>&1 )"
echo "$IMP" | grep -q "imports 1.0" || restore
say "[6/7] clinic-finance up, healthz $HC, the tree's door imports (the page itself is behind the login gate)"
md5sum "$FIN/darpan_kal.py" "$FIN/finance_ui/finance_approvals.html" "$FIN/finance_ui/finance_approvals_old.html" "$FIN/sanjeevni_approvals.py"
say "[7/7] $KIT: DONE -- open the approvals page: Needs you, Days, Cash, Bank, Returns, Month, Checks. The old page: /finance/approvals/old"
