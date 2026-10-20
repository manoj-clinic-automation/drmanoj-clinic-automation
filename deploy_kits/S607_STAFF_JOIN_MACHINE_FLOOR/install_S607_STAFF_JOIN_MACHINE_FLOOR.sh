#!/bin/bash
# =============================================================================
#  install_S607_STAFF_JOIN_MACHINE_FLOOR.sh · kit S607 (session S331, 20-Oct-2026) · follows S606 (installed 18:36 IST)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S607_STAFF_JOIN_MACHINE_FLOOR/install_S607_STAFF_JOIN_MACHINE_FLOOR.sh
#  DRY=1 before bash: pins, rebuild, walk and control only -- nothing changed.   --undo at the end: the S606 files back.
#
#  Found by reading the live page after S606 went in: the machine card offered two fingers from the machine's set-up
#  day (07-Oct: number 2 -- likely the owner's own administrator finger -- and the retired 100). A "Yes" there would
#  have made the owner's finger Arjun Dev's. Now only fingers pressed from the day before the joining was opened are
#  offered (and only those can be linked). staff_easy.py + staff_easy.html; nothing else.
# =============================================================================
set -u
KIT="S607_STAFF_JOIN_MACHINE_FLOOR"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s607_backup}"
FD="${FD:-/root/finance}"
SR_DB="${SR_DB:-/root/staff_register/staff_register.db}"
SMASTER="${SMASTER:-/root/staff_master.csv}"
PUNCH="${PUNCH:-/root/punches.csv}"
USERS="${USERS:-/root/portal/clinic_users.json}"
PORTAL_DIR="${PORTAL_DIR:-/root/portal}"
SVC="${SVC:-clinic-finance}"
BASE="${BASE:-http://127.0.0.1:8106}"
PIN_PY="b120ff1f187d763f329503c6da176249"
PIN_HTML="d0cb85b9a81a32cc26a3b408cb0e7337"
PIN_PAGES="856644e9e5dfbf70d7ce92e35a3954fd"
PIN_JOINER="6305b05dccf0d915924c9f698eddc94e"
PIN_SCHEMA="8bb6aeb99e758fba279d353cfa7990ee"
W=/tmp/s607_walk
HAVE_LOCK=0
on_exit() { rm -rf "$W"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
PYTHONPYCACHEPREFIX=/tmp/s607_pyc "$PY" -m py_compile staff_easy.py walk_s607.py rebuild_s607.py \
  || stop "the kit's code does not compile"
rm -rf /tmp/s607_pyc
NEW_PY=$(m5 staff_easy.py); NEW_HTML=$(m5 staff_easy.html)

restart_and_check() {             # sets OKH=1 when the new page answers; never inside $( )
  OKH=0
  T0=$(date '+%Y-%m-%d %H:%M:%S')
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1
  TOK=$(systemctl show -p Environment "$SVC" 2>/dev/null | tr ' ' '\n' | sed -n 's/^FINANCE_CRON_TOKEN=//p')
  for i in $(seq 1 30); do
    sleep 1
    H=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' "$BASE/finance/healthz")
    [ "$H" = "200" ] && break
  done
  NEWP=$(curl -s --max-time 8 -o /dev/null -w '%{http_code}' -H "X-Finance-Cron: $TOK" "$BASE/finance/staff/new")
  OLDP=$(curl -s --max-time 8 -o /dev/null -w '%{http_code}' -H "X-Finance-Cron: $TOK" "$BASE/finance/staff")
  APIP=$(curl -s --max-time 8 -o /dev/null -w '%{http_code}' -H "X-Finance-Cron: $TOK" "$BASE/finance/staff/easy/api/list")
  unset TOK
  NOTM=$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c "S606) NOT mounted")
  # a route that exists answers 403 to the cron door (no person); a missing one answers 404
  [ "$H" = "200" ] && [ "$NEWP" = "403" ] && [ "$OLDP" = "403" ] && [ "$APIP" = "403" ] && [ "$NOTM" = "0" ] && OKH=1
}

if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  for f in staff_easy.py staff_easy.html; do
    b=$(ls -1t "$BK/$f".bak_S607_* 2>/dev/null | head -1)
    [ -n "$b" ] && \cp -f "$b" "$FD/$f" && echo "    $f put back ($(m5 "$FD/$f" | cut -c1-8))"
  done
  restart_and_check
  echo "    $SVC: $(systemctl is-active "$SVC") · /finance/staff/new answers $NEWP"
  echo "UNDONE."; exit 0
fi

echo "[1] pins"
[ "$(m5 "$FD/joiner_app.py")" = "$PIN_JOINER" ] || stop "joiner_app.py is not the file this kit was built on"
[ "$(m5 "$FD/staff_pages.py")" = "$PIN_PAGES" ] || stop "staff_pages.py is not the S606 file (${PIN_PAGES:0:8}) -- S606 must be installed first"
NOWP=$(m5 "$FD/staff_easy.py"); NOWH=$(m5 "$FD/staff_easy.html")
if [ "$NOWP" = "$NEW_PY" ] && [ "$NOWH" = "$NEW_HTML" ]; then
  echo "    ALREADY INSTALLED (staff_easy.py ${NEW_PY:0:8}, staff_easy.html ${NEW_HTML:0:8})"
  exit 0
fi
[ "$NOWP" = "$PIN_PY" ] || stop "staff_easy.py is not the S606 file (${NOWP:0:8}, expected ${PIN_PY:0:8})"
[ "$NOWH" = "$PIN_HTML" ] || stop "staff_easy.html is not the S606 file (${NOWH:0:8}, expected ${PIN_HTML:0:8})"
echo "    staff_easy.py ${NOWP:0:8} · staff_easy.html ${NOWH:0:8} · readers staff_pages ${PIN_PAGES:0:8}, joiner_app ${PIN_JOINER:0:8}"

echo "[2] rebuild from the live bytes"
"$PY" -B rebuild_s607.py "$FD" "$KDIR" /tmp/s607_rb || { rm -rf /tmp/s607_rb; stop "the kit's files are not exactly the live files plus this kit's edits"; }
rm -rf /tmp/s607_rb

echo "[3] the walk, on scratch copies (made-up people, punches dated 2099)"
prep() {
  rm -rf "$W"; mkdir -p "$W/scratch" "$W/code"; chmod 700 "$W"
  "$PY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$FD/finance.db" "$W/scratch/finance.db" || return 1
  "$PY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$SR_DB" "$W/scratch/staff_register.db" || return 1
  \cp -f "$SMASTER" "$W/scratch/staff_master.csv" && \cp -f "$PUNCH" "$W/scratch/punches.csv" && \cp -f "$USERS" "$W/scratch/clinic_users.json" || return 1
  \cp -f "$FD/joiner_app.py" "$FD/joiner_schema.sql" "$FD/staff_pages.py" "$FD/staff_manage.html" "$W/code/"
}
prep || stop "the scratch copies could not be made"
\cp -f staff_easy.py staff_easy.html "$W/code/"
"$PY" -B walk_s607.py --code "$W/code" --scratch "$W/scratch" --portal-dir "$PORTAL_DIR" > "$W/walk.txt" 2>&1
WK=$?; grep -E "^WALK" "$W/walk.txt" | sed 's/^/    /'; tail -1 "$W/walk.txt" | sed 's/^/    walk: /'
[ "$WK" = 0 ] || { grep "FAIL\|RED\|Error" "$W/walk.txt" | head -8; stop "the walk on the scratch copies is not green"; }
prep || stop "the scratch copies could not be made (control)"
\cp -f "$FD/staff_easy.py" "$FD/staff_easy.html" "$W/code/"
"$PY" -B walk_s607.py --code "$W/code" --scratch "$W/scratch" --portal-dir "$PORTAL_DIR" > "$W/ctl.txt" 2>&1
CK=$?
[ "$CK" != 0 ] && echo "    control on the live (S606) files: RED, as it must be ($(grep -m1 'FAIL' "$W/ctl.txt" | cut -c1-80))" \
               || stop "the control did not go red -- the walk cannot tell old from new"
rm -rf "$W"
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[4] backups -> $BK"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -f "$FD/staff_easy.py" "$BK/staff_easy.py.bak_S607_$NOWP"
\cp -f "$FD/staff_easy.html" "$BK/staff_easy.html.bak_S607_$NOWH"
chmod 600 "$BK"/*

echo "[5] placed"
\cp -f staff_easy.py staff_easy.html "$FD/"
for f in staff_easy.py staff_easy.html; do
  [ "$(m5 "$FD/$f")" = "$(m5 "$f")" ] || stop "$f did not land byte-exact" "Run the line again with --undo at the end."
done
echo "    staff_easy.py ${NOWP:0:8} -> ${NEW_PY:0:8} · staff_easy.html ${NOWH:0:8} -> ${NEW_HTML:0:8}"

echo "[6] $SVC restarted and checked"
restart_and_check
if [ "$OKH" != 1 ]; then
  \cp -f "$BK/staff_easy.py.bak_S607_$NOWP" "$FD/staff_easy.py"; \cp -f "$BK/staff_easy.html.bak_S607_$NOWH" "$FD/staff_easy.html"
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1
  stop "the finance app did not come back with the page (health $H · new page $NEWP · old page $OLDP · api $APIP · not-mounted lines $NOTM)" \
       "The S606 files were put back and $SVC restarted."
fi
echo "    health $H · /finance/staff/new $NEWP · /finance/staff $OLDP · api $APIP (403 = there, and closed to a caller with no login)"

echo "[7] pins"
for f in staff_easy.py staff_easy.html staff_pages.py; do echo "    $(md5sum "$FD/$f")"; done
echo "DONE. Open https://followup.dr-manoj.in/finance/staff/new"
