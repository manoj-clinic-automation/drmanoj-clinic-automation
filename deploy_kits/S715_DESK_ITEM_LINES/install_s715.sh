#!/bin/bash
# install_s715.sh -- S715_DESK_ITEM_LINES (board _numbers v944 -> v945; the owner's 'build' 10:09 IST 06-Nov-2026 on the mock-up
#   https://claude.ai/artifact/XpbAyqQAyCimRnv3dz1ECm; built in the Scan App chat, session 363).
#   The sorting desk: the supplier picked from a searchable list, the date from a calendar, the stationery lines workable (+ Add a line,
#   x, a searchable item list with a tick, "+ Add <name> to the list" with unit and rate, the lines total), a listed supplier's
#   challan (Variety Stationers) sorted on the desk with Clinic or NK on each line, the procedure room product search, Read it again.
#   ONE file: /root/assetapp/sorting_desk.py 35fdd6c5 -> the kit's TO, rebuilt on the box by make_s715.py (19 counted edits + 2
#   whole JavaScript functions) and checked against the kit's whole file. No data step; no table; restarts assetapp only.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S715_DESK_ITEM_LINES/install_s715.sh
set -u
KIT="S715_DESK_ITEM_LINES"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S715_APP_DIR:-/root/assetapp}"
SERVICE="${S715_SERVICE:-assetapp}"
HEALTH="${S715_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S715_PYTHON:-python3}"
RESTART="${S715_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S715_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S715_HOST:-srv1746119}"
REH="${S715_REHEARSAL:-}"
if [ -z "${S715_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S715_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S715_HEALTH_TRIES:-20}"
F="sorting_desk.py"
READONLY="clinic_papers.py asset_register.py asset_machine.py procroom.py batteries.py xray_costs.py claude_reader.py claude_reread.py stationery.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; rm -f "$APP/$F.s715tmp"; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S715_FAKE_HEALTH:-}" ]; then echo "$S715_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }
FROM="$(pin PIN_FROM_sorting_desk.txt)"; TO="$(pin PIN_TO_sorting_desk.txt)"

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s715.py edits_s715.py walk_s715_app.py sorting_desk.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
[ ${#FROM} -eq 32 ] && [ ${#TO} -eq 32 ] || die "the kit's pins are missing"
[ "$(md5 "$HERE/$F")" = "$TO" ] || die "the kit's $F is not at its TO pin"
[ -f "$APP/$F" ] || die "$APP/$F missing"
for f in $READONLY; do v="$(pin PIN_READ_$(base $f).txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base $f).txt is missing in the kit"; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    the kit and $APP ok"

log "the server-wide build lock (one build at a time on the shared server)"
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pins -- the live bytes"
L="$(md5 "$APP/$F")"
if [ "$L" = "$TO" ]; then echo "$KIT: ALREADY INSTALLED ($F at the kit's TO pin ${TO:0:8})"; exit 0; fi
[ "$L" = "$FROM" ] || die "$F is ${L:0:8}, not the pinned ${FROM:0:8} -- another kit moved it; S715 is to be rebuilt on the new bytes"
echo "    $F ${L:0:8} = the FROM pin"
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s715work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
cp -p "$APP/$F" "$WORK/from/$F"

log "the kit's $F rebuilt on the pinned FROM bytes, equal to the kit's TO"
"$PY" -B "$HERE/make_s715.py" "$WORK/from/$F" "$WORK/to/$F" --expect "$TO" | sed 's/^/    /'
[ "$(md5 "$WORK/to/$F" 2>/dev/null)" = "$TO" ] || die "the rebuilt $F is not the TO pin"
echo "    the TO file = its pin and compiles"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s715_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s715_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { sed 's/^/    /' "$WORK/capp.txt" | cut -c1-170; die "the control on the live file is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"

log "read only: papers of the last 7 days the reader did not read, and why (their own records; nothing changed)"
"$PY" - "$DB" <<'PYEOF' 2>/dev/null | sed 's/^/    /' || echo "    (could not read them -- nothing depends on this line)"
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
try:
    rows = c.execute("SELECT b.id, b.stamp_no, b.ocr_status, substr(b.created_at,1,16), r.ok, r.error, r.at FROM bills b LEFT JOIN claude_reading r ON r.bill_id=b.id "
                     "WHERE b.created_at >= datetime('now','-7 days') AND COALESCE(b.lane,'clinic') NOT IN ('other_doc') "
                     "AND COALESCE(b.subgroup,'') NOT IN ('personal','resume','patient_paper') AND (r.ok IS NULL OR r.ok=0) "
                     "AND COALESCE(b.vendor,'')='' ORDER BY b.id DESC LIMIT 12").fetchall()
except sqlite3.Error as e:
    print("could not read: %s" % e); sys.exit(0)
if not rows:
    print("none -- every paper of the last 7 days was read")
for i, s, o, at, ok, err, rat in rows:
    print("%s scanned %s: read status %s; Claude: %s" % (s or "#%d" % i, at, o or "(none)", "never asked" if ok is None else "failed %s -- %s" % ((rat or "")[:16], (err or "")[:80])))
PYEOF
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "the backup beside the live file"
cp -p "$APP/$F" "$APP/$F.bak_S715_${FROM:0:8}" || die "backup of $F failed"; echo "    $F.bak_S715_${FROM:0:8}"

restore(){
  echo "RESTORING $F from its backup"
  cp -p "$APP/$F.bak_S715_${FROM:0:8}" "$APP/$F"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S715_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  echo "    $F back at $(md5 "$APP/$F" | cut -c1-8) · healthz $RH after the restore"
  [ "$(md5 "$APP/$F")" = "$FROM" ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE: $APP/$F.bak_S715_${FROM:0:8} is the way back"
  exit 1
}

log "place (through a temporary file) and read back"
cp -p "$WORK/to/$F" "$APP/$F.s715tmp" && mv -f "$APP/$F.s715tmp" "$APP/$F" || restore
[ "$(md5 "$APP/$F")" = "$TO" ] || restore
echo "    $F $(md5 "$APP/$F" | cut -c1-8) = the TO pin"

log "restart $SERVICE only, then its health, the desk and the new door"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S715_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
for u in desk desk/api/suppliers; do X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/$u")"; [ -n "${S715_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S715_SLEEP:-2}"; done
  [ "$X" = "302" ] || { echo "    /$u answered ${X:-nothing}, not 302"; restore; }
  echo "    /$u 302 (the login door: mounted)"; done
if [ -z "$REH" ]; then
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

echo
echo "WHAT THE DESK NOW SHOWS (your login and Shavez's):"
echo "  - Supplier: type two letters and pick from the list of known suppliers; a typed name that is not picked is not taken (Save says"
echo "    'Pick the supplier from the list'); '+ New supplier' for a new one, with a warning when it looks like a known supplier."
echo "  - Date: a calendar, with Scan day and Today; the Read line shows it dd-mm-yyyy."
echo "  - Stationery lines: '+ Add a line', x to remove, an item box that searches the list (a tick when chosen), '+ Add <name> to the"
echo "    list' with unit and rate right on the line; the rate is optional and on your screen only; the lines total against the paper."
echo "  - Variety Stationers' challans can be sorted on the desk: each line Clinic or NK Pathology (the Stationery page works as before)."
echo "  - Procedure room lines: the product box searches the list."
echo "  - 'Read it again' under 'Nothing could be read': the empty boxes fill by themselves if it reads."
echo "UNDO (puts the file back and restarts the scan app):"
echo "  \\cp $APP/$F.bak_S715_${FROM:0:8} $APP/$F && systemctl restart $SERVICE"
echo "$KIT: DONE"
