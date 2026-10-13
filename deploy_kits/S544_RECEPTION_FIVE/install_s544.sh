#!/bin/bash
# install_s544.sh -- S544_RECEPTION_FIVE (D719 kit a; F-891): reception's four lane buttons and the Challan button (installed
# OFF, the owner's switch on /scanapp/admin); "Dr MK expense" becomes Personal expense with Dr MK / Dr Bhawna; the asset
# category Medical Equipment becomes Dr MK Clinic Equipment; a Personal paper closed to managers on the bill doors.
# BUILD_NORM_v1 s3 order: gates -> pins -> rebuild -> walk + control -> backups -> place -> restart (assetapp only) -> health
#                         -> data step (the app's own migration at start: one additive column, the category renamed; read back)
#                         -> words -> undo.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S544_RECEPTION_FIVE/install_s544.sh
set -u
KIT="S544_RECEPTION_FIVE"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S544_APP_DIR:-/root/assetapp}"
SERVICE="${S544_SERVICE:-assetapp}"
HEALTH="${S544_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S544_PYTHON:-python3}"
RESTART="${S544_RESTART_CMD:-systemctl restart $SERVICE}"
FILES="asset_register.py clinic_papers.py"
declare -A FROM=([asset_register.py]=35f9e823b07830b5831efc586f48d46b [clinic_papers.py]=476e157c82f17a0af164019b04ccbb2b)
declare -A TO
for f in $FILES; do TO[$f]="$(tr -d ' \n' < "$HERE/PIN_TO_${f%.*}.txt" 2>/dev/null)"; done
WORK="$(mktemp -d "${HOME:-/root}/s544_install_XXXX")" && [ -n "$WORK" ] && [ -d "$WORK" ] || { echo "REFUSED: no temporary folder"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
trap 'rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.tmp"; done' EXIT
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
dbread(){ "$PY" - "$APP/assets.db" <<'PYEOF'
import sqlite3, sys
db = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
c = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
old = db.execute("SELECT COUNT(*) FROM assets WHERE category='Medical Equipment'").fetchone()[0]
new = db.execute("SELECT COUNT(*) FROM assets WHERE category='Dr MK Clinic Equipment'").fetchone()[0]
pe = db.execute("SELECT COUNT(*) FROM bills WHERE COALESCE(lane,'clinic')='owner_expense' AND status<>'rejected'").fetchone()[0]
sw = db.execute("SELECT value FROM settings WHERE key='scan.lanes5'").fetchone()
print("pe_who column %s . assets in Medical Equipment %d . in Dr MK Clinic Equipment %d . personal expenses %d . lane buttons %s"
      % ("yes" if "pe_who" in c else "no", old, new, pe, (sw[0] if sw else "OFF (not set)")))
PYEOF
}

log "gates"
for f in $FILES; do [ -n "${TO[$f]}" ] || die "PIN_TO_${f%.*}.txt missing"; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$APP/assets.db" ] || die "no $APP/assets.db"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
for k in make_s544.py walk_s544.py; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done

log "pins -- the live bytes must be the ones this kit was built on"
ALL_TO=1; for f in $FILES; do [ "$(md5 "$APP/$f")" = "${TO[$f]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then echo "$KIT: ALREADY INSTALLED (both files at the kit's pins)"; echo "    $(dbread)"; exit 0; fi
for f in $FILES; do L="$(md5 "$APP/$f")"; [ "$L" = "${FROM[$f]}" ] || die "$f is ${L:0:8}, not the pinned ${FROM[$f]:0:8} -- another kit moved it; rebuild S544 on the new bytes"; echo "    $f ${L:0:8} ok"; done

log "rebuild on the box, from the live bytes"
mkdir -p "$WORK/live_in" "$WORK/built"
for f in $FILES scanner_widget.js; do cp "$APP/$f" "$WORK/live_in/"; done
"$PY" "$HERE/make_s544.py" "$WORK/live_in" "$WORK/built" >/dev/null || die "the builder refused"
cp "$APP/scanner_widget.js" "$WORK/built/"
for f in $FILES; do B="$(md5 "$WORK/built/$f")"; [ "$B" = "${TO[$f]}" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${TO[$f]:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"; done
"$PY" -m py_compile "$WORK/built/asset_register.py" "$WORK/built/clinic_papers.py" || die "a built file does not compile"

log "walk on a copy of the live database (under the session's home, removed after; made-up rows) -- and the control on the live files"
( cd "$WORK" && HOME="$WORK" "$PY" -B "$HERE/walk_s544.py" "$WORK/built" "$APP/assets.db" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^(RED|GREEN)|checks' "$WORK/walk.txt"; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
( cd "$WORK" && HOME="$WORK" "$PY" -B "$HERE/walk_s544.py" "$WORK/live_in" "$APP/assets.db" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
echo "    before: $(dbread)"

log "backups beside the live files"
for f in $FILES; do cp -p "$APP/$f" "$APP/$f.bak_S544_${FROM[$f]:0:8}" || die "backup of $f failed"; done
cp -p "$APP/assets.db" "$APP/assets.db.bak_S544_$(date +%Y%m%d_%H%M%S)" || die "database backup failed"
echo "    .bak_S544_<from8> beside each file; assets.db.bak_S544_<stamp>"

restore(){
  echo "RESTORING the two files from their backups"
  for f in $FILES; do cp -p "$APP/$f.bak_S544_${FROM[$f]:0:8}" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; done
  "$PY" - "$APP/assets.db" <<'PYEOF' || true
import sqlite3, sys
db = sqlite3.connect(sys.argv[1], timeout=20)
db.execute("UPDATE assets SET category='Medical Equipment' WHERE category='Dr MK Clinic Equipment'")
db.commit()
PYEOF
  eval "$RESTART" || true
  for f in $FILES; do [ "$(md5 "$APP/$f")" = "${FROM[$f]}" ] || { echo "RESTORE FAILED for $f -- run the UNDO line in the README"; exit 2; }; done
  echo "$KIT: NOT INSTALLED (restored; the category name put back; the added column, if any, stays -- additive, read by nothing in the old files)"
  exit 1
}

log "place"
for f in $FILES; do
  if ! { cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; }; then restore; fi
done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "${TO[$f]}" ] || restore; done
echo "    placed: both files at the kit's pins"

log "restart $SERVICE only, then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 20); do sleep 2; HC="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$HEALTH" || true)"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing} for 40 s"; restore; }
echo "    healthz 200"

log "data step -- the app's own migration at start; read back (a gate: the column there, nothing left in Medical Equipment)"
AFTER="$(dbread)"; echo "    after:  $AFTER"
case "$AFTER" in *"pe_who column yes . assets in Medical Equipment 0 "*) ;; *) echo "    the database did not take the change"; restore;; esac
echo
echo "$KIT: DONE."
echo "  PINS (read back): asset_register.py $(md5 "$APP/asset_register.py") . clinic_papers.py $(md5 "$APP/clinic_papers.py")"
echo "  WHAT CHANGES NOW (owner pages): the lane reads Personal expense everywhere; each personal expense's page asks Dr MK or"
echo "  Dr Bhawna (none = Dr MK); the papers page has a Personal expenses fold (you and Shavez); Medical Equipment reads"
echo "  Dr MK Clinic Equipment; a Personal paper no longer opens for a manager on the bill pages."
echo "  WHAT STAFF SEE: nothing yet -- reception's lane buttons are installed OFF. The owner's switch:"
echo "  https://followup.dr-manoj.in/scanapp/admin  (card: Bill intake -- reception's lane buttons)"
echo "  UNDO (one line): cp -p $APP/asset_register.py.bak_S544_35f9e823 $APP/asset_register.py && cp -p $APP/clinic_papers.py.bak_S544_476e157c $APP/clinic_papers.py && $PY -c \"import sqlite3; d=sqlite3.connect('$APP/assets.db'); d.execute(\\\"UPDATE assets SET category='Medical Equipment' WHERE category='Dr MK Clinic Equipment'\\\"); d.commit()\" && systemctl restart $SERVICE"
exit 0
