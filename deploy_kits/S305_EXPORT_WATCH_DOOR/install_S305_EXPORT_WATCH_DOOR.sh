#!/bin/bash
# install_S305_EXPORT_WATCH_DOOR.sh -- the missed-export watch judges Amir's days from the server's own door
# too (D467 phase 2c): what the medical PC pushed and the door VERIFIED counts, so a sleeping clinic PC no
# longer makes a day "unknown", and the watch no longer depends on the PC that is to be retired.
#   /root/finance/export_watch.py   2920c28e -> f6845ec5  (whole file; the table, the cron lines, the screens unchanged)
# No restart: cron runs the script fresh at 23:40 and 10:45.
# Before anything is placed: the selftest, and the last ten days judged old vs new on a scratch copy of the live db.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S305_EXPORT_WATCH_DOOR/install_S305_EXPORT_WATCH_DOOR.sh
#
# Env (test only): ROOT=/some/dir   NOWALK=1
set -u
KIT="S305_EXPORT_WATCH_DOOR"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DBF="${FINANCE_DB:-$FIN/finance.db}"
PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s305_walk_$STAMP"
F=export_watch.py; FROM=2920c28ee7e9f87b89f771d4c1923831; TO=f6845ec5ae1dc8fe200ebf5f4c3ad173
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
echo "== $KIT installer =="
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 && [ "$(m5 $F)" = "$TO" ] || { echo "!! [1/6] kit sums / the kit's $F not as predicted - nothing installed"; exit 1; }
echo "[1/6] kit sums green"
cur="$(m5 "$FIN/$F")"; echo "$F : from $FROM -> to $TO ; live $cur"
[ "$cur" = "$TO" ] && { echo "ALREADY INSTALLED (live md5 == the to-pin)."; exit 0; }
[ "$cur" = "$FROM" ] || { echo "!! [2/6] $FIN/$F is $cur, expected $FROM - nothing installed"; exit 1; }
echo "[2/6] the live pin is exact"
"$PY" -c "import sys, os, tempfile, py_compile; py_compile.compile(sys.argv[1], cfile=os.path.join(tempfile.mkdtemp(), 'x.pyc'), doraise=True)" $F \
  || { echo "!! [3/6] the kit's file does not compile - nothing placed"; exit 1; }
echo "[3/6] compiles"
if [ "${NOWALK:-0}" != "1" ]; then
  mkdir -p "$WALK" && \cp -p $F "$WALK/new_$F" && \cp -p "$FIN/$F" "$WALK/old_$F"
  "$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
    || { echo "!! [4/6] scratch copy of the database failed - nothing placed"; rm -rf "$WALK"; exit 1; }
  WOUT="$( cd "$WALK" && timeout 170 "$PY" -B "$KDIR/walk_s305.py" "$WALK/old_$F" "$WALK/new_$F" "$WALK/walk.db" 2>&1 | tail -11 )"
  echo "$WOUT" | sed 's/^/       /'
  echo "$WOUT" | tail -1 | grep -q "^WALK OK" || { echo "!! [4/6] walk red - nothing placed"; rm -rf "$WALK"; exit 1; }
  rm -rf "$WALK"; echo "[4/6] walk green"
else echo "[4/6] walk skipped (NOWALK=1, test only)"; fi
BAK="$FIN/$F.bak_S305_${FROM:0:8}"; \cp -p "$FIN/$F" "$BAK" || { echo "!! [5/6] backup failed - nothing placed"; exit 1; }; echo "backup : $BAK"
\cp -p $F "$FIN/$F.S305new" && mv -f "$FIN/$F.S305new" "$FIN/$F" || { \cp -p "$BAK" "$FIN/$F"; rm -f "$FIN/$F.S305new"; echo "!! [5/6] placing failed - restored"; exit 1; }
[ "$(m5 "$FIN/$F")" = "$TO" ] || { \cp -p "$BAK" "$FIN/$F"; echo "!! [5/6] placed file not as predicted - restored $(m5 "$FIN/$F")"; exit 1; }
echo "[5/6] placed"
echo "[6/6] $KIT: DONE -- $(md5sum "$FIN/$F")"
