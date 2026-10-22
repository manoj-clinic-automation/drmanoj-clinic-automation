#!/bin/bash
# install_s625.sh -- S625_MONTH_AND_DAY (board _numbers v596 -> v597; built in the Scan App chat, session 337, 22-Oct-2026).
#   F-976 a machine edited with the same month and year keeps its day (asset_register.py: purchase / coverage / EMI start);
#   F-980 the owner's ruling (22-Oct, "Bill's own month"): a bill dated in an earlier month than its scan counts in the bill's own
#         month, for papers scanned from this install on -- the ONE shared rule clinic_papers.MONTH_OF; the paper's own page says it.
# Files: /root/assetapp/clinic_papers.py 6db07c12 (1 counted edit), /root/assetapp/asset_register.py 70e35b10 (S618's TO; 6 counted
# edits). Read only, pinned: sorting_desk.py, and S624's three TO files (S624 is installed FIRST). Database: ONE settings row,
# papers.month_from_bill_date = the moment of this install (the switch: 'off' = the old rule). Restarts assetapp only.
# Order (BUILD_NORM_v1 s3): gates -> the build lock -> pins (TO + the key = ALREADY INSTALLED; else FROM; read-only) -> rebuild
# (make_s625.py) -> TO pins -> compile -> the walk on the REAL app with the TO files on a COPY of the live database + the control on
# the FROM files (must be red) + S624's real-app walk on the new app -- DRY=1 stops here -> backups -> place -> read back -> restart
# -> /healthz 200, the pages 302, no part 'NOT mounted' -> the data step (the switch-on row) -> what the pages show -> undo line.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S625_MONTH_AND_DAY/install_s625.sh
set -u
KIT="S625_MONTH_AND_DAY"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K624="${S625_K624:-$(cd "$HERE/.." && pwd)/S624_SCANAPP_SMALL_FIXES}"
APP="${S625_APP_DIR:-/root/assetapp}"
SERVICE="${S625_SERVICE:-assetapp}"
HEALTH="${S625_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S625_PYTHON:-python3}"
RESTART="${S625_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S625_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S625_HOST:-srv1746119}"
REH="${S625_REHEARSAL:-}"
TRIES="${S625_HEALTH_TRIES:-20}"
SKEY="papers.month_from_bill_date"
FILES="clinic_papers.py asset_register.py"
READONLY="sorting_desk.py batteries.py asset_machine.py stationery.py xray_costs.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
if [ -z "${S625_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S625_DB:-${DB0:-$APP/assets.db}}"
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s625tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S625_FAKE_HEALTH:-}" ]; then echo "$S625_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }
keyval(){ "$PY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); r=c.execute('SELECT value FROM settings WHERE key=?', (sys.argv[2],)).fetchone(); print(r[0] if r else '')" "$DB" "$SKEY" 2>/dev/null; }

STAMP="$(date +%Y%m%d_%H%M%S)"
datastep(){
log "the data step: the rule's switch-on moment (one settings row; papers scanned from now count in their bill's own month)"
  "$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S625_$STAMP" || { echo "    the database backup failed -- the code is in place and the OLD rule stands; paste the line again"; exit 1; }
  chmod 600 "$DB.bak_S625_$STAMP" 2>/dev/null; echo "    the database first: $(basename "$DB").bak_S625_$STAMP"
  "$PY" -c "
import sqlite3,sys
c=sqlite3.connect(sys.argv[1], timeout=30)
r=c.execute('SELECT value FROM settings WHERE key=?', (sys.argv[2],)).fetchone()
if r is None or (r[0] or '') in ('', 'off'):
    c.execute(\"INSERT OR REPLACE INTO settings(key,value) VALUES(?, datetime('now'))\", (sys.argv[2],))
    c.commit()
print(c.execute('SELECT value FROM settings WHERE key=?', (sys.argv[2],)).fetchone()[0])" "$DB" "$SKEY" > "$WORK/key.txt" 2>&1 || { cat "$WORK/key.txt"; echo "    the switch-on row could not be written -- the code is in place and the OLD rule stands; paste the line again (it goes straight to this step)"; exit 1; }
  KU="$(cat "$WORK/key.txt")"
  KI="$(TZ=Asia/Kolkata date -d "$KU UTC" '+%d-%m-%Y %H:%M IST' 2>/dev/null || echo "$KU UTC")"
  echo "    on since $KI"
  
  echo
  echo "WHAT THE PAGES NOW SHOW:"
  echo "  - a machine edited without changing its month keeps its day (28-04 stays 28-04);"
  echo "  - a paper scanned from $KI whose bill is dated in an earlier month counts in that month on The month, the desk and"
  echo "    X-ray costs; its own page says 'Month: <the bill's month> (the bill's own date -- scanned as <the scan month>)';"
  echo "  - papers scanned before that keep the months they had; a month a person chooses on the paper's page still wins if earlier."
  echo "UNDO (puts the two files back and restarts; the old rule then stands, whatever the settings row says):"
  for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S625_${P:0:8} $APP/$f"; done
  echo "  systemctl restart $SERVICE"
  echo "$KIT: DONE"
  exit 0
}

log "gates (the box, root, the kit, the files; S624 installed first)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s625.py walk_s625_app.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
[ -f "$K624/walk_s624_app.py" ] || die "S624_SCANAPP_SMALL_FIXES is not beside this kit"
for f in $FILES; do for k in PIN_FROM_$(base $f).txt PIN_TO_$(base $f).txt; do v="$(pin $k)"; [ ${#v} -eq 32 ] || die "$k is missing in the kit"; done; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
for f in $READONLY; do v="$(pin PIN_READ_$(base $f).txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base $f).txt is missing"; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
for f in batteries asset_machine stationery; do [ "$(pin PIN_READ_$f.txt)" = "$(tr -d ' \r\n' < "$K624/PIN_TO_$f.txt")" ] || die "this kit's $f.py pin is not S624's TO pin"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    the kit, S624 beside it, and $APP ok"

log "the server-wide build lock (one build at a time on the shared server)"
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pins -- the live bytes"
ALL_TO=1; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || ALL_TO=0; done
KV="$(keyval)"
if [ "$ALL_TO" = 1 ] && [ -n "$KV" ] && [ "$KV" != "off" ]; then
  echo "$KIT: ALREADY INSTALLED (both files at the kit's TO pins; the rule on since $KV UTC)"; exit 0
fi
if [ "$ALL_TO" = 1 ]; then
  echo "    both files are already at the TO pins and the switch-on row is '${KV:-absent}' -- an earlier run stopped at the data step; doing it now"
  WORK="$(mktemp -d /tmp/s625work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
  datastep
fi
for f in $FILES; do L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S625 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only$( case $f in batteries.py|asset_machine.py|stationery.py) echo '; S624 must be installed FIRST';; esac)) -- stop"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s625work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "rebuild from the live bytes (counted edits) and the TO pins"
"$PY" -B "$HERE/make_s625.py" "$WORK/from" "$WORK/to" | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is not the TO pin"; done
for f in $FILES; do "$PY" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$WORK/to/$f" || die "$f does not compile"; done
echo "    both TO files = their pins and compile"

log "the walk on the REAL app (TO files) on a COPY of the live database -- made-up rows only -- and the control on the FROM files"
"$PY" -B "$HERE/walk_s625_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/w.txt" 2>&1; WR=$?
sed 's/^/    /' "$WORK/w.txt" | cut -c1-160
[ "$WR" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s625_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/c.txt" 2>&1 || { cat "$WORK/c.txt"; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/c.txt")"
mkdir -p "$WORK/new"; for f in "$APP"/*.py "$APP"/*.js; do [ -f "$f" ] && cp -p "$f" "$WORK/new/"; done; cp -p "$WORK/to/"*.py "$WORK/new/"
"$PY" -B "$K624/walk_s624_app.py" --live "$WORK/new" --files "$WORK/new" --db "$DB" > "$WORK/w624.txt" 2>&1 || { cat "$WORK/w624.txt"; die "S624's walk is not green on the new app"; }
echo "    S624's real-app walk on the new app: $(tail -1 "$WORK/w624.txt")"
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backups; nothing placed"; exit 0; fi

log "backups beside each live file"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S625_${P:0:8}" || die "backup of $f failed"; echo "    $f.bak_S625_${P:0:8}"; done

restore(){
  echo "RESTORING the two files from their backups"
  RB=0; for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S625_${P:0:8}" "$APP/$f"; [ "$(md5 "$APP/$f")" = "$P" ] || RB=1; done
  [ "$RB" = 0 ] || echo "    !! A FILE DID NOT COME BACK TO ITS FROM PIN -- the .bak_S625_ copies beside it are the way back"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S625_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  for f in $FILES; do echo "    $f back at $(md5 "$APP/$f" | cut -c1-8)"; done
  echo "    healthz $RH after the restore"
  [ "$RB" = 0 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE (see above)"; exit 1
}

log "place (each through a temporary file) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s625tmp" && mv -f "$APP/$f.s625tmp" "$APP/$f" || restore; done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore; echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health, the pages and the log"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S625_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
for pg in stationery batteries papers/month bills/1 assets/1/edit; do
  X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/$pg")"; [ -n "${S625_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S625_SLEEP:-2}"; done
  [ "$X" = "302" ] || { echo "    /$pg answered ${X:-nothing}, not 302"; restore; }
  echo "    /$pg 302 (the login door: the page is mounted)"
done
if [ -z "$REH" ]; then
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

datastep

