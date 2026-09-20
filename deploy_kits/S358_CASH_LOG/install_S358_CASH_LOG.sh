#!/bin/bash
# =============================================================================
#  install_S358_CASH_LOG.sh · kit S358_CASH_LOG (session 275, Sanjeevni, 20-Sep-2026) -- on S357 (LIVE 22:27)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S358_CASH_LOG/install_S358_CASH_LOG.sh
#
#  THE OWNER'S RULING (20-Sep, 22:4x): Darpan hands the cash daily, to him or to Dr Bhawna; BOTH must be able to
#  log what they received (he can, or they can), and that logging clears the backlog -- Darpan has handed
#  everything to date.  Plus a month-wise table for the owner: total sale, UPI, cash, less home and procedure
#  medicine.
#    /root/finance/darpan_kal.py     04bb1586 (S357) -> TO below, FULL FILE: api/pending, api/log, the month page + api
#    /root/finance/darpan_kal.html   31f737f2 (S357) -> TO below, FULL FILE: the owner lands on his English view,
#                                    the 'Cash received' block (one day / all as expected), the month link
#    /root/finance/darpan_month.html NEW -- the month-wise table (doctors only)
#    /root/portal/tile_grants.json   v23 a5f8b3b1 -> v24 (grant_kal_s358.py): 'Kal ka hisaab' to bhawna -- A DATA EDIT
#                                    ON THE PARENT'S FILE, DECLARED
#    clinic-finance and clinic-portal RESTARTED -- DECLARED TO THE PARENT
#  No code of the parent's changed.  finance.db is not touched by the install (the doctors' logs write later).
# =============================================================================
set -u
KIT="S358_CASH_LOG"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
POR="${POR:-/root/portal}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s358_walk_$STAMP"
declare -A FROM=( [darpan_kal.py]=04bb158650393e1cff2ce9bd3b38bceb [darpan_kal.html]=31f737f26bab765ae35aaa12f9c74232 [tile_grants.json]=a5f8b3b1ef40047052b65d9735f02e3f )
declare -A TO=( [darpan_kal.py]=cc8253a6943091ea92a825763dd1e933 [darpan_kal.html]=6f3250ec5ba61dc2640fd33044bce9c0 [darpan_month.html]=c4e81f7c982c23a2880c36c1ff20ee21 [tile_grants.json]=76448c678b31925dad281710b330621a )
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in darpan_kal.py darpan_kal.html darpan_month.html; do [ "$(m5 "$f")" = "${TO[$f]}" ] || { say "!! [1/8] kit $f is not its pin - nothing installed"; exit 1; }; done
say "[1/8] kit gates green"
if [ "$(m5 "$FIN/darpan_kal.py")" = "${TO[darpan_kal.py]}" ] && [ "$(m5 "$FIN/darpan_kal.html")" = "${TO[darpan_kal.html]}" ] && \
   [ "$(m5 "$FIN/darpan_month.html")" = "${TO[darpan_month.html]}" ] && [ "$(m5 "$POR/tile_grants.json")" = "${TO[tile_grants.json]}" ]; then
  say "-- ALREADY INSTALLED"; exit 0; fi
[ "$(m5 "$FIN/darpan_kal.py")" = "${FROM[darpan_kal.py]}" ] || { say "!! [2/8] $FIN/darpan_kal.py is not S357's ${FROM[darpan_kal.py]} - nothing installed"; exit 1; }
[ "$(m5 "$FIN/darpan_kal.html")" = "${FROM[darpan_kal.html]}" ] || { say "!! [2/8] $FIN/darpan_kal.html is not S357's - nothing installed"; exit 1; }
[ "$(m5 "$POR/tile_grants.json")" = "${FROM[tile_grants.json]}" ] || { say "!! [2/8] $POR/tile_grants.json is not v23 ${FROM[tile_grants.json]} - nothing installed"; exit 1; }
[ -e "$FIN/darpan_month.html" ] && { say "!! [2/8] $FIN/darpan_month.html exists already - nothing installed"; exit 1; }
[ -f "$FIN/darpan_kal_schema.sql" ] && [ -s "$FIN/finance.db" ] || { say "!! [2/8] the kal schema or finance.db is missing - nothing installed"; exit 1; }
say "[2/8] S357 live; tile_grants.json v23; no month page yet"
mkdir -p "$WALK/compile" || exit 1
cp -p darpan_kal.py selftest_s358.py grant_kal_s358.py darpan_kal.html darpan_month.html views_s358.sql "$WALK/compile/" && cp -p "$FIN/darpan_kal_schema.sql" "$WALK/compile/" \
  && ( cd "$WALK/compile" && "$SPY" -m py_compile darpan_kal.py selftest_s358.py grant_kal_s358.py && "$VPY" -m py_compile darpan_kal.py selftest_s358.py grant_kal_s358.py ) \
  || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green on both pythons (on copies)"
SOUT="$( cd "$WALK/compile" && "$VPY" -B selftest_s358.py --python "$VPY" 2>&1 )"
echo "$SOUT" | grep -E '^  FAIL|selftest:' | sed 's/^/   /'
echo "$SOUT" | grep -q "^selftest: 24/24" || { say "!! [4/8] selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
"$VPY" -B grant_kal_s358.py "$POR/tile_grants.json" "$WALK/tg24.json" | sed 's/^/   /' && [ "$(m5 "$WALK/tg24.json")" = "${TO[tile_grants.json]}" ] \
  || { say "!! [4/8] the grants edit does not produce the predicted v24 bytes - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] selftest 24/24 on a scratch database in the live shape; the grants edit rehearsed = the predicted bytes"
# the kit module against the LIVE database, read-only: the pending list and the month rows must compute
POUT="$( cd "$WALK/compile" && "$VPY" - "$FIN/finance.db" <<'EOF' 2>&1
import sqlite3, sys, types
fl = types.ModuleType("flask")
class BP:
    def __init__(s, *a, **k): pass
    def route(s, *a, **k): return lambda f: f
fl.Blueprint = BP; fl.jsonify = lambda **k: k; fl.request = None; fl.send_file = lambda p: p
sys.modules["flask"] = fl
import darpan_kal as k
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); con.row_factory = sqlite3.Row
pend = k._pending_days(con, ("owner", "dr_manoj"))
unl = [d for d in pend if d["kind"] == "unlogged"]
print("pending: %d unlogged day(s) since %s, expected in all Rs %.2f; %d typed by Darpan not yet received" % (
    len(unl), k._log_from(con), sum(d["expected_p"] or 0 for d in unl) / 100.0, len(pend) - len(unl)))
ms = k._month_rows(con)
for m in ms[-2:]:
    print("month %s: sale %.0f · UPI %.0f · cash %.0f · home %.0f · procedure %.0f · adj %.0f · net cash %.0f · handed %.0f" % (
        m["ym"], m["sale_p"]/100, m["upi_p"]/100, m["cash_p"]/100, m["home_p"]/100, m["proc_p"]/100, m["adjust_p"]/100, m["net_cash_p"]/100, m["handed_p"]/100))
print("READ-ONLY OK")
EOF
)"
echo "$POUT" | sed 's/^/   /'
echo "$POUT" | grep -q "READ-ONLY OK" || { say "!! [5/8] the kit module could not read the live database - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[5/8] the pending list and the month rows compute on the live database (read-only, nothing written)"
for f in darpan_kal.py darpan_kal.html; do \cp -p "$FIN/$f" "$FIN/$f.bak_S358_${FROM[$f]:0:8}" || exit 1; done
\cp -p "$POR/tile_grants.json" "$POR/tile_grants.json.bak_S358_${FROM[tile_grants.json]:0:8}" || exit 1
say "[6/8] backups: darpan_kal.py/.html .bak_S358_<from8> · tile_grants.json.bak_S358_a5f8b3b1"
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$FIN/darpan_kal.py.bak_S358_${FROM[darpan_kal.py]:0:8}" "$FIN/darpan_kal.py"
  \cp -p "$FIN/darpan_kal.html.bak_S358_${FROM[darpan_kal.html]:0:8}" "$FIN/darpan_kal.html"
  \cp -p "$POR/tile_grants.json.bak_S358_${FROM[tile_grants.json]:0:8}" "$POR/tile_grants.json"
  rm -f "$FIN/darpan_month.html"
  systemctl restart clinic-finance clinic-portal 2>/dev/null; sleep 3
  say "   darpan_kal.py $(m5 "$FIN/darpan_kal.py") · darpan_kal.html $(m5 "$FIN/darpan_kal.html") · tile_grants.json $(m5 "$POR/tile_grants.json") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  exit 1
}
\cp -p darpan_kal.py "$FIN/darpan_kal.py" && \cp -p darpan_kal.html "$FIN/darpan_kal.html" && \cp -p darpan_month.html "$FIN/darpan_month.html" || restore
"$VPY" -B grant_kal_s358.py "$POR/tile_grants.json.bak_S358_${FROM[tile_grants.json]:0:8}" "$POR/tile_grants.json" >/dev/null || restore
for f in darpan_kal.py darpan_kal.html darpan_month.html; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
[ "$(m5 "$POR/tile_grants.json")" = "${TO[tile_grants.json]}" ] || restore
say "[7/8] placed the three page files and tile_grants.json v24"
systemctl restart clinic-finance || restore
systemctl restart clinic-portal || restore
sleep 3
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || restore; done
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
KH=$(curl -s -m 8 http://127.0.0.1:8106/finance/darpan/kal/api/healthz)
echo "$KH" | grep -q '"module"' && echo "$KH" | grep -q 'darpan_kal' || restore
IMP="$( cd "$FIN" && "$VPY" -B -c "import darpan_kal as k; print('routes:', all(hasattr(k, n) for n in ('api_pending','api_log','api_month','page_month')))" 2>&1 )"
echo "$IMP" | grep -q "routes: True" || restore
say "[8/8] both services up, healthz $HC, the kal module answers and carries the four new routes"
md5sum "$FIN/darpan_kal.py" "$FIN/darpan_kal.html" "$FIN/darpan_month.html" "$POR/tile_grants.json"
say "$KIT: DONE -- the doctors log Darpan's cash at /finance/darpan/kal (the backlog is listed there with its expected cash); the month table is at /finance/darpan/kal/month."
