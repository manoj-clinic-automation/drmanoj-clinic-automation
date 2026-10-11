#!/bin/bash
# install_s530.sh -- S530_PAPERS_SECTIONS (D710, D689 item 1): the four sections, sorted = accepted, where each paper stands.
# BUILD_NORM_v1 s3 order: gates -> pins -> rebuild -> walk + control -> backup -> place -> restart (assetapp only) -> health
#                         -> data step (the heal runs inside the app at start; read back here) -> the owner's words -> undo.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S530_PAPERS_SECTIONS/install_s530.sh
set -u
KIT="S530_PAPERS_SECTIONS"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S530_APP_DIR:-/root/assetapp}"
SERVICE="${S530_SERVICE:-assetapp}"
HEALTH="${S530_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S530_PYTHON:-python3}"                       # the scan app's own service runs the system python3 (F-53)
RESTART="${S530_RESTART_CMD:-systemctl restart $SERVICE}"
FROM_C="5e21f4916272270d5e1a54366b43c5ad"          # clinic_papers.py S466.1
APP_PIN="d3f1b64ee103efe22266426af9280fbe"        # asset_register.py after S523 -- read, not edited
TO_C="$(cat "$HERE/PIN_TO_clinic_papers.txt" 2>/dev/null | tr -d ' \n')"
WORK="$(mktemp -d "${HOME:-/root}/s530_install_XXXX")"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; rm -rf "$WORK"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
count_grouped_drafts(){ "$PY" - "$APP/assets.db" <<'EOF'
import sqlite3, sys
db = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
print(db.execute("SELECT COUNT(*) FROM bills WHERE COALESCE(lane,'clinic')='clinic' AND status='draft' AND dup_of IS NULL AND COALESCE(subgroup,'')<>''").fetchone()[0])
EOF
}

log "gates"
[ -n "$TO_C" ] || die "the kit's PIN_TO_clinic_papers.txt is missing"
[ -d "$APP" ] || die "$APP is not a folder"
[ -f "$APP/clinic_papers.py" ] && [ -f "$APP/asset_register.py" ] && [ -f "$APP/assets.db" ] || die "the live files are not in $APP"
command -v "$PY" >/dev/null || die "no $PY"
"$PY" -c "import flask, jinja2" 2>/dev/null || die "$PY has no flask"
for f in make_s530.py walk_s530.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done

log "pins -- the live bytes must be the ones this kit was built on"
LC="$(md5 "$APP/clinic_papers.py")"; LA="$(md5 "$APP/asset_register.py")"
if [ "$LC" = "$TO_C" ]; then echo "$KIT: ALREADY INSTALLED (clinic_papers.py ${TO_C:0:8})"; rm -rf "$WORK"; exit 0; fi
[ "$LC" = "$FROM_C" ] || die "clinic_papers.py is ${LC:0:8}, not the pinned ${FROM_C:0:8} -- another kit moved it; rebuild S530 on the new bytes"
[ "$LA" = "$APP_PIN" ] || die "asset_register.py is ${LA:0:8}, not ${APP_PIN:0:8} (S523's) -- the kit was walked against that app; rebuild S530 on the new bytes"
echo "    clinic_papers.py ${LC:0:8} ok . asset_register.py ${LA:0:8} ok (read only)"

log "rebuild on the box, from the live bytes"
mkdir -p "$WORK/live_in" "$WORK/built"; cp "$APP/clinic_papers.py" "$WORK/live_in/"; cp "$HERE/make_s530.py" "$WORK/"
"$PY" "$WORK/make_s530.py" "$WORK/live_in" "$WORK/built" || die "the builder refused"
BC="$(md5 "$WORK/built/clinic_papers.py")"
[ "$BC" = "$TO_C" ] || die "the rebuilt clinic_papers.py is ${BC:0:8}, the kit says ${TO_C:0:8}"
"$PY" -m py_compile "$WORK/built/clinic_papers.py" || die "the built file does not compile"
echo "    rebuilt: clinic_papers.py ${BC:0:8} -- equal to the kit's pin"

log "walk on a copy of the live database (under the session's home, removed after) -- and the control on the live file"
cd "$WORK" && HOME="$WORK" "$PY" "$HERE/walk_s530.py" "$WORK/built" "$APP/asset_register.py" "$APP/assets.db" > "$WORK/walk.txt" 2>&1 || { cat "$WORK/walk.txt"; die "the walk is RED on the built file"; }
tail -1 "$WORK/walk.txt" | sed 's/^/    walk: /'
HOME="$WORK" "$PY" "$HERE/walk_s530.py" "$WORK/live_in" "$APP/asset_register.py" "$APP/assets.db" --expect-red > "$WORK/control.txt" 2>&1 || { cat "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live file"; }
tail -1 "$WORK/control.txt" | sed 's/^/    control (live file, must be red): /'
cd "$HERE"
BEFORE="$(count_grouped_drafts)"
echo "    clinic drafts that already have a group (to be accepted by the heal at start): $BEFORE"

log "backups beside the live file"
cp -p "$APP/clinic_papers.py" "$APP/clinic_papers.py.bak_S530_${FROM_C:0:8}" || die "backup failed"
cp -p "$APP/assets.db" "$APP/assets.db.bak_S530_$(date +%Y%m%d_%H%M%S)" || die "database backup failed (the heal writes rows)"
echo "    clinic_papers.py.bak_S530_${FROM_C:0:8} . assets.db.bak_S530_<stamp>"

log "place"
cp "$WORK/built/clinic_papers.py" "$APP/clinic_papers.py.tmp" && mv -f "$APP/clinic_papers.py.tmp" "$APP/clinic_papers.py" || die "could not place"
PC="$(md5 "$APP/clinic_papers.py")"; [ "$PC" = "$TO_C" ] || die "read-back after placing differs"
echo "    placed: clinic_papers.py ${PC:0:8}"

restore(){
  echo "RESTORING clinic_papers.py from its backup"
  cp -p "$APP/clinic_papers.py.bak_S530_${FROM_C:0:8}" "$APP/clinic_papers.py"
  eval "$RESTART" || true
  echo "$KIT: NOT INSTALLED (restored: clinic_papers.py $(md5 "$APP/clinic_papers.py" | cut -c1-8); the database backup assets.db.bak_S530_* stands beside it -- rows the heal accepted stay accepted, as a tap would have)"
  rm -rf "$WORK"; exit 1
}

log "restart $SERVICE only, then health"
eval "$RESTART" || restore; sleep 4
HC="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$HEALTH" || echo 000)"
[ "$HC" = "200" ] || { echo "    healthz answered $HC"; restore; }
echo "    healthz 200"

log "data step -- the heal ran inside the app at start (sorted = accepted, D710); read back"
AFTER="$(count_grouped_drafts)"
echo "    clinic drafts with a group: before $BEFORE, after $AFTER (the rest, if any, are same-vendor-number-amount doubles held for a person)"
rm -rf "$WORK"
echo
echo "$KIT: DONE."
echo "  PINS (read back): clinic_papers.py $PC . asset_register.py $LA (unchanged)"
echo "  WHAT THE OWNER SEES on https://followup.dr-manoj.in/scanapp/papers : the list is 'Papers to sort' and now also carries"
echo "  the Other-document papers; a folded line 'Where each paper stands' at the top (owner only); on a paper, the picker"
echo "  offers Clinic consumables (its three groups) and Construction work, Resumes, Miscellaneous documents, Personal (owner only);"
echo "  one tap on a clinic paper sorts it AND accepts it. On /scanapp/papers/month an 'Other sections' card. Staff screens: unchanged."
echo "  UNDO (one line): cp -p $APP/clinic_papers.py.bak_S530_${FROM_C:0:8} $APP/clinic_papers.py && systemctl restart $SERVICE"
exit 0
