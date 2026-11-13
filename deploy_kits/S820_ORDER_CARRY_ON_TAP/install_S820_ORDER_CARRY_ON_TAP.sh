#!/bin/bash
# =============================================================================
#  install_S820_ORDER_CARRY_ON_TAP.sh · kit S820 (13-Nov-2026, Sanjeevni session 451) · the owner's "Go" 18:15 IST
#  An undelivered medicine no longer rides on the dealer's next order by itself (S619's carry); it waits in the red "Purane order"
#  box and goes to the dealer only on "Dobara order karo". A setting order.carry_on_card (0 now; 1 = as before) on his settings card.
#  1. /root/finance/order_sheet.py   53abf461 -> TO : the setting; entries() puts the open carries on a card only at 1
#  2. /root/finance/order_s778.py    819f60ff -> TO : an undelivered line is in the box at once (not after three working days)
#  3. /root/finance/porders_s454.py  21bf0abc -> TO : the settings card accepts 0 / 1 for it
#  4. /root/finance/order_track.py   6f4746c5 -> TO : the short line, Darpan's line, the owner's Needs-you line follow the setting
#  5. /root/finance/order_track_page.py 4e6bd715 -> TO : the order list's short section names the box      clinic-finance is restarted.
#  The five files are REBUILT HERE from the live bytes by make_s820.py and checked against the TO pins. No database change.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s820kit && cp -rp /root/deploy/repo/deploy_kits/S820_ORDER_CARRY_ON_TAP /tmp/s820kit && bash /tmp/s820kit/install_S820_ORDER_CARRY_ON_TAP.sh
#  (DRY=1 before bash: every gate, the walk and its control; NOTHING written.)
# =============================================================================
set -u
KIT="S820_ORDER_CARRY_ON_TAP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FILES="order_sheet.py order_s778.py porders_s454.py order_track.py order_track_page.py"
declare -A FROM=( [order_sheet.py]="53abf46175d3f22eb834be246e2233f6" [order_s778.py]="819f60ff71a0dfae73e1c36689082037" [porders_s454.py]="21bf0abc4ab46aeeca90d644ac8c1598" [order_track.py]="6f4746c570323942bffb0d5eea4b3cba" [order_track_page.py]="4e6bd715a27ecf64833107abf5c4fa76" )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="finance/$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s820_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/finance/$1.bak_S820_${FROM[$1]:0:8}"; }
stg() { echo "$ROOT/finance/.$1.s820"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
pins() { local s=""; for f in $FILES; do s="$s $f $(m5 "$ROOT/finance/$f" | cut -c1-8)"; done; echo "$s"; }
restore() { say "!! RED after placing ($1) - putting the five files back"
  for f in $FILES; do \cp -p "$(bak "$f")" "$ROOT/finance/$f"; done; "$SYSTEMCTL" restart "$FSVC" || true
  say "   now:$(pins) (expected the FROM pins: ${FROM[order_sheet.py]:0:8} ${FROM[order_s778.py]:0:8} ${FROM[porders_s454.py]:0:8} ${FROM[order_track.py]:0:8} ${FROM[order_track_page.py]:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
w820() { (cd /tmp && PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s820.py" "$1" "$ROOT/finance" "$ROOT/shared" "$DB" $2 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] && [ -f "$ROOT/finance/$f" ] || { say "!! [1/6] a TO pin or $ROOT/finance/$f missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/6] $DB missing - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/finance/$f")" = "${TO[$f]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED (the five files are at their TO pins); nothing to do."; exit 0; }
mkdir -p "$SCR/built" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f")" = "${FROM[$f]}" ] || stop "!! [2/6] $ROOT/finance/$f is $(m5 "$ROOT/finance/$f" | cut -c1-8), expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
"$APY" -B make_s820.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/6] the builder refused - nothing installed"; }
for f in $FILES; do [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop "!! [2/6] rebuilt, $f is not at its TO pin - nothing installed"; done
for py in "$APY" "$VPY"; do for f in $FILES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop "!! [2/6] $f does not compile on $py - nothing installed"; done; done
say "[2/6] live pins exact; rebuilt here at their TO pins; all compile on both pythons"
O=$(w820 "$SCR/built" ""); R=$(printf '%s\n' "$O" | tail -1); [ "$R" = "WALK S820 GREEN" ] || { printf '%s\n' "$O" | grep -E "RED|Error|STOP" | head -6 | sed 's/^/      /'; stop "!! [3/6] walk_s820: $R - nothing installed"; }
O0=$(w820 "$ROOT/finance" "--control"); R0=$(printf '%s\n' "$O0" | tail -1); [ "$R0" = "CONTROL S820 RED as it must be" ] || stop "!! [3/6] the control on the live files: $R0 - nothing installed"
say "[3/6] walk_s820 on the rebuilt files (a copy of the database, made-up rows): $R; its control on the live files red as it must be"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and its control green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for f in $FILES; do { \cp -p "$ROOT/finance/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop "!! [4/6] could not write the backup of $f - nothing placed"; done
for f in $FILES; do S="$(stg "$f")"; { cat "$SCR/built/$f" > "$S" && chmod --reference="$ROOT/finance/$f" "$S" 2>/dev/null; chown --reference="$ROOT/finance/$f" "$S" 2>/dev/null; [ "$(m5 "$S")" = "${TO[$f]}" ]; } || stop "!! [4/6] could not stage $f - nothing placed"; done
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/finance/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
O4=$(w820 "$ROOT/finance" ""); R4=$(printf '%s\n' "$O4" | tail -1); [ "$R4" = "WALK S820 GREEN" ] || restore "walk_s820 on the placed files: $R4"
release_lock
say "[4/6] placed and read back:$(pins); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1; walk_s820 on the placed files GREEN"
say "[5/6] the setting order.carry_on_card is 0 (his settings card on the old Purchase orders page; 1 puts the old way back)"
U=""; for f in $FILES; do U="$U\\cp -p $(bak "$f") $ROOT/finance/$f && "; done
say "[6/6] undo (one line): ${U}$SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. A medicine that did not come now waits in the red Purane order box on reception's order screen and goes to the dealer only when they tap Dobara order karo -- it is no longer added to the next WhatsApp order by itself."
exit 0
