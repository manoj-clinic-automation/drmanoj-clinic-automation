#!/bin/bash
# =============================================================================
#  install_S574_PHONEBOOK_ONE_RECORD.sh · kit S574 (18-Oct-2026) · brief claude_code_briefs/S574_PHONEBOOK_ONE_RECORD.md (v2)
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S574_PHONEBOOK_ONE_RECORD):
#    rm -rf /tmp/s574kit && cp -rp <kit> /tmp/s574kit && bash /tmp/s574kit/install_S574_PHONEBOOK_ONE_RECORD.sh
#  (DRY=1 before bash: every gate and the walks, nothing written, no lock.)
#
#  One dealer, one record: the phone book's one reader (book_number), numbers 1-4 and the owner's three picks, his one tap that joins the
#  13 linked pairs (and its undo), Marg's push adding into the record. INSTALLS SWITCHED OFF (purchase.book_one_record.on = '0'): every
#  reader, page and message works exactly as before until the owner turns it on. This installer never turns it on and never merges.
#   /root/finance/purchase_app.py     147201dd -> TO     the reader, the door, the merge, the push, /page/book
#   /root/finance/order_sheet.py      247eeb48 -> TO     book_card (was _phones), the cards, the WhatsApp queue
#   /root/finance/order_sheet_pdf.py  b0cc8694 -> TO     the band's numbers
#   /root/finance/porders_s454.py     1c3d3927 -> TO     the staff card's words and numbers
#   /root/finance/supplier_msg.py     2f43af75 -> TO     the NEFT / cheque notice's number
#  Read only (must not move): amir_day.py, porders.py, order_rules.py, finance_app.py, portal.py, tile_grants.json, the crontab.
#  No data step: the schema (new columns, two tables, the switch at '0') is added by the app itself on its first phone-book read.
#  ORDER: gates -> pins (ALREADY first) + read-only pins -> compile (both pythons) -> rebuild from the live bytes -> the walk on scratch
#  copies (the old files first: every control red; then the new files: green, the old pages byte for byte while OFF) -> DRY stops -> the
#  owner's state BEFORE -> backups -> place -> md5 read-back -> ONE restart of clinic-finance -> healthz 200, the pages 302 (login gate,
#  expected) -> journal clean -> the owner's state AFTER on a copy (switch OFF, the book page as before plus his line) -> nothing else moved.
#  Red after placing: the five files put back byte-identically, restart, healthz. The build lock stays held by S574 until the report.
# =============================================================================
set -u
KIT="S574_PHONEBOOK_ONE_RECORD"
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
DMAP="$REPO/claude_code_briefs/DUTY_MAP.json"
EDITED="purchase_app.py order_sheet.py order_sheet_pdf.py porders_s454.py supplier_msg.py"
declare -A FROM TO READ
FROM[purchase_app.py]=147201dd288d291323023a764df3411e
FROM[order_sheet.py]=247eeb48db8cc007faedfe14f3676893
FROM[order_sheet_pdf.py]=b0cc86945d560e8cce842b799913e021
FROM[porders_s454.py]=1c3d3927163e08114e3e26c5f06052a4
FROM[supplier_msg.py]=2f43af754a160376cec955f92f3aa43a
READ[amir_day.py]=73882a8391fde24f31e07b0191c5bd89
READ[porders.py]=a5a823bf30661a4bf65ced39b2355500
READ[order_rules.py]=79f21c1ee1f763b1ac06b370e3d77b79
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s574_inst_$STAMP"
PLACED=0
DBBAK="$FIN/finance.db.bak_S574_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S574_${FROM[$1]:0:8}"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the five files back"
  for n in $EDITED; do [ -f "$(bak $n)" ] && \cp -p "$(bak $n)" "$FIN/$n"; done
  rm -f "$FIN"/.*.s574
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK (the app may have added the S574 columns on a read; the old files never read them)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort cmp crontab; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [1/12] $FIN/$n is not there - nothing installed"; exit 1; }; done
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the five files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/12] DRY RUN: kit gates green (SUMS, KIT_ID, PINS); no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] kit gates green (SUMS, KIT_ID, PINS); the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/12] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi

for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; exit 1; }; done
for n in "${!READ[@]}"; do C="$(m5 "$FIN/$n")"; [ "$C" = "${READ[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$POR/portal.py" ] && [ -f "$POR/tile_grants.json" ] && [ -f "$DMAP" ] || { say "!! [2/12] the database, the assets database, the portal or the duty map is missing - nothing installed"; exit 1; }
NOTT=("$FIN/amir_day.py" "$FIN/porders.py" "$FIN/order_rules.py" "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json")
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
LASTPUSH="$("$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print(c.execute(\"SELECT MAX(at) FROM purchase_audit WHERE action='vendors'\").fetchone()[0])" "$DB" 2>/dev/null)"
say "[2/12] live pins exact (purchase_app 147201dd, order_sheet 247eeb48, order_sheet_pdf b0cc8694, porders_s454 1c3d3927, supplier_msg 2f43af75); read-only amir_day 73882a83, porders a5a823bf, order_rules 79f21c1e at their pins"
say "       what the kit leans on (charter 1b): nothing scheduled -- the phone book only; Marg's nightly number push last came $LASTPUSH (it keeps working as before while the switch is OFF)"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s574.py walk_s574.py || { say "!! [3/12] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s574.py --fin "$FIN" --out "$SCR/built" > "$SCR/make.txt" || { cat "$SCR/make.txt"; say "!! [4/12] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  for n in $EDITED; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/12] the built $n does not compile on $py - nothing installed"; exit 1; }; done
done
say "[3/12] the kit's python files and the five built files compile on $APY and $VPY"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") counted edits): each file at its TO pin"

copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" || { say "!! [5/12] no copy of the databases - nothing installed"; exit 1; }
mkside() {   # $1 = side: a copy of the live finance code, the order door's reader and its archive, the databases (one snapshot for every side)
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  cp -p "$SCR/base.db" "$d/f.db" && cp -p "$SCR/base_a.db" "$d/a.db"
}
for side in new old; do mkside "$side" || { say "!! [5/12] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/"; done
mkdir -p "$SCR/oldpy"; for n in $EDITED; do cp -p "$FIN/$n" "$SCR/oldpy/"; done
mkdir -p "$SCR/por"; for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$SCR/por/"; done; cp -p "$POR/tile_grants.json" "$SCR/por/"
ROUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s574.py" --fin "$SCR/old/finance" --old "$SCR/oldpy" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" --portal "$SCR/por" --map "$DMAP" --dump "$SCR/dump_old" --expect-red 2>&1 )"; RRC=$?
WOUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s574.py" --fin "$SCR/new/finance" --old "$SCR/oldpy" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --portal "$SCR/por" --map "$DMAP" --dump "$SCR/dump_new" --old-dump "$SCR/dump_old" 2>&1 )"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S574"; then say "!! [5/12] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^WALK OK negative|^NEGATIVE CONTROL" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [5/12] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | mask | tail -30; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [5/12] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[5/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
rm -rf "$SCR/new" "$SCR/old" "$SCR/dump_new" "$SCR/dump_old"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

looks() {   # $1 = before|after: the owner's state by the files in /root/finance as they stand, on a fresh copy of the live database
  local d="$SCR/look_$1"; mkside "look_$1" >/dev/null 2>&1 || return 1; copydb "$DB" "$d/f.db" || return 1
  ( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s574.py" --page $([ "$1" = after ] && echo --after) --fin "$d/finance" --db "$d/f.db" --adb "$d/a.db" --marg "$d/marg_ingest" --map "$DMAP" 2>&1 ) | mask
}
say "[6/12] the owner's state BEFORE placing (the live files, a copy of the live database, the walk's own session):"
looks before | grep -E "^   |^PAGE" | sed 's/^/ /'
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [6/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [7/12] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [7/12] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [7/12] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[7/12] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(for n in $EDITED; do printf '%s ' "$(basename "$(bak $n)")"; done)"

for n in $EDITED; do
  { \cp -p "$FIN/$n" "$FIN/.$n.s574" && cat "$SCR/built/$n" > "$FIN/.$n.s574" && [ "$(m5 "$FIN/.$n.s574")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s574; say "!! [8/12] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
for n in $EDITED; do mv -f "$FIN/.$n.s574" "$FIN/$n" || restore "placing $n"; done
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && cmp -s "$FIN/$n" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[8/12] placed by rename; md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's TO pins, byte-identical to the walked files)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/purchase/page/book); c3=$(health /finance/porders/s454/order); c4=$(health /finance/purchase/page/staff)
for c in "$c2" "$c3" "$c4"; do case "$c" in 302|401) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): book $c2 / order $c3 / staff $c4";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[9/12] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /page/book $c2, /s454/order $c3, /page/staff $c4 without a login (302 = the login gate, expected) - journal clean"

say "[10/12] the owner's state AFTER placing (the placed files, a copy of the live database, the walk's own session):"
LA="$(looks after)"
echo "$LA" | grep -E "^   |^PAGE" | sed 's/^/ /'
echo "$LA" | grep -q "^PAGE OK S574" || restore "the owner's state on a copy of the placed files is red"

for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
say "[11/12] nothing else moved (amir_day, porders, order_rules, finance_app, portal.py, tile_grants.json, the crontab); healthz 200"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[12/12] md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: DONE - installed switched OFF (purchase.book_one_record.on = '0'); the owner turns it on and taps Merge all on /finance/purchase/page/book. The build lock stays held by $KIT until the report is written."
say "undo: $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak $n)" "$FIN/$n"; done)$SYSTEMCTL restart $SVC"
exit 0
