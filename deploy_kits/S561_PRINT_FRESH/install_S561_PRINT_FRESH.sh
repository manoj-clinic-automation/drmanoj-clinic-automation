#!/bin/bash
# =============================================================================
#  install_S561_PRINT_FRESH.sh · kit S561 (15-Oct-2026) · brief claude_code_briefs/S561_PRINT_FRESH.md (v2)
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S561_PRINT_FRESH):
#    rm -rf /tmp/s561kit && cp -rp <kit> /tmp/s561kit && bash /tmp/s561kit/install_S561_PRINT_FRESH.sh
#  (DRY=1 before bash: every gate and the walks, nothing written.)
#
#  A phone reopened an old copy of "Print the order sheet" (15-Oct 14:24): the button opened the same address all day and the file had the
#  same name all day. After this kit both buttons open a new address at every tap, each file is named by the export's time (the order
#  sheet also by the print's), the routes send no-store / no-cache, and the order sheet's foot says when it was printed.
#   /root/finance/porders_s454.py     72e7fd56 -> TO   the two buttons (?s=&t=, data-fresh, the click script), the two routes' names/headers/audit
#   /root/finance/order_sheet_pdf.py  d0735df8 -> TO   "chhapa: dd-mm-yyyy hh:mm  ·  Sanjeevni" on every page's foot; build(..., now=None)
#  Read only: marg_order_pdf.py c9cd44a5, order_sheet.py 247eeb48. No data step: finance.db is backed up and never written by this kit.
#  ORDER: gates -> pins (ALREADY first) + read-only pins -> compile (both pythons) -> rebuild from the live bytes -> walk on scratch copies
#  (new green; the old files red) + S543's walk on the new files beside the old -> DRY stops -> backups -> place -> md5 read-back -> ONE
#  restart of clinic-finance -> healthz 200, the pages 302 (login gate, expected) -> journal clean -> the placed files on a copy of the
#  database: the new file names and the printed time. Red after placing: both files put back byte-identically, restart, healthz.
# =============================================================================
set -u
KIT="S561_PRINT_FRESH"
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
DMAP="$REPO/claude_code_briefs/DUTY_MAP.json"
EDITED="porders_s454.py order_sheet_pdf.py"
declare -A FROM TO READ
FROM[porders_s454.py]=72e7fd563dadf2ae657fadef66e4e72e;    TO[porders_s454.py]=1c3d3927163e08114e3e26c5f06052a4
FROM[order_sheet_pdf.py]=d0735df84f17a67474bc0cecd58e5c6c; TO[order_sheet_pdf.py]=b0cc86945d560e8cce842b799913e021
READ[marg_order_pdf.py]=c9cd44a55d4cb39247d3c2e8e2602f1d;  READ[order_sheet.py]=247eeb48db8cc007faedfe14f3676893
V12_PIN=f499dd1fb53cb9b23422154aac41596e; V13_PIN=ead2be78869605dfd2580347f33d4017     # the maps S543's walk reads (from the clone's history)
S543_OK_RED="C: both buttons on the page with nothing to order"                        # walk_s543.py 353: the link now carries ?s= (re-checked by walk_s561)
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s561_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
DBBAK="$FIN/finance.db.bak_S561_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S561_${FROM[$1]:0:8}"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting both files back"
  for n in $EDITED; do [ -f "$(bak $n)" ] && \cp -p "$(bak $n)" "$FIN/$n"; done
  rm -f "$FIN"/.*.s561
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK (this kit wrote nothing to the database)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort comm; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
if [ "${LOCK_HELD:-0}" = 1 ]; then
  grep -q "$KIT" "$LOCK/owner" 2>/dev/null || { say "!! [1/10] LOCK_HELD=1 but $LOCK/owner does not name $KIT - nothing installed"; exit 3; }
else
  mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
  if [ "$HAVE_LOCK" != 1 ]; then
    say "!! [1/10] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
    exit 3
  fi
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
fi
say "[1/10] kit gates green (SUMS, KIT_ID); the build lock is ours"

for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [2/10] $FIN/$n is not there - nothing installed"; exit 1; }; done
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: both files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null)"; exit 0; fi
for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/10] $FIN/$n is $C, expected ${FROM[$n]} - it changed after this kit was built: STOP, nothing installed"; exit 1; }; done
for n in "${!READ[@]}"; do C="$(m5 "$FIN/$n")"; [ "$C" = "${READ[$n]}" ] || { say "!! [2/10] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading that file: STOP, nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$POR/portal.py" ] && [ -f "$POR/tile_grants.json" ] && [ -f "$DMAP" ] || { say "!! [2/10] the database, the assets database, the portal or the duty map is missing - nothing installed"; exit 1; }
say "[2/10] live pins exact (porders_s454 72e7fd56, order_sheet_pdf d0735df8); read-only marg_order_pdf c9cd44a5, order_sheet 247eeb48 at their pins"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s561.py walk_s561.py || { say "!! [3/10] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s561.py --fin "$FIN" --out "$SCR/built" >/dev/null || { say "!! [4/10] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/10] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  for n in $EDITED; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/10] the built $n does not compile on $py - nothing installed"; exit 1; }; done
done
say "[3/10] the kit's python files and the two built files compile on $APY and $VPY"
say "[4/10] rebuilt here from this box's live bytes (4 + 4 counted edits): each at its TO pin"

mkside() {   # $1 = side: a copy of the live finance code, the door's reader and its ORDER_PENDING archive, the two databases (backup API)
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  copydb "$DB" "$d/f.db" && copydb "$ADB" "$d/a.db"
}
for side in new old s543new s543old; do mkside "$side" || { say "!! [5/10] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/" && cp -p "$SCR/built/$n" "$SCR/s543new/finance/"; done
mkdir -p "$SCR/oldpy"; for n in $EDITED; do cp -p "$FIN/$n" "$SCR/oldpy/"; done
mkdir -p "$SCR/por"; for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$SCR/por/"; done; cp -p "$POR/tile_grants.json" "$SCR/por/"
WOUT="$( cd /tmp && timeout 1800 "$APY" -B "$KDIR/walk_s561.py" --fin "$SCR/new/finance" --old "$SCR/oldpy" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --portal "$SCR/por" --map "$DMAP" 2>&1 )"; WRC=$?
ROUT="$( cd /tmp && timeout 1800 "$APY" -B "$KDIR/walk_s561.py" --fin "$SCR/old/finance" --old "$SCR/oldpy" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" --portal "$SCR/por" --map "$DMAP" --expect-red 2>&1 )"; RRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S561"; then say "!! [5/10] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | grep -E "^  RED on the old files:|^WALK OK negative|^NEGATIVE CONTROL" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [5/10] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | tail -12; exit 1; fi
# S543's walk, read-only, on the new files and on the live ones beside them: its markers stay as they are, but its 353 check
for pin in "$V12_PIN:map12" "$V13_PIN:map13"; do
  P="${pin%%:*}"; N="${pin##*:}"; H=""
  for h in $("$GIT" -C "$REPO" log --format=%H -n 120 -- claude_code_briefs/DUTY_MAP.json); do
    [ "$("$GIT" -C "$REPO" show "$h:claude_code_briefs/DUTY_MAP.json" 2>/dev/null | md5sum | awk '{print $1}')" = "$P" ] && { H=$h; break; }
  done
  [ -n "$H" ] || { say "!! [5/10] DUTY_MAP ${P:0:8} ($N, read by S543's walk) not found in the clone's history - nothing installed"; exit 1; }
  "$GIT" -C "$REPO" show "$H:claude_code_briefs/DUTY_MAP.json" > "$SCR/$N.json"
done
S543K="$REPO/deploy_kits/S543_ORDER_SHEET_MARG"
for side in s543new s543old; do
  ( cd /tmp && timeout 1800 "$APY" -B "$S543K/walk_s543.py" --fin "$SCR/$side/finance" --db "$SCR/$side/f.db" --adb "$SCR/$side/a.db" --marg "$SCR/$side/marg_ingest" \
      --portal "$SCR/por" --map12 "$SCR/map12.json" --map13 "$SCR/map13.json" --kit "$S543K" > "$SCR/$side.txt" 2>&1 )
done
find "$S543K" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
grep -E '^  FAIL ' "$SCR/s543new.txt" | sed 's/   \[.*$//' | sort > "$SCR/fn.txt"; grep -E '^  FAIL ' "$SCR/s543old.txt" | sed 's/   \[.*$//' | sort > "$SCR/fo.txt"
GN="$(grep -c -E '^  ok ' "$SCR/s543new.txt")"; GO="$(grep -c -E '^  ok ' "$SCR/s543old.txt")"
ONLY_NEW="$(comm -13 "$SCR/fo.txt" "$SCR/fn.txt" | grep -v -F "$S543_OK_RED")"; ONLY_OLD="$(comm -23 "$SCR/fo.txt" "$SCR/fn.txt")"
N353="$(grep -c -F "$S543_OK_RED" "$SCR/fn.txt")"
if [ -n "$ONLY_NEW" ] || [ -n "$ONLY_OLD" ] || [ "$(grep -c -E '^  (ok|FAIL) ' "$SCR/s543new.txt")" != "$(grep -c -E '^  (ok|FAIL) ' "$SCR/s543old.txt")" ]; then
  say "!! [5/10] S543's walk moved on the new files beyond the expected 353 check (new: $GN green, old: $GO green):"; echo "$ONLY_NEW" | head -5; echo "$ONLY_OLD" | head -5; exit 1
fi
S543SAY="S543's walk on the new files: $GN green; red: $(sed 's/^  FAIL //' "$SCR/fn.txt" | cut -c1-70 | tr '\n' '|') (the same as on the live files beside it$([ "$N353" = 1 ] && echo ", plus the 353 check, expected: re-checked by walk_s561 as marg.pdf?s="))"
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [5/10] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[5/10] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
say "       $S543SAY"
rm -rf "$SCR/new" "$SCR/old" "$SCR/s543new" "$SCR/s543old"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [6/10] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [6/10] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [6/10] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[6/10] backups: $(basename "$DBBAK") (sqlite backup API); $(for n in $EDITED; do printf '%s ' "$(basename "$(bak $n)")"; done)"

for n in $EDITED; do
  { \cp -p "$FIN/$n" "$FIN/.$n.s561" && cat "$SCR/built/$n" > "$FIN/.$n.s561" && [ "$(m5 "$FIN/.$n.s561")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s561; say "!! [7/10] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
for n in $EDITED; do mv -f "$FIN/.$n.s561" "$FIN/$n" || restore "placing $n"; done
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "$n did not land at its pin"; done
say "[7/10] placed; md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/porders/s454/order); c3=$(health "/finance/porders/s454/sheet.pdf?s=x&t=1"); c4=$(health "/finance/porders/s454/marg.pdf?s=x&t=1")
for c in "$c2" "$c3" "$c4"; do case "$c" in 302|401) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): order $c2 / sheet.pdf $c3 / marg.pdf $c4";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[8/10] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /s454/order $c2, sheet.pdf $c3, marg.pdf $c4 without a login (302 = the login gate, expected) - journal clean"

mkdir -p "$SCR/placed/finance/spine" "$SCR/placed/marg_ingest/archive"; cp -p "$FIN"/*.py "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/placed/finance/" 2>/dev/null
cp -rp "$FIN/finance_ui" "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$SCR/placed/finance/spine/" 2>/dev/null
for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$SCR/placed/marg_ingest/"; done; cp -rp "$MARG/archive/ORDER_PENDING" "$SCR/placed/marg_ingest/archive/"
copydb "$DB" "$SCR/placed/f.db" && copydb "$ADB" "$SCR/placed/a.db" || restore "no copy of the database for the page look"
POUT="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/walk_s561.py" --page --fin "$SCR/placed/finance" --db "$SCR/placed/f.db" --adb "$SCR/placed/a.db" --marg "$SCR/placed/marg_ingest" --map "$DMAP" 2>&1 )"; PRC=$?
echo "$POUT" | grep -E "^   /finance|^PAGE" | sed 's/^/ /'
[ "$PRC" = 0 ] && echo "$POUT" | grep -q "^PAGE OK" || restore "the order sheet on a copy of the placed files is red"
say "[9/10] the placed files (copied) on a copy of the live database, the walk's own session: the new file names and 'chhapa' on every page"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[10/10] md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: DONE - both PDF buttons open a new address at every tap; the files are named by the export's time; the order sheet says when it was printed"
say "undo: $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak $n)" "$FIN/$n"; done)$SYSTEMCTL restart $SVC"
exit 0
