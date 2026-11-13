#!/bin/bash
# =============================================================================
#  install_S810_MARG_DOOR_STORE_RULE.sh · kit S810 (13-Nov-2026, Sanjeevni session 441) · the owner's "ok" 06:42 IST (D913)
#  A Marg stock report of one store (MAIN STORE, DTH, SCRAP STORE, or stores without WHOLE) was filed as good.
#  1. /root/marg_ingest/marg_router.py  318086e3 -> TO : verify() refuses a closing stock, stock valuation or batch
#     stock whose title names no WHOLE store, the store named: "MAIN STORE only -- the WHOLE STORES report is needed".
#  2. /root/finance/reports_tile.py     4eaeadbd -> TO : the staff tile says it in Hindi: "Yeh sirf MAIN STORE ki
#     report hai. Select Store mein WHOLE chuniye, phir dobara nikaaliye."          clinic-finance is restarted.
#  Both files are REBUILT HERE from the live bytes by make_s810.py (exact anchors) and checked against the TO pins.
#  The same marg_router.py goes to manojz (D:\Downloads\margsync\MargPull\) -- placed by Claude after this.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s810kit && cp -rp /root/deploy/repo/deploy_kits/S810_MARG_DOOR_STORE_RULE /tmp/s810kit && bash /tmp/s810kit/install_S810_MARG_DOOR_STORE_RULE.sh
#  (DRY=1 before bash: every gate, the walk and its control; NOTHING written.)
# =============================================================================
set -u
KIT="S810_MARG_DOOR_STORE_RULE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FR="marg_ingest/marg_router.py"; FT="finance/reports_tile.py"
FROM_R="318086e36b0088f2da57b95d19a86b98"; FROM_T="4eaeadbdbb7ea02c14849ff03ebaa42b"
TO_R="$(awk -v f="$FR" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; TO_T="$(awk -v f="$FT" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s810_inst_$STAMP"; TOOK_LOCK=0; PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK_R="$ROOT/$FR.bak_S810_${FROM_R:0:8}"; BAK_T="$ROOT/$FT.bak_S810_${FROM_T:0:8}"
STG_R="$ROOT/marg_ingest/.marg_router.py.s810"; STG_T="$ROOT/finance/.reports_tile.py.s810"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG_R" "$STG_T"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting both files back"; PLACED=2
  \cp -p "$BAK_R" "$ROOT/$FR"; \cp -p "$BAK_T" "$ROOT/$FT"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   marg_router.py $(m5 "$ROOT/$FR" | cut -c1-8) (expected ${FROM_R:0:8}) · reports_tile.py $(m5 "$ROOT/$FT" | cut -c1-8) (expected ${FROM_T:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
walk() { (cd /tmp && PYTHONPATH="$3:$ROOT/marg_ingest:$ROOT/finance${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s810.py" "$1" "$2" $4 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO_R" ] && [ -n "$TO_T" ] && [ -f "$ROOT/$FR" ] && [ -f "$ROOT/$FT" ] && [ -f "$ROOT/marg_ingest/signatures.json" ] || { say "!! [1/6] a TO pin, $ROOT/$FR, $ROOT/$FT or signatures.json missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$FR")" = "$TO_R" ] && [ "$(m5 "$ROOT/$FT")" = "$TO_T" ]; then say "-- $KIT is ALREADY INSTALLED (marg_router.py ${TO_R:0:8}, reports_tile.py ${TO_T:0:8}); nothing to do."; exit 0; fi
mkdir -p "$SCR/built" "$SCR/r" "$SCR/t" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$FR")" = "$FROM_R" ] || stop "!! [2/6] $ROOT/$FR is $(m5 "$ROOT/$FR" | cut -c1-8), expected ${FROM_R:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
[ "$(m5 "$ROOT/$FT")" = "$FROM_T" ] || stop "!! [2/6] $ROOT/$FT is $(m5 "$ROOT/$FT" | cut -c1-8), expected ${FROM_T:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
"$APY" -B make_s810.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/6] the builder refused - nothing installed"; }
[ "$(m5 "$SCR/built/marg_router.py")" = "$TO_R" ] && [ "$(m5 "$SCR/built/reports_tile.py")" = "$TO_T" ] || stop "!! [2/6] rebuilt, the files are not at their TO pins - nothing installed"
for py in "$APY" "$VPY"; do for f in marg_router.py reports_tile.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop "!! [2/6] $f does not compile on $py - nothing installed"; done; done
say "[2/6] live pins exact (${FROM_R:0:8}, ${FROM_T:0:8}); rebuilt here at their TO pins (${TO_R:0:8}, ${TO_T:0:8}); both compile on both pythons"
\cp -p "$SCR/built/marg_router.py" "$SCR/r/"; \cp -p "$ROOT/marg_ingest/signatures.json" "$SCR/r/"; \cp -p "$SCR/built/reports_tile.py" "$SCR/t/"
O=$(walk "$SCR/r" "$SCR/t" "$SCR/r" ""); R=$(printf '%s\n' "$O" | tail -1)
[ "$R" = "WALK S810 GREEN" ] || { printf '%s\n' "$O" | grep -E "RED|Error|Traceback" | head -8 | sed 's/^/      /'; stop "!! [3/6] the walk: $R - nothing installed"; }
O0=$(walk "$ROOT/marg_ingest" "$ROOT/finance" "$ROOT/marg_ingest" "--control"); R0=$(printf '%s\n' "$O0" | tail -1)
[ "$R0" = "CONTROL S810 RED as it must be" ] || { printf '%s\n' "$O0" | tail -4 | sed 's/^/      /'; stop "!! [3/6] the control: $R0 - nothing installed"; }
say "[3/6] walk_s810: $(printf '%s\n' "$O" | tail -2 | head -1) -- $R; its control on the live files red as it must be"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the control green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$FR" "$BAK_R" && [ "$(m5 "$BAK_R")" = "$FROM_R" ] && \cp -p "$ROOT/$FT" "$BAK_T" && [ "$(m5 "$BAK_T")" = "$FROM_T" ]; } || stop "!! [4/6] could not write the backups - nothing placed"
{ cat "$SCR/built/marg_router.py" > "$STG_R" && chmod --reference="$ROOT/$FR" "$STG_R" 2>/dev/null; chown --reference="$ROOT/$FR" "$STG_R" 2>/dev/null; [ "$(m5 "$STG_R")" = "$TO_R" ]; } || stop "!! [4/6] could not stage the router - nothing placed"
{ cat "$SCR/built/reports_tile.py" > "$STG_T" && chmod --reference="$ROOT/$FT" "$STG_T" 2>/dev/null; chown --reference="$ROOT/$FT" "$STG_T" 2>/dev/null; [ "$(m5 "$STG_T")" = "$TO_T" ]; } || stop "!! [4/6] could not stage the tile - nothing placed"
PLACED=1
mv -f "$STG_R" "$ROOT/$FR" || restore "the rename of the router"
mv -f "$STG_T" "$ROOT/$FT" || restore "the rename of the tile"
[ "$(m5 "$ROOT/$FR")" = "$TO_R" ] && [ "$(m5 "$ROOT/$FT")" = "$TO_T" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
say "[4/6] placed and read back: marg_router.py ${TO_R:0:8}, reports_tile.py ${TO_T:0:8}; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
ST=$(cd "$SCR" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$APY" -W ignore -B "$ROOT/$FR" --selftest 2>&1 | tail -1)
[ "$ST" = "SELFTEST OK" ] || restore "the router's own selftest in place: $ST"
O2=$(walk "$ROOT/marg_ingest" "$ROOT/finance" "$ROOT/marg_ingest" ""); R2=$(printf '%s\n' "$O2" | tail -1)
[ "$R2" = "WALK S810 GREEN" ] || restore "the walk on the placed files: $R2"
release_lock
say "[5/6] in place: the router's own selftest OK; walk_s810 on the placed files: GREEN"
say "[6/6] undo (one line): \\cp -p $BAK_R $ROOT/$FR && \\cp -p $BAK_T $ROOT/$FT && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. A stock report of one store is now refused when it arrives, and Shavez's tile says in Hindi to choose WHOLE."
exit 0
