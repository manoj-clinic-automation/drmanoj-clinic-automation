#!/bin/bash
# =============================================================================
#  install_S543_ORDER_SHEET_MARG.sh · kit S543 (14-Oct-2026) · brief claude_code_briefs/S543_ORDER_SHEET_MARG.md (v3.1, D716)
#
#  Run from a copy of the kit folder BEFORE /root/deploy/repo is pulled (the clone's DUTY_MAP must still be v12 -- this installer pulls it):
#    rm -rf /tmp/s543kit && cp -rp <kit> /tmp/s543kit && bash /tmp/s543kit/install_S543_ORDER_SHEET_MARG.sh
#  (DRY=1 before bash: every gate, the state and the walk, nothing written.)
#
#  THE OWNER, 13-Oct 05:24 IST (D716): the ordering sheet's system faults removed, the flow otherwise as it is, Marg's own purchase-order PDF
#  beside the system's. ONE RULE: a medicine is on the ordering pages and the printed sheet exactly while Marg's newest export prints it.
#   /root/finance/order_sheet.py      012e21c9 -> TO   open_order, the rank, Marg's columns + heal, qty_of, refresh, old words, map rule
#   /root/finance/porders_s454.py     9c463e7c -> TO   the heading, the two buttons, the old block, Maal aaya? + the arrival door, reorder door
#   /root/finance/order_sheet_pdf.py  6e7a5e1a -> TO   the printed sheet from open_order, Aaya ticks, _build(size)
#   /root/finance/marg_order_pdf.py   (new)    -> TO   Marg's own export printed (route /finance/porders/s454/marg.pdf)
#   /root/deploy/repo/claude_code_briefs/DUTY_MAP.json f499dd1f (v12) -> v13 by the repository's pull (published first)
#  finance.db: two additive columns on order_sheet_line (laid by the code), filled once by heal_marg_cols; backup first; never a DELETE.
#  ORDER: gates -> pins (ALREADY first) + read-only pins + the clone at v12 -> the install-day state (read-only) + the collector -> compile
#  (both pythons) -> rebuild from the live bytes -> walk on scratch copies (new green; the old files red) -> DRY stops -> backups -> place ->
#  md5 read-back -> pull + map gate v13 -> ONE restart of clinic-finance -> heal_marg_cols once -> healthz 200, the pages 302 -> the state
#  after + the page as shavez on a copy. Red after placing: every file put back byte-identically (the new file removed), restart, healthz.
# =============================================================================
set -u
KIT="S543_ORDER_SHEET_MARG"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
REPO="${REPO:-/root/deploy/repo}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
GIT="${GIT:-git}"
BRF="$REPO/claude_code_briefs"; DMAP="$BRF/DUTY_MAP.json"; DMD="$BRF/DUTY_MAP.md"
EDITED="order_sheet.py porders_s454.py order_sheet_pdf.py"
NEWF="marg_order_pdf.py"
declare -A FROM TO READ
FROM[order_sheet.py]=012e21c92233d0eec4c828e15f7912e1
FROM[porders_s454.py]=9c463e7c326c95beb20da0829cc537cc
FROM[order_sheet_pdf.py]=6e7a5e1a7ae68cb4548c8c8f15cf27cb
source "$KDIR/PINS.sh"                                # TO[...] of the four files and the map; MAP_FROM, MD_PIN
READ[porders.py]=a5a823bf30661a4bf65ced39b2355500;      READ[qty_words.py]=706db7ccfa7489fb8d296f663590f107
READ[order_rules.py]=79f21c1ee1f763b1ac06b370e3d77b79;  READ[darpan_kal.py]=fd799a56cf212625cfaadce768d3431d
READ[supplier_msg.py]=2f43af754a160376cec955f92f3aa43a; READ[loss_piles.py]=81ae481e4480a12fead3016515037214
READ[aaj_seed.py]=a97cd07bfc7270184c62c16dff4dff48;     READ[aaj_kaam.py]=cd232b1c987417aa07d341d498c5effc
READ[owner_console.py]=2b985708b1dc3239fafbb7f41e969e55; READ[darpan_kal.html]=f5e279eb26e7f24827f29b79f95b2769
MARG_TAKE_PIN=5cad2d24d63344146f562fd5d441dbdf
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s543_inst_$STAMP"
HAVE_LOCK=0; PLACED=0; PULLED=0
DBBAK="$FIN/finance.db.bak_S543_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S543_${FROM[$1]:0:8}"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting every file back"
  for n in $EDITED; do [ -f "$(bak $n)" ] && \cp -p "$(bak $n)" "$FIN/$n"; done
  rm -f "$FIN/$NEWF" "$FIN"/.*.s543
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   $FIN/$NEWF $([ -e "$FIN/$NEWF" ] && echo 'STILL THERE' || echo 'removed (it did not exist before)')"
  say "   after the restore: finance healthz $h"
  [ "$PULLED" = 1 ] && say "   the clone was pulled: DUTY_MAP.json is $(m5 "$DMAP") (v13 reads the same tables with the old files; its revert is the repository's)"
  say "   the database backup stays: $DBBAK (the two added columns are harmless to the old files)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 "$NEWF")" = "${TO[$NEWF]}" ] || { say "!! [1/12] the kit's $NEWF is not the file this installer names - nothing installed"; exit 1; }
if [ "${LOCK_HELD:-0}" = 1 ]; then
  grep -q "$KIT" "$LOCK/owner" 2>/dev/null || { say "!! [1/12] LOCK_HELD=1 but $LOCK/owner does not name $KIT - nothing installed"; exit 3; }
else
  mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
  if [ "$HAVE_LOCK" != 1 ]; then
    say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
    exit 3
  fi
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
fi
say "[1/12] kit gates green (SUMS, KIT_ID, marg_order_pdf.py at its own md5); the build lock is ours"

for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [2/12] $FIN/$n is not there - nothing installed"; exit 1; }; done
ALL_TO=1; for n in $EDITED $NEWF; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the four files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); the clone's DUTY_MAP.json $(m5 "$DMAP")"; exit 0; fi
for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, expected ${FROM[$n]} - it changed after this kit was built: STOP, nothing installed"; exit 1; }; done
[ -e "$FIN/$NEWF" ] && { say "!! [2/12] $FIN/$NEWF already exists ($(m5 "$FIN/$NEWF")) and is not the kit's - STOP, nothing installed"; exit 1; }
for n in "${!READ[@]}"; do C="$(m5 "$FIN/$n")"; [ "$C" = "${READ[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading that file: STOP, nothing installed"; exit 1; }; done
[ "$(m5 "$MARG/marg_take.py")" = "$MARG_TAKE_PIN" ] || { say "!! [2/12] $MARG/marg_take.py moved - STOP, nothing installed"; exit 1; }
[ "$(m5 "$DMAP")" = "$MAP_FROM" ] || { say "!! [2/12] the clone's DUTY_MAP.json is $(m5 "$DMAP"), not v12's FROM $MAP_FROM (run this BEFORE pulling the repository) - nothing installed"; exit 1; }
[ "$(m5 "$DMD")" = "$MD_PIN" ] || { say "!! [2/12] the clone's DUTY_MAP.md is $(m5 "$DMD"), not $MD_PIN - nothing installed"; exit 1; }
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$POR/portal.py" ] && [ -f "$POR/tile_grants.json" ] || { say "!! [2/12] the database, the assets database or the portal is missing - nothing installed"; exit 1; }
say "[2/12] live pins exact (order_sheet 012e21c9, porders_s454 9c463e7c, order_sheet_pdf 6e7a5e1a; marg_order_pdf.py absent); 11 read-only files and marg_take at their pins; the clone's DUTY_MAP.json v12 f499dd1f, DUTY_MAP.md ${MD_PIN:0:8}"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
say "[3/12] the install-day state, read-only on the live database (before):"
"$APY" -B state_s543.py --db "$DB" --map12 "$DMAP" --marg "$MARG" || { say "!! [3/12] the collector is red (the newest ORDER_PENDING file not VERIFIED, not on disk or not taken) - charter 1b: nothing installed"; exit 1; }

for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$NEWF" make_s543.py walk_s543.py state_s543.py || { say "!! [4/12] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s543.py --fin "$FIN" --briefs "$BRF" --out "$SCR/built" >/dev/null || { say "!! [5/12] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED DUTY_MAP.json; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [5/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  for n in $EDITED; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [4/12] the built $n does not compile on $py - nothing installed"; exit 1; }; done
done
say "[4/12] the kit's python files and the three built files compile on $APY and $VPY"
say "[5/12] rebuilt here from this box's live bytes (35 + 28 + 21 counted edits) and DUTY_MAP v13 from the clone's v12 (3): each at its TO pin"

mkside() {   # $1 = side: a copy of the live finance code, the door's reader and its ORDER_PENDING archive, the two databases (backup API)
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  copydb "$DB" "$d/f.db" && copydb "$ADB" "$d/a.db"
}
for side in new old; do mkside "$side" || { say "!! [6/12] no scratch side '$side' - nothing installed"; exit 1; }; done
cp -p "$SCR/built/order_sheet.py" "$SCR/built/porders_s454.py" "$SCR/built/order_sheet_pdf.py" "$NEWF" "$SCR/new/finance/"
mkdir -p "$SCR/por"; for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$SCR/por/"; done; cp -p "$POR/tile_grants.json" "$SCR/por/"
WARGS="--portal $SCR/por --map12 $DMAP --map13 $SCR/built/DUTY_MAP.json --kit $KDIR"
WOUT="$( cd /tmp && timeout 1800 "$APY" -B "$KDIR/walk_s543.py" --fin "$SCR/new/finance" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" $WARGS 2>&1 )"; WRC=$?
ROUT="$( cd /tmp && timeout 1800 "$APY" -B "$KDIR/walk_s543.py" --fin "$SCR/old/finance" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" $WARGS --expect-red 2>&1 )"; RRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S543"; then say "!! [6/12] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | grep -E "^  RED on the old files:|^WALK OK negative|^NEGATIVE CONTROL" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/12] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | tail -12; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [6/12] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
[ "$(m5 "$DMAP")" = "$MAP_FROM" ] || { say "!! [6/12] the clone's DUTY_MAP.json moved during the walk - nothing installed"; exit 1; }
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
rm -rf "$SCR/new" "$SCR/old"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the state and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [7/12] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [7/12] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [7/12] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[7/12] backups: $(basename "$DBBAK") (sqlite backup API); $(for n in $EDITED; do printf '%s ' "$(basename "$(bak $n)")"; done)"

for n in $EDITED; do
  { \cp -p "$FIN/$n" "$FIN/.$n.s543" && cat "$SCR/built/$n" > "$FIN/.$n.s543" && [ "$(m5 "$FIN/.$n.s543")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s543; say "!! [8/12] could not stage $n - nothing placed"; exit 1; }
done
{ \cp -p "$FIN/order_sheet_pdf.py" "$FIN/.$NEWF.s543" && cat "$NEWF" > "$FIN/.$NEWF.s543" && [ "$(m5 "$FIN/.$NEWF.s543")" = "${TO[$NEWF]}" ]; } || { rm -f "$FIN"/.*.s543; say "!! [8/12] could not stage $NEWF - nothing placed"; exit 1; }
PLACED=1
for n in $EDITED $NEWF; do mv -f "$FIN/.$n.s543" "$FIN/$n" || restore "placing $n"; done
for n in $EDITED $NEWF; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "$n did not land at its pin"; done
say "[8/12] placed; md5 read back: $(for n in $EDITED $NEWF; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's)"

PULL="$("$GIT" -C "$REPO" pull --ff-only 2>&1)"; PRC=$?; PULLED=1
[ "$PRC" = 0 ] && [ "$(m5 "$DMAP")" = "${TO[DUTY_MAP.json]}" ] && [ "$(m5 "$DMD")" = "$MD_PIN" ] || { echo "$PULL" | tail -3; restore "the pull did not bring DUTY_MAP v13 (exit $PRC; DUTY_MAP.json $(m5 "$DMAP"), .md $(m5 "$DMD"))"; }
( cd "$REPO/deploy_kits/$KIT" 2>/dev/null && md5sum -c SUMS.md5 >/dev/null 2>&1 ) && KITREPO="byte-identical to this run" || KITREPO="NOT found byte-identical in the clone"
say "[9/12] $REPO pulled: DUTY_MAP.json v13 at its TO pin $(m5 "$DMAP" | cut -c1-8); DUTY_MAP.md unchanged ${MD_PIN:0:8}; the kit in the clone: $KITREPO"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/porders/s454/order); c3=$(health /finance/porders/s454/marg.pdf); c4=$(health /finance/porders/s454/sheet.pdf)
for c in "$c2" "$c3" "$c4"; do case "$c" in 302|401) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): order $c2 / marg.pdf $c3 / sheet.pdf $c4";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[10/12] $SVC restarted (nothing else) and active - healthz $c1 - /s454/order $c2, marg.pdf $c3, sheet.pdf $c4 without a login (302 = the login gate, expected) - journal clean"

HOUT="$( cd /tmp && "$APY" -B -c "import sys, sqlite3; sys.path.insert(0, sys.argv[1]); import order_sheet as OS; c = sqlite3.connect(sys.argv[2], timeout=60); c.row_factory = sqlite3.Row; n = OS.heal_marg_cols(c); m = OS.heal_marg_cols(c); print('heal_marg_cols: %d lines filled, a second run %d' % (n, m))" "$FIN" "$DB" 2>&1 )" || { echo "$HOUT" | tail -3; restore "heal_marg_cols on the live database"; }
say "[11/12] $HOUT"

say "[12/12] the state after, read-only on the live database:"
"$APY" -B state_s543.py --db "$DB" --map13 "$DMAP" --marg "$MARG" || say "   (the collector line above is red -- the files are placed and green; said for the report)"
mkdir -p "$SCR/placed/finance"; cp -p "$FIN"/*.py "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/placed/finance/" 2>/dev/null
cp -rp "$FIN/finance_ui" "$SCR/placed/finance/" 2>/dev/null; mkdir -p "$SCR/placed/finance/spine"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$SCR/placed/finance/spine/" 2>/dev/null
copydb "$DB" "$SCR/placed/f.db" || restore "no copy of the database for the page look"
POUT="$( cd /tmp && MARG_INGEST_DIR="$MARG" ASSETS_DB="$ADB" timeout 300 "$APY" -B "$KDIR/state_s543.py" --page --fin "$SCR/placed/finance" --db "$SCR/placed/f.db" --map13 "$DMAP" 2>&1 )"; PRC=$?
echo "$POUT" | grep -E "^   /finance|^PAGE" | sed 's/^/ /'
[ "$PRC" = 0 ] && echo "$POUT" | grep -q "^PAGE OK" || restore "the ordering page as shavez on a copy is red"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
for n in $EDITED $NEWF; do md5sum "$FIN/$n"; done
say "$KIT: DONE - the ordering pages and the printed sheet follow Marg's own open order; 'Marg ka order (PDF)' beside 'Order sheet print karo'"
say "undo: $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak $n)" "$FIN/$n"; done)rm -f $FIN/$NEWF && $SYSTEMCTL restart $SVC"
exit 0
