#!/bin/bash
# install_S255_PORTAL_CHANNEL.sh -- D510: portal money (Docterz Wallet / Patient APP /
# Net Banking = Razorpay -> Yes Bank) stops being expected in the ICICI MPR.
# Two full-file replacements in $ROOT/finance, each pinned from -> to by md5.
# Rolls BOTH back and restarts the old code on any failure.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S255_PORTAL_CHANNEL/install_S255_PORTAL_CHANNEL.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   FORCE_FAIL=1
set -e
set -u

ROOT="${ROOT:-/root}"
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
FIN="$ROOT/finance"

A_NAME="finance_clinic_day.py"; A_FROM="b2b7ff7d8ed654aa4cca067b1cfe5716"; A_TO="992865c032c20abd33d21ee1abb12c38"
B_NAME="clinic_money.py";       B_FROM="d5c3a8459b04753e09e9630cb2de6560"; B_TO="97368596e774969fdaea3cfc09f9d64f"

PY="$ROOT/wa/venv/bin/python3"
if [ ! -x "$PY" ]; then PY="/usr/bin/python3"; fi
if [ ! -x "$PY" ]; then PY="$(command -v python3)"; fi

md5of() { md5sum "$1" | awk '{print $1}'; }

echo "== S255_PORTAL_CHANNEL installer =="
echo "target : $FIN"
echo "python : $PY"

for pair in "$A_NAME:$A_FROM:$A_TO" "$B_NAME:$B_FROM:$B_TO"; do
  n="${pair%%:*}"; rest="${pair#*:}"; f="${rest%%:*}"; t="${rest##*:}"
  [ -f "$FIN/$n" ] || { echo "REFUSED: $FIN/$n not found"; exit 1; }
  echo "$n : from $f -> to $t ; live $(md5of "$FIN/$n")"
done

A_LIVE="$(md5of "$FIN/$A_NAME")"; B_LIVE="$(md5of "$FIN/$B_NAME")"
if [ "$A_LIVE" = "$A_TO" ] && [ "$B_LIVE" = "$B_TO" ]; then
  echo "ALREADY INSTALLED (both live md5 == to-pin). Nothing to do."
  md5sum "$FIN/$A_NAME" "$FIN/$B_NAME"; exit 0
fi
if [ "$A_LIVE" != "$A_FROM" ]; then echo "REFUSED: $A_NAME is $A_LIVE, expected $A_FROM"; exit 1; fi
if [ "$B_LIVE" != "$B_FROM" ]; then echo "REFUSED: $B_NAME is $B_LIVE, expected $B_FROM"; exit 1; fi

A_BAK="$FIN/$A_NAME.bak_S255_${A_FROM:0:8}"; B_BAK="$FIN/$B_NAME.bak_S255_${B_FROM:0:8}"
\cp -p "$FIN/$A_NAME" "$A_BAK"; \cp -p "$FIN/$B_NAME" "$B_BAK"
echo "backup : $A_BAK"
echo "backup : $B_BAK"

restore() {
  echo "!! restoring both files byte-identically"
  \cp -p "$A_BAK" "$FIN/$A_NAME"; \cp -p "$B_BAK" "$FIN/$B_NAME"
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/$A_NAME" "$FIN/$B_NAME"
  exit 1
}

\cp -p "$KIT_DIR/$A_NAME" "$FIN/$A_NAME" || restore
\cp -p "$KIT_DIR/$B_NAME" "$FIN/$B_NAME" || restore

"$PY" -m py_compile "$FIN/$A_NAME" "$FIN/$B_NAME" || restore
echo "smoke  : py_compile OK"

if [ "${FORCE_FAIL:-0}" = "1" ]; then echo "smoke  : FORCED FAILURE"; restore; fi

# import-only smoke: the three figures exist and agree on a throwaway in-memory day
"$PY" - "$FIN" <<'PYSMOKE' || restore
import importlib.util, sqlite3, sys
fin = sys.argv[1]
def load(n):
    s = importlib.util.spec_from_file_location(n, fin + "/" + n + ".py")
    m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
con = sqlite3.connect(":memory:"); con.row_factory = sqlite3.Row
con.executescript("CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, sn INTEGER,"
                  " patient TEXT, clinic_id TEXT, amount_p INTEGER, mode TEXT, shift TEXT);"
                  "CREATE TABLE clinic_day_tender (business_date TEXT, clinic_id TEXT,"
                  " invoice_no TEXT, tender TEXT, amount_p INTEGER);")
con.executemany("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?)",
                [("2026-01-01","consult",1,"A","C1",50000,"Online Payment","m"),
                 ("2026-01-01","consult",2,"B","C2",60000,"Wallet","m")])
con.commit()
fcd = load("finance_clinic_day"); cm = load("clinic_money")
assert fcd.our_online_p(con,"2026-01-01") == 110000, "online total"
assert fcd.our_icici_online_p(con,"2026-01-01") == 50000, "icici only"
assert fcd.our_portal_p(con,"2026-01-01") == 60000, "portal only"
assert cm._channel_of("Patient APP") == "portal" and cm._channel_of("Online Payment") == "icici"
print("smoke  : SMOKE_OK icici=50000 portal=60000 total=110000")
PYSMOKE

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore
  sleep 3
  systemctl is-active --quiet clinic-finance || restore
  echo "service: clinic-finance active after restart"
fi

echo "md5sum of installed files:"
md5sum "$FIN/$A_NAME" "$FIN/$B_NAME"
echo "S255_PORTAL_CHANNEL: DONE"
