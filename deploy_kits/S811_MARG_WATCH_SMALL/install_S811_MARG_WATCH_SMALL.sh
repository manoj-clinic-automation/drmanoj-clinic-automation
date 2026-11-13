#!/bin/bash
# =============================================================================
#  install_S811_MARG_WATCH_SMALL.sh · kit S811 (13-Nov-2026, Sanjeevni session 441) · the owner's "ok" 06:42 IST
#  1. /root/finance/marg_billwatch.py 616490b4 -> TO : the Marg watch page's five small things (the scan full width on an agreeing
#     row; "entries"; the time on a day with two lists; a sale bill named in "Added late"; "held none of the 25").
#  2. /root/finance/owner_console.py  ba977832 -> TO : ONE line in the Sanjeevni section -- the Marg watch, its count, its link
#     (the parent's file, PLANNED on board/_numbers v1332; nothing else in it changes).             clinic-finance is restarted.
#  3. repair_s811.py : the three 05-Oct purchase lists of 1 Sep - 3 Oct marked as replaced by September's complete list (F-1280),
#     proved first: every line of them is in a later list; September's and October's bills and line sets unchanged.
#  Both files are REBUILT HERE from the live bytes by make_s811.py and checked against the TO pins.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s811kit && cp -rp /root/deploy/repo/deploy_kits/S811_MARG_WATCH_SMALL /tmp/s811kit && bash /tmp/s811kit/install_S811_MARG_WATCH_SMALL.sh
#  (DRY=1 before bash: every gate, both walks, the controls and the repair's proof; NOTHING written.)
# =============================================================================
set -u
KIT="S811_MARG_WATCH_SMALL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FW="finance/marg_billwatch.py"; FC="finance/owner_console.py"
FROM_W="616490b4a0d30edacf5b3724856be4e0"; FROM_C="ba97783223b689ab538a7ccaf0028ef7"
TO_W="$(awk -v f="$FW" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; TO_C="$(awk -v f="$FC" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s811_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK_W="$ROOT/$FW.bak_S811_${FROM_W:0:8}"; BAK_C="$ROOT/$FC.bak_S811_${FROM_C:0:8}"
STG_W="$ROOT/finance/.marg_billwatch.py.s811"; STG_C="$ROOT/finance/.owner_console.py.s811"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG_W" "$STG_C"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting both files back (the database is not touched)"
  \cp -p "$BAK_W" "$ROOT/$FW"; \cp -p "$BAK_C" "$ROOT/$FC"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   marg_billwatch.py $(m5 "$ROOT/$FW" | cut -c1-8) (expected ${FROM_W:0:8}) · owner_console.py $(m5 "$ROOT/$FC" | cut -c1-8) (expected ${FROM_C:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
w811() { (cd /tmp && PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s811.py" "$1" "$ROOT/finance" $2 2>&1); }
w803() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s803.py" "$1" "$ROOT/shared" "$ROOT/finance" "$DB" 2>&1); }
repair() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/repair_s811.py" --db "$DB" $1 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO_W" ] && [ -n "$TO_C" ] && [ -f "$ROOT/$FW" ] && [ -f "$ROOT/$FC" ] && [ -f "$DB" ] || { say "!! [1/7] a TO pin, a live file or $DB missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$FW")" = "$TO_W" ] && [ "$(m5 "$ROOT/$FC")" = "$TO_C" ]; then say "-- the two files are ALREADY INSTALLED; only the database step runs."
  [ "${DRY:-0}" = 1 ] && { repair "" | sed 's/^/      /'; say "-- DRY RUN: nothing written"; exit 0; }
  repair "--apply" | sed 's/^/      /'; say "$KIT: DONE (the files were already in place)."; exit 0; fi
mkdir -p "$SCR/built" "$SCR/w" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/7] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken by $KIT"
else say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$FW")" = "$FROM_W" ] || stop "!! [2/7] $ROOT/$FW is $(m5 "$ROOT/$FW" | cut -c1-8), expected ${FROM_W:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
[ "$(m5 "$ROOT/$FC")" = "$FROM_C" ] || stop "!! [2/7] $ROOT/$FC is $(m5 "$ROOT/$FC" | cut -c1-8), expected ${FROM_C:0:8} - it changed after this kit was built (the parent's file): STOP, nothing installed. Tell Claude."
"$APY" -B make_s811.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused - nothing installed"; }
[ "$(m5 "$SCR/built/marg_billwatch.py")" = "$TO_W" ] && [ "$(m5 "$SCR/built/owner_console.py")" = "$TO_C" ] || stop "!! [2/7] rebuilt, the files are not at their TO pins - nothing installed"
for py in "$APY" "$VPY"; do for f in marg_billwatch.py owner_console.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop "!! [2/7] $f does not compile on $py - nothing installed"; done; done
say "[2/7] live pins exact (${FROM_W:0:8}, ${FROM_C:0:8}); rebuilt here at their TO pins (${TO_W:0:8}, ${TO_C:0:8}); both compile on both pythons"
O=$(w811 "$SCR/built" ""); R=$(printf '%s\n' "$O" | tail -1); [ "$R" = "WALK S811 GREEN" ] || { printf '%s\n' "$O" | grep -E "RED|Error" | head -6 | sed 's/^/      /'; stop "!! [3/7] walk_s811: $R - nothing installed"; }
O0=$(w811 "$ROOT/finance" "--control"); R0=$(printf '%s\n' "$O0" | tail -1); [ "$R0" = "CONTROL S811 RED as it must be" ] || stop "!! [3/7] the control: $R0 - nothing installed"
\cp -p "$SCR/built/marg_billwatch.py" "$SCR/w/"; \cp -p "$ROOT/finance/finance_ui/finance_approvals.html" "$SCR/w/"
O3=$(w803 "$SCR/w"); R3=$(printf '%s\n' "$O3" | tail -1); [ "$R3" = "WALK S803 GREEN" ] || { printf '%s\n' "$O3" | grep -E "RED|Error" | head -6 | sed 's/^/      /'; stop "!! [3/7] the Marg watch's own walk (S803) on the rebuilt page: $R3 - nothing installed"; }
say "[3/7] walk_s811: $R (its control red as it must be); the Marg watch's own walk S803 on the rebuilt page: $R3"
RP=$(repair ""); printf '%s\n' "$RP" | sed 's/^/      /'; printf '%s\n' "$RP" | grep -q -E "^(DRY: proved|ALREADY)" || stop "!! [4/7] the repair's proof did not hold - nothing installed"
say "[4/7] the repair's proof holds (nothing written yet)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, both walks, the control and the repair's proof green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [5/7] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$FW" "$BAK_W" && [ "$(m5 "$BAK_W")" = "$FROM_W" ] && \cp -p "$ROOT/$FC" "$BAK_C" && [ "$(m5 "$BAK_C")" = "$FROM_C" ]; } || stop "!! [5/7] could not write the backups - nothing placed"
{ cat "$SCR/built/marg_billwatch.py" > "$STG_W" && chmod --reference="$ROOT/$FW" "$STG_W" 2>/dev/null; chown --reference="$ROOT/$FW" "$STG_W" 2>/dev/null; [ "$(m5 "$STG_W")" = "$TO_W" ]; } || stop "!! [5/7] could not stage - nothing placed"
{ cat "$SCR/built/owner_console.py" > "$STG_C" && chmod --reference="$ROOT/$FC" "$STG_C" 2>/dev/null; chown --reference="$ROOT/$FC" "$STG_C" 2>/dev/null; [ "$(m5 "$STG_C")" = "$TO_C" ]; } || stop "!! [5/7] could not stage - nothing placed"
mv -f "$STG_W" "$ROOT/$FW" || restore "the rename of marg_billwatch.py"
mv -f "$STG_C" "$ROOT/$FC" || restore "the rename of owner_console.py"
[ "$(m5 "$ROOT/$FW")" = "$TO_W" ] && [ "$(m5 "$ROOT/$FC")" = "$TO_C" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/7]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
O4=$(w811 "$ROOT/finance" ""); R4=$(printf '%s\n' "$O4" | tail -1); [ "$R4" = "WALK S811 GREEN" ] || restore "walk_s811 on the placed files: $R4"
release_lock
say "[5/7] placed and read back: marg_billwatch.py ${TO_W:0:8}, owner_console.py ${TO_C:0:8}; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1; walk_s811 on the placed files GREEN"
RA=$(repair "--apply"); printf '%s\n' "$RA" | sed 's/^/      /'
if printf '%s\n' "$RA" | grep -q -E "^(DONE|ALREADY)"; then say "[6/7] the three old 05-Oct purchase lists are marked as replaced"; RC=0
else say "!! [6/7] the database step did not finish - the two files ARE in place, the database is as it was. Send a photo of this screen to Claude."; RC=1; fi
say "[7/7] undo the files (one line): \\cp -p $BAK_W $ROOT/$FW && \\cp -p $BAK_C $ROOT/$FC && $SYSTEMCTL restart $FSVC"
say ""
[ "$RC" = 0 ] && say "$KIT: DONE. The Marg watch page has its five small fixes, your command console carries its line, and the three old part lists of 5 Oct are retired."
exit "$RC"
