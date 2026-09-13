#!/bin/bash
# install_S256_GATEWAY_REF.sh -- keep the Razorpay reference Docterz already sends.
# Two full-file replacements in $ROOT/finance, each pinned from -> to by md5.
# Additive: one new column with a default. No existing figure changes.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S256_GATEWAY_REF/install_S256_GATEWAY_REF.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   FORCE_FAIL=1
set -e
set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
A_NAME="docterz_day.py";    A_FROM="e939235ee5d37bcbf21ce2c5c4de1f01"; A_TO="75f89072f368a5f60bb6b75510d7a959"
B_NAME="docterz_ingest.py"; B_FROM="80bf760dd6103504776964c58d876f17"; B_TO="3809f046e4b33d834e164c5320d91b4c"
PY="$ROOT/wa/venv/bin/python3"
if [ ! -x "$PY" ]; then PY="/usr/bin/python3"; fi
if [ ! -x "$PY" ]; then PY="$(command -v python3)"; fi
md5of() { md5sum "$1" | awk '{print $1}'; }

echo "== S256_GATEWAY_REF installer =="; echo "target : $FIN"; echo "python : $PY"
for n in "$A_NAME" "$B_NAME"; do [ -f "$FIN/$n" ] || { echo "REFUSED: $FIN/$n not found"; exit 1; }; done
A_LIVE="$(md5of "$FIN/$A_NAME")"; B_LIVE="$(md5of "$FIN/$B_NAME")"
echo "$A_NAME : from $A_FROM -> to $A_TO ; live $A_LIVE"
echo "$B_NAME : from $B_FROM -> to $B_TO ; live $B_LIVE"
if [ "$A_LIVE" = "$A_TO" ] && [ "$B_LIVE" = "$B_TO" ]; then
  echo "ALREADY INSTALLED (both live md5 == to-pin). Nothing to do."; md5sum "$FIN/$A_NAME" "$FIN/$B_NAME"; exit 0
fi
[ "$A_LIVE" = "$A_FROM" ] || { echo "REFUSED: $A_NAME is $A_LIVE, expected $A_FROM"; exit 1; }
[ "$B_LIVE" = "$B_FROM" ] || { echo "REFUSED: $B_NAME is $B_LIVE, expected $B_FROM"; exit 1; }

A_BAK="$FIN/$A_NAME.bak_S256_${A_FROM:0:8}"; B_BAK="$FIN/$B_NAME.bak_S256_${B_FROM:0:8}"
\cp -p "$FIN/$A_NAME" "$A_BAK"; \cp -p "$FIN/$B_NAME" "$B_BAK"
echo "backup : $A_BAK"; echo "backup : $B_BAK"
restore() {
  echo "!! restoring both files byte-identically"
  \cp -p "$A_BAK" "$FIN/$A_NAME"; \cp -p "$B_BAK" "$FIN/$B_NAME"
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/$A_NAME" "$FIN/$B_NAME"; exit 1
}
\cp -p "$KIT_DIR/$A_NAME" "$FIN/$A_NAME" || restore
\cp -p "$KIT_DIR/$B_NAME" "$FIN/$B_NAME" || restore
"$PY" -m py_compile "$FIN/$A_NAME" "$FIN/$B_NAME" || restore
echo "smoke  : py_compile OK"
[ "${FORCE_FAIL:-0}" = "1" ] && { echo "smoke  : FORCED FAILURE"; restore; }
"$PY" - "$FIN" <<'PYSMOKE' || restore
import importlib.util, sqlite3, sys
fin = sys.argv[1]
def load(n):
    s = importlib.util.spec_from_file_location(n, fin + "/" + n + ".py")
    m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
day = load("docterz_day"); ing = load("docterz_ingest")
con = sqlite3.connect(":memory:"); con.row_factory = sqlite3.Row
con.executescript(ing.SCHEMA)
d = {"business_date": "2026-01-01", "lines": [
     {"section":"consult","sn":1,"patient":"A","clinic_id":"1","amount_p":60000,
      "mode":"Online Payment","gateway_ref":"pay_SMOKE123456","shift":"Morning"},
     {"section":"consult","sn":2,"patient":"B","clinic_id":"2","amount_p":60000,
      "mode":"Cash","gateway_ref":"","shift":"Morning"}]}
ing.upsert_lines(con, d)
got = [r["gateway_ref"] for r in con.execute("SELECT gateway_ref FROM clinic_day_line ORDER BY sn")]
assert got == ["pay_SMOKE123456", ""], got
assert day._GATEWAY.search("Online Payment pay_ABCDEF1234"), "regex"
print("smoke  : SMOKE_OK reference stored, blank kept blank")
PYSMOKE
if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore
  sleep 3
  systemctl is-active --quiet clinic-finance || restore
  echo "service: clinic-finance active after restart"
fi
echo "md5sum of installed files:"; md5sum "$FIN/$A_NAME" "$FIN/$B_NAME"
echo "S256_GATEWAY_REF: DONE"
