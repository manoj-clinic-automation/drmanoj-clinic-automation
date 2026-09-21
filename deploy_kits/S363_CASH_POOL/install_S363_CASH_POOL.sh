#!/bin/bash
# =============================================================================
#  install_S363_CASH_POOL.sh · kit S363_CASH_POOL (session 280, Sanjeevni, 21-Sep-2026)
#  Supersedes S362_CASH_SCREENS (built, never installed). Part 2 of S280_CASH_ARCHITECTURE, on the owner's
#  ruling of 21-Sep: "Darpan handed all cash daily from 1st to 19th Sept, and Dr Bhawna's receivings and
#  yours go to the same pool, so maintain that flow; I will mark each day of Sept in approvals."
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S363_CASH_POOL/install_S363_CASH_POOL.sh
#
#  Needs S361_CASH_CORE live. Changes:
#    /root/finance/sanjeevni_cash.py   a92801a7 (v1.0) -> v1.1: the doctors' ONE POOL; an APPROVED day's drawer
#        cash went to the pool; the pool's cash deposits (03-Sep 3,00,000 · 15-Sep 1,00,000, Yes Bank) are
#        their own record, never a drawer movement.
#    finance.db: ONE NEW TABLE cash_pool_deposit, seeded with those two deposits in one transaction that
#        commits only if the proof is green; one setting (darpan_kal.log_from = 2026-08-17). Nothing else.
#    /root/finance/finance_app.py      4a399f30 -> TO -- THE PARENT'S FILE, DECLARED: every Sanjeevni cash
#        screen reads the one calculation (the S362 edits + the pool).
#    /root/finance/finance_ui/finance_approvals.html c940c46f -> TO -- THE PARENT'S FILE, DECLARED: one
#        pool row; the drawer names the days awaiting your approval.
#    /root/finance/darpan_app.py df3224c5 · darpan_kal.py 2072e290 · finance_yesbank.py cc55b5f4 ·
#        darpan_month.html c4e81f7c -> TO below.
#    clinic-finance RESTARTED -- DECLARED TO THE PARENT.
# =============================================================================
set -u
KIT="S363_CASH_POOL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s363_walk_$STAMP"
FILES="finance_app.py darpan_app.py darpan_kal.py finance_yesbank.py finance_ui/finance_approvals.html darpan_month.html sanjeevni_cash.py"
declare -A FROM=( [finance_app.py]=4a399f3068799917b8e58f89a1645131 [darpan_app.py]=df3224c5fb45964d8b53df660ff60def
  [darpan_kal.py]=2072e2904f2b363eab9cb494533bd198 [finance_yesbank.py]=cc55b5f4bae367de3c194808da9dfdbc
  [finance_ui/finance_approvals.html]=c940c46f5fce12a67836da951bb9b117 [darpan_month.html]=c4e81f7c982c23a2880c36c1ff20ee21
  [sanjeevni_cash.py]=a92801a7c362ce2d368a6bff4ad7bd6e )
declare -A TO=( [finance_app.py]=70cff4981c2ebf554308545fb071f0d4 [darpan_app.py]=2c22822d49a20143058b5d781eb3c06e [darpan_kal.py]=63c707499efc2a370df65d3f219ce6a5
  [finance_yesbank.py]=825016c02364dc5d22027ff192d1d29d [finance_ui/finance_approvals.html]=5b6ecceb0a78ea0c9b16040f2f4a5496
  [darpan_month.html]=cee5478bc7384812c787c5149283854f [sanjeevni_cash.py]=8e58691bac16fceb00602e7f8eabdaf8 )
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in darpan_month.html sanjeevni_cash.py; do [ "$(m5 "$f")" = "${TO[$f]}" ] || { say "!! [1/8] kit $f is not its pin - nothing installed"; exit 1; }; done
say "[1/8] kit gates green"
all_to=1; for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || all_to=0; done
if [ $all_to = 1 ]; then say "-- ALREADY INSTALLED"; exit 0; fi
for f in $FILES; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/8] $FIN/$f is not its pin ${FROM[$f]:0:8} - nothing installed (moved since; re-pin)"; exit 1; }; done
( cd "$FIN" && "$SPY" -B sanjeevni_cash.py report --db "$FIN/finance.db" 2>/dev/null | grep -q "^PROOF GREEN" ) || { say "!! [2/8] S361's proof is not green on the live database - nothing installed"; exit 1; }
say "[2/8] all seven live files at their pins; S361 live and its proof green"
mkdir -p "$WALK/before/finance_ui" "$WALK/after/finance_ui" "$WALK/kit" || exit 1
cp -p apply_s363.py apply_s362.py walk_s363.py darpan_month.html sanjeevni_cash.py selftest_s361.py selftest_s363.py "$WALK/kit/" || exit 1
( cd "$WALK/kit" && "$SPY" -m py_compile sanjeevni_cash.py selftest_s361.py selftest_s363.py && "$VPY" -m py_compile sanjeevni_cash.py ) || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
SOUT="$( cd "$WALK/kit" && "$SPY" -B selftest_s361.py "$WALK/kit/sanjeevni_cash.py" 2>&1; cd "$WALK/kit" && "$SPY" -B selftest_s363.py "$WALK/kit/sanjeevni_cash.py" 2>&1 )"
echo "$SOUT" | grep -E 'FAILED|checks passed' | sed 's/^/   /'
{ echo "$SOUT" | grep -q "^SELFTEST_S361 GREEN" && echo "$SOUT" | grep -q "^SELFTEST_S363 GREEN"; } || { say "!! [3/8] selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
for d in before after; do
  for p in "$FIN"/*.py "$FIN"/*.json "$FIN"/*.sql "$FIN"/*.html "$FIN"/*.txt; do [ -f "$p" ] && cp -p "$p" "$WALK/$d/"; done
  cp -p "$FIN"/finance_ui/* "$WALK/$d/finance_ui/" 2>/dev/null
done
( cd "$WALK/kit" && "$SPY" -B apply_s363.py --dir "$FIN" --out "$WALK/after" ) | sed 's/^/   /'
cp -p "$WALK/kit/darpan_month.html" "$WALK/kit/sanjeevni_cash.py" "$WALK/after/"
for f in $FILES; do [ "$(m5 "$WALK/after/$f")" = "${TO[$f]}" ] || { say "!! [3/8] the patch does not produce the predicted $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
( cd "$WALK/after" && "$SPY" -m py_compile finance_app.py darpan_app.py darpan_kal.py finance_yesbank.py sanjeevni_cash.py && "$VPY" -m py_compile finance_app.py darpan_app.py darpan_kal.py finance_yesbank.py sanjeevni_cash.py ) \
  || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/8] selftests green (S361's 19 on v1.1 + the pool's 11); the patch produces exactly the predicted bytes; compiles on both pythons"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" "$WALK/unseeded.db" "$WALK/kit/sanjeevni_cash.py" <<'PYEOF' || { say "!! [4/8] could not prepare the walk's databases - nothing installed"; rm -rf "$WALK"; exit 1; }
import importlib.util, sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
for p in sys.argv[2:4]:
    d = sqlite3.connect(p); s.backup(d); d.close()
spec = importlib.util.spec_from_file_location("sc", sys.argv[4]); sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
d = sqlite3.connect(sys.argv[2]); sc.ensure_schema(d); sc.seed_september(d, "S363walk", "walk")
d.execute("INSERT INTO setting(key,value,note) VALUES('darpan_kal.log_from','2026-08-17','S363') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
d.commit(); d.close()
u = sqlite3.connect(sys.argv[3])
for t in ("cash_anchor", "cash_handover_cover", "cash_bill_ruling", "cash_period_close", "cash_pool_deposit"):
    u.execute("DROP TABLE IF EXISTS %s" % t)
u.commit(); u.close()
PYEOF
WOUT="$( cd "$WALK/kit" && FINANCE_YESBANK_DIR="$WALK/yb" timeout 900 "$SPY" -B walk_s363.py --before "$WALK/before" --after "$WALK/after" --db "$WALK/scratch.db" --unseeded "$WALK/unseeded.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S363 GREEN" || { say "!! [4/8] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/8] walk green: the real app, live files vs patched, over a scratch copy of the live database (above)"
for f in darpan_month.html sanjeevni_cash.py; do \cp -p "$FIN/$f" "$FIN/$f.bak_S363_${FROM[$f]:0:8}" || exit 1; done
"$SPY" - "$FIN/finance.db" "$FIN/finance.db.bak_S363_$STAMP" <<'PYEOF' || { say "!! [5/8] database backup failed - nothing placed"; exit 1; }
import sqlite3, sys
s = sqlite3.connect(sys.argv[1]); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()
PYEOF
OLDLF="$("$SPY" -c "import sqlite3;c=sqlite3.connect('$FIN/finance.db');r=c.execute(\"SELECT value FROM setting WHERE key='darpan_kal.log_from'\").fetchone();print(r[0] if r else '')")"
say "[5/8] backups: finance.db.bak_S363_$STAMP · .bak_S363_<from8> beside every file · darpan_kal.log_from was '${OLDLF:-unset}'"
restore() {
  say "!! RED after placing - restoring byte-identically"
  for f in $FILES; do [ -f "$FIN/$f.bak_S363_${FROM[$f]:0:8}" ] && \cp -p "$FIN/$f.bak_S363_${FROM[$f]:0:8}" "$FIN/$f"; done
  "$SPY" - "$FIN/finance.db" "$OLDLF" <<'PYEOF'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.execute("DROP TABLE IF EXISTS cash_pool_deposit")
if sys.argv[2]:
    c.execute("UPDATE setting SET value=? WHERE key='darpan_kal.log_from'", (sys.argv[2],))
else:
    c.execute("DELETE FROM setting WHERE key='darpan_kal.log_from'")
c.commit()
PYEOF
  systemctl restart clinic-finance 2>/dev/null; sleep 3
  for f in $FILES; do say "   $f $(m5 "$FIN/$f")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  exit 1
}
( cd "$KDIR" && "$SPY" -B apply_s363.py --dir "$FIN" ) | sed 's/^/   /'
\cp -p darpan_month.html "$FIN/darpan_month.html" && \cp -p sanjeevni_cash.py "$FIN/sanjeevni_cash.py" || restore
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
SEED="$( cd "$FIN" && "$SPY" -B sanjeevni_cash.py seed --db "$FIN/finance.db" --who "S363 (owner's ruling of 21-Sep)" 2>&1 )"
echo "$SEED" | sed 's/^/   /'
echo "$SEED" | grep -q '^SEEDED .*"pool_deposits": 2' || restore
"$SPY" - "$FIN/finance.db" <<'PYEOF' || restore
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.execute("INSERT INTO setting(key,value,note) VALUES('darpan_kal.log_from','2026-08-17',"
          "'S363: from the 17-Aug count; August covered (S361); an approved day is paid over (owner, 21-Sep)') "
          "ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note")
c.commit()
PYEOF
say "[6/8] placed; every md5 read back = the kit; the pool's two deposits recorded in one transaction with the proof green"
systemctl restart clinic-finance || restore
sleep 3
systemctl is-active --quiet clinic-finance || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
# F-525 / F-573: the cash pages are behind the login gate; curl proves nothing about them. The placed modules
# are proven by IMPORTING them with the service's python; the figures by the walk above and the report below.
IMP="$( cd "$FIN" && "$SPY" -B -c "import sanjeevni_cash, darpan_kal, darpan_app, finance_yesbank; print('imports', sanjeevni_cash.VERSION, hasattr(darpan_kal, '_covered_days'))" 2>&1 )"
echo "$IMP" | grep -q "imports 1.1 True" || restore
say "[7/8] clinic-finance up, healthz $HC, the placed modules import"
ROUT="$( cd "$FIN" && "$SPY" -B sanjeevni_cash.py report --db "$FIN/finance.db" 2>&1 )"
echo "$ROUT" | grep -E '^  (ok|FAIL)|position at|^PROOF' | sed 's/^/   /'
echo "$ROUT" | grep -q "^PROOF GREEN" || restore
for f in $FILES; do md5sum "$FIN/$f"; done
say "[8/8] $KIT: DONE -- every Sanjeevni cash screen reads the one calculation; approve each September day on the approvals page and its cash moves from Darpan's drawer to the pool."
