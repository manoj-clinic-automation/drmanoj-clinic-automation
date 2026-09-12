#!/bin/bash
# =============================================================================
#  install_S240_MARG_DOOR.sh · kit S240_MARG_DOOR · D467 phase 2a
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_MARG_DOOR
#
#  ONE DOOR for Marg exports, and the worst-case way in that the owner asked for:
#    * marg_take.py  -> /root/marg_ingest/   the single "take these bytes" function. De-duplicated
#                       by the file's own md5, classified by the same router the 5-minute collector
#                       uses, sale reports read into PHI-free lines and the file deleted (S186).
#    * marg_door.py  -> /root/finance/       a page: /finance/clinic/marg/upload -- send an export
#                       from any browser, no medical PC, no Drive, no Tailscale.
#    * one mount line inside finance_app.py, anchored on the last module already mounted.
#
#  It creates no schedule, sends nothing, and changes no existing page. The service is restarted
#  and probed; anything short of green puts finance_app.py back as it was and restarts again.
#  Needs S240_MARG_INGEST already installed.
# =============================================================================
set -u
KIT="S240_MARG_DOOR"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${MI_PY:-/root/wa/venv/bin/python3}"
APY="${APP_PY:-/usr/bin/python3}"
DEST="${MI_DEST:-/root/marg_ingest}"
FIN="${FINANCE_DIR:-/root/finance}"
DB="$FIN/finance.db"
FA="$FIN/finance_app.py"
SVC="${FIN_SVC:-clinic-finance.service}"
PORT="${FIN_PORT:-8106}"
PATCH_BAK=""
red() { echo "!! RED -- $*"; exit 1; }

rollback() {
  if [ -n "$PATCH_BAK" ] && [ -f "$PATCH_BAK" ]; then
    \cp -f "$PATCH_BAK" "$FA"
    systemctl restart "$SVC"; sleep 4
    systemctl is-active --quiet "$SVC" && echo "   finance_app.py put back and the service is up again"
  fi
  red "$*"
}

cd "$KDIR" || red "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum marg_door.py | awk '{print $1}')" ] \
  || red "KIT_ID does not match marg_door.py (F-88)"
[ -x "$PY" ] || red "$PY not found"
[ -x "$APY" ] || red "$APY not found -- that is the interpreter the finance app runs under"
[ -f "$DEST/marg_ingest.py" ] || red "$DEST/marg_ingest.py is not there -- install S240_MARG_INGEST first"
[ -d "$DEST/archive" ] || red "$DEST/archive is not there -- let S240_MARG_INGEST run once first"
[ -f "$FA" ] || red "$FA is not there"
[ -f "$DB" ] || red "$DB is not there"
echo "-- gates green"

# 1. the two files -------------------------------------------------------------------------
for pair in "marg_take.py:$DEST" "marg_door.py:$FIN"; do
  f="${pair%%:*}"; d="${pair##*:}"
  if [ -f "$d/$f" ]; then
    old="$(md5sum "$d/$f" | awk '{print $1}')"
    if [ "$old" != "$(md5sum "$f" | awk '{print $1}')" ]; then
      \cp -f "$d/$f" "$d/$f.bak_${KIT}_${old:0:8}" || red "backup of $d/$f"
    fi
  fi
  \cp -f "$f" "$d/$f" || red "copy $f -> $d"
done
"$PY" -m py_compile "$DEST/marg_take.py" || red "marg_take.py does not compile under $PY"
"$APY" -m py_compile "$FIN/marg_door.py" || red "marg_door.py does not compile under $APY"
rm -rf "$DEST/__pycache__" "$FIN/__pycache__/marg_door.cpython-"*.pyc 2>/dev/null
echo "-- marg_take.py in $DEST · marg_door.py in $FIN"

# 2. prove the door on this box's own files, into a TEMP db -------------------------------
echo "-- selftest (temp database, temp archive, real exports from $DEST/archive):"
MARG_INGEST_DIR="$DEST" PYTHONPATH="$DEST" "$PY" -B "$KDIR/selftest_marg_door.py" --from "$DEST/archive" || red "the selftest failed -- nothing was mounted"

# 3. a copy of the books before the mount --------------------------------------------------
BDB="$FIN/finance.db.bak_${KIT}_$(date +%Y%m%d_%H%M%S)"
"$PY" - "$DB" "$BDB" <<'PYEOF' || red "finance.db backup failed"
import sqlite3, sys
s = sqlite3.connect(sys.argv[1]); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()
PYEOF
echo "-- finance.db backed up to $BDB"

# 4. the mount ------------------------------------------------------------------------------
OUT="$(FA_PATH="$FA" "$PY" -B "$KDIR/patch_finance_app_S240_door.py" 2>&1)" || { echo "$OUT"; red "the mount refused -- nothing was changed"; }
echo "$OUT" | sed 's/^/   /'
PATCH_BAK="$(echo "$OUT" | awk -F': *' '/backup +:/{print $2}')"

# 5. restart, and prove the app is well ----------------------------------------------------
systemctl restart "$SVC"; sleep 4
systemctl is-active --quiet "$SVC" || rollback "$SVC did not come back after the mount"
HZ="$(curl -s -o /dev/null -w '%{http_code}' "localhost:$PORT/finance/healthz")"
UP="$(curl -s -o /dev/null -w '%{http_code}' "localhost:$PORT/finance/clinic/marg/upload")"
echo "-- healthz $HZ · the upload page, not logged in: $UP  (200/302/303/401/403 = mounted and gated)"
[ "$HZ" = "200" ] || rollback "healthz is not 200 after the mount"
case "$UP" in
  200|302|303|401|403) : ;;
  *) rollback "the upload page answered $UP -- it is not mounted properly" ;;
esac

# 6. what the next phase needs to know, read from the box rather than assumed ---------------
echo "-- for phase 2b, how this app treats its token routes:"
grep -n "marg-push\|PUBLIC_PATHS\|_unit_for_path" "$FA" | head -6 | sed 's/^/     /'
echo "-- disk: $(df -h "$FIN" | awk 'NR==2{print $4" free on "$6}')"

echo
echo "PINS  $FIN/marg_door.py   $(md5sum "$FIN/marg_door.py" | awk '{print $1}')"
echo "      $DEST/marg_take.py  $(md5sum "$DEST/marg_take.py" | awk '{print $1}')"
echo "      $FA  $(md5sum "$FA" | awk '{print $1}')"
echo
echo "$KIT GREEN -- open it here, on a phone or anywhere:"
echo "https://followup.dr-manoj.in/finance/clinic/marg/upload"
