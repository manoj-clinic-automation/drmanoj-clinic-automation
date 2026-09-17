#!/bin/bash
# install_S307_SUPPLIER_CHECK_2.sh -- the wrong-supplier check, second stage, on Amir's step 4: a purchase return
# written under a supplier who never supplied the item says so; the same bill number and date under two suppliers
# is named on both bills (the same amount = one bill possibly entered twice).
#   /root/finance/amir_day.py   b3c20319 -> 00c443cb   (three anchored edits, patched ON THE BOX from its live bytes)
# No table, no setting. clinic-finance restarted.
# Before anything is placed: the patched file walks a SCRATCH copy of the live database.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S307_SUPPLIER_CHECK_2/install_S307_SUPPLIER_CHECK_2.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   NOWALK=1
set -u
KIT="S307_SUPPLIER_CHECK_2"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DBF="${FINANCE_DB:-$FIN/finance.db}"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s307_walk_$STAMP"
F="$FIN/amir_day.py"; FROM="b3c20319c4808ebc64bec197c951468c"; TO="00c443cbce0b07ba763bbe655a3e3c58"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
echo "== $KIT installer =="
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
echo "[1/7] kit sums green"
cur="$(m5 "$F")"; echo "amir_day.py : from $FROM -> to $TO ; live $cur"
[ "$cur" = "$TO" ] && { echo "ALREADY INSTALLED (live md5 == the to-pin)."; exit 0; }
[ "$cur" = "$FROM" ] || { echo "!! [2/7] $F is $cur, expected $FROM - nothing installed"; exit 1; }
echo "[2/7] the live pin is exact"
rm -f "$F.S307new"*; \cp -p "$F" "$F.S307new" || { echo "!! [3/7] copy failed"; exit 1; }
"$PY" -B patch_supplier_check2_s307.py --file "$F.S307new" --from "$FROM" || { rm -f "$F.S307new"*; echo "!! [3/7] patch refused - nothing placed"; exit 1; }
rm -f "$F.S307new.bak_S307_"*
[ "$(m5 "$F.S307new")" = "$TO" ] || { rm -f "$F.S307new"; echo "!! [3/7] patched to an unpredicted md5 - nothing placed"; exit 1; }
"$PY" -c "import sys, os, tempfile, py_compile; py_compile.compile(sys.argv[1], cfile=os.path.join(tempfile.mkdtemp(), 'x.pyc'), doraise=True)" "$F.S307new" \
  || { rm -f "$F.S307new"; echo "!! [3/7] compile failed - nothing placed"; exit 1; }
echo "[3/7] patched on the box to the predicted md5; compiles"
if [ "${NOWALK:-0}" != "1" ]; then
  mkdir -p "$WALK" && \cp -p "$F.S307new" "$WALK/amir_new.py" && \cp -p "$F" "$WALK/amir_live.py"
  "$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
    || { echo "!! [4/7] scratch copy of the database failed - nothing placed"; rm -rf "$WALK"; rm -f "$F.S307new"; exit 1; }
  WOUT="$( cd "$FIN" && timeout 170 "$PY" -B "$KDIR/walk_s307.py" "$WALK/amir_live.py" "$WALK/amir_new.py" "$WALK/walk.db" 2>&1 | tail -2 )"
  echo "$WOUT" | sed 's/^/       /'
  echo "$WOUT" | tail -1 | grep -q "^WALK OK" || { echo "!! [4/7] walk red - nothing placed"; rm -rf "$WALK"; rm -f "$F.S307new"; exit 1; }
  rm -rf "$WALK"; echo "[4/7] walk green on a scratch copy of the live database"
else echo "[4/7] walk skipped (NOWALK=1, test only)"; fi
BAK="$F.bak_S307_${FROM:0:8}"; \cp -p "$F" "$BAK" || { rm -f "$F.S307new"; echo "!! [5/7] backup failed - nothing placed"; exit 1; }; echo "backup : $BAK"
restore() { echo "!! RED - restoring amir_day.py byte-identically"; \cp -p "$BAK" "$F"; rm -f "$F.S307new"
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; sleep 3; fi
  echo "   $F $(m5 "$F")"; exit 1; }
mv -f "$F.S307new" "$F" || restore
[ "$(m5 "$F")" = "$TO" ] || restore
echo "[5/7] placed"
if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore; sleep 4
  systemctl is-active --quiet clinic-finance || { echo "!! clinic-finance not active"; restore; }
  c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/amir/api/healthz)
  echo "health : amir $c1"; [ "$c1" = 200 ] || restore
  echo "[6/7] clinic-finance active and answering"
else echo "[6/7] restart skipped (NORESTART=1, test only)"; fi
echo "[7/7] $KIT: DONE -- $(md5sum "$F")"
