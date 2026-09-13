#!/bin/bash
# install_S257_PORTAL_EVIDENCE.sh -- D510: portal money recognised by its Razorpay id, never by the
# mode word. Two full-file replacements in $ROOT/finance, pinned from -> to; restart; then a re-read
# of every Docterz export on Drive so past days gain their ids (docterz_ingest.py --all, S256).
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S257_PORTAL_EVIDENCE/install_S257_PORTAL_EVIDENCE.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   NOBACKFILL=1   FORCE_FAIL=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
A_NAME="finance_clinic_day.py"; A_FROM="b2b7ff7d8ed654aa4cca067b1cfe5716"; A_TO="15818d91ab1b553e76e317d603d37963"
B_NAME="clinic_money.py";       B_FROM="d5c3a8459b04753e09e9630cb2de6560"; B_TO="14e96b76230f25eccac2bcb28e741ea4"
ING_TO="3809f046e4b33d834e164c5320d91b4c"     # docterz_ingest.py as installed by S256
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S257_PORTAL_EVIDENCE installer =="; echo "target : $FIN"; echo "python : $PY"
for n in "$A_NAME" "$B_NAME" docterz_ingest.py; do [ -f "$FIN/$n" ] || { echo "REFUSED: $FIN/$n not found"; exit 1; }; done
[ "$(md5of "$FIN/docterz_ingest.py")" = "$ING_TO" ] || { echo "REFUSED: S256_GATEWAY_REF is not installed (docterz_ingest.py is $(md5of "$FIN/docterz_ingest.py")). Install S256 first."; exit 1; }
A_LIVE="$(md5of "$FIN/$A_NAME")"; B_LIVE="$(md5of "$FIN/$B_NAME")"
echo "$A_NAME : from $A_FROM -> to $A_TO ; live $A_LIVE"
echo "$B_NAME : from $B_FROM -> to $B_TO ; live $B_LIVE"
if [ "$A_LIVE" = "$A_TO" ] && [ "$B_LIVE" = "$B_TO" ]; then echo "ALREADY INSTALLED (both live md5 == to-pin)."; md5sum "$FIN/$A_NAME" "$FIN/$B_NAME"; exit 0; fi
[ "$A_LIVE" = "$A_FROM" ] || { echo "REFUSED: $A_NAME is $A_LIVE, expected $A_FROM"; exit 1; }
[ "$B_LIVE" = "$B_FROM" ] || { echo "REFUSED: $B_NAME is $B_LIVE, expected $B_FROM"; exit 1; }
A_BAK="$FIN/$A_NAME.bak_S257_${A_FROM:0:8}"; B_BAK="$FIN/$B_NAME.bak_S257_${B_FROM:0:8}"
\cp -p "$FIN/$A_NAME" "$A_BAK"; \cp -p "$FIN/$B_NAME" "$B_BAK"; echo "backup : $A_BAK"; echo "backup : $B_BAK"
restore() { echo "!! restoring both files byte-identically"; \cp -p "$A_BAK" "$FIN/$A_NAME"; \cp -p "$B_BAK" "$FIN/$B_NAME"
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi; md5sum "$FIN/$A_NAME" "$FIN/$B_NAME"; exit 1; }
\cp -p "$KIT_DIR/$A_NAME" "$FIN/$A_NAME" || restore
\cp -p "$KIT_DIR/$B_NAME" "$FIN/$B_NAME" || restore
"$PY" -m py_compile "$FIN/$A_NAME" "$FIN/$B_NAME" || restore; echo "smoke  : py_compile OK"
[ "${FORCE_FAIL:-0}" = "1" ] && { echo "smoke  : FORCED FAILURE"; restore; }
"$PY" - "$FIN" <<'PYSMOKE' || restore
import importlib.util, sqlite3, sys
fin = sys.argv[1]
def load(n):
    s = importlib.util.spec_from_file_location(n, fin + "/" + n + ".py"); m = importlib.util.module_from_spec(s)
    sys.modules[n] = m; s.loader.exec_module(m); return m
con = sqlite3.connect(":memory:"); con.row_factory = sqlite3.Row
con.executescript("CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, sn INTEGER, patient TEXT,"
  " clinic_id TEXT, amount_p INTEGER, mode TEXT, shift TEXT, gateway_ref TEXT NOT NULL DEFAULT '');"
  "CREATE TABLE clinic_day_tender (business_date TEXT, clinic_id TEXT, invoice_no TEXT, tender TEXT, amount_p INTEGER);")
con.executemany("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?,?)",
  [("2026-01-01","consult",1,"A","1",60000,"Wallet","m",""), ("2026-01-01","consult",2,"B","2",60000,"Online Payment","m","pay_SMOKE1234")])
fcd = load("finance_clinic_day"); cm = load("clinic_money")
assert fcd.our_online_p(con,"2026-01-01") == 120000
assert fcd.our_icici_online_p(con,"2026-01-01") == 60000 and fcd.our_portal_p(con,"2026-01-01") == 60000
d = cm._docterz(con,"2026-01-01"); assert [o["channel"] for o in d["online"]] == ["icici","portal"]
print("smoke  : SMOKE_OK wallet-without-id=icici, online-with-id=portal")
PYSMOKE
if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || restore; sleep 3; systemctl is-active --quiet clinic-finance || restore; echo "service: clinic-finance active after restart"; fi
echo "md5sum of installed files:"; md5sum "$FIN/$A_NAME" "$FIN/$B_NAME"
echo "S257_PORTAL_EVIDENCE: DONE"
if [ "${NOBACKFILL:-0}" != "1" ]; then
  echo; echo "== backfill: re-reading every Docterz export on Drive so past days gain their Razorpay ids =="
  if "$PY" -B "$FIN/docterz_ingest.py" --all; then
    echo "backfill: DONE"
    "$PY" - "$FIN" <<'PYCOUNT' || true
import sqlite3, sys
try:
    con = sqlite3.connect(sys.argv[1] + "/finance.db")
    n, s = con.execute("SELECT COUNT(*), COALESCE(SUM(amount_p),0) FROM clinic_day_line WHERE gateway_ref != ''").fetchone()
    print("backfill: %d line(s) now carry a Razorpay id, Rs %s in all" % (n, "{:,}".format(s // 100)))
    for r in con.execute("SELECT business_date, COUNT(*) FROM clinic_day_line WHERE gateway_ref != '' GROUP BY 1 ORDER BY 1"):
        print("  ", r[0], r[1])
except Exception as e:
    print("backfill: count skipped (%s)" % e)
PYCOUNT
  else
    echo "backfill: FAILED -- the code is installed and correct; past days simply have no ids yet. Re-run later:"
    echo "  $PY -B $FIN/docterz_ingest.py --all"
  fi
fi
