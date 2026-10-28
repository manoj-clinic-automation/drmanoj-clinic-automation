#!/bin/bash
# =============================================================================
#  install_S677_RETURNS_ON_SPINE.sh · kit S677 (28-Oct-2026, Sanjeevni session 362) · rung 4d stage 1: the returns engine's lines and
#  credit notes from the spine; the patient from sale_item; the S212 ladder retired. No data step; no staff screen changes.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s677kit && cp -rp /root/deploy/repo/deploy_kits/S677_RETURNS_ON_SPINE /tmp/s677kit && bash /tmp/s677kit/install_S677_RETURNS_ON_SPINE.sh
#  (DRY=1 before bash: every gate, the walk and the old = new proof, nothing written.)
#   /root/finance/spine/spine_read.py         ad441b1d -> TO   credit_notes / return_days / sale_lines / lines_of_bills
#   /root/finance/finance_returns_audit.py    d693c0b4 -> TO   the engine reads the spine (v3)
#   /root/finance/returns_kinds.py            bd45cfeb -> TO   the days from return_days
#   /root/finance/finance_returns_escalate.py c4864500 -> TO   the lines and the days from the engine
#   /root/finance/sanjeevni_approvals.py      26a8dbdb -> TO   the fallback count's days from return_days
#  THE GATE THAT DECIDES: on this box, on a copy of the database and the live spine (read only), every real credit note since 1-Sep is
#  judged under the OLD files and the NEW files -- identical, or the one allowed difference (the old store had no lines, the spine has).
#  Every caller of the engine (the approvals page, Needs-you, returns_kinds, darpan_kal, darpan_app's cn-detail, the daily gaps, the
#  hourly escalation) runs inside clinic-finance -- the one service restarted here.
#  Restarts clinic-finance. Red after placing: all five files back, finance restarted.
# =============================================================================
set -u
KIT="S677_RETURNS_ON_SPINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
SINCE="${SINCE:-2026-09-01}"
RELS="finance/spine/spine_read.py finance/finance_returns_audit.py finance/returns_kinds.py finance/finance_returns_escalate.py finance/sanjeevni_approvals.py"
declare -A FROM=( [finance/spine/spine_read.py]=ad441b1dabf489e1bd54bb5aa62310a4 [finance/finance_returns_audit.py]=d693c0b4064acae8edc7876ef6dffe11
                  [finance/returns_kinds.py]=bd45cfebbaad8ab4f909d025f8b6f948 [finance/finance_returns_escalate.py]=c4864500d2efbd03c9c6a1e350eaf1b5
                  [finance/sanjeevni_approvals.py]=26a8dbdb56f17e2bf3d24f460530e319 )
declare -A TO
while read -r h f; do TO[$f]=$h; done < "$KDIR/TO_PINS.md5"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s677_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="32 of 32 green"; GREEN_BOX="33 of 33 green"
CONTROL="8 S677 check(s) red · 0 older red · 3 green"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S677_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }   # a red keeps $SCR (the proof's lines) for the photo
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 1500 "$VPY" -B "$KDIR/walk_s677.py" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the five files back"
  PLACED=2
  for f in $RELS; do \cp -p "$(bak $f)" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$ROOT/$(dirname $f)/.$(basename $f).s677"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $RELS; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $RELS; do [ -n "${TO[$f]:-}" ] || { say "!! [1/8] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; [ -f "$ROOT/$f" ] || { say "!! [1/8] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$SPINE" ] || { say "!! [1/8] $DB or $SPINE is missing - nothing installed"; exit 1; }
ALL_TO=1; ANY_TO=0; for f in $RELS; do if [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ]; then ANY_TO=1; else ALL_TO=0; fi; done
[ "$ALL_TO" = 1 ] && { say "-- ALREADY INSTALLED: all five files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
[ "$ANY_TO" = 1 ] && { say "!! [1/8] HALF PLACED: some of the five files are already the kit's and others are not (an earlier run was cut while placing). Put the placed ones back from their .bak_S677_* copies, then run this again. Nothing written."; exit 1; }
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/8] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
for f in $RELS; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/8] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed"; done
say "[2/8] live pins exact: all five files at their FROM"

mkdir -p "$SCR/built" "$SCR/pyc" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s677.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live files - nothing installed"; }
for f in $RELS; do [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/8] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"; done
for py in "$APY" "$VPY"; do for f in $RELS; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/8] $f does not compile on $py - nothing installed"; done; done
say "[3/8] rebuilt here from this box's live bytes: all five at their TO pins; all compile under both pythons"

copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
copydb "$SPINE" "$SCR/spine.db" || stop_unlocked "!! [4/8] no copy of the spine (it is rebuilt every ten minutes; run again) - nothing installed"
R=$(walk --new "$SCR/built" --lib "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w1" --box-spine "$SCR/spine.db" --old-root "$ROOT" --since "$SINCE" --also-since "${ALSO_SINCE:-2026-04-01}")
L1="$(echo "$R" | tail -1)"
echo "$R" | grep -E '^  --  |^      20' | head -60 | sed 's/^/         /'
[ "$L1" = "$GREEN_BOX" ] || { echo "$R" | grep -E 'RED|Error|Traceback' | head -20; PLACED=2; stop_unlocked "!! [4/8] the walk, or the old = new proof on this box's returns since $SINCE, is not green ($L1) - nothing installed (the lines above are kept in $SCR)"; }
R=$(walk --old "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w0" | tail -1)
[ "$R" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live files is not as expected ($R) - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk on a copy of the database and the live spine: $L1 (old = new since $SINCE proven above); the control on the live files: $R; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the proof green; NOTHING written"; exit 0; fi

for f in $RELS; do \cp -p "$ROOT/$f" "$(bak $f)" && [ "$(m5 "$(bak $f)")" = "${FROM[$f]}" ] || stop_unlocked "!! [5/8] could not write the backup of $ROOT/$f - nothing placed"; done
for f in $RELS; do STG="$ROOT/$(dirname $f)/.$(basename $f).s677"; { cat "$SCR/built/$f" > "$STG" && [ "$(m5 "$STG")" = "${TO[$f]}" ]; } || { for g in $RELS; do rm -f "$ROOT/$(dirname $g)/.$(basename $g).s677"; done; stop_unlocked "!! [5/8] could not stage $f - nothing placed"; }; chmod --reference="$ROOT/$f" "$STG" 2>/dev/null; chown --reference="$ROOT/$f" "$STG" 2>/dev/null; done
PLACED=1
for f in $RELS; do STG="$ROOT/$(dirname $f)/.$(basename $f).s677"; mv -f "$STG" "$ROOT/$f" || restore "the rename of $f"; [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "$f read back"; done
say "[5/8] placed and read back: all five at their TO pins (backups *.bak_S677_<from8>)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/sanjeevni/approvals); case "$c2" in 302|401|303|403) ;; *) restore "the approvals page answered $c2 without a login";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/8] $FSVC restarted at $T0: healthz $c1; the approvals page $c2 without a login; journal clean"
say "[7/8] no data step: the spine is read, nothing is written"
copydb "$DB" "$SCR/walk2.db" || restore "no copy of the database for the walk on the placed files"
R=$(walk --new "$ROOT" --db "$SCR/walk2.db" --scratch "$SCR/w2" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && R="rehearsal: a forced red at [8/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
release_lock
say "[8/8] the walk on the placed files: $R; the build lock released"
say "undo (one line): \\cp -p $(bak finance/spine/spine_read.py) $ROOT/finance/spine/spine_read.py && \\cp -p $(bak finance/finance_returns_audit.py) $ROOT/finance/finance_returns_audit.py && \\cp -p $(bak finance/returns_kinds.py) $ROOT/finance/returns_kinds.py && \\cp -p $(bak finance/finance_returns_escalate.py) $ROOT/finance/finance_returns_escalate.py && \\cp -p $(bak finance/sanjeevni_approvals.py) $ROOT/finance/sanjeevni_approvals.py && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The returns engine reads the spine; every credit note since $SINCE reads as before, or better."
exit 0
