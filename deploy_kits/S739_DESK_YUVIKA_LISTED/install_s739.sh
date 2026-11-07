#!/bin/bash
# install_s739.sh -- S739_DESK_YUVIKA_LISTED (board _numbers v1012 -> v1013; built in the Scan App chat, session 398, 07-Nov-2026, on
#   the owner's FINAL 05:50 IST on the mock-up https://claude.ai/artifact/RAA6esA8dF8Bi5ojdazUzo). On the sorting desk: (F-1159) a listed
#   supplier's challan (Variety) says it is sorted on the Stationery page, with the link -- its destinations and Save do not move it and
#   the server refuses such a Save; a paper whose supplier is newly picked as a listed one is sent there by its Save, with no lines.
#   (D845 (3)) Yuvika's paper on the clinic side: her handwritten slip opens with Procedure room chosen, her printed bill with Pharmacy
#   (Sanjeevni), one with no number and no line read offers two buttons -- a suggestion only, nothing moves until a person's Save. The
#   Yuvika part is behind the owner's switch 'Yuvika slips on the desk' (settings desk.yuvika, absent = OFF) on the home page's Switches
#   card: INSTALLED OFF. ONE file: /root/assetapp/sorting_desk.py 52e959da -> TO, rebuilt on the box by make_s739.py (13 counted edits)
#   and checked against the kit's whole file. No data step; no table; restarts assetapp only.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S739_DESK_YUVIKA_LISTED/install_s739.sh
set -u
KIT="S739_DESK_YUVIKA_LISTED"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S739_APP_DIR:-/root/assetapp}"
SERVICE="${S739_SERVICE:-assetapp}"
HEALTH="${S739_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S739_PYTHON:-python3}"
RESTART="${S739_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S739_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S739_HOST:-srv1746119}"
REH="${S739_REHEARSAL:-}"
if [ -z "${S739_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S739_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S739_HEALTH_TRIES:-20}"
FILES="sorting_desk.py"
READONLY="asset_register.py clinic_papers.py asset_machine.py procroom.py batteries.py xray_costs.py claude_reader.py claude_reread.py stationery.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s739tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S739_FAKE_HEALTH:-}" ]; then echo "$S739_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s739.py edits_s739.py walk_s739_app.py sorting_desk.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
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
if [ "$NTO" = 1 ]; then echo "$KIT: ALREADY INSTALLED (the file at the kit's TO pin)"; exit 0; fi
for f in $FILES; do L="$(md5 "$APP/$f")"; FR="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$FR" ] || die "$f is ${L:0:8}, not the pinned ${FR:0:8} -- another kit moved it; S739 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s739work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "the kit's file rebuilt on the pinned FROM bytes, equal to the kit's TO"
"$PY" -B "$HERE/make_s739.py" "$WORK/from/sorting_desk.py" "$WORK/to/sorting_desk.py" --expect | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f" 2>/dev/null)" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is not its TO pin"; done
echo "    the TO file = its pin and compiles"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s739_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s739_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { sed 's/^/    /' "$WORK/capp.txt" | cut -c1-170; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"

if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "the backup beside the live file"
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S739_${FR:0:8}" || die "backup of $f failed"; echo "    $f.bak_S739_${FR:0:8}"; done

restore(){
  echo "RESTORING the file from its backup"
  for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S739_${FR:0:8}" "$APP/$f"; done
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S739_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  BACK=0; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base $f).txt)" ] && BACK=$((BACK+1)); done
  echo "    the file back: $BACK of 1 · healthz $RH after the restore"
  [ "$BACK" = 1 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE: the .bak_S739_ files in $APP are the way back"
  exit 1
}

log "place (through a temporary file) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s739tmp" && mv -f "$APP/$f.s739tmp" "$APP/$f" || restore
  [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore
  echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health and the desk"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S739_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/desk")"; [ -n "${S739_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S739_SLEEP:-2}"; done
[ "$X" = "302" ] || { echo "    /desk answered ${X:-nothing}, not 302"; restore; }
echo "    /desk 302 (the login door: mounted)"
if [ -z "$REH" ]; then
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -cE 'NOT mounted|NOT wrapped')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted / NOT wrapped since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

echo
echo "WHAT THE DESK NOW SHOWS (your login and Shavez's):"
echo "  - A Variety challan opened on the desk says it is sorted on the Stationery page, with a button to open it there."
echo "    The desk cannot move it any more (the NK lane mix-up of B-0235, F-1159)."
echo "  - A challan whose supplier you pick as Variety on the desk is sent to the Stationery page by its Save, to be sorted there."
echo "  - Yuvika's slips: nothing changes until you switch 'Yuvika slips on the desk' ON (the Switches card on the scan app's home page)."
echo "    ON: her handwritten slip opens with Procedure room chosen, her printed bill with Pharmacy -- still only your or Shavez's Save moves it."
echo "UNDO (puts the file back and restarts the scan app):"
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S739_${FR:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
