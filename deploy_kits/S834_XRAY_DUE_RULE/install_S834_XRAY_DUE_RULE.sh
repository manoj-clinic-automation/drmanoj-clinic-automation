#!/bin/bash
# =============================================================================
#  install_S834_XRAY_DUE_RULE.sh · kit S834 (14-Nov-2026, the parent, session S462) · D979 item 1 (the approved mock-up, his word 16:08 IST)
#  THE DUE RULE for X-ray photos, the same in four places: a morning X-ray is due at 15:00 the same day, an evening X-ray at 15:00 the next
#  day (Docterz's own shift; a slip with no Docterz line yet goes by its own time); a photo filed within two days counts; nothing is
#  pending before it is due.
#   1. /root/finance/xray_photo_nudge.py 73d5a43f -> 20823798  (the 3 / 6 pm notice: due only, 7 days back)
#   2. /root/finance/slip_log.py         b47a5ded -> 231aebde  (Report baaki: due only; 'der ho gayi' a day after due)
#   3. /root/finance/records.py          b81e4e8f -> 29114ddd  (Check karein's 'X-ray taken, no file': due only, today included)
#   4. claude_code_briefs/DUTY_MAP.json v25 (alisha.xray_photo) rides the publish -- this installer stops unless the repository carries it.
#  clinic-finance is restarted (slip_log, records). The notice is a cron job: its next run (15:00 / 18:00) takes the new file.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s834kit && cp -rp /root/deploy/repo/deploy_kits/S834_XRAY_DUE_RULE /tmp/s834kit && bash /tmp/s834kit/install_S834_XRAY_DUE_RULE.sh
#  DRY=1 before bash: every gate, the walk and the control; nothing live changes (a scratch folder in /tmp, removed on exit).
#  --undo: the three files back from their backups (only while they are still this kit's).
# =============================================================================
set -u
KIT="S834_XRAY_DUE_RULE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
DMAP="${DMAP:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="xray_photo_nudge.py slip_log.py records.py"
from_of() { case "$1" in xray_photo_nudge.py) echo 73d5a43f0d6bc8ee30046b71a7fb8e5d;; slip_log.py) echo b47a5ded64d0c9828bb7343bc7328a6b;; records.py) echo b81e4e8fe2f7c78e89f7d8fba37bcd14;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s834_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/finance/$1.bak_S834_${f:0:8}"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$ROOT/finance/.$n.s834"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the three files back"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f -name '*.py' -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/records.py" ]; }
walk() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s834.py" "$1" "$2" "$SCR/finance.db" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  for n in $NAMES; do b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || { say "!! $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/finance/$n"; done; "$SYSTEMCTL" restart "$FSVC"
  for n in $NAMES; do say "   $n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($FSVC restarted, finance healthz 200). The duty map v25 stays in the repository; tell Claude."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] && [ -f "$ROOT/finance/$n" ] || { say "!! [1/6] $n: the kit's copy or the live file is not as built - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/6] $DB missing - nothing installed"; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
"$APY" -c "import json,sys;m=json.load(open(sys.argv[1]));d=[x for x in m.get('duties',[]) if x.get('id')=='alisha.xray_photo'];sys.exit(0 if int(m.get('version',0))>=25 and d and \"' 15:00:00'\" in d[0].get('due_sql','') and \"date(s.day, '+2 day')\" in d[0].get('due_sql','') else 1)" "$DMAP" 2>/dev/null \
  || { say "!! [1/6] the duty map $DMAP does not carry the S834 rule (v25) - publish first, then run this line again. Nothing installed."; exit 1; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; the duty map v25 carries the rule; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the duty map v25 carries the rule; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/finance/$n")" = "$fr" ] || stop "!! [2/6] $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
for py in "$APY" "$VPY"; do for n in $NAMES; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/6] $n does not compile on $py - nothing installed"; done; done
say "[2/6] three live pins exact; the three new files compile on both pythons"
"$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$SCR/finance.db" || stop "!! [3/6] could not copy the database for the walk - nothing installed"
{ mkfin new && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n" || exit 9; done; } || stop "!! [3/6] could not lay out the walk - nothing installed"
O=$(walk "$SCR/fin_new" "$DMAP"); R=$(printf '%s\n' "$O" | tail -1)
printf '%s\n' "$O" | grep -E "^RED|Error" | head -8 | sed 's/^/      /'
case "$R" in "S834 walk: "*" green, 0 red") ;; *) stop "!! [3/6] walk_s834 on the new files: $R - nothing installed";; esac
mkfin old || stop "!! [3/6] could not lay out the control - nothing installed"
R0=$(walk "$SCR/fin_old" "$DMAP" | tail -1)
case "$R0" in "S834 walk: "*" green, 0 red") stop "!! [3/6] the control on the live files did not go red ($R0) - nothing installed";; "S834 walk: "*) ;; *) stop "!! [3/6] the control did not run ($R0) - nothing installed";; esac
say "[3/6] walk_s834 on a copy of the live database (made-up patients ZZ9xxx, January 2027): $R; the control on the live files: ${R0#S834 walk: }"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the control green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$ROOT/finance/.$n.s834"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$ROOT/finance/$n" "$st" 2>/dev/null; chown --reference="$ROOT/finance/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
for n in xray_photo_nudge.py records.py slip_log.py; do mv -f "$ROOT/finance/.$n.s834" "$ROOT/finance/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
say "[4/6] placed and read back: the three files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
NZ=$(cd "$ROOT/finance" && FINANCE_DB="$DB" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B xray_photo_nudge.py --dry 2>&1 | tail -1)
say "      the notice, read-only, sends nothing: $NZ"
case "$NZ" in DRY*) ;; *) restore "the notice's dry run: $NZ";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
release_lock
say "[5/6] the notice reads the live database by the new rule (nothing sent)"
say "[6/6] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE. X-ray photos now count only once due: a morning X-ray at 3 pm the same day, an evening one at 3 pm the next day; the 3 and 6 pm notice looks back 7 days."
exit 0
