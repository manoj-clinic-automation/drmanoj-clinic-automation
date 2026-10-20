#!/bin/bash
# =============================================================================
#  install_S606_STAFF_JOIN_EASY.sh · kit S606 (session S331, 20-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S606_STAFF_JOIN_EASY/install_S606_STAFF_JOIN_EASY.sh
#  DRY=1 before bash: pins, rebuild, walk and control only -- nothing changed.   --undo at the end: the files back.
#
#  THE OWNER, 20-Oct-2026: "look into new staff addition flow, because when I tried with one new staff, Arjun Dev,
#  I got stuck up at one point of the flow" · "Few might not have whatsapp or smartphone occasionally, build this
#  functionality, biometric new staff entry is also confusing for us".
#   1. /finance/staff/new -- ADD STAFF: one form; his login given the way his phone allows (WhatsApp into HIS chat,
#      SMS, printed slip, or no login at all); the machine step shows his new finger by itself -- one tap "Yes, this
#      is him" puts him in staff_master.csv and the staff register, and closes the joining.
#   2. staff_pages.py mounts it (finance_app.py untouched); the old page /finance/staff gets one banner line.
#   3. the data step: open joinings settled -- Arjun Dev's login "arjun dev" (with a space) becomes "arjundev".
# =============================================================================
set -u
KIT="S606_STAFF_JOIN_EASY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s606_backup}"
FD="${FD:-/root/finance}"
SR_DB="${SR_DB:-/root/staff_register/staff_register.db}"
SMASTER="${SMASTER:-/root/staff_master.csv}"
PUNCH="${PUNCH:-/root/punches.csv}"
USERS="${USERS:-/root/portal/clinic_users.json}"
PORTAL_DIR="${PORTAL_DIR:-/root/portal}"
SVC="${SVC:-clinic-finance}"
BASE="${BASE:-http://127.0.0.1:8106}"
PIN_PAGES="0fde34ca56cb6e0905b7ea7fb7475466"
PIN_HTML="71540e8c610b02636d08ae7d0739df1d"
PIN_JOINER="6305b05dccf0d915924c9f698eddc94e"
PIN_SCHEMA="8bb6aeb99e758fba279d353cfa7990ee"
W=/tmp/s606_walk
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
PYTHONPYCACHEPREFIX=/tmp/s606_pyc "$PY" -m py_compile staff_easy.py staff_pages.py walk_s606.py rebuild_s606.py settle_s606.py \
  || stop "the kit's code does not compile"
rm -rf /tmp/s606_pyc
NEW_PAGES=$(m5 staff_pages.py); NEW_HTML=$(m5 staff_manage.html)

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
  for f in staff_pages.py staff_manage.html; do
    b=$(ls -1t "$BK/$f".bak_S606_* 2>/dev/null | head -1)
    [ -n "$b" ] && \cp -f "$b" "$FD/$f" && echo "    $f put back ($(m5 "$FD/$f" | cut -c1-8))"
  done
  mkdir -p "$BK/_removed"
  for f in staff_easy.py staff_easy.html; do [ -f "$FD/$f" ] && mv -f "$FD/$f" "$BK/_removed/$f" && echo "    $f moved to $BK/_removed/"; done
  restart_and_check
  echo "    $SVC: $(systemctl is-active "$SVC") · /finance/staff answers $OLDP"
  echo "    Data written by the new page (logins, staff rows, staff_master rows) stays; backups are in $BK."
  echo "UNDONE."; exit 0
fi

echo "[1] pins"
[ "$(m5 "$FD/joiner_app.py")" = "$PIN_JOINER" ] || stop "joiner_app.py is not the file this kit was built on ($(m5 "$FD/joiner_app.py" | cut -c1-8), expected ${PIN_JOINER:0:8})"
[ "$(m5 "$FD/joiner_schema.sql")" = "$PIN_SCHEMA" ] || stop "joiner_schema.sql is not the file this kit was built on"
NOWP=$(m5 "$FD/staff_pages.py"); NOWH=$(m5 "$FD/staff_manage.html")
ALREADY=0
if [ "$NOWP" = "$NEW_PAGES" ] && [ "$NOWH" = "$NEW_HTML" ] && [ "$(m5 "$FD/staff_easy.py")" = "$(m5 staff_easy.py)" ] \
   && [ "$(m5 "$FD/staff_easy.html")" = "$(m5 staff_easy.html)" ]; then
  ALREADY=1; echo "    ALREADY INSTALLED (all four files are the S606 ones)"
else
  [ "$NOWP" = "$PIN_PAGES" ] || [ "$NOWP" = "$NEW_PAGES" ] || stop "staff_pages.py is not the file this kit was built on (${NOWP:0:8}, expected ${PIN_PAGES:0:8})"
  [ "$NOWH" = "$PIN_HTML" ] || [ "$NOWH" = "$NEW_HTML" ] || stop "staff_manage.html is not the file this kit was built on (${NOWH:0:8}, expected ${PIN_HTML:0:8})"
  echo "    joiner_app ${PIN_JOINER:0:8} · schema ${PIN_SCHEMA:0:8} · staff_pages ${NOWP:0:8} · staff_manage ${NOWH:0:8}"
fi

if [ "$ALREADY" = 0 ]; then
  echo "[2] rebuild from the live bytes"
  if [ "$NOWP" = "$PIN_PAGES" ] && [ "$NOWH" = "$PIN_HTML" ]; then
    "$PY" -B rebuild_s606.py "$FD" "$KDIR" /tmp/s606_rb || { rm -rf /tmp/s606_rb; stop "the kit's files are not exactly the live files plus this kit's edits"; }
    rm -rf /tmp/s606_rb
  else echo "    (part already placed by an earlier run -- skipped)"; fi

  echo "[3] the walk, on scratch copies (made-up people, punches dated 2099)"
  prep() {
    rm -rf "$W"; mkdir -p "$W/scratch" "$W/code"; chmod 700 "$W"
    "$PY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$FD/finance.db" "$W/scratch/finance.db" || return 1
    "$PY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$SR_DB" "$W/scratch/staff_register.db" || return 1
    \cp -f "$SMASTER" "$W/scratch/staff_master.csv" && \cp -f "$PUNCH" "$W/scratch/punches.csv" && \cp -f "$USERS" "$W/scratch/clinic_users.json" || return 1
    \cp -f "$FD/joiner_app.py" "$FD/joiner_schema.sql" "$W/code/"
  }
  prep || stop "the scratch copies could not be made"
  \cp -f staff_pages.py staff_easy.py staff_easy.html staff_manage.html "$W/code/"
  "$PY" -B walk_s606.py --code "$W/code" --scratch "$W/scratch" --portal-dir "$PORTAL_DIR" > "$W/walk.txt" 2>&1
  WK=$?; tail -1 "$W/walk.txt" | sed 's/^/    walk: /'; grep -E "^WALK" "$W/walk.txt" | sed 's/^/    /'
  [ "$WK" = 0 ] || { grep "FAIL\|RED\|Error" "$W/walk.txt" | head -8; stop "the walk on the scratch copies is not green"; }
  prep || stop "the scratch copies could not be made (control)"
  \cp -f "$FD/staff_pages.py" "$FD/staff_manage.html" "$W/code/"
  [ "$NOWP" = "$PIN_PAGES" ] || \cp -f "$BK"/staff_pages.py.bak_S606_* "$W/code/staff_pages.py" 2>/dev/null
  "$PY" -B walk_s606.py --code "$W/code" --scratch "$W/scratch" --portal-dir "$PORTAL_DIR" > "$W/ctl.txt" 2>&1
  CK=$?
  [ "$CK" != 0 ] && echo "    control on the live files: RED, as it must be ($(grep -m1 'RED' "$W/ctl.txt" | cut -c1-60))" \
                 || stop "the control did not go red -- the walk cannot tell old from new"
  rm -rf "$W"
  if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

  echo "[4] backups -> $BK"
  mkdir -p "$BK"; chmod 700 "$BK"
  \cp -f "$FD/staff_pages.py" "$BK/staff_pages.py.bak_S606_$(m5 "$FD/staff_pages.py")"
  \cp -f "$FD/staff_manage.html" "$BK/staff_manage.html.bak_S606_$(m5 "$FD/staff_manage.html")"
  STAMP=$(date +%Y%m%d-%H%M%S)
  "$PY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$SR_DB" "$BK/staff_register.db.before_S606_$STAMP" \
    && "$PY" -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$FD/finance.db" "$BK/finance.db.before_S606_$STAMP" \
    && \cp -f "$USERS" "$BK/clinic_users.json.before_S606_$STAMP" && \cp -f "$SMASTER" "$BK/staff_master.csv.before_S606_$STAMP" \
    || stop "the backups could not be taken"
  chmod 600 "$BK"/*
  echo "    4 files and 2 databases kept"

  echo "[5] placed"
  \cp -f staff_easy.py staff_easy.html staff_pages.py staff_manage.html "$FD/"
  for f in staff_easy.py staff_easy.html staff_pages.py staff_manage.html; do
    [ "$(m5 "$FD/$f")" = "$(m5 "$f")" ] || stop "$f did not land byte-exact" "Run the line again with --undo at the end."
  done
  echo "    staff_pages ${NOWP:0:8} -> ${NEW_PAGES:0:8} · staff_manage ${NOWH:0:8} -> ${NEW_HTML:0:8} · staff_easy.py + .html new"

  echo "[6] $SVC restarted and checked"
  restart_and_check
  if [ "$OKH" != 1 ]; then
    \cp -f "$BK/staff_pages.py.bak_S606_$PIN_PAGES" "$FD/staff_pages.py" 2>/dev/null
    \cp -f "$BK/staff_manage.html.bak_S606_$PIN_HTML" "$FD/staff_manage.html" 2>/dev/null
    mkdir -p "$BK/_removed"; mv -f "$FD/staff_easy.py" "$FD/staff_easy.html" "$BK/_removed/" 2>/dev/null
    systemctl restart "$SVC" </dev/null >/dev/null 2>&1
    stop "the finance app did not come back with the new page (health $H · new page $NEWP · old page $OLDP · api $APIP · not-mounted lines $NOTM)" \
         "The old files were put back and $SVC restarted."
  fi
  echo "    health $H · /finance/staff/new $NEWP · /finance/staff $OLDP · api $APIP (403 = there, and closed to a caller with no login)"
fi

echo "[7] the open joinings, settled"
FINANCE_DB="$FD/finance.db" STAFF_EASY_SR_DB="$SR_DB" ATT_STAFF_MASTER="$SMASTER" ATT_PUNCH_CSV="$PUNCH" \
  CLINIC_USERS_FILE="$USERS" PORTAL_DIR="$PORTAL_DIR" "$PY" -B settle_s606.py "$FD" apply || echo "    (the settle did not run -- the page settles on its first open)"

echo "[8] pins"
for f in staff_pages.py staff_manage.html staff_easy.py staff_easy.html joiner_app.py; do echo "    $(md5sum "$FD/$f")"; done
echo "DONE. Open https://followup.dr-manoj.in/finance/staff/new"
