#!/bin/bash
# =============================================================================
#  install_S795_PART_EXPORT_GUARD.sh · kit S795 (12-Nov-2026, Sanjeevni session 434) · the owner's "proceed with it" 06:51 IST
#  On 11-Nov two bill-wise reports of 1-11 Nov arrived 15 seconds apart: 29 bills, then 4.  The 4-bill list retired the
#  29-bill one, and 25 of November's bills stopped counting (the scan pairing: "no bill on the server yet").
#  1. /root/finance/purchase_app.py   54d27cd3 -> TO : a part list (under half the rows of the live report it would
#     retire, and more than two short) is kept, marked, and retires nothing.            clinic-finance is restarted.
#  2. repair_s795.py : the 11-Nov pair put right in finance.db (the 29-bill list live again, the 4 bills re-hung on it);
#     the scan pairing's "seen" mark cleared so the pairing runs again at the next look.  Before-state saved beside the db.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s795kit && cp -rp /root/deploy/repo/deploy_kits/S795_PART_EXPORT_GUARD /tmp/s795kit && bash /tmp/s795kit/install_S795_PART_EXPORT_GUARD.sh
# =============================================================================
set -u
KIT="S795_PART_EXPORT_GUARD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
F="finance/purchase_app.py"
FROM="54d27cd34b5088383887ecc19cafd4c8"
TO="$(awk -v f="$F" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s795_inst_$STAMP"; TOOK_LOCK=0; PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK="$ROOT/$F.bak_S795_${FROM:0:8}"; STG="$(dirname "$ROOT/$F")/.$(basename "$F").s795"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; [ "$PLACED" = 2 ] || rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the file back"; PLACED=2; \cp -p "$BAK" "$ROOT/$F"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   $ROOT/$F $(m5 "$ROOT/$F" | cut -c1-8) (expected ${FROM:0:8}); $FSVC restarted, finance healthz $(wait200). The database was not touched. Send a photo of this screen to Claude."; release_lock; exit 1; }
repair() { say "[5/5] the 11-Nov pair in the database:"; "$VPY" -B "$KDIR/repair_s795.py" --db "$DB" --apply 2>&1 | sed 's/^/      /'
  [ "${PIPESTATUS[0]}" = 0 ] || { say "!! [5/5] the repair did not run clean - the new rule IS in place, the database is as it was. Send a photo of this screen to Claude."; return 1; }; return 0; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] && [ -f "$ROOT/$F" ] && [ -f "$DB" ] || { say "!! [1/5] TO pin, $ROOT/$F or $DB missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$F")" = "$TO" ]; then say "-- the rule is ALREADY INSTALLED (purchase_app.py ${TO:0:8}); only the database step runs."
  [ "${DRY:-0}" = 1 ] && { say "-- DRY RUN: nothing written"; exit 0; }; repair; say "$KIT: DONE (the rule was already in place)."; exit 0; fi
mkdir -p "$SCR/built" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$F")" = "$FROM" ] || stop "!! [2/5] $ROOT/$F is $(m5 "$ROOT/$F" | cut -c1-8), expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
"$APY" -B make_s795.py "$ROOT/finance" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/5] the builder refused - nothing installed"; }
[ "$(m5 "$SCR/built/purchase_app.py")" = "$TO" ] || stop "!! [2/5] rebuilt, the file is not at its TO pin - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/purchase_app.py" || stop "!! [2/5] the built file does not compile on $py - nothing installed"; done
R=$("$APY" -B walk_s795.py "$SCR/built/purchase_app.py" | tail -1); [ "$R" = "WALK S795 GREEN" ] || stop "!! [3/5] the walk: $R - nothing installed"
R0=$("$APY" -B walk_s795.py "$ROOT/$F" --control | tail -1); [ "$R0" = "CONTROL S795 RED as it must be" ] || stop "!! [3/5] the control: $R0 - nothing installed"
say "[2/5] live pin exact (${FROM:0:8}); rebuilt here at its TO pin (${TO:0:8}); compiles on both pythons · [3/5] walk_s795: $R; its control red as it must be"
"$VPY" -B repair_s795.py --db "$DB" 2>&1 | sed 's/^/      /'
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the control green; the repair listed only; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
{ cat "$SCR/built/purchase_app.py" > "$STG" && chmod --reference="$ROOT/$F" "$STG" 2>/dev/null; chown --reference="$ROOT/$F" "$STG" 2>/dev/null; [ "$(m5 "$STG")" = "$TO" ]; } || stop "!! [4/5] could not stage - nothing placed"
PLACED=1
mv -f "$STG" "$ROOT/$F" || restore "the rename"
[ "$(m5 "$ROOT/$F")" = "$TO" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
release_lock
say "[4/5] placed and read back: purchase_app.py ${TO:0:8}; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
repair; RC=$?
say "undo the rule (one line): \\cp -p $BAK $ROOT/$F && $SYSTEMCTL restart $FSVC      (the database step's before-state: $(dirname "$DB")/s795_repair_before_*.json)"
say ""
[ "$RC" = 0 ] && say "$KIT: DONE. November's purchase bills all count again; the scans pair with them at the next look at the Purchase bills page." || say "$KIT: the rule is in place; the database step is NOT done (see above)."
exit "$RC"
