#!/bin/bash
# =============================================================================
#  install_S631_SET_ASIDE_SCANS_R2.sh · kit S631 (22-Oct-2026, Sanjeevni session 339) · the owner's question 19:01 IST
#  S631 = S630 re-issued (S630 frozen: published, then refused by its own negative control -- nothing installed): the SAME two built files;
#  the walk lays its own family of scans (walk_s631.py). Under set -u, not set -e: every gate is a test.
#  The order list never offers "Send back for rescan" on a scan the scan app has SET ASIDE (a copy / rejected -- the server refuses it), and
#  never names a set-aside scan in "The same paper scanned twice". The clearer copy still feeds the order list's notes (S628).
#
#   /root/finance/order_track.py    4edfef6b -> TO in TO_PINS.md5   (_aside; the flags on each scan; same_paper skips set-aside scans)
#   /root/finance/porders_s454.py   0ce83525 -> TO                   (_s628_send_back: the tied scan when its clearer copy is set aside)
#  finance.db: not written. No setting, no DDL, no crontab change, no other file. One restart of clinic-finance.
#  ORDER: gates -> lock -> pins -> build from the live bytes (make_s630.py) -> compile (both pythons) -> scratch copies -> walk NEW green, OLD
#  red on every control -> DRY stops -> backups -> DOCTOR_AUTO_OFF -> staged + renamed -> md5 read back -> ONE restart -> healthz, the track
#  page 302 without a login, journal clean -> DOCTOR_AUTO_OFF removed -> lock released -> DONE. Red after placing: both files back, restart.
# =============================================================================
# =============================================================================
set -u
KIT="S631_SET_ASIDE_SCANS_R2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
DB="${DB:-$FIN/finance.db}"
ADB="${ADB:-/root/assetapp/assets.db}"
SHD="${SHD:-/root/shared}"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EFIN="order_track.py porders_s454.py"
NEWF=""
declare -A FROM TO
FROM[order_track.py]=4edfef6b21b0734b79028d0bf6e3930e
FROM[porders_s454.py]=0ce8352597a0c2a45ba977c7ebf510ed
while read -r h f; do TO[$f]=$h; done < "$KDIR/TO_PINS.md5"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s631_inst_$STAMP"
DBBAK="$DB.bak_S631_$STAMP"
PLACED=0; TOOK_LOCK=0; OFF_MINE=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
bak() { echo "$FIN/$1.bak_S631_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting every file back"
  for n in $EFIN; do \cp -p "$(bak "$n")" "$FIN/$n" || say "   !! could not put back $n"; done
  rm -f "$FIN"/.*.s631
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EFIN; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   finance healthz $h; the database was never written by this kit"
  [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep sleep find sed timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
{ { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } \
  || { say "!! [1/9] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $EFIN; do [ -f "$FIN/$n" ] || { say "!! [1/9] $FIN/$n is not there - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$FIN/spine/spine.db" ] || { say "!! [1/9] a database or the spine is missing - nothing installed"; exit 1; }
ALL=1; for n in $EFIN; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: both files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/9] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/9] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

for n in $EFIN; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || stop_unlocked "!! [2/9] $FIN/$n is $C, expected ${FROM[$n]} - it changed after this kit was built: STOP, nothing installed"; done
say "[2/9] live pins exact: $(for n in $EFIN; do printf '%s %s . ' "$n" "${FROM[$n]:0:8}"; done)"
say "       read only (not pinned): order_sheet.py $(m5 "$FIN/order_sheet.py" | cut -c1-8) . stock_watch.py $(m5 "$FIN/stock_watch.py" | cut -c1-8) . purchase_app.py $(m5 "$FIN/purchase_app.py" | cut -c1-8) . scan_quality.py $(m5 "$SHD/scan_quality.py" | cut -c1-8)"

mkdir -p "$SCR/built" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s630.py --finance "$FIN" --out "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/9] the builder refused a live file - nothing installed"; }
for n in $EFIN $NEWF; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || stop_unlocked "!! [3/9] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; done
for py in "$APY" "$VPY"; do for n in $EFIN $NEWF; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || stop_unlocked "!! [3/9] the built $n does not compile on $py - nothing installed"; done; done
say "[3/9] rebuilt here from this box's live bytes: each at its TO pin; compiles under both pythons"

copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" && copydb "$FIN/spine/spine.db" "$SCR/spine_live.db" || stop_unlocked "!! [4/9] no copy of the databases - nothing installed"
mkside() {
  local d="$SCR/$1"; mkdir -p "$d/fin/spine" "$d/fin/finance_ui" "$d/marg/lib" "$d/marg/archive" "$d/shared" "$d/por"
  cp -p "$FIN"/*.py "$d/fin/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/fin/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/fin/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$d/fin/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg/" 2>/dev/null; done
  cp -p "$MARG"/lib/*.py "$d/marg/lib/" 2>/dev/null; cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg/archive/" 2>/dev/null
  cp -p "$SHD"/*.py "$d/shared/" 2>/dev/null
  for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$d/por/"; done
  cp -p "$POR/tile_grants.json" "$d/por/" 2>/dev/null; cp -rp "$POR/forms" "$d/por/" 2>/dev/null
  cp -p "$SCR/base.db" "$d/finance.db" && cp -p "$SCR/base_a.db" "$d/assets.db" && cp -p "$SCR/spine_live.db" "$d/fin/spine/spine.db"
}
for side in new old; do rm -rf "$SCR/$side"; mkside "$side" || stop_unlocked "!! [4/9] no scratch side '$side' - nothing installed"; done
for n in $EFIN $NEWF; do cp -p "$SCR/built/$n" "$SCR/new/fin/$n"; done
say "[4/9] scratch: finance.db, assets.db and the spine by the backup API; the finance folder twice -- NEW (the built files) and OLD (as they are)"
w628() { ( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s631.py" --fin "$SCR/$1/fin" --db "$SCR/$1/finance.db" --adb "$SCR/$1/assets.db" --shared "$SCR/$1/shared" \
           --por "$SCR/$1/por" --marg "$SCR/$1/marg" "${@:2}" 2>&1 ) | mask; }
w628 new > "$SCR/walk_new.txt"; w628 old --expect-red > "$SCR/walk_old.txt"
say "       walk NEW: $(grep '^WALK' "$SCR/walk_new.txt") . walk OLD: $(grep '^WALK' "$SCR/walk_old.txt")"
grep -q "^WALK OK S631" "$SCR/walk_new.txt" || { cat "$SCR/walk_new.txt"; stop_unlocked "!! [5/9] the walk on the NEW files is red - nothing installed"; }
grep -q "^WALK NEGATIVE CONTROL RED S631" "$SCR/walk_old.txt" || { cat "$SCR/walk_old.txt"; stop_unlocked "!! [5/9] the negative control is not red on the OLD files - nothing installed"; }
say "[5/9] the walks: NEW green, OLD red on every control"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and both walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

for n in $EFIN; do \cp -p "$FIN/$n" "$(bak "$n")" && [ "$(m5 "$(bak "$n")")" = "${FROM[$n]}" ] || stop_unlocked "!! [6/9] could not write the backup of $n - nothing placed"; done
if [ -e "$OFFSW" ]; then
  say "       $OFFSW was already on ($(head -c 120 "$OFFSW" 2>/dev/null)) -- left exactly as found"
else
  mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" && OFF_MINE=1 || stop_unlocked "!! [6/9] could not write $OFFSW - nothing placed"
fi
for n in $EFIN $NEWF; do
  STG="$FIN/.$n.s631"
  { cat "$SCR/built/$n" > "$STG" && [ "$(m5 "$STG")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s631; [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; stop_unlocked "!! [6/9] could not stage $n - nothing placed"; }
  [ -f "$FIN/$n" ] && chmod --reference="$FIN/$n" "$STG" 2>/dev/null; [ -f "$FIN/$n" ] && chown --reference="$FIN/$n" "$STG" 2>/dev/null
done
PLACED=1
for n in $EFIN $NEWF; do mv -f "$FIN/.$n.s631" "$FIN/$n" || restore "the rename of $n"; [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "the md5 read back of $n"; done
say "[6/9] placed and read back: $(for n in $EFIN $NEWF; do printf '%s %s . ' "$n" "${TO[$n]:0:8}"; done)(backups *.bak_S631_<from8>)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000; for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/porders/s454/track); c3=$(health /finance/porders/s454/scans)
case "$c2$c3" in 302302|401401|303303|302401|401302) ;; *) restore "the track / scans pages answered $c2 / $c3 without a login (302 = the login gate, expected)";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[7/9] $SVC restarted at $T0 (the box's clock) and active - healthz $c1 - track $c2, scans $c3 without a login; journal clean"

if [ "$OFF_MINE" = 1 ]; then rm -f "$OFFSW"; say "[8/9] $OFFSW removed (this kit's)"; else say "[8/9] $OFFSW not this kit's -- left as found"; fi
release_lock
say "[9/9] the build lock released"
UNDO=""; for n in $EFIN; do UNDO="$UNDO\\cp -p $(bak "$n") $FIN/$n && "; done
say "undo (one line): ${UNDO}$SYSTEMCTL restart $SVC"
say "$KIT: DONE"
exit 0
