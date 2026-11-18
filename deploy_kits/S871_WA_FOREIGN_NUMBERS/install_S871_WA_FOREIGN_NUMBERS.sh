#!/bin/bash
# =============================================================================
#  install_S871_WA_FOREIGN_NUMBERS.sh · kit S871 (the parent, S480, 18-Nov-2026) · his "go" 13:09
#  A WhatsApp sender with a number abroad (a US number reached him 13-Nov and 18-Nov) was kept as its last 10 digits
#  and treated as Indian: Reply went to +91 + the cut number and MyOperator refused it; the screens said +91; Call rang
#  an invalid Indian number.
#   1. /root/portal/portal_inbox.py  ff0f02a8 -> TO   the whole number kept; Reply sent with its own country code;
#                                                     shown "+1 xxxxx xxxxx · abroad"; Call and templates refused for it in
#                                                     plain words; once, the chats already cut are moved to the whole number
#   2. /root/portal/calls_console.py 36f6221c -> TO   the Call Console keeps and shows the whole number; no Call button for it
#   Indian numbers: nothing changes. clinic-portal restarted, the doctor's auto-fix paused for it.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s871kit && cp -rp /root/deploy/repo/deploy_kits/S871_WA_FOREIGN_NUMBERS /tmp/s871kit && bash /tmp/s871kit/install_S871_WA_FOREIGN_NUMBERS.sh
#  DRY=1 before bash: every gate, the walks and the proof on a copy of the live store; nothing live changes.
#  --undo: the two files back (a chat already moved to its whole number stays under it; the old files still show it).
# =============================================================================
set -u
KIT="S871_WA_FOREIGN_NUMBERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; PD="$ROOT/portal"; WA="$ROOT/wa"; FIN="$ROOT/finance"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
IDB="${IDB:-$WA/wa_inbox/inbox.db}"; RAWD="${RAWD:-$WA/wa_logs}"
LB="${LB:-$WA/portal_console.py}"
NAMES="portal_inbox.py calls_console.py"
from_of() { case "$1" in portal_inbox.py) echo ff0f02a89d66863b228de0a22e888367;; calls_console.py) echo 36f6221cca5a2bb2edef4229f1724ece;; esac; }
to_of() { awk -v f="portal/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s871_inst_$STAMP"; TOOK_LOCK=0; OFF_MINE=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
isfrom() { [ "$(m5 "$PD/$1")" = "$(from_of "$1")" ]; }
say() { echo "$@"; }
bak() { echo "$PD/$1.bak_S871_$(from_of "$1" | cut -c1-8)"; }
hget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PPORT$1"; fi; }
phz() { hget /portal/health; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(phz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$PD/.$n.s871"; done; release; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
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
  say "$KIT: UNDONE (two files back; $PSVC restarted, portal health 200)."; exit 0; fi

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
[ -f "$LB" ] && [ -f "$IDB" ] && [ -d "$RAWD" ] || stop "!! [2/5] $LB, $IDB or $RAWD is not there (the walks and the proof read them) - nothing installed"
for n in $NAMES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $VPY - nothing installed"; done
say "[2/5] the live pins exact; the two files compile"
{ mkdir -p "$SCR/new" "$SCR/live" "$SCR/w859" && cp -p "$PD"/*.py "$SCR/new/" && cp -p "$PD"/*.py "$SCR/live/" && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/new/$n"; done; } \
  || stop "!! [3/5] could not lay out the walks - nothing installed"
R1=$(pyv "$KDIR/walk_s871.py" "$SCR/new/portal_inbox.py" "$SCR/new/calls_console.py" --deps "$SCR/new" | tail -1)
allok() { local x="${1#WALK }"; [ "${1%% *}" = WALK ] && [ "${x%/*}" = "${x#*/}" ] && [ "${x#*/}" -ge 54 ] 2>/dev/null; }   # 58 with node, 54 without
if allok "$R1"; then :; else pyv "$KDIR/walk_s871.py" "$SCR/new/portal_inbox.py" "$SCR/new/calls_console.py" --deps "$SCR/new" | grep RED | head -6
  stop "!! [3/5] walk_s871 (made-up data) on the new files: $R1 - nothing installed"; fi
R1c=$(pyv "$KDIR/walk_s871.py" "$SCR/live/portal_inbox.py" "$SCR/live/calls_console.py" --deps "$SCR/live" | tail -1)
case "$R1c" in "WALK "*) allok "$R1c" && stop "!! [3/5] walk_s871's control (the live files) did not go red - nothing installed";;
  *) stop "!! [3/5] walk_s871's control did not finish ($R1c) - nothing installed";; esac
R2=$(cd "$SCR/w859" && TMPDIR="$SCR/w859" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s859.py" "$SCR/new/portal_inbox.py" 2>&1 | tail -1)
case "$R2" in "WALK OK"*) ;; *) stop "!! [3/5] S859's inbox walk on the new portal_inbox.py: $R2 - nothing installed";; esac
R3=$(pyv "$KDIR/walk_s817.py" "$SCR/new" "$PD" "$LB" "$FIN" | tail -1)
case "$R3" in "WALK OK"*) ;; *) stop "!! [3/5] S817's Call Console walk on the new calls_console.py: $R3 - nothing installed";; esac
pyv "$KDIR/proof_s871.py" "$SCR/new/portal_inbox.py" "$IDB" "$RAWD" "$SCR" > "$SCR/proof.txt"
grep -q "^PROOF chats moved" "$SCR/proof.txt" || { sed 's/^/      /' "$SCR/proof.txt" | tail -4; stop "!! [3/5] the proof on a copy of the live store did not finish - nothing installed"; }
say "[3/5] walk_s871 $R1 (made-up; control red: $R1c); S859's walk $R2; S817's walk $R3; on a copy of the live store (counts only):"; sed 's/^/      /' "$SCR/proof.txt"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the proof green; nothing live changed"; exit 0; fi
p0=$(phz); [ "$p0" = 200 ] || stop "!! [4/5] portal health $p0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$PD/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$PD/.$n.s871"; { cat "$KDIR/$n" > "$st" && chmod --reference="$PD/$n" "$st" 2>/dev/null; chown --reference="$PD/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
pause_doctor
for n in calls_console.py portal_inbox.py; do mv -f "$PD/.$n.s871" "$PD/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$PD/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1 after the restart"
for u in /portal/inbox /portal/console /portal/inbox/health; do pg=$(hget "$u"); case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg";; esac; done
ABR=$(cd "$PD" && TZ=Asia/Kolkata timeout 120 "$VPY" -W ignore -B -c 'import portal_inbox as p; p.ingest(force=True); print(p.abroad_count())' 2>&1 | tail -1)
release
say "[4/5] placed and read back: two files at their TO pins; $PSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), portal health $p1, the pages answer; chats from abroad now kept whole: $ABR"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""; say "$KIT: DONE. The WhatsApp inbox: https://followup.dr-manoj.in/portal/inbox"; exit 0
