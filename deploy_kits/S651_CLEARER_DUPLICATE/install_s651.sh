#!/bin/bash
# install_s651.sh -- S651_CLEARER_DUPLICATE (board _numbers v691 -> v692; built in the Scan App chat, session 352, 25-Oct-2026).
#   D761 for the scan app (F-992's scan-app half; message sanjeevni_S339_1): when two scans are one paper, the one with item lines
#   is kept over one with none -- only when the scan given up is untouched. Three files replaced whole (FROMs pinned):
#   /root/shared/scan_checks_s441.py (the rule; the owner's 'same' answer; the sure double-scan rule), /root/assetapp/asset_register.py
#   (_mark_dup; the checker's two-tap words), /root/assetapp/sorting_desk.py (the desk's words). No data step; restarts assetapp
#   only (the finance app reads scan_checks_s441.answered_recent only -- unchanged; it takes the new file at its own next restart).
#   Same order and gates as S649's installer (BUILD_NORM_v1 s3).
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S651_CLEARER_DUPLICATE/install_s651.sh
set -u
KIT="S651_CLEARER_DUPLICATE"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S651_APP_DIR:-/root/assetapp}"
SHARED="${S651_SHARED_DIR:-/root/shared}"
SERVICE="${S651_SERVICE:-assetapp}"
HEALTH="${S651_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S651_PYTHON:-python3}"
RESTART="${S651_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S651_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S651_HOST:-srv1746119}"
REH="${S651_REHEARSAL:-}"
if [ -z "${S651_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S651_DB:-${DB0:-$APP/assets.db}}"
if [ -z "${S651_FIN_DB:-}" ]; then
  FIN0="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null | tr ' ' '\n' | sed -n 's/^FINANCE_DB_FOR_SCANS=//p' | head -1)"
fi
FINDB="${S651_FIN_DB:-${FIN0:-/root/finance/finance.db}}"
if [ -z "${S651_PYTHON:-}" ] && [ -z "$REH" ]; then                   # walk in the very python the running service uses
  MP="$(systemctl show "$SERVICE" -p MainPID --value 2>/dev/null || echo 0)"
  if [ "${MP:-0}" -gt 0 ] 2>/dev/null; then SP0="$(readlink -f /proc/$MP/exe 2>/dev/null || true)"; [ -x "$SP0" ] && "$SP0" -c "import flask" 2>/dev/null && PY="$SP0"; fi
fi
TRIES="${S651_HEALTH_TRIES:-20}"
# name : live folder
FILES="scan_checks_s441.py:$SHARED asset_register.py:$APP sorting_desk.py:$APP"
READONLY="procroom.py claude_reader.py clinic_papers.py asset_machine.py stationery.py batteries.py xray_costs.py claude_reread.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
nm(){ echo "${1%%:*}"; }
dir(){ echo "${1#*:}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for e in $FILES; do rm -f "$(dir $e)/$(nm $e).s651tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S651_FAKE_HEALTH:-}" ]; then echo "$S651_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files, the service python)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s651.py build_s651.py walk_s651_app.py walk_s648_app.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
for e in $FILES; do f="$(nm $e)"; for k in PIN_FROM_$(base $f).txt PIN_TO_$(base $f).txt; do v="$(pin $k)"; [ ${#v} -eq 32 ] || die "$k is missing in the kit"; done
  [ -f "$(dir $e)/$f" ] || die "$(dir $e)/$f missing"; [ -f "$HERE/$f" ] || die "kit file $f missing"
  [ "$(md5 "$HERE/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the kit's $f is not at its pin"; done
for f in $READONLY; do v="$(pin PIN_READ_$(base $f).txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base $f).txt is missing in the kit"; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    the kit, $APP and $SHARED ok; the service python: $PY"

log "the server-wide build lock (one build at a time on the shared server)"
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pins -- the live bytes"
ALL_TO=1; for e in $FILES; do f="$(nm $e)"; [ "$(md5 "$(dir $e)/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (the three files at the kit's TO pins)"
  for e in $FILES; do echo "  PIN $(nm $e) $(md5 "$(dir $e)/$(nm $e)")"; done
  exit 0
fi
for e in $FILES; do f="$(nm $e)"; L="$(md5 "$(dir $e)/$f")"; P="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S651 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s651work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to" "$WORK/app"
for e in $FILES; do cp -p "$(dir $e)/$(nm $e)" "$WORK/from/$(nm $e)"; done

log "the kit's three files on the pinned FROM bytes, and their TO pins"
"$PY" -B "$HERE/make_s651.py" "$WORK/from" "$WORK/to" | sed 's/^/    /'
for e in $FILES; do f="$(nm $e)"; [ "$(md5 "$WORK/to/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is $(md5 "$WORK/to/$f" | cut -c1-8), not the TO pin"
  "$PY" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$WORK/to/$f" || die "$f does not compile"; done
"$PY" -B "$HERE/build_s651.py" "$WORK/from" "$WORK/to2" > "$WORK/b.txt" 2>&1 || { cat "$WORK/b.txt"; die "the counted edits do not apply to the live bytes"; }
for e in $FILES; do f="$(nm $e)"; [ "$(md5 "$WORK/to2/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the counted edits on the live $f give $(md5 "$WORK/to2/$f" | cut -c1-8), not the TO pin"; done
"$PY" -I -c "import sys; sys.path.insert(0, sys.argv[1]); import scan_checks_s441 as m; assert callable(m.answered_recent) and callable(m.clearer)" "$WORK/to" \
  || die "the new scan_checks_s441.py does not import, or lost answered_recent (the finance app's one call)"
echo "    the TO files = their pins, the counted edits on the live bytes give the same, they compile, and scan_checks_s441 keeps answered_recent"

log "the finance database's schema, read only: every column named *scan* is one the rule knows (K1 C1)"
if [ -f "$FINDB" ]; then
  "$PY" -I -c "
import sqlite3, sys
sys.path.insert(0, sys.argv[1])
import scan_checks_s441 as m
c = sqlite3.connect('file:%s?mode=ro' % sys.argv[2], uri=True)
bad = []
for (t,) in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"):
    for x in [r[1] for r in c.execute('PRAGMA table_info(%s)' % m._q(t))]:
        if 'scan' in x.lower() and x not in m.D761_FIN_KNOWN:
            bad.append('%s.%s' % (t, x))
print('    columns named *scan*, unknown to the rule: ' + (', '.join(bad) or 'none'))
sys.exit(1 if bad else 0)
" "$WORK/to" "$FINDB" || die "the finance database has a column named *scan* the rule does not know -- S651 is to be rebuilt with it"
else
  echo "    no finance database at $FINDB -- the rule will swap nothing until it can read one"
fi

log "the walk on the REAL app with the new files (made-up papers, a made-up finance database) on a COPY of the live database -- and its control"
"$PY" -B "$HERE/walk_s651_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/w.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/w.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk is not all green"
"$PY" -B "$HERE/walk_s651_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/c.txt" 2>&1 || { cat "$WORK/c.txt"; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/c.txt")"

log "the whole app (S648's walk: every part it mounts) with the two new app files in it, on a COPY of the live database"
for f in "$APP"/*.py "$APP"/*.js "$APP"/*.json; do [ -f "$f" ] && cp -p "$f" "$WORK/app/"; done
cp -p "$WORK/to/asset_register.py" "$WORK/to/sorting_desk.py" "$WORK/app/"
"$PY" -B "$HERE/walk_s648_app.py" --live "$WORK/app" --files "$WORK/app" --db "$DB" > "$WORK/wapp.txt" 2>&1; WP=$?
echo "    $(tail -1 "$WORK/wapp.txt")"
[ "$WP" = 0 ] || { grep -E '^RED' "$WORK/wapp.txt" | cut -c1-170 | sed 's/^/    /'; die "the app's walk with the new files is not all green"; }
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "backups beside the live files, and of the database"
for e in $FILES; do f="$(nm $e)"; P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$(dir $e)/$f" "$(dir $e)/$f.bak_S651_${P:0:8}" || die "backup of $f failed"; echo "    $(dir $e)/$f.bak_S651_${P:0:8}"; done
STAMP="$(date '+%Y%m%d_%H%M%S')"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S651_$STAMP" || die "the database backup failed"
echo "    $(basename "$DB").bak_S651_$STAMP"

restore(){
  echo "RESTORING the three files from their backups"
  RB=0; for e in $FILES; do f="$(nm $e)"; P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$(dir $e)/$f.bak_S651_${P:0:8}" "$(dir $e)/$f"; [ "$(md5 "$(dir $e)/$f")" = "$P" ] || RB=1; done
  [ "$RB" = 0 ] || echo "    !! A FILE DID NOT COME BACK TO ITS FROM PIN -- the .bak_S651_ copies beside them are the way back"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S651_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  for e in $FILES; do echo "    $(nm $e) back at $(md5 "$(dir $e)/$(nm $e)" | cut -c1-8)"; done
  echo "    healthz $RH after the restore"
  [ "$RB" = 0 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE (see above)"; exit 1
}

log "place (through temporary files) and read back"
for e in $FILES; do f="$(nm $e)"; d="$(dir $e)"; cp -p "$WORK/to/$f" "$d/$f.s651tmp" && mv -f "$d/$f.s651tmp" "$d/$f" || restore; done
for e in $FILES; do f="$(nm $e)"; d="$(dir $e)"; P="$(pin PIN_FROM_$(base $f).txt)"; chown --reference="$d/$f.bak_S651_${P:0:8}" "$d/$f" 2>/dev/null || true; done
for e in $FILES; do f="$(nm $e)"; [ "$(md5 "$(dir $e)/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore; echo "    $f $(md5 "$(dir $e)/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health and its pages"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S651_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
for u in /desk /bills; do X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}$u")"; [ -n "${S651_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S651_SLEEP:-2}"; done
  [ "$X" = "302" ] || { echo "    $u answered ${X:-nothing}, not 302"; restore; }; echo "    $u 302 (the login door: the page is mounted)"; done
"$PY" -I -c "import sys; sys.path.insert(0, sys.argv[1]); import scan_checks_s441 as m; assert m.VERSION.startswith('S441.2') and callable(m.clearer)" "$SHARED" \
  || { echo "    the placed scan_checks_s441.py does not import as S441.2"; restore; }
echo "    the placed scan_checks_s441.py imports as S441.2"
if [ -z "$REH" ]; then
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

echo
echo "WHAT CHANGES:"
echo "  - Two scans of one paper: the one with item lines is kept, the one with none set aside -- on the checker's Duplicate tap,"
echo "    the desk's 'same paper', the owner's 'same' on Scan ka kaam, and the server's own sure double-scan and after-reading checks."
echo "    Only in the clinic's own lanes (not pharmacy), both read, of the same kind, and only when the scan given up is untouched"
echo "    (not approved, no Marg/order link, no machine, X-ray or other record, nothing a person did to it after the scan)."
echo "  - Papers already set aside stay as they are."
echo "UNDO (puts the three files back and restarts the scan app):"
for e in $FILES; do f="$(nm $e)"; P="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp -p $(dir $e)/$f.bak_S651_${P:0:8} $(dir $e)/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
