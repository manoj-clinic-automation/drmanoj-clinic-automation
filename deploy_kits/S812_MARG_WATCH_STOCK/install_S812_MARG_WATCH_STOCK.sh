#!/bin/bash
# =============================================================================
#  install_S812_MARG_WATCH_STOCK.sh · kit S812 (13-Nov-2026, Sanjeevni session 445) · the owner's approval of 06:42 IST (D951), floor none (D943)
#  The Marg watch, section A -- stock moved in Marg with no record:
#  1. /root/finance/marg_hand_change.py 3b8c2160 -> TO : the records behind a move (a bill changed after its day, a bill Marg took in late,
#     a voucher on a sibling, a voucher of another quantity, a sale Marg did not take off, free goods) -- such a move is "explained after
#     all", never counted, never told (D914); the late bill noted even on an unjudged day (F-1279); a rise waits for a purchase list taken
#     after its closing (F-1278); the whole-sum line (F-1270); the rupees; the floor (D943, 0 = none). Added columns only.
#  2. /root/finance/marg_billwatch.py   9be1b460 -> TO : section A on top of the Marg watch page -- the moves, his close on each row (D923),
#     the floor field, Explained after all, the stock record's own health line (F-1329). Section B is unchanged.
#  Both REBUILT HERE from the live bytes (make_s812.py, make_s812b.py), checked against the TO pins. clinic-finance is restarted, then one
#  refresh of section A runs (its own table: additive columns; what it finds the first time is history -- shown, never told).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s812kit && cp -rp /root/deploy/repo/deploy_kits/S812_MARG_WATCH_STOCK /tmp/s812kit && bash /tmp/s812kit/install_S812_MARG_WATCH_STOCK.sh
#  (DRY=1 before bash: every gate, both walks and the control; NOTHING written.)
# =============================================================================
set -u
KIT="S812_MARG_WATCH_STOCK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; SPDB="${SPDB:-$ROOT/finance/spine/spine.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FH="finance/marg_hand_change.py"; FW="finance/marg_billwatch.py"
FROM_H="3b8c216011941abe86af2bb0ce836b1e"; FROM_W="9be1b460f2ebf763af98afc7e56b068f"
TO_H="$(awk -v f="$FH" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; TO_W="$(awk -v f="$FW" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s812_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK_H="$ROOT/$FH.bak_S812_${FROM_H:0:8}"; BAK_W="$ROOT/$FW.bak_S812_${FROM_W:0:8}"
STG_H="$ROOT/finance/.marg_hand_change.py.s812"; STG_W="$ROOT/finance/.marg_billwatch.py.s812"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG_H" "$STG_W"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
HOLD_PY="import sqlite3,sys;c=sqlite3.connect(sys.argv[1],timeout=30);h={r[1] for r in c.execute('PRAGMA table_info(marg_hand_change)')};c.execute('UPDATE marg_hand_change SET hist=1 WHERE rec_kind IS NOT NULL') if 'rec_kind' in h else None;c.commit()"
restore() { say "!! RED after placing ($1) - putting both files back (section A's added columns stay; the old files ignore them)"
  "$VPY" -c "$HOLD_PY" "$DB" 2>/dev/null || true             # the old notice must never tell a move S812 had explained (review)
  \cp -p "$BAK_H" "$ROOT/$FH"; \cp -p "$BAK_W" "$ROOT/$FW"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   marg_hand_change.py $(m5 "$ROOT/$FH" | cut -c1-8) (expected ${FROM_H:0:8}) · marg_billwatch.py $(m5 "$ROOT/$FW" | cut -c1-8) (expected ${FROM_W:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
# a working copy of the finance code with the files under test, and copies of the two databases (the walk writes only to its copies)
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1/spine" && \cp -p "$ROOT"/finance/*.py "$SCR/fin_$1/" && \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/fin_$1/spine/" 2>/dev/null; }
w812() { (cd /tmp && PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s812.py" "$1" "$SCR/spine.db" "$SCR/finance.db" 2>&1); }
w803() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s803.py" "$1" "$ROOT/shared" "$ROOT/finance" "$DB" 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO_H" ] && [ -n "$TO_W" ] && [ -f "$ROOT/$FH" ] && [ -f "$ROOT/$FW" ] && [ -f "$DB" ] && [ -f "$SPDB" ] || { say "!! [1/7] a TO pin, a live file, $DB or $SPDB missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$FH")" = "$TO_H" ] && [ "$(m5 "$ROOT/$FW")" = "$TO_W" ]; then say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; fi
mkdir -p "$SCR/built" "$SCR/w803" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/7] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken by $KIT"
else say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$FH")" = "$FROM_H" ] || stop "!! [2/7] $ROOT/$FH is $(m5 "$ROOT/$FH" | cut -c1-8), expected ${FROM_H:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
[ "$(m5 "$ROOT/$FW")" = "$FROM_W" ] || stop "!! [2/7] $ROOT/$FW is $(m5 "$ROOT/$FW" | cut -c1-8), expected ${FROM_W:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
"$APY" -B make_s812.py "$ROOT/$FH" "$KDIR" "$SCR/built/marg_hand_change.py" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused (marg_hand_change) - nothing installed"; }
"$APY" -B make_s812b.py "$ROOT/$FW" "$KDIR/seg_bw_hand.py" "$SCR/built/marg_billwatch.py" >> "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused (marg_billwatch) - nothing installed"; }
[ "$(m5 "$SCR/built/marg_hand_change.py")" = "$TO_H" ] && [ "$(m5 "$SCR/built/marg_billwatch.py")" = "$TO_W" ] || stop "!! [2/7] rebuilt, the files are not at their TO pins - nothing installed"
for py in "$APY" "$VPY"; do for f in marg_hand_change.py marg_billwatch.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop "!! [2/7] $f does not compile on $py - nothing installed"; done; done
say "[2/7] live pins exact (${FROM_H:0:8}, ${FROM_W:0:8}); rebuilt here at their TO pins (${TO_H:0:8}, ${TO_W:0:8}); both compile on both pythons"
"$VPY" -B copy_dbs.py "$DB" "$SCR/finance.db" >/dev/null && "$VPY" -B copy_dbs.py "$SPDB" "$SCR/spine.db" >/dev/null || stop "!! [3/7] could not copy the databases for the walk - nothing installed"
mkfin new && \cp -p "$SCR/built/marg_hand_change.py" "$SCR/built/marg_billwatch.py" "$SCR/fin_new/" || stop "!! [3/7] could not lay out the walk - nothing installed"
O=$(w812 "$SCR/fin_new"); R=$(printf '%s\n' "$O" | tail -1); N=$(printf '%s\n' "$O" | grep -c '^PASS')
printf '%s\n' "$O" | grep -E "^FAIL|Error" | head -8 | sed 's/^/      /'
case "$R" in "WALK "*) A=${R#WALK }; [ "${A%/*}" = "${A#*/}" ] || stop "!! [3/7] walk_s812: $R - nothing installed";; *) stop "!! [3/7] walk_s812 did not finish: $R - nothing installed";; esac
mkfin old; "$VPY" -B copy_dbs.py "$DB" "$SCR/finance.db" >/dev/null
O0=$(w812 "$SCR/fin_old"); F0=$(printf '%s\n' "$O0" | grep -c '^FAIL'); [ "$F0" -ge 10 ] || stop "!! [3/7] the control on the live files went red on only $F0 checks - nothing installed"
\cp -p "$SCR/built/marg_billwatch.py" "$SCR/w803/"; \cp -p "$ROOT/finance/sanjeevni_approvals.py" "$ROOT/finance/owner_notice.py" "$ROOT/finance/finance_ui/finance_approvals.html" "$SCR/w803/"
O3=$(w803 "$SCR/w803"); R3=$(printf '%s\n' "$O3" | tail -1); [ "$R3" = "WALK S803 GREEN" ] || { printf '%s\n' "$O3" | grep -E "RED|Error" | head -6 | sed 's/^/      /'; stop "!! [3/7] the Marg watch's own walk (S803) on the rebuilt page: $R3 - nothing installed"; }
say "[3/7] walk_s812 on copies of the live databases: $R (control on the live files: $F0 red); the Marg watch's own walk S803 on the rebuilt page: $R3"
printf '%s\n' "$O" | grep -E "counted \(got|newer moves" | sed 's/^/      /'
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, both walks and the control green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/7] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$FH" "$BAK_H" && [ "$(m5 "$BAK_H")" = "$FROM_H" ] && \cp -p "$ROOT/$FW" "$BAK_W" && [ "$(m5 "$BAK_W")" = "$FROM_W" ]; } || stop "!! [4/7] could not write the backups - nothing placed"
{ cat "$SCR/built/marg_hand_change.py" > "$STG_H" && chmod --reference="$ROOT/$FH" "$STG_H" 2>/dev/null; chown --reference="$ROOT/$FH" "$STG_H" 2>/dev/null; [ "$(m5 "$STG_H")" = "$TO_H" ]; } || stop "!! [4/7] could not stage - nothing placed"
{ cat "$SCR/built/marg_billwatch.py" > "$STG_W" && chmod --reference="$ROOT/$FW" "$STG_W" 2>/dev/null; chown --reference="$ROOT/$FW" "$STG_W" 2>/dev/null; [ "$(m5 "$STG_W")" = "$TO_W" ]; } || stop "!! [4/7] could not stage - nothing placed"
mv -f "$STG_H" "$ROOT/$FH" || restore "the rename of marg_hand_change.py"
mv -f "$STG_W" "$ROOT/$FW" || restore "the rename of marg_billwatch.py"
[ "$(m5 "$ROOT/$FH")" = "$TO_H" ] && [ "$(m5 "$ROOT/$FW")" = "$TO_W" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/7]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
say "[4/7] placed and read back: marg_hand_change.py ${TO_H:0:8}, marg_billwatch.py ${TO_W:0:8}; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
RF=$(cd "$ROOT/finance" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B marg_hand_change.py refresh --db "$DB" --spine "$SPDB" 2>&1 | tail -1)
say "      $RF"
printf '%s\n' "$RF" | grep -q '"ok": true' || restore "section A's first refresh: $RF"
release_lock
say "[5/7] section A filled once (everything it found now is history: on the page, never told)"
say "[6/7] undo (one line): $VPY -c \"$HOLD_PY\" $DB && \\cp -p $BAK_H $ROOT/$FH && \\cp -p $BAK_W $ROOT/$FW && $SYSTEMCTL restart $FSVC"
say "[7/7] the phone: only a move with NO record is told, as before; nothing new is told until something new is found."
say ""
say "$KIT: DONE. The Marg watch now opens with section A -- stock moved in Marg with no record, each move yours to close, and the explained ones folded below."
exit 0
