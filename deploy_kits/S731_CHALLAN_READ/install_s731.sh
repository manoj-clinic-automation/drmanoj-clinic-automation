#!/bin/bash
# install_s731.sh -- S731_CHALLAN_READ (board _numbers v976 -> v977; F-1136; built in the Scan App chat, session 392, 06-Nov-2026).
#   The cause of F-1136: B-0250, a Variety challan scanned with the Challan button on the Other-document lane ("bill nahi"), was never
#   put to Claude -- that lane is not read and Sarvam is off -- so it said 'read failed' with no reading; moving it on the desk did not
#   read it either. The fix: a CHALLAN is read on any lane (never a person's section); after the desk's Save or the lane button, a paper
#   that was NEVER put to Claude, marked failed, is read once in the background (only what is empty is filled).
#   TWO files: /root/assetapp/asset_register.py 63a8b15b -> TO, /root/assetapp/sorting_desk.py 4990350b -> TO, rebuilt on the box by
#   make_s731.py (3 counted edits) and checked against the kit's whole files. No data step; no table; restarts assetapp only.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S731_CHALLAN_READ/install_s731.sh
set -u
KIT="S731_CHALLAN_READ"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S731_APP_DIR:-/root/assetapp}"
SERVICE="${S731_SERVICE:-assetapp}"
HEALTH="${S731_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S731_PYTHON:-python3}"
RESTART="${S731_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S731_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S731_HOST:-srv1746119}"
REH="${S731_REHEARSAL:-}"
if [ -z "${S731_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S731_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S731_HEALTH_TRIES:-20}"
FILES="asset_register.py sorting_desk.py"
READONLY="clinic_papers.py asset_machine.py procroom.py batteries.py xray_costs.py claude_reader.py claude_reread.py stationery.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s731tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S731_FAKE_HEALTH:-}" ]; then echo "$S731_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s731.py edits_s731.py walk_s731_app.py asset_register.py sorting_desk.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; T="$(pin PIN_TO_$(base $f).txt)"
  [ ${#FR} -eq 32 ] && [ ${#T} -eq 32 ] || die "the kit's pins for $f are missing"
  [ "$(md5 "$HERE/$f")" = "$T" ] || die "the kit's $f is not at its TO pin"
  [ -f "$APP/$f" ] || die "$APP/$f missing"; done
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
NTO=0
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] && NTO=$((NTO+1)); done
if [ "$NTO" = 2 ]; then echo "$KIT: ALREADY INSTALLED (both files at the kit's TO pins)"; exit 0; fi
for f in $FILES; do L="$(md5 "$APP/$f")"; FR="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$FR" ] || die "$f is ${L:0:8}, not the pinned ${FR:0:8} -- another kit moved it; S731 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s731work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "the kit's two files rebuilt on the pinned FROM bytes, equal to the kit's TO"
"$PY" -B "$HERE/make_s731.py" "$WORK/from" "$WORK/to" --expect | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f" 2>/dev/null)" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is not its TO pin"; done
echo "    both TO files = their pins and compile"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s731_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s731_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { sed 's/^/    /' "$WORK/capp.txt" | cut -c1-170; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"

log "read only: challans scanned on Other document in the last 30 days, and whether Claude ever read them (their own records)"
"$PY" - "$DB" <<'PYEOF' 2>/dev/null | sed 's/^/    /' || echo "    (could not read them -- nothing depends on this line)"
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
try:
    rows = c.execute("SELECT b.stamp_no, substr(a.at,1,16), b.lane, b.ocr_status, r.ok FROM bill_audit a JOIN bills b ON b.id=a.bill_id "
                     "LEFT JOIN claude_reading r ON r.bill_id=b.id WHERE a.action='challan' AND a.detail LIKE '%other_doc%' "
                     "AND a.at >= datetime('now','-30 days') ORDER BY a.at DESC LIMIT 15").fetchall()
except sqlite3.Error as e:
    print("could not read: %s" % e); sys.exit(0)
if not rows:
    print("none in the last 30 days")
for s, at, lane, o, ok in rows:
    W = {"clinic": "the clinic lane", "other_doc": "Other document", "lab_purchase": "the NK Pathology lane", "owner_expense": "Dr MK expense", "pharmacy": "the pharmacy lane"}
    print("%s scanned %s IST on Other document; now on %s; %s" % (s, at, W.get(lane or "clinic", lane), "read by Claude" if ok == 1 else ("Claude failed on it" if ok == 0 else "NEVER put to Claude -- read by itself once sorted on the desk, or 'Read it again'")))
PYEOF
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backups; nothing placed"; exit 0; fi

log "the backups beside the live files"
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S731_${FR:0:8}" || die "backup of $f failed"; echo "    $f.bak_S731_${FR:0:8}"; done

restore(){
  echo "RESTORING both files from their backups"
  for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S731_${FR:0:8}" "$APP/$f"; done
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S731_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  BACK=0; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base $f).txt)" ] && BACK=$((BACK+1)); done
  echo "    both files back: $BACK of 2 · healthz $RH after the restore"
  [ "$BACK" = 2 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE: the .bak_S731_ files in $APP are the way back"
  exit 1
}

log "place (each through a temporary file) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s731tmp" && mv -f "$APP/$f.s731tmp" "$APP/$f" || restore
  [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore
  echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health and the desk"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S731_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/desk")"; [ -n "${S731_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S731_SLEEP:-2}"; done
[ "$X" = "302" ] || { echo "    /desk answered ${X:-nothing}, not 302"; restore; }
echo "    /desk 302 (the login door: mounted)"
if [ -z "$REH" ]; then
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -cE 'NOT mounted|NOT wrapped')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted / NOT wrapped since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

echo
echo "WHAT CHANGES (nothing on any screen):"
echo "  - A challan is read by Claude whichever lane reception pressed -- also 'Other document'. Letters, forms, resumes, Personal"
echo "    papers and patients' papers on that lane stay unread, as before."
echo "  - A paper that was never put to Claude and says 'read failed' is read by itself once it is sorted on the desk or its lane"
echo "    is changed. A paper Claude already tried is not tried again this way ('Read it again' stays for that)."
echo "UNDO (puts both files back and restarts the scan app):"
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S731_${FR:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
