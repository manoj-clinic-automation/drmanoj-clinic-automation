#!/bin/bash
# =============================================================================
#  install_S583_ARRIVALS_ONE_RULE.sh · kit S583 (18-Oct-2026) · brief claude_code_briefs/S583_ARRIVALS_ONE_RULE.md (v3)
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S583_ARRIVALS_ONE_RULE), 08:00-23:59 IST only:
#    rm -rf /tmp/s583kit && cp -rp <kit> /tmp/s583kit && bash /tmp/s583kit/install_S583_ARRIVALS_ONE_RULE.sh
#  (DRY=1 before bash: every gate, the scratch sides and both walks, nothing written, no lock.)
#
#  ONE rule for "Marg carries this arrival" (stock_figure.carried / expired): a tapped or scan-tied order line counts on the shelf while Marg's
#  purchases do not carry it (its own Marg bill; the own vendor's bill from arrival.back_days before the order day; another supplier's bill from
#  the order day; never a bill that answered another line) and the spine's purchase reach has not passed it by arrival.bill_grace_days. An
#  expired arrival leaves the shelf and goes to the owner's Needs-you (scan-tied orders; the untied taps stay with D712). shelf_figure loses
#  scan_arrivals; stock_watch._arrivals and bill_pending_lines test carried().
#   /root/finance/stock_figure.py   cb5f24aa -> TO   carried, expired, taps, scan_lines, scan_arrivals, arrivals_open; shelf() adds both
#   /root/finance/shelf_figure.py   a544afda -> TO   scan_arrivals removed; the header
#   /root/finance/stock_watch.py    bc688521 -> TO   _arrivals (in_spine = carried), bill_pending_lines, arrival_needs_you, the setting arrival.back_days
#  Read only, must not move (this kit was built reading them): porders, order_sheet, order_rules, stock_app, amir_day, loss_piles, purchase_app,
#  item_alias, qty_words, finance_app, portal.py, tile_grants.json, the crontab, the spine's files. No DUTY_MAP change. No data step.
#  ORDER: gates (window, lock, SUMS, KIT_ID, PINS) -> pins (ALREADY first) + the read-only md5s printed -> the spine green and fresh -> build from
#  the live bytes -> compile (both pythons) -> scratch: the finance folder twice, the databases and the spine by the backup API; the walk on the
#  OLD files (every control red) then on the NEW files (green) -> DRY stops -> the install-day state on the OLD and the NEW files (same copy) ->
#  backups -> DOCTOR_AUTO_OFF -> the three files staged and renamed in ONE command (stock_figure.py first) -> ONE restart of clinic-finance ->
#  healthz 200, the pages 302 -> journal clean -> the state AFTER (the live files) -> nothing else moved -> md5 read-back -> DOCTOR_AUTO_OFF removed.
#  Red after placing: the three files put back in one command, one restart, healthz. The build lock stays held by S583 until the report is written.
# =============================================================================
set -u
KIT="S583_ARRIVALS_ONE_RULE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
SPN="$FIN/spine"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
REPO="${REPO:-/root/deploy/repo}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
DMAP="$REPO/claude_code_briefs/DUTY_MAP.json"
EDITED="stock_figure.py shelf_figure.py stock_watch.py"                     # placed in the ONE move, stock_figure.py first
declare -A FROM TO READ
FROM[stock_figure.py]=cb5f24aacf7748752206619ce8bbb1e3
FROM[shelf_figure.py]=a544afda07b4632e9bc05e97c256dde6
FROM[stock_watch.py]=bc6885217a9f7ca7d8273021fcf6315a
READ[porders.py]=a5a823bf30661a4bf65ced39b2355500
READ[order_sheet.py]=f00f0163bdd66a074c5af261c9b80a49
READ[order_rules.py]=79f21c1ee1f763b1ac06b370e3d77b79
READ[stock_app.py]=f279a3be440878bb30e418c20a5cf608
READ[amir_day.py]=73882a8391fde24f31e07b0191c5bd89
READ[loss_piles.py]=2b9023fd06aadc0ddaef30e2f26eccb3
READ[purchase_app.py]=98f7d9f05bc06ef6be80181dd9be4c8c
READ[item_alias.py]=111a8e4877035e5a02665dd586e01b06
READ[qty_words.py]=706db7ccfa7489fb8d296f663590f107
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s583_inst_$STAMP"
PLACED=0
DBBAK="$FIN/finance.db.bak_S583_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S583_${FROM[$1]:0:8}"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the three files back in one command"
  \cp -p "$(bak stock_figure.py)" "$FIN/stock_figure.py" && \cp -p "$(bak shelf_figure.py)" "$FIN/shelf_figure.py" && \cp -p "$(bak stock_watch.py)" "$FIN/stock_watch.py"
  rm -f "$FIN"/.*.s583
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK (no data step was made)"
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
HH="$(TZ=Asia/Kolkata date +%H)"
[ "$HH" -ge 8 ] || { say "!! [1/12] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:00-23:59 IST (the spine builds */10 8-23) - nothing installed"; exit 1; }
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
say "[2/12] live pins exact: stock_figure cb5f24aa, shelf_figure a544afda, stock_watch bc688521"
say "       the read-only files' live md5s (the brief, section 1):"
for n in porders.py order_sheet.py order_rules.py stock_app.py amir_day.py loss_piles.py purchase_app.py item_alias.py qty_words.py; do
  C="$(m5 "$FIN/$n")"; say "         $n $C"
  [ "$C" = "${READ[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"; exit 1; }
done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$DMAP" ] && [ -f "$SPN/spine.db" ] && [ -f "$SPN/spine_state.json" ] || { say "!! [2/12] a database, the duty map or the spine is missing - nothing installed"; exit 1; }
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] && [ "$SP_AGE" -le 30 ] \
  || { say "!! [2/12] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - the kit depends on it; nothing installed (charter 1b)"; exit 4; }
NOTT=("$FIN/porders.py" "$FIN/order_sheet.py" "$FIN/order_rules.py" "$FIN/stock_app.py" "$FIN/amir_day.py" "$FIN/loss_piles.py" "$FIN/purchase_app.py" "$FIN/item_alias.py" "$FIN/qty_words.py" "$FIN/stockmatch.py" "$FIN/porders_s454.py" "$FIN/darpan_kal.py" "$FIN/finance_app.py" "$SPN/spine_build.py" "$SPN/spine_read.py" "$SPN/selftest_spine.py" "$POR/portal.py" "$POR/tile_grants.json" "$DMAP")
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "       charter 1b: the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago)"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s583.py walk_s583.py || { say "!! [3/12] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s583.py --finance "$FIN" --out "$SCR/built" > "$SCR/make.txt" || { cat "$SCR/make.txt"; say "!! [4/12] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  for n in $EDITED; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/12] the built $n does not compile on $py - nothing installed"; exit 1; }; done
done
say "[3/12] the kit's python files and the three built files compile on $APY and $VPY"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits): each file at its TO pin"

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
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/"; done
say "[5/12] scratch: the finance folder twice (NEW with the three built files, OLD as it is), finance.db, assets.db and the spine by the backup API"
ROUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s583.py" --fin "$SCR/old/finance" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" --map "$DMAP" --dump "$SCR/dump_old" --expect-red 2>&1 )"; RRC=$?
WOUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s583.py" --fin "$SCR/new/finance" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --map "$DMAP" --dump "$SCR/dump_new" --old-dump "$SCR/dump_old" 2>&1 )"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S583"; then say "!! [6/12] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^  FAIL C:|^WALK OK negative|^NEGATIVE CONTROL|^  NOT RED|^WALK RED" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/12] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | mask | tail -30; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [6/12] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S583: //')"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the scratch sides and both walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

# ---- 7: the install-day state on the OLD and the NEW files (fresh copies of the live database) --------------------------------------------
statelook() {   # $1 = a scratch finance folder, or LIVE (a fresh scratch copy of /root/finance as it stands, its spine.db beside it); $2 = label
  local d="$SCR/st_$2" fin="$1"; mkdir -p "$d"
  if [ "$1" = LIVE ]; then
    mkside "st_$2" >/dev/null 2>&1 || return 1
    copydb "$SPN/spine.db" "$d/finance/spine/spine.db" || return 1
    fin="$d/finance"
  fi
  copydb "$DB" "$d/f.db" || return 1
  ( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s583.py" --state --label "$2" --fin "$fin" --db "$d/f.db" --adb "$SCR/base_a.db" --marg "$SCR/new/marg_ingest" --map "$DMAP" 2>&1 ) | mask
}
say "[7/12] the install-day state BEFORE (the live files on a copy) and as the NEW files read the same copy:"
SB="$(statelook "$SCR/old/finance" before)"; echo "$SB" | grep -E "^STATE|^   " | sed 's/^/ /'
SN="$(statelook "$SCR/new/finance" new)"; echo "$SN" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SB" | grep -q "^STATE OK S583" && echo "$SN" | grep -q "^STATE OK S583" || { say "!! [7/12] the install-day state could not be read - nothing placed"; exit 1; }
BPD="$("$APY" -c "
import json,sys
b=json.load(open(sys.argv[1])); n=json.load(open(sys.argv[2]))
print('' if b['bill_pending']==n['bill_pending'] else 'Amir bill_pending differs: %s -> %s' % (b['bill_pending'], n['bill_pending']))" "$SCR/st_before/state_before.json" "$SCR/st_new/state_new.json")"
[ -z "$BPD" ] || { say "!! [7/12] $BPD - the brief says Amir's lines are equal before and after: STOP before placing"; exit 6; }
say "       Amir's 'bill entry baaki' lines are the same on both files; the owner's arrival lines above are the ones the install brings"
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 8: backups ---------------------------------------------------------------------------------------------------------------------------
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [8/12] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [8/12] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [8/12] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[8/12] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(for n in $EDITED; do printf '%s ' "$(basename "$(bak $n)")"; done)"

# ---- 9-10: the three files in ONE move, one restart ----------------------------------------------------------------------------------------
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || { say "!! [9/12] could not write $OFFSW - nothing placed"; exit 1; }
for n in $EDITED; do
  { \cp -p "$FIN/$n" "$FIN/.$n.s583" && cat "$SCR/built/$n" > "$FIN/.$n.s583" && [ "$(m5 "$FIN/.$n.s583")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s583 "$OFFSW"; say "!! [9/12] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
mv -f "$FIN/.stock_figure.py.s583" "$FIN/stock_figure.py" && mv -f "$FIN/.shelf_figure.py.s583" "$FIN/shelf_figure.py" && mv -f "$FIN/.stock_watch.py.s583" "$FIN/stock_watch.py" || restore "placing the three files"
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && cmp -s "$FIN/$n" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[9/12] placed by rename in ONE command (stock_figure.py first); md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's TO pins, byte-identical to the walked files)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/amir); c3=$(health /finance/stock/page/now); c4=$(health /finance/stockmatch); c5=$(health /finance/porders)
for c in "$c2" "$c3" "$c4" "$c5"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): amir $c2 / now $c3 / stockmatch $c4 / porders $c5";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[10/12] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/amir $c2, /stock/page/now $c3, /stockmatch $c4, /porders $c5 without a login (302 = the login gate, expected) - journal clean"

# ---- 11: the state AFTER (the live files on a fresh copy), nothing else moved ----------------------------------------------------------------
say "[11/12] the install-day state AFTER placing (the live files, a fresh copy of the live database):"
SA_="$(statelook LIVE after)"; echo "$SA_" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SA_" | grep -q "^STATE OK S583" || restore "the state after placing could not be read"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
rm -f "$OFFSW"
say "       nothing else moved (the read-only files, finance_app, the spine's files, portal.py, tile_grants.json, DUTY_MAP, the crontab); healthz 200; $OFFSW removed"
say "       the order_rules tick and the 06:30 stock_watch job pick the new files up on their next run"

find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[12/12] md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: DONE. The build lock stays held by $KIT until the report is written."
say "undo: $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak $n)" "$FIN/$n"; done)$SYSTEMCTL restart $SVC"
exit 0
