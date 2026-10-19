#!/bin/bash
# =============================================================================
#  install_S598_ARRIVALS_BY_LINE.sh · kit S598 (19-Oct-2026) · brief claude_code_briefs/S598_ARRIVALS_BY_LINE.md (v2) · closes F-942
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S598_ARRIVALS_BY_LINE), 08:00-23:49 IST only:
#    rm -rf /tmp/s598kit && cp -rp <kit> /tmp/s598kit && bash /tmp/s598kit/install_S598_ARRIVALS_BY_LINE.sh
#  (DRY=1 before bash: every gate, the scratch sides and both walks, nothing written, no lock.)
#
#  THE BILL LINE IS THE UNIT OF THE ONE ARRIVALS RULE (F-942): a bill line answers only the size it names; one bill line is never
#  credited to two order lines; the owner's arrival line names the family's bill that carried other sizes.
#   /root/finance/stock_figure.py   92367a19 -> TO   _line_forms / _siblings / _matches / _purchase_lines_of / _taken_lines / _family_bill; _carried on lines;
#                                                    _purchases_of and _taken_bills retired; arrivals_open()['family_bill']
#   /root/finance/stock_watch.py    c5f3ce21 -> TO   arrival_needs_you: the ' (its bill N of dd-mm carried SIZE, SIZE, not this size)' clause (English, owner only)
#   /root/finance/porders.py        78ea72be -> TO   detect_supplies writes the matched bill LINE's packs (qty + free from carried()); the key-level SUM(qty) gone
#  ONE data step on finance.db (rejudge_s598.py, after placing): S593's marks of 19-Oct re-judged under the new rule; the rows the rule
#  disagrees with are cleared (the system's own write undone; the rows saved whole to purchase_order_line.bak_S598_<stamp>.json first;
#  undo_s598.py restores them -- written, never run here). No new table, no new setting, no staff word.
#  Read only, must not move (this kit was built reading them): shelf_figure, order_rules, porders_s454, order_sheet, stock_app, amir_day,
#  spine/spine_build, spine/spine_read, item_alias, qty_words, marg_purchase_rows; and proved unmoved: finance_app, portal.py, tile_grants.json,
#  the crontab (84 lines, S577_WITNESS in), spine.db's schema. No duty added, moved or removed (DUTY_MAP untouched).
#  ORDER: gates (window, lock, SUMS, KIT_ID, PINS) -> pins (ALREADY first) + the read-only md5s -> the four ticked renames in item_alias.done_rows
#  -> the spine green and fresh -> build from the live bytes (anchored edits, each anchor once) -> compile (both pythons) -> scratch: the finance
#  folder twice, finance.db / assets.db / spine.db by the backup API; the walk on the OLD files (every control red) then on the NEW files (green)
#  -> DRY stops -> the install-day state BEFORE (the live files on a copy) and as the NEW files read the same copy -> backups -> DOCTOR_AUTO_OFF ->
#  the three files staged and renamed in ONE command -> ONE restart of clinic-finance -> healthz 200, the pages 302 -> journal clean ->
#  rejudge_s598.py ONCE on the live database (its table quoted; the cleared set must equal the walk's) -> porders.detect_supplies once (its
#  writes quoted -- expected none new) -> the state AFTER -> nothing else moved -> md5 read-back -> DOCTOR_AUTO_OFF removed. Red after placing:
#  the three files put back in one command, one restart, healthz; if the re-judge had run, undo_s598.py from the JSON and the row diff printed.
#  The build lock stays held until the report is written. Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S598_ARRIVALS_BY_LINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
SPN="$FIN/spine"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDITED="stock_figure.py stock_watch.py porders.py"
declare -A FROM TO READ
FROM[stock_figure.py]=92367a196b360f0cded4cda6a5ded700
FROM[stock_watch.py]=c5f3ce21a785c45df58f21932cf920e7
FROM[porders.py]=78ea72be7d87a7c56c65de7d4c96a952
READ[shelf_figure.py]=23b2394a7a10a99ff0c30121087813f1
READ[order_rules.py]=8d078dbe1b63a4706dc6f35e3c31ac9a
READ[porders_s454.py]=40f1755a7655deb733765456b9a466fe
READ[order_sheet.py]=1f1e85c12c64521b50a10cea48220170
READ[stock_app.py]=4f73d0b02a167289d9439af7a35b5fa0
READ[amir_day.py]=3af992d9e6b6c6050b1427e34757ca78
READ[spine/spine_build.py]=e3d3ed85973eab2df0326dc9621e230e
READ[spine/spine_read.py]=827b00402add288d028c910128084b90
READ[item_alias.py]=111a8e4877035e5a02665dd586e01b06
READ[qty_words.py]=706db7ccfa7489fb8d296f663590f107
READ[marg_purchase_rows.py]=41d68148fc3aa461da30a9eb4053b649
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s598_inst_$STAMP"
PLACED=0; REJUDGED=0
DBBAK="$FIN/finance.db.bak_S598_$STAMP"
JSONBAK="$FIN/purchase_order_line.bak_S598_$STAMP.json"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S598_${FROM[$1]:0:8}"; }
stg() { echo "$FIN/.$1.s598"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
schema5() { "$APY" -c "import sqlite3,sys,hashlib; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); print(hashlib.md5('\n'.join(sorted(r[0] or '' for r in c.execute(\"SELECT sql FROM sqlite_master WHERE type IN ('table','index')\"))).encode()).hexdigest())" "$1" 2>/dev/null; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the three files back in one command"
  \cp -p "$(bak stock_figure.py)" "$FIN/stock_figure.py" && \cp -p "$(bak stock_watch.py)" "$FIN/stock_watch.py" && \cp -p "$(bak porders.py)" "$FIN/porders.py"
  rm -f "$FIN"/.*.s598
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  if [ "$REJUDGED" = 1 ] && [ -f "$JSONBAK" ]; then
    say "   the re-judge had run: undo_s598.py from $JSONBAK (the row diff must print empty)"
    ( cd /tmp && "$APY" -B "$KDIR/undo_s598.py" --db "$DB" --json "$JSONBAK" 2>&1 ) | mask | sed 's/^/      /'
  fi
  say "   the database backup stays: $DBBAK"
  rm -f "$OFFSW"
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
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"
{ [ "$HH" -ge 8 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } || { say "!! [1/12] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:00-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [1/12] $FIN/$n is not there - nothing installed"; exit 1; }; done
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/12] DRY RUN: kit gates green (SUMS, KIT_ID, PINS, the window); no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] kit gates green (SUMS, KIT_ID, PINS, the window); the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/12] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi

for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; exit 1; }; done
say "[2/12] live pins exact: $(for n in $EDITED; do printf '%s %s . ' "$n" "${FROM[$n]:0:8}"; done)"
say "       the read-only files' live md5s (the brief, section 1):"
for n in shelf_figure.py order_rules.py porders_s454.py order_sheet.py stock_app.py amir_day.py spine/spine_build.py spine/spine_read.py item_alias.py qty_words.py marg_purchase_rows.py; do
  C="$(m5 "$FIN/$n")"; say "         $n $C"
  [ "$C" = "${READ[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"; exit 1; }
done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SPN/spine.db" ] && [ -f "$SPN/spine_state.json" ] || { say "!! [2/12] a database or the spine is missing - nothing installed"; exit 1; }
CRONN="$(crontab -l 2>/dev/null | wc -l | awk '{print $1}')"; CRONW="$(crontab -l 2>/dev/null | grep -c S577_WITNESS || true)"
say "       the crontab: $CRONN lines, S577_WITNESS lines ${CRONW:-0}"
[ "$CRONN" = 84 ] && [ "${CRONW:-0}" = 1 ] || { say "!! [2/12] the crontab is not as the brief read it (84 lines, S577_WITNESS once) - STOP, nothing installed"; exit 1; }
say "       the four ticked renames (R1-C1), item_alias.done_rows on the live database (read only):"
REN="$( cd "$FIN" && "$APY" -B -c '
import sqlite3, sys
sys.path.insert(0, ".")
import item_alias
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True, timeout=60); con.row_factory = sqlite3.Row
rows = {(r["old_name"], r["new_name"]): r["state"] for r in item_alias.done_rows(con)}
want = [("ANKLE BINDER BAMBOO M", "ANKLE BINDER M BAMBOO"), ("ANKLE BINDER BAMBOO L", "ANKLE BINDER L BAMBOO"), ("KNEE SUPPORT HINGED XL", "KNEE SUPPORT XL HINGED"), ("KNEE SUPPORT HINGED XXL UNISO", "KNEE SUPPORT XXL HINGED")]
miss = 0
for o, n in want:
    print("         %-30s -> %-30s %s" % (o, n, rows.get((o, n), "MISSING")))
    miss += 0 if (o, n) in rows else 1
print("RENAMES_MISSING %d" % miss)
' "$DB" 2>&1 )"
echo "$REN" | grep -v '^RENAMES_MISSING'
echo "$REN" | grep -q '^RENAMES_MISSING 0$' || { say "!! [2/12] a rename this kit stands on is not ticked in item_alias.done_rows - STOP, nothing installed"; exit 1; }
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] && [ "$SP_AGE" -le 30 ] \
  || { say "!! [2/12] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - the kit depends on it; nothing installed (charter 1b)"; exit 4; }
NOTT=("$FIN/shelf_figure.py" "$FIN/order_rules.py" "$FIN/porders_s454.py" "$FIN/order_sheet.py" "$FIN/stock_app.py" "$FIN/amir_day.py" "$SPN/spine_build.py" "$SPN/spine_read.py" "$FIN/item_alias.py" "$FIN/qty_words.py" "$FIN/marg_purchase_rows.py" "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json")
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"; SCHEMA0="$(schema5 "$SPN/spine.db")"
[ -n "$SCHEMA0" ] || { say "!! [2/12] the spine's schema could not be read - nothing installed"; exit 1; }
say "       charter 1b: the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago); spine.db schema $SCHEMA0; sp_meta.built $("$APY" -c "import sqlite3,sys; print(sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True).execute(\"SELECT value FROM sp_meta WHERE key='built'\").fetchone()[0])" "$SPN/spine.db" 2>/dev/null)"
say "       the settings: $("$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print(dict(c.execute(\"SELECT key, value FROM setting WHERE key IN ('arrival.bill_grace_days','arrival.back_days','order.source','order.stock_basis','porders.ortho_vendor') ORDER BY key\").fetchall()))" "$DB")"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s598.py walk_s598.py rejudge_s598.py undo_s598.py || { say "!! [3/12] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s598.py --finance "$FIN" --out "$SCR/built" > "$SCR/make.txt" || { cat "$SCR/make.txt"; say "!! [4/12] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  for n in $EDITED; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/12] the built $n does not compile on $py - nothing installed"; exit 1; }; done
done
say "[3/12] the kit's python files and the three built files compile on $APY and $VPY"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits): each of the three files at its TO pin"

copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" && copydb "$SPN/spine.db" "$SCR/spine.db" || { say "!! [5/12] no copy of the databases - nothing installed"; exit 1; }
mkside() {   # $1 = side: a copy of the live finance code (spine folder included), the ingest reader, the databases (backup API), the spine copy
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  cp -p "$SCR/base.db" "$d/f.db" && cp -p "$SCR/base_a.db" "$d/a.db" && cp -p "$SCR/spine.db" "$d/finance/spine/spine.db"
}
for side in new old; do mkside "$side" || { say "!! [5/12] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/$n"; done
say "[5/12] scratch: the finance folder twice (NEW with the three built files, OLD as it is), finance.db, assets.db and the spine by the backup API"
ROUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s598.py" --fin "$SCR/old/finance" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" --kit "$KDIR" --dump "$SCR/dump_old" --expect-red 2>&1 )"; RRC=$?
WOUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s598.py" --fin "$SCR/new/finance" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --kit "$KDIR" --dump "$SCR/dump_new" --old-dump "$SCR/dump_old" 2>&1 )"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S598"; then say "!! [6/12] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^  FAIL C:|^WALK OK negative|^NEGATIVE CONTROL|^  NOT RED|^WALK RED" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/12] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | mask | tail -30; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [6/12] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
WALK_REJ="$(echo "$WOUT" | grep -o 'REJUDGE OK S598: .*' | head -1 | sed -E 's/ \[DRY.*//')"
[ -n "$WALK_REJ" ] || { say "!! [6/12] the walk did not print the re-judge's result line - nothing installed"; exit 1; }
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S598: //')"
say "       the walk's re-judge on the copy: $WALK_REJ"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the scratch sides and both walks green; NOTHING written, nothing placed, nothing restarted, no re-judge"; exit 0; fi

# ---- 7: the install-day state on the OLD and the NEW files (fresh copies of the live database) ----------------------------------------------
statelook() {   # $1 = a scratch finance folder, or LIVE (a fresh scratch copy of /root/finance as it stands, its spine.db beside it); $2 = label
  local d="$SCR/st_$2" fin="$1"; mkdir -p "$d"
  if [ "$1" = LIVE ]; then
    mkside "st_$2" >/dev/null 2>&1 || return 1
    copydb "$SPN/spine.db" "$d/finance/spine/spine.db" || return 1
    fin="$d/finance"
  fi
  copydb "$DB" "$d/f.db" || return 1
  ( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s598.py" --state --label "$2" --fin "$fin" --db "$d/f.db" --adb "$SCR/base_a.db" --marg "$SCR/new/marg_ingest" --kit "$KDIR" 2>&1 ) | mask
}
say "[7/12] the install-day state BEFORE (the live files on a copy) and as the NEW files read the same copy (before the data step; charter 7):"
SB="$(statelook "$SCR/old/finance" before)"; echo "$SB" | grep -E "^STATE|^   " | sed 's/^/ /'
SN="$(statelook "$SCR/new/finance" new)"; echo "$SN" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SB" | grep -q "^STATE OK S598" && echo "$SN" | grep -q "^STATE OK S598" || { say "!! [7/12] the install-day state could not be read - nothing placed"; exit 1; }
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 8: backups ---------------------------------------------------------------------------------------------------------------------------
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [8/12] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [8/12] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [8/12] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[8/12] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(for n in $EDITED; do printf '%s ' "$(bak $n | sed "s#$FIN/##")"; done)"

# ---- 9-10: the three files in ONE move, one restart -----------------------------------------------------------------------------------------
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || { say "!! [9/12] could not write $OFFSW - nothing placed"; exit 1; }
for n in $EDITED; do
  { \cp -p "$FIN/$n" "$(stg $n)" && cat "$SCR/built/$n" > "$(stg $n)" && [ "$(m5 "$(stg $n)")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s598 "$OFFSW"; say "!! [9/12] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
mv -f "$(stg stock_figure.py)" "$FIN/stock_figure.py" && mv -f "$(stg stock_watch.py)" "$FIN/stock_watch.py" && mv -f "$(stg porders.py)" "$FIN/porders.py" || restore "placing the three files"
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && cmp -s "$FIN/$n" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[9/12] placed by rename in ONE command; md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's TO pins, byte-identical to the walked files)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/porders); c3=$(health /finance/porders/s454/order); c4=$(health /finance/stockmatch); c5=$(health /finance/amir); c6=$(health /finance/reports/aaj); c7=$(health /finance/sanjeevni/api/needs-you)
for c in "$c2" "$c3" "$c4" "$c5" "$c6" "$c7"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): porders $c2 / s454-order $c3 / stockmatch $c4 / amir $c5 / reports-aaj $c6 / needs-you $c7";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[10/12] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/porders $c2, /s454/order $c3, /stockmatch $c4, /amir $c5, /reports/aaj $c6, /sanjeevni/api/needs-you $c7 without a login (302 = the login gate, expected) - journal clean"

# ---- 11: the data step ONCE on the live database; detect_supplies once; the state AFTER; nothing else moved --------------------------------
say "[11/12] rejudge_s598.py ONCE on the live database (the seven rows saved whole to $(basename "$JSONBAK") first; the table quoted):"
REJUDGED=1
RJ="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/rejudge_s598.py" --fin "$FIN" --db "$DB" --json "$JSONBAK" 2>&1 )"; RJRC=$?
echo "$RJ" | mask | sed 's/^/        /'
[ "$RJRC" = 0 ] && echo "$RJ" | grep -q "^REJUDGE OK S598" || restore "the re-judge on the live database did not run clean (exit $RJRC)"
LIVE_REJ="$(echo "$RJ" | grep -o 'REJUDGE OK S598: .*' | head -1)"
[ "$LIVE_REJ" = "$WALK_REJ" ] || restore "the re-judge on live differs from the walk's on the copy: live '$LIVE_REJ' vs walk '$WALK_REJ'"
[ -s "$JSONBAK" ] && chmod 600 "$JSONBAK" || restore "the rows' JSON was not written"
say "        the rows' JSON: $JSONBAK ($(stat -c %s "$JSONBAK") bytes, md5 $(m5 "$JSONBAK")); undo_s598.py --db $DB --json $JSONBAK puts them back (never run by this installer)"
say "        porders.detect_supplies once on the live database (what the page's every read and the ten-minute tick do; its writes quoted -- expected none new):"
DOUT="$( cd "$FIN" && FINANCE_DB="$DB" timeout 600 "$APY" -B -c '
import os, sqlite3, sys
sys.path.insert(0, os.getcwd())
import porders
db = os.environ["FINANCE_DB"]
con = sqlite3.connect(db, timeout=60); con.row_factory = sqlite3.Row
def rows():
    return {int(r[0]): dict(r) for r in con.execute("SELECT l.id, l.item, l.packs, l.billed_qty, l.billed_bill_no, l.billed_date, l.supplied, l.short, o.vendor, o.id AS oid FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE o.status IN (\"sent\",\"received\")")}
b = rows()
n = porders.detect_supplies(con)
a = rows()
print("detect_supplies wrote %d line(s)" % n)
for i in sorted(a):
    if a[i]["billed_qty"] is not None and (b.get(i) or {}).get("billed_qty") is None:
        r = a[i]
        print("   line %-4s order %-3s %-30s %-26s ordered %3s packs -> billed %3s by bill %-14s of %s supplied %s short %s" % (i, r["oid"], r["item"][:30], r["vendor"][:26], r["packs"], r["billed_qty"], r["billed_bill_no"], r["billed_date"], r["supplied"], r["short"]))
con.close()
' 2>&1 )" || true
echo "$DOUT" | mask | sed 's/^/        /'
echo "$DOUT" | grep -q "^detect_supplies wrote" || restore "detect_supplies on the live database did not run"
say "        the install-day state AFTER placing and the data step (the live files, a fresh copy of the live database):"
SA_="$(statelook LIVE after)"; echo "$SA_" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SA_" | grep -q "^STATE OK S598" || restore "the state after placing could not be read"
echo "$SA_" | grep -q "3 KNEE SUPPORT HINGED XL=open" && echo "$SA_" | grep -q "50 L S BELT CONT GRAY UNISON =open" || restore "order 1 line 3 / order 20 line 50 do not read open after the data step"
echo "$SA_" | grep "the orthotic shortage card" | grep -q "KNEE SUPPORT HINGED XL" && restore "KNEE SUPPORT HINGED XL is still on the orthotic shortage card"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(schema5 "$SPN/spine.db")" = "$SCHEMA0" ] || restore "spine.db's schema moved -- no table may be added to the spine"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
rm -f "$OFFSW"
say "        nothing else moved (the read-only files, finance_app, the spine's files and schema, portal.py, tile_grants.json, the crontab); healthz 200; $OFFSW removed"
say "        the ten-minute tick, the 06:30 job and every page read pick the new files up on their next run"

find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[12/12] md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: DONE. The build lock stays held by $KIT until the report is written."
say "undo (the files): $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak $n)" "$FIN/$n"; done)$SYSTEMCTL restart $SVC"
say "undo (the rows, only if the chat says the data change must be reversed): cd /tmp && $APY -B $KDIR/undo_s598.py --db $DB --json $JSONBAK"
exit 0
