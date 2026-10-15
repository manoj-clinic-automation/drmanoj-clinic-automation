#!/bin/bash
# install_s560.sh -- S560_RECEIPTS_STATEMENTS (D728): Receipt and Statement are paper kinds, never counted as spend (the bill is);
# one payment record (paper_payment + paper_payment_bill, fingerprinted, append-only); "Paid?" on a bill; the bill shows
# "Paid dd-mm-yyyy . Rs . mode . ref" with the receipt's scan; Construction's "Send to accountant" (bills.to_accountant) and the
# accountants' pack's new item 8.4; every bundle leaves out receipts, statements and awaiting challans; the desk on one laptop
# screen; the papers to put right listed for one tap each; Bills awaited's items line.
# Files: /root/assetapp/sorting_desk.py, clinic_papers.py, asset_register.py (the scan app) and /root/finance/packs.py (THE
# PARENT'S: build_bundle and the item-8 list only). Data step: sorting_desk's own ensure() -- additive, idempotent, guarded for
# two workers -- AFTER the database is backed up by SQLite's backup API.
# BUILD_NORM_v1 s3 order (S559's shape): gates -> the build lock -> FROM pins (and the read-only pins) -> rebuild from the live
# bytes -> TO pins -> compile (both pythons) -> the walk + control, the pack walk + control, the S559 / S557 / S555 / S551 and
# S548 walks on a scratch copy (DRY=1 stops here) -> backups (files; the database by the backup API) -> the data step (ensure)
# -> place -> md5 read-back -> restart assetapp, then clinic-finance -> /healthz 200, /desk 302 (302 ONLY), /finance/healthz
# 200 AND no "packs NOT mounted" in the finance journal since its restart (FIX1 C2) -> what his pages now show -> undo line.
# A failure after placing restores all four files and restarts both services.
# FIX1 (15-Oct-2026): B1 a payment recorded once; C1 a ticked construction bill only in 8.4; C2 the journal check; C3 the old
# Approve refuses a receipt / statement; N1 the desk measured at a real laptop's 1366 x 620.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S560_RECEIPTS_STATEMENTS/install_s560.sh
set -u
KIT="S560_RECEIPTS_STATEMENTS"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KITS="${S560_KITS_DIR:-$(cd "$HERE/.." && pwd)}"
APP="${S560_APP_DIR:-/root/assetapp}"
FIN="${S560_FIN_DIR:-/root/finance}"
SERVICE="${S560_SERVICE:-assetapp}"
FSERVICE="${S560_FIN_SERVICE:-clinic-finance}"
HEALTH="${S560_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
FHEALTH="${S560_FIN_HEALTH_URL:-http://127.0.0.1:8106/finance/healthz}"
PY="${S560_PYTHON:-python3}"
PYV="${S560_PYTHON_VENV:-/root/wa/venv/bin/python3}"
RESTART="${S560_RESTART_CMD:-systemctl restart $SERVICE}"
FRESTART="${S560_FIN_RESTART_CMD:-systemctl restart $FSERVICE}"
SHARED="${S560_SHARED_DIR:-/root/shared}"
LOCK="${S560_LOCK:-/root/deploy/.claude_code_build.lock}"
JOURNAL="${S560_JOURNAL_CMD:-journalctl}"                                     # FIX1 C2 (the rehearsal points it at a made-up stub)
TRIES="${S560_HEALTH_TRIES:-20}"
W559FROM="${S560_W559_FROM:-$APP/scanner_widget.js.bak_S559_1143c77b}"     # the widget before S559 (its walk's J1 compares against it)
FILES="sorting_desk.py clinic_papers.py asset_register.py"                    # the scan app's: placed in this order, the app's own file last
PYFILES="sorting_desk.py clinic_papers.py asset_register.py"
READERS="asset_machine.py scanner_widget.js claude_reader.py claude_reread.py" # read only; pinned (the walks import / serve them)
PF="packs.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
if [ -z "${S560_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S560_DB:-${DB0:-$APP/assets.db}}"
STAMP="$(date +%Y%m%d_%H%M%S)"
W559="$KITS/S559_ONE_ROAD/walk_s559.py"
L559="$KITS/S559_ONE_ROAD/s551_lines_s559.py"
W557="$KITS/S557_MACHINE_PAGES/walk_s557.py"
W555="$KITS/S555_DESK_CORRECTIONS/walk_s555.py"
W551="$KITS/S551_SORTING_DESK/walk_s551.py"
W548="$KITS/S548_PACK_BHAWNA_FILE/walk_s548.py"
HAVE_LOCK=0
WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.tmp"; done; rm -f "$FIN/$PF.tmp"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap cleanup EXIT

log "gates (the box, root, the files)"
case "$(hostname)" in *srv1746119*) ;; *) die "this is not srv1746119";; esac
[ "$(id -u)" = "0" ] || die "run as root"
for f in $FILES $PF; do for k in FROM TO; do v="$(pin PIN_${k}_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_${k}_$(base "$f").txt is missing in the kit"; done; done
for f in $READERS; do v="$(pin PIN_READ_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base "$f").txt is missing in the kit"; done
v="$(pin PIN_READ_widget_before_s559.txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_widget_before_s559.txt is missing in the kit"
for f in make_s560.py s560_sd_block.txt s560_ar_block.txt s560_js.txt walk_s560.py walk_s560_pack.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
for w in "$W559" "$L559" "$W557" "$W555" "$W551" "$W548"; do [ -f "$w" ] || die "the earlier walk $w (regression) is not beside this kit"; done
for f in $FILES $READERS; do [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$FIN/$PF" ] || die "$FIN/$PF missing"
[ -f "$W559FROM" ] && [ "$(md5 "$W559FROM")" = "$(pin PIN_READ_widget_before_s559.txt)" ] || die "the widget before S559 (S559's walk compares against it) is not at $W559FROM"
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    $APP and $FIN ok; the database read from the service (not shown)"

log "the server-wide build lock (one build at a time on the shared server)"
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pins -- the live bytes must be the ones this kit was built on"
ALL_TO=1; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || ALL_TO=0; done
[ "$(md5 "$FIN/$PF")" = "$(pin PIN_TO_packs.txt)" ] || ALL_TO=0
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (the four files at the kit's pins)"
  echo "  PINS (read back): $(for f in $FILES; do printf '%s %s . ' "$f" "$(md5 "$APP/$f")"; done)$PF $(md5 "$FIN/$PF")"
  exit 0
fi
for f in $FILES; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; rebuild S560 on the new bytes"
  echo "    $f ${P:0:8} ok"
done
L="$(md5 "$FIN/$PF")"; P="$(pin PIN_FROM_packs.txt)"
[ "$L" = "$P" ] || die "$PF (the parent's) is ${L:0:8}, not the pinned ${P:0:8} -- the parent moved it; rebuild S560 on the new bytes"
echo "    $PF ${P:0:8} ok (the parent's)"
for f in $READERS; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f (read only) is ${L:0:8}, not the pinned ${P:0:8} -- the walk was proven on other bytes"
  echo "    $f ${P:0:8} ok (read only)"
done

WORK="$(mktemp -d /tmp/s560_install_XXXX)" && [ -n "$WORK" ] && [ -d "$WORK" ] || die "no temporary folder"

log "rebuild on the box, from the live bytes (each anchor exactly once)"
mkdir -p "$WORK/live_in" "$WORK/built" "$WORK/am" "$WORK/noam" "$WORK/pk"
for f in $FILES $READERS; do cp "$APP/$f" "$WORK/live_in/"; done
cp "$FIN/$PF" "$WORK/live_in/"
"$PY" -B "$HERE/make_s560.py" "$WORK/live_in" "$WORK/built" > "$WORK/make.txt" 2>&1 || { cat "$WORK/make.txt"; die "the builder refused"; }
sed 's/^/    /' "$WORK/make.txt"
for f in $READERS; do cp "$APP/$f" "$WORK/built/"; done
for f in $FILES $PF; do
  B="$(md5 "$WORK/built/$f")"; P="$(pin PIN_TO_$(base "$f").txt)"
  [ "$B" = "$P" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${P:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"
done
cp "$WORK/built/asset_machine.py" "$WORK/am/"
for f in $FILES scanner_widget.js claude_reader.py claude_reread.py; do cp "$WORK/built/$f" "$WORK/noam/"; done
mv "$WORK/built/$PF" "$WORK/pk/$PF"; mv "$WORK/live_in/$PF" "$WORK/pk/live_$PF"

log "compile on both pythons"
mkdir -p "$WORK/cc"; for f in $PYFILES; do cp "$WORK/built/$f" "$WORK/cc/"; done; cp "$WORK/pk/$PF" "$WORK/cc/"
( cd "$WORK/cc" && "$PY" -m py_compile $PYFILES $PF ) || die "a built file does not compile on $PY"
if [ -x "$PYV" ]; then ( cd "$WORK/cc" && "$PYV" -m py_compile $PYFILES $PF ) || die "a built file does not compile on $PYV"; echo "    compiles on $PY and $PYV"; else echo "    compiles on $PY ($PYV not present)"; fi
rm -rf "$WORK/cc"

log "walks on a scratch copy of the database (made-up rows; nothing sent anywhere) -- S560's walk and control, the pack's walk and control, the S559, S557, S555, S551 and S548 walks"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$WORK/snap.db" || die "the scratch copy of the database failed"
( cd "$WORK" && "$PY" -B "$HERE/walk_s560.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w1" --shared "$SHARED" --live-stamps > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/walk.txt"; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
grep -E '^SIZES|^LIVE-STAMPS' "$WORK/walk.txt" | sed 's/^/    /'
( cd "$WORK" && "$PY" -B "$HERE/walk_s560.py" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w2" --shared "$SHARED" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks|^CONTROL' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
grep -E '^CONTROL' "$WORK/control.txt" | tail -1 | sed 's/^/    /'
( cd "$WORK" && HOME="$WORK" "$PY" -B "$HERE/walk_s560_pack.py" "$WORK/pk/$PF" "$FIN" --before "$WORK/pk/live_$PF" > "$WORK/pack.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/pack.txt"; die "the pack walk is RED on the built packs.py"; }
grep -E 'pack checks' "$WORK/pack.txt" | tail -1 | sed 's/^/    pack walk: /'
sed -n '/^BEFORE/,/^GREEN P2/p' "$WORK/pack.txt" | grep -v '^GREEN' | sed 's/^/    /'
( cd "$WORK" && HOME="$WORK" "$PY" -B "$HERE/walk_s560_pack.py" "$WORK/pk/live_$PF" "$FIN" --before "$WORK/pk/live_$PF" --expect-red > "$WORK/packc.txt" 2>&1 ) || { grep -E 'checks|^CONTROL' "$WORK/packc.txt"; die "the pack's NEGATIVE CONTROL did not go red on the live packs.py"; }
grep -E 'pack checks' "$WORK/packc.txt" | tail -1 | sed 's/^/    pack control (live packs.py, must be red): /'
grep -E '^CONTROL' "$WORK/packc.txt" | tail -1 | sed 's/^/    /'
( cd "$WORK" && HOME="$WORK" "$PY" -B "$W548" "$WORK/pk/$PF" "$FIN" > "$WORK/s548.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s548.txt"; die "the S548 pack walk is RED on the built packs.py"; }
grep -E 'checks' "$WORK/s548.txt" | tail -1 | sed 's/^/    S548 pack walk on the new packs.py: /'
( cd "$WORK" && "$PY" -B "$W559" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w3" --shared "$SHARED" --dump "$WORK/b559.json" > "$WORK/s559base.txt" 2>&1 ) || { tail -3 "$WORK/s559base.txt"; die "the S559 walk's baseline could not be taken on the live files"; }
( cd "$WORK" && "$PY" -B "$W559" "$WORK/built" "$WORK/snap.db" --work "$WORK/w4" --shared "$SHARED" --baseline "$WORK/b559.json" --from-widget "$W559FROM" > "$WORK/s559.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s559.txt"; die "the S559 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s559.txt" | tail -1 | sed 's/^/    S559 walk on the new files: /'
( cd "$WORK" && "$PY" -B "$W557" "$WORK/noam" "$WORK/snap.db" --work "$WORK/w5" --shared "$SHARED" --dump "$WORK/b557.json" > "$WORK/s557base.txt" 2>&1 ) || { tail -3 "$WORK/s557base.txt"; die "the S557 walk's baseline could not be taken"; }
( cd "$WORK" && "$PY" -B "$W557" "$WORK/built" "$WORK/snap.db" --work "$WORK/w6" --shared "$SHARED" --baseline "$WORK/b557.json" > "$WORK/s557.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s557.txt"; die "the S557 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s557.txt" | tail -1 | sed 's/^/    S557 walk on the new files: /'
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$W555" "$WORK/built" "$WORK/snap.db" --work "$WORK/w7" --shared "$SHARED" > "$WORK/s555.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s555.txt"; die "the S555 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s555.txt" | tail -1 | sed 's/^/    S555 walk on the new files: /'
"$PY" -B "$L559" "$W551" "$WORK/walk_s551_s559.py" > "$WORK/s551lines.txt" 2>&1 || { cat "$WORK/s551lines.txt"; die "the S551 walk's three agreed lines (S559's) were not each found exactly once"; }
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$WORK/walk_s551_s559.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w8" --shared "$SHARED" > "$WORK/s551.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s551.txt"; die "the S551 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s551.txt" | tail -1 | sed 's/^/    S551 walk (S559'"'"'s three agreed lines) on the new files: /'
if [ -n "${DRY:-}" ]; then echo "DRY=1: stopped before placing. $KIT: NOT INSTALLED (dry run)"; exit 0; fi

log "backups beside the live files, and the database by the backup API (BEFORE the data step)"
for f in $FILES; do
  P="$(pin PIN_FROM_$(base "$f").txt)"; cp -p "$APP/$f" "$APP/$f.bak_S560_${P:0:8}" || die "backup of $f failed"
done
P="$(pin PIN_FROM_packs.txt)"; cp -p "$FIN/$PF" "$FIN/$PF.bak_S560_${P:0:8}" || die "backup of $PF failed"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S560_$STAMP" || die "database backup failed"
echo "    the four files .bak_S560_<from8> . $(basename "$DB").bak_S560_$STAMP"

hc(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; }
restore(){
  echo "RESTORING the four files from their backups"
  for f in $FILES; do
    P="$(pin PIN_FROM_$(base "$f").txt)"
    cp -p "$APP/$f.bak_S560_${P:0:8}" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"
  done
  P="$(pin PIN_FROM_packs.txt)"; cp -p "$FIN/$PF.bak_S560_${P:0:8}" "$FIN/$PF.tmp" && mv -f "$FIN/$PF.tmp" "$FIN/$PF"
  eval "$RESTART" || true
  eval "$FRESTART" || true
  for f in $FILES; do
    [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || { echo "RESTORE FAILED ($f) -- run the UNDO line in the README"; exit 2; }
  done
  [ "$(md5 "$FIN/$PF")" = "$(pin PIN_FROM_packs.txt)" ] || { echo "RESTORE FAILED ($PF) -- run the UNDO line in the README"; exit 2; }
  RH=""; for i in $(seq 1 "$TRIES"); do sleep 2; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  RF=""; for i in $(seq 1 "$TRIES"); do RF="$(hc "$FHEALTH")"; [ "$RF" = "200" ] && break; sleep 2; done
  [ "$RH" = "200" ] && [ "$RF" = "200" ] || { echo "RESTORED THE FILES, BUT A SERVICE DOES NOT ANSWER (scan app ${RH:-nothing}, finance ${RF:-nothing}) -- tell Claude now"; exit 2; }
  echo "    files back at $(for f in $FILES; do printf '%s ' "$(md5 "$APP/$f" | cut -c1-8)"; done)$(md5 "$FIN/$PF" | cut -c1-8) (the FROM pins); healthz 200 and /finance/healthz 200 after the restore"
  echo "$KIT: NOT INSTALLED (restored; the database backup stays -- the data step only ADDED two empty tables and one column, read by nothing else)"
  exit 1
}

log "the data step: sorting_desk's own ensure() from the built file -- paper_payment, paper_payment_bill, bills.to_accountant (additive, idempotent)"
( cd "$WORK/built" && "$PY" -B -c "import sqlite3,sys,importlib.util as u; s=u.spec_from_file_location('sd560','sorting_desk.py'); m=u.module_from_spec(s); s.loader.exec_module(m); c=sqlite3.connect(sys.argv[1], timeout=30); m.ensure(c); c.close()" "$DB" ) > "$WORK/ensure.txt" 2>&1 || { cat "$WORK/ensure.txt"; die "the data step (ensure) failed -- the database backup is $(basename "$DB").bak_S560_$STAMP"; }
"$PY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); t={r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}; k={r[1] for r in c.execute('PRAGMA table_info(bills)')}; sys.exit(0 if {'paper_payment','paper_payment_bill'} <= t and 'to_accountant' in k else 1)" "$DB" || die "the data step did not leave the two tables and the column"
echo "    paper_payment, paper_payment_bill and bills.to_accountant present (nothing else changed; no row written)"

log "place (the modules first, the app's own file last; then the parent's packs.py), and read the md5 back"
for f in $FILES; do
  if ! { cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; }; then restore; fi
done
if ! { cp "$WORK/pk/$PF" "$FIN/$PF.tmp" && mv -f "$FIN/$PF.tmp" "$FIN/$PF"; }; then restore; fi
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || restore; done
[ "$(md5 "$FIN/$PF")" = "$(pin PIN_TO_packs.txt)" ] || restore
echo "    placed: the four files at the kit's pins"

log "restart $SERVICE, then $FSERVICE, then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep 2; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ -n "${S560_FORCE_RED:-}" ] && { echo "    (rehearsal: a red after placing is forced)"; HC="forced-red"; }
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
DESK=""; for i in $(seq 1 "$TRIES"); do DESK="$(hc "${HEALTH%/healthz}/desk")"; [ "$DESK" = "302" ] && break; sleep 2; done
if [ "$DESK" = "302" ]; then
  echo "    /desk answers 302 (the login gate -- expected, not a failure): the app is up and gated"
else
  echo "    /desk answered ${DESK:-nothing}, not 302: the desk did not mount, or its login gate is open"; restore
fi
FT0="$(date -d '-1 second' '+%Y-%m-%d %H:%M:%S')"                       # FIX1 C2: the finance journal is read from here on
eval "$FRESTART" || restore
FC=""; for i in $(seq 1 "$TRIES"); do sleep 2; FC="$(hc "$FHEALTH")"; [ "$FC" = "200" ] && break; done
[ "$FC" = "200" ] || { echo "    /finance/healthz answered ${FC:-nothing}"; restore; }
sleep 1
# FIX1 C2: /finance/healthz answers 200 even when packs.py failed to load -- finance_app.py then writes "packs NOT mounted: ..."
# to its journal. Read the journal since the restart, quietly (grep -q: not one line of it is printed); the message = a failed health.
if "$JOURNAL" -u "$FSERVICE" --since "$FT0" --no-pager -q 2>/dev/null | grep -q "packs NOT mounted"; then
  echo "    /finance/healthz 200, but packs.py did not load (the finance journal says 'packs NOT mounted')"; restore
fi
echo "    /finance/healthz 200; packs.py loaded (no 'packs NOT mounted' in the finance journal since the restart)"

echo
echo "$KIT: DONE."
echo "  PINS (read back): $(for f in $FILES; do printf '%s %s . ' "$f" "$(md5 "$APP/$f")"; done)$PF $(md5 "$FIN/$PF")"
echo "  WHAT HIS PAGES NOW SHOW: the sorting desk fits one laptop screen -- What was read folds to one line, every destination"
echo "  button in a compact grid (Clinic consumables . Clinic expense . My expense -- Dr MK / Dr Bhawna . Handed over . Documents"
echo "  . Not here). Paper kinds: Bill . Estimate slip . Challan . Receipt . Statement. A Receipt asks 'Pays which bill?' and is"
echo "  filed with that bill; a Statement ticks the invoices it covers and shows any difference; neither is ever counted as"
echo "  spend. A bill shows 'Paid dd-mm-yyyy . Rs . mode . no.' with the receipt's scan; All papers shows a small 'Paid'. A"
echo "  Construction bill can be ticked 'Send to accountant' -- the accountants' pack has a new item 8.4 for those bills, and its"
echo "  bundles no longer carry receipts, statements or challans still waiting for their bill. The papers to put right wait at"
echo "  the top of the desk's list, each with its reason, for one tap. Bills awaited lists each challan's items."
echo "  UNDO (one line): $(for f in $FILES; do P="$(pin PIN_FROM_$(base "$f").txt)"; printf '\\cp -p %s %s && ' "$APP/$f.bak_S560_${P:0:8}" "$APP/$f"; done)$(P="$(pin PIN_FROM_packs.txt)"; printf '\\cp -p %s %s && ' "$FIN/$PF.bak_S560_${P:0:8}" "$FIN/$PF")systemctl restart $SERVICE && systemctl restart $FSERVICE"
exit 0
