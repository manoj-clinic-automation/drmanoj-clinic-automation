#!/bin/bash
# =============================================================================
#  install_S604_PAY_SHEET_FIXES.sh · kit S604 (20-Oct-2026) · brief claude_code_briefs/S604_PAY_SHEET_FIXES.md (v2)
#  F-956 B (returns counted as returns), F-955 (the clipped-name twin: the rule and the one audited data step), F-954 (the two boxes),
#  the owner's ask of 20-Oct 08:25 (the month-end reports card) and the one lock gate. The SERVER half; the medical PC's reader
#  (F-956 A, marg_txt.py) is delivered through Drive by the build runner (README, "the medical-PC half").
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S604_PAY_SHEET_FIXES), 08:02-23:49 IST only:
#    S604_TEXT=/tmp/s604data/<this morning's refused text> bash /tmp/s604kit/install_S604_PAY_SHEET_FIXES.sh
#  (DRY=1 before bash: every gate, the scratch sides and the walks, nothing written, no lock.)
#  S604_TEXT is the 20-Oct 08:06:12 SUPPLIER/ITEM WISE text (md5 405e52bb...), copied from Drive FromMedical\refused_text -- data, never
#  in the repository; the walk converts it with the kit's reader and pushes it onto a scratch copy.
#
#   /root/finance/purchase_app.py   60f2d846 -> TO   returns signed at read time; _s604_bill_lookup; _month_reports, the card, the refusal
#                                                     line; _lock_gate (api_finalise, the month page, the hub); _verify_statement on the last
#                                                     day; the two boxes (a phone's minus, malformed refused, the note kept, the saved line)
#   /root/finance/finance.db        one audited data step (data_s604.py): bill 542 takes 5307d3e5's supplier-wise carrying, 579 retired
#  No DDL, no new table, no new setting. Read only, must not move: amir_day 1169a3d6, stock_app 40f2c922, stock_watch f0d9092a, amir_salts
#  fc5c1d16, marg_purchase_rows 41d68148, supplier_msg 6366ed0f, packs e46264b8, bank_sms aa527840, export_watch f6845ec5, reports_tile 535b5790,
#  marg_door dc5c1e36; proved unmoved: finance_app, portal.py, tile_grants.json, the crontab, spine.db's schema.
#  ORDER: gates (window, lock, SUMS, KIT_ID, PINS, S603's kit, the text) -> the pin (ALREADY first) + the read-only md5s + the crontab -> the
#  spine green -> the live facts printed (F-510) -> build from the live bytes -> compile (both pythons) -> scratch: the finance folder twice, a
#  portal copy, finance.db / assets.db / spine.db by the backup API; the walk on the OLD file (every control red) then on the NEW file (green);
#  S603's walk on the NEW file -> DRY stops -> the state BEFORE (the OLD file on a copy) and as the NEW file reads it -> backups ->
#  DOCTOR_AUTO_OFF -> the file staged and renamed -> the data step on the live database -> ONE restart of clinic-finance -> healthz 200, the
#  pages 302 -> journal clean -> the state AFTER (the live file, a fresh copy) -> nothing else moved -> md5 read-back -> DOCTOR_AUTO_OFF removed.
#  Red after placing: the file put back, the data step undone from its audit row, one restart, healthz. The build lock stays held until the
#  report is written (released with rm -f .../owner; rmdir ...). Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S604_PAY_SHEET_FIXES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
SPN="$FIN/spine"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
DB="${DB:-$FIN/finance.db}"
REPO="${REPO:-/root/deploy/repo}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
S603KIT="${S603KIT:-$REPO/deploy_kits/S603_AMIR_CALENDAR_SAFE}"
TEXT="${S604_TEXT:-}"
TEXT_MD5=405e52bbc187ac6c20d44712ae33549a
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
N=purchase_app.py
FROM=60f2d846155659c4eddc33e4a0d42b39
declare -A READ
READ[amir_day.py]=1169a3d6ae451ebb4c9806052de0856c
READ[stock_app.py]=40f2c92260ae6b6715d49729fef464ff
READ[stock_watch.py]=f0d9092a051c4cd043645e4510ef4cee
READ[amir_salts.py]=fc5c1d169cf971deb6b59010141a4550
READ[marg_purchase_rows.py]=41d68148fc3aa461da30a9eb4053b649
READ[supplier_msg.py]=6366ed0f75e0496fcd5ea98866dbddbd
READ[packs.py]=e46264b85f22563f3e0d8643597e1d58
READ[bank_sms.py]=aa5278403ec85c898d808486e4c3cde3
READ[export_watch.py]=f6845ec5ae1dc8fe200ebf5f4c3ad173
READ[reports_tile.py]=535b579011004ba2e8d8c41070067b2c
READ[marg_door.py]=dc5c1e36d2c8bee2cd556de5c5e4f018
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s604_inst_$STAMP"
PLACED=0; STEPPED=0
DBBAK="$FIN/finance.db.bak_S604_$STAMP"
BAK="$FIN/$N.bak_S604_${FROM:0:8}"
STG="$FIN/.$N.s604"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
schema5() { "$APY" -c "import sqlite3,sys,hashlib; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); print(hashlib.md5('\n'.join(sorted(r[0] or '' for r in c.execute(\"SELECT sql FROM sqlite_master WHERE type IN ('table','index')\"))).encode()).hexdigest())" "$1" 2>/dev/null; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
sqlro() { "$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); [print('   ', *[str(x) for x in r]) for r in c.execute(sys.argv[2]).fetchall()]" "$1" "$2" 2>/dev/null | mask; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting $N back"
  \cp -p "$BAK" "$FIN/$N"
  rm -f "$STG"
  if [ "$STEPPED" = 1 ]; then say "   the data step undone from its audit row:"; "$APY" -B "$KDIR/data_s604.py" --db "$DB" --undo 2>&1 | mask | sed 's/^/     /'; fi
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  say "   $FIN/$N $(m5 "$FIN/$N") (expected $FROM)"
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK"
  rm -f "$OFFSW"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort cmp crontab diff; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"
{ { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } || { say "!! [1/12] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
[ -f "$FIN/$N" ] || { say "!! [1/12] $FIN/$N is not there - nothing installed"; exit 1; }
[ "$(m5 "$KDIR/marg_txt.py")" = "${TO[marg_txt.py]}" ] || { say "!! [1/12] the kit's marg_txt.py is not at its TO pin - nothing installed"; exit 1; }
[ -f "$S603KIT/walk_s603.py" ] && ( cd "$S603KIT" && md5sum -c SUMS.md5 >/dev/null 2>&1 ) || { say "!! [1/12] S603's kit is not at $S603KIT or fails its SUMS (its walk is run on the NEW file) - nothing installed"; exit 1; }
[ -n "$TEXT" ] && [ -f "$TEXT" ] && [ "$(m5 "$TEXT")" = "$TEXT_MD5" ] || { say "!! [1/12] S604_TEXT must name this morning's refused text (md5 ${TEXT_MD5:0:8}) - nothing installed"; exit 1; }
if [ "$(m5 "$FIN/$N")" = "${TO[$N]}" ]; then say "-- ALREADY INSTALLED: $N is the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; "$APY" -B "$KDIR/data_s604.py" --db "$DB" --show 2>&1 | mask; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/12] DRY RUN: kit gates green (SUMS, KIT_ID, PINS, the reader's pin, S603's kit, the text, the window); no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] kit gates green (SUMS, KIT_ID, PINS, S603's kit, the text, the window); the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/12] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi

C="$(m5 "$FIN/$N")"; [ "$C" = "$FROM" ] || { say "!! [2/12] $FIN/$N is $C, expected $FROM - it changed after the brief: STOP, nothing installed"; exit 1; }
say "[2/12] live pin exact: $N ${FROM:0:8}"
say "       the read-only files' live md5s (the brief, section 1):"
for n in amir_day.py stock_app.py stock_watch.py amir_salts.py marg_purchase_rows.py supplier_msg.py packs.py bank_sms.py export_watch.py reports_tile.py marg_door.py; do
  C="$(m5 "$FIN/$n")"; say "         $n $C"
  [ "$C" = "${READ[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"; exit 1; }
done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SPN/spine.db" ] && [ -f "$SPN/spine_state.json" ] && [ -f "$POR/tile_grants.json" ] && [ -f "$POR/clinic_users.py" ] && [ -f "$MARG/lib/marg_purchase.py" ] || { say "!! [2/12] a database, the spine, the portal or the ingest reader is missing - nothing installed"; exit 1; }
CRONN="$(crontab -l 2>/dev/null | wc -l | awk '{print $1}')"
say "       the crontab: $CRONN lines (proved unmoved below)"
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] && [ "$SP_AGE" -le 30 ] \
  || { say "!! [2/12] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - nothing installed (charter 1b)"; exit 4; }
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json")
for n in amir_day.py stock_app.py stock_watch.py amir_salts.py marg_purchase_rows.py supplier_msg.py packs.py bank_sms.py export_watch.py reports_tile.py marg_door.py; do NOTT+=("$FIN/$n"); done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"; SCHEMA0="$(schema5 "$SPN/spine.db")"; FSCHEMA0="$(schema5 "$DB")"
[ -n "$SCHEMA0" ] && [ -n "$FSCHEMA0" ] || { say "!! [2/12] a schema could not be read - nothing installed"; exit 1; }
say "       charter 1b: the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago); spine.db schema $SCHEMA0; finance.db schema $FSCHEMA0"
say "       F-510, the live facts read from the live database (read only) at $(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M:%S IST'):"
say "         September's purchase_export rows received since 01-Oct (type, period, stamp, received, rows, grand, live, md5):"
sqlro "$DB" "SELECT type, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p, superseded_by IS NULL, substr(md5,1,8) FROM purchase_export WHERE received_at>='2026-10-01' AND period_from<='2026-09-30' AND period_to>='2026-09-01' ORDER BY received_at"
say "         bills 542 / 579 (and every 14538):"
"$APY" -B "$KDIR/data_s604.py" --db "$DB" --show 2>&1 | mask | sed 's/^/      /'
say "         mi_file REFUSED purchase rows since 19-Oct:"
sqlro "$DB" "SELECT received_at, verdict, substr(md5,1,8), reason FROM mi_file WHERE verdict='REFUSED' AND reason LIKE 'the medical PC refused it: PURCHASE text%' AND received_at>='2026-10-19' ORDER BY received_at"
say "         the pay lines:"
sqlro "$DB" "SELECT month, vendor_norm, carry_fwd_p, paid_p, COALESCE(note,''), updated_by, updated_at FROM purchase_pay_line ORDER BY month, vendor_norm"
say "         purchase_month:"
sqlro "$DB" "SELECT month, status, finalised_by, finalised_at FROM purchase_month ORDER BY month"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s604.py walk_s604.py data_s604.py marg_txt.py || { say "!! [3/12] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s604.py --finance "$FIN" --out "$SCR/built" > "$SCR/make.txt" || { cat "$SCR/make.txt"; say "!! [4/12] the builder refused the live file - nothing installed"; exit 1; }
[ "$(m5 "$SCR/built/$N")" = "${TO[$N]}" ] || { say "!! [4/12] rebuilt, $N is $(m5 "$SCR/built/$N"), not ${TO[$N]} - nothing installed"; exit 1; }
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$N" || { say "!! [3/12] the built $N does not compile on $py - nothing installed"; exit 1; }; done
say "[3/12] the kit's python files and the built $N compile on $APY and $VPY"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits): $N at its TO pin ${TO[$N]:0:8}"

copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" && copydb "$SPN/spine.db" "$SCR/spine.db" || { say "!! [5/12] no copy of the databases - nothing installed"; exit 1; }
mkside() {   # $1 = side: a copy of the live finance code (spine folder included), a portal copy (never the live secret or user store), the ingest reader, the databases
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive" "$d/marg_ingest/lib" "$d/portal"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -p "$MARG"/lib/*.py "$d/marg_ingest/lib/" || return 1
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$d/portal/"; done
  cp -p "$POR/tile_grants.json" "$d/portal/" || return 1; cp -rp "$POR/forms" "$d/portal/" 2>/dev/null
  cp -p "$SCR/base.db" "$d/f.db" && cp -p "$SCR/base.db" "$d/f603.db" && cp -p "$SCR/base_a.db" "$d/a.db" && cp -p "$SCR/spine.db" "$d/finance/spine/spine.db"
  mkdir -p "$d/por603" && cp -rp "$d/portal/." "$d/por603/"
  cp -p "$TEXT" "$d/text.txt" && cp -p "$KDIR/marg_txt.py" "$d/marg_txt_s604.py"
}
for side in new old; do mkside "$side" || { say "!! [5/12] no scratch side '$side' - nothing installed"; exit 1; }; done
cp -p "$SCR/built/$N" "$SCR/new/finance/$N"
say "[5/12] scratch: the finance folder twice (NEW with the built file, OLD as it is), a portal copy per side, finance.db (this walk's and S603's), assets.db and the spine by the backup API, the text"
walk() { ( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s604.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/portal" \
           --reader "$SCR/$1/marg_txt_s604.py" --text "$SCR/$1/text.txt" --kit "$KDIR" --dump "$SCR/dump_$1" "${@:2}" 2>&1 ); }
ROUT="$(walk old --expect-red)"; RRC=$?
WOUT="$(walk new --old-dump "$SCR/dump_old")"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S604"; then say "!! [6/12] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | mask | grep -E "^  RED on the old file:|^  FAIL C:|^WALK OK negative|^NEGATIVE CONTROL|^  NOT RED|^WALK RED" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/12] the negative control did not go red on the old file - the walk proves nothing; nothing installed"; echo "$ROUT" | mask | tail -30; exit 1; fi
[ "$(m5 "$FIN/$N")" = "$FROM" ] || { say "!! [6/12] $FIN/$N changed during the walk - nothing installed"; exit 1; }
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old file: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S604: //')"
say "       S603's walk (walk_s603.py, whole) on the NEW file and on the OLD file -- its check lines must be the same on both (this kit changes nothing"
say "       it sees; on 20-Oct its walk is red on the untouched live files too: the live copy now carries real open visit days its scenarios did not expect):"
w603() { ( cd /tmp && timeout 2400 "$APY" -B "$S603KIT/walk_s603.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f603.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por603" --duty-map "$S603KIT/DUTY_MAP.json" --dump "$SCR/dump603_$1" 2>&1 ); }
W603N="$(w603 new)"; W603O="$(w603 old)"
find "$S603KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
w603lines() { grep -E '^  (ok|FAIL) ' | sed -E 's/[0-9]+\.[0-9]+s/N.Ns/g; s/[0-9]{2}:[0-9]{2}(:[0-9]{2})?/HH:MM/g; s/\(200, [0-9]+ bytes\)/(200, N bytes)/'; }
echo "$W603N" | w603lines > "$SCR/w603_new.txt"
echo "$W603O" | w603lines > "$SCR/w603_old.txt"
say "         NEW: $(echo "$W603N" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-60)... ($(grep -c '^  FAIL ' "$SCR/w603_new.txt") FAIL line(s) of $(wc -l < "$SCR/w603_new.txt"))"
say "         OLD: $(echo "$W603O" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-60)... ($(grep -c '^  FAIL ' "$SCR/w603_old.txt") FAIL line(s) of $(wc -l < "$SCR/w603_old.txt"))"
[ -s "$SCR/w603_new.txt" ] || { say "!! [6/12] S603's walk printed no check line - nothing installed"; exit 1; }
if ! cmp -s "$SCR/w603_new.txt" "$SCR/w603_old.txt"; then say "!! [6/12] S603's walk reads differently on the NEW file than on the OLD file - nothing installed"; diff "$SCR/w603_old.txt" "$SCR/w603_new.txt" | mask | head -20; exit 1; fi
grep '^  FAIL ' "$SCR/w603_new.txt" | mask | cut -c1-200 | sed 's/^/         (both sides, today'"'"'s data) /'
say "         S603's walk: $(wc -l < "$SCR/w603_new.txt") check lines identical on both sides"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the scratch sides and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

# ---- 7: the install-day state on the OLD and the NEW file (fresh copies of the live database) -----------------------------------------------
statelook() {   # $1 = a scratch finance folder, or LIVE (a fresh scratch copy of /root/finance as it stands); $2 = label
  local d="$SCR/st_$2" fin="$1"; mkdir -p "$d"
  if [ "$1" = LIVE ]; then
    mkside "st_$2" >/dev/null 2>&1 || return 1
    copydb "$SPN/spine.db" "$d/finance/spine/spine.db" || return 1
    fin="$d/finance"
  fi
  copydb "$DB" "$d/f.db" || return 1
  ( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s604.py" --state --label "$2" --fin "$fin" --db "$d/f.db" --adb "$SCR/base_a.db" --marg "$SCR/new/marg_ingest" --kit "$KDIR" 2>&1 ) | mask
}
say "[7/12] the install-day state BEFORE (the live file on a copy) and as the NEW file reads the same copy (charter 7):"
SB="$(statelook "$SCR/old/finance" before)"; echo "$SB" | grep -E "^STATE|^   " | sed 's/^/ /'
SN="$(statelook "$SCR/new/finance" new)"; echo "$SN" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SB" | grep -q "^STATE OK S604" && echo "$SN" | grep -q "^STATE OK S604" || { say "!! [7/12] the install-day state could not be read - nothing placed"; exit 1; }
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 8: backups ---------------------------------------------------------------------------------------------------------------------------
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [8/12] database backup failed - nothing placed"; exit 1; }
\cp -p "$FIN/$N" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! [8/12] the backup of $N is not the live file - nothing placed"; exit 1; }
say "[8/12] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(basename "$BAK")"

# ---- 9-10: the file placed, the data step, one restart -----------------------------------------------------------------------------------------
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || { say "!! [9/12] could not write $OFFSW - nothing placed"; exit 1; }
{ \cp -p "$FIN/$N" "$STG" && cat "$SCR/built/$N" > "$STG" && [ "$(m5 "$STG")" = "${TO[$N]}" ]; } || { rm -f "$STG" "$OFFSW"; say "!! [9/12] could not stage $N - nothing placed"; exit 1; }
PLACED=1
mv -f "$STG" "$FIN/$N" || restore "placing $N"
[ "$(m5 "$FIN/$N")" = "${TO[$N]}" ] && cmp -s "$FIN/$N" "$SCR/built/$N" || restore "$N did not land at its pin"
say "[9/12] placed by rename; md5 read back: $N $(m5 "$FIN/$N") (= the kit's TO pin, byte-identical to the walked file)"
DS="$("$APY" -B "$KDIR/data_s604.py" --db "$DB" 2>&1)"; DSRC=$?
echo "$DS" | mask | sed 's/^/       /'
echo "$DS" | grep -q "^DATA S604: DONE" && STEPPED=1
[ "$DSRC" = 0 ] || restore "the data step refused (exit $DSRC)"
say "       the data step: $(echo "$DS" | grep '^DATA S604' | head -1)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/purchase/page/pay/2026-09); c3=$(health /finance/purchase/page/hub); c4=$(health /finance/purchase/page/month/2026-09); c5=$(health /finance/amir); c6=$(health /finance/reports/aaj)
for c in "$c2" "$c3" "$c4" "$c5" "$c6"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): pay/2026-09 $c2 / hub $c3 / month/2026-09 $c4 / amir $c5 / reports-aaj $c6";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[10/12] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /purchase/page/pay/2026-09 $c2, /page/hub $c3, /page/month/2026-09 $c4, /amir $c5, /reports/aaj $c6 without a login (302 = the login gate, expected) - journal clean"

# ---- 11: the state AFTER; nothing else moved --------------------------------------------------------------------------------------------------
say "[11/12] the install-day state AFTER placing (the live file, a fresh copy of the live database; the box's clock in the first STATE line):"
SA_="$(statelook LIVE after)"; echo "$SA_" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SA_" | grep -q "^STATE OK S604" || restore "the state after placing could not be read"
echo "$SA_" | grep -q "^STATE after: files NEW (S604)" || restore "the state after placing does not read the NEW file"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(schema5 "$SPN/spine.db")" = "$SCHEMA0" ] || restore "spine.db's schema moved"
[ "$(schema5 "$DB")" = "$FSCHEMA0" ] || restore "finance.db's schema moved -- this kit has no DDL"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
rm -f "$OFFSW"
say "        nothing else moved (the read-only files, finance_app, portal.py, tile_grants.json, the crontab, the spine's and finance.db's schemas); healthz 200; $OFFSW removed"

find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[12/12] md5 read back:"
md5sum "$FIN/$N"
say "$KIT: DONE (the server half). The build lock stays held by $KIT until the report is written (release: rm -f $LOCK/owner; rmdir $LOCK)."
say "undo (the file): \\cp -p $BAK $FIN/$N && $SYSTEMCTL restart $SVC ; the data step: $APY -B $KDIR/data_s604.py --db $DB --undo (from its audit row)"
exit 0
