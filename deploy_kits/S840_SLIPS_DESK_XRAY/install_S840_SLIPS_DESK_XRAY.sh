#!/bin/bash
# =============================================================================
#  install_S840_SLIPS_DESK_XRAY.sh · kit S840 (the parent, built S465, rebuilt S467, 14-Nov-2026) · D979 item 4, A-D55
#  The slips desk: "X-ray upload baaki N" on its green strip, a box "X-ray, pichhle 7 din", and the three clinic-ID boxes find a
#  patient by NAME (a list under the box; the mobile's last four only); a name is never saved as a clinic ID.
#   1. /root/finance/parchi_desk.py 5ec8aebc -> TO pin.   clinic-finance is restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s840kit && cp -rp /root/deploy/repo/deploy_kits/S840_SLIPS_DESK_XRAY /tmp/s840kit && bash /tmp/s840kit/install_S840_SLIPS_DESK_XRAY.sh
#  DRY=1 before bash: every gate, the walk and the control; nothing live changes. --undo: the file back from its backup.
# =============================================================================
set -u
KIT="S840_SLIPS_DESK_XRAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="parchi_desk.py"
from_of() { case "$1" in parchi_desk.py) echo 5ec8aebce77f6b631884956b51e36066;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s840_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/finance/$1.bak_S840_${f:0:8}"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$ROOT/finance/.$n.s840"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the file back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f -name '*.py' -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/records.py" ]; }
walk() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s840.py" "$1" "$SCR/finance.db" $2 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  for n in $NAMES; do b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || { say "!! $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done; "$SYSTEMCTL" restart "$FSVC"
  for n in $NAMES; do say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] && [ -f "$ROOT/finance/$n" ] || { say "!! [1/5] $n: the kit's copy or the live file is not as built - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/5] $DB missing - nothing installed"; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/finance/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
for py in "$APY" "$VPY"; do for n in $NAMES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $py - nothing installed"; done; done
say "[2/5] the live pin exact; the new file compiles on both pythons"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$SCR/finance.db" || stop "!! [3/5] could not copy the database for the walk - nothing installed"
{ mkfin new && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n" || exit 9; done; } || stop "!! [3/5] could not lay out the walk - nothing installed"
O=$(walk "$SCR/fin_new" ""); R=$(printf '%s\n' "$O" | tail -1)
printf '%s\n' "$O" | grep -E "^BAD|Error" | head -8 | sed 's/^/      /'
case "$R" in "WALK OK "*) ;; *) stop "!! [3/5] walk_s840 on the new files: $R - nothing installed";; esac
mkfin old || stop "!! [3/5] could not lay out the control - nothing installed"
R0=$(walk "$SCR/fin_old" "--control" | tail -1)
case "$R0" in "CONTROL: red"*) ;; *) stop "!! [3/5] the control on the live files did not go red ($R0) - nothing installed";; esac
say "[3/5] walk_s840 on a copy of the live database (made-up patients, January 2027): $R; the control on the live files: $R0"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the control green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$ROOT/finance/.$n.s840"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$ROOT/finance/$n" "$st" 2>/dev/null; chown --reference="$ROOT/finance/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in $NAMES; do mv -f "$ROOT/finance/.$n.s840" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
release_lock
say "[4/5] placed and read back: the file at its TO pin; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE. The slips desk shows 'X-ray upload baaki', the 7-day X-ray box, and finds a patient by name."
exit 0
