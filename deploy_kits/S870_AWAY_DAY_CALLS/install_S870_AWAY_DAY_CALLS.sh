#!/bin/bash
# =============================================================================
#  install_S870_AWAY_DAY_CALLS.sh · kit S870 (the parent, S480, 18-Nov-2026) · his "proceed" 12:11 -- S868's second half
#  A follow-up due on a day Dr Manoj is not sitting (S868's clinic_off_day):
#   1. /root/portal/calls_console.py         efd51956 -> TO   the Call Console row says "Dr Manoj was away that day -- offer a new date"
#   2. /root/portal/portal_followups.py      ed1121ec -> TO   the follow-up WhatsApp batch never offers a message for it, says why
#   3. /root/portal/wa_ladder.py             c5e6a74c -> TO   the WhatsApp ladder HOLDS its tomorrow / date-passed / overdue message
#   4. /root/portal/docterz_missing_alert.py 9cc227e1 -> TO   his not-sitting mark is no sign the clinic worked (no push on a shut day)
#   No table yet (S868 not installed) = nothing changes. clinic-portal restarted, the doctor's auto-fix paused for it.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s870kit && cp -rp /root/deploy/repo/deploy_kits/S870_AWAY_DAY_CALLS /tmp/s870kit && bash /tmp/s870kit/install_S870_AWAY_DAY_CALLS.sh
#  DRY=1 before bash: every gate, the walks and the proof on the live stores; nothing live changes.   --undo: the four files back.
# =============================================================================
set -u
KIT="S870_AWAY_DAY_CALLS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; PD="$ROOT/portal"; WA="$ROOT/wa"; FIN="$ROOT/finance"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CDB="${CDB:-$WA/console.db}"; IDB="${IDB:-$WA/wa_inbox/inbox.db}"; FDB="${FDB:-$FIN/finance.db}"
SM="${SM:-/root/staff_master.csv}"; PU="${PU:-/root/punches.csv}"; RVDB="${RVDB:-$PD/call_review.db}"
LB="${LB:-$WA/portal_console.py}"
NAMES="calls_console.py portal_followups.py wa_ladder.py docterz_missing_alert.py"
from_of() { case "$1" in calls_console.py) echo efd51956c0ea8be6399aaa084fb0e8b2;; portal_followups.py) echo ed1121ec09d039bc9176f065f1bcb731;;
  wa_ladder.py) echo c5e6a74cf6803f0de11912aefe12fb91;; docterz_missing_alert.py) echo 9cc227e12cbe88d1a6784a0da46a9915;; esac; }
to_of() { awk -v f="portal/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s870_inst_$STAMP"; TOOK_LOCK=0; OFF_MINE=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
isfrom() { [ "$(m5 "$PD/$1")" = "$(from_of "$1")" ]; }
say() { echo "$@"; }
bak() { echo "$PD/$1.bak_S870_$(from_of "$1" | cut -c1-8)"; }
hget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PPORT$1"; fi; }
phz() { hget /portal/health; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(phz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$PD/.$n.s870"; done; release; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release; exit 1; }
pause_doctor() { if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do [ -f "$(bak "$n")" ] && \cp -p "$(bak "$n")" "$PD/$n"; done
  "$SYSTEMCTL" restart "$PSVC" || true
  for n in $NAMES; do say "   $n $(m5 "$PD/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   $PSVC restarted, portal health $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
pyv() { (cd "$SCR" && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 600 "$VPY" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do isfrom "$n" || U=0; done
  [ "$U" = 1 ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  for n in $NAMES; do isfrom "$n" || [ "$(m5 "$PD/$n")" = "$(to_of "$n")" ] || { say "!! $PD/$n is $(m5 "$PD/$n" | cut -c1-8), not this kit's - nothing undone. Tell Claude."; exit 1; }; done
  for n in $NAMES; do isfrom "$n" && continue; b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"; pause_doctor
  for n in $NAMES; do isfrom "$n" || \cp -p "$(bak "$n")" "$PD/$n"; done; "$SYSTEMCTL" restart "$PSVC"
  h=$(wait200); release
  [ "$h" = 200 ] || { say "!! UNDONE but portal health is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (four files back; $PSVC restarted, portal health 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
ALL=1; for n in $NAMES; do [ "$(m5 "$PD/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do isfrom "$n" || stop "!! [2/5] $PD/$n is $(m5 "$PD/$n" | cut -c1-8), expected $(from_of "$n" | cut -c1-8) - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
[ -f "$LB" ] && [ -f "$FIN/patient_sync_on_arrival.sh" ] || stop "!! [2/5] $LB or $FIN/patient_sync_on_arrival.sh is not there (the walks read them) - nothing installed"
for n in $NAMES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $VPY - nothing installed"; done
say "[2/5] the live pins exact; the four files compile"
{ mkdir -p "$SCR/new" "$SCR/live" "$SCR/k811/finance" "$SCR/k811/portal" && cp -p "$PD"/*.py "$SCR/new/" && cp -p "$PD"/*.py "$SCR/live/" && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/new/$n"; done \
  && cp -p "$FIN/patient_sync_on_arrival.sh" "$SCR/k811/finance/" && \cp -p "$KDIR/docterz_missing_alert.py" "$SCR/k811/portal/"; } || stop "!! [3/5] could not lay out the walks - nothing installed"
R1=$(pyv "$KDIR/walk_s870.py" "$SCR/new" "$PD" "$LB" "$FIN" "$KDIR/walk_s817.py" "$SCR/w_new" | tail -1)
case "$R1" in "WALK 20/20") ;; *) stop "!! [3/5] walk_s870 (made-up data) on the new files: $R1 - nothing installed";; esac
R1c=$(pyv "$KDIR/walk_s870.py" "$SCR/live" "$PD" "$LB" "$FIN" "$KDIR/walk_s817.py" "$SCR/w_live" | tail -1)
case "$R1c" in "WALK 20/20") stop "!! [3/5] walk_s870's control (the live files) did not go red - nothing installed";; esac
R2=$(pyv "$KDIR/walk_s811.py" "$SCR/k811" | tail -1)
case "$R2" in "WALK OK"*) ;; *) stop "!! [3/5] S811's walk on the new docterz_missing_alert.py: $R2 - nothing installed";; esac
pyv "$KDIR/proof_s870.py" "$SCR/new" "$SCR/live" "$CDB" "$IDB" "$FDB" "$SM" "$PU" "$RVDB" > "$SCR/proof.txt"
tail -1 "$SCR/proof.txt" | grep -q '^PROOF CLEAN' || { sed 's/^/      /' "$SCR/proof.txt"; stop "!! [3/5] the proof on the live stores is not clean - nothing installed"; }
say "[3/5] walk_s870 $R1 (made-up; control red: $R1c); S811's walk $R2; on the live stores (read only):"; sed 's/^/      /' "$SCR/proof.txt"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the proof green; nothing live changed"; exit 0; fi
p0=$(phz); [ "$p0" = 200 ] || stop "!! [4/5] portal health $p0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$PD/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$PD/.$n.s870"; { cat "$KDIR/$n" > "$st" && chmod --reference="$PD/$n" "$st" 2>/dev/null; chown --reference="$PD/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
pause_doctor
for n in docterz_missing_alert.py wa_ladder.py portal_followups.py calls_console.py; do mv -f "$PD/.$n.s870" "$PD/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$PD/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1 after the restart"
for u in /portal/console /portal/wa/followups /portal/messages; do pg=$(hget "$u"); case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg";; esac; done
release
say "[4/5] placed and read back: four files at their TO pins; $PSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), portal health $p1, the three pages answer"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""; say "$KIT: DONE. The Call Console: https://followup.dr-manoj.in/portal/console"; exit 0
