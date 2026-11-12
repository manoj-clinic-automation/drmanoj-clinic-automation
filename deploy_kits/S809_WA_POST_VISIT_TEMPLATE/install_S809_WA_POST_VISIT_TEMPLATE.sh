#!/bin/bash
# =============================================================================
#  install_S809_WA_POST_VISIT_TEMPLATE.sh . kit S809 (13-Nov-2026, session S442, the parent).
#  The owner's new post-visit wording (approved in the MyOperator panel as copy_drmanoj_post_visit: it no longer promises
#  reports in the Docterz app) is ADDED to the portal sender's list, and the "After today's visit" list uses it.
#  ON TOP OF kit S808. TWO files: /root/portal/portal_wa.py (e8b27db9 -> 4b153e7d) and /root/portal/wa_ladder.py (5189a155 -> c5e6a74c),
#  both remade on the box from the live bytes (the kit ships no copy of a live file). The "After today's visit" switch is set
#  OFF and its test is asked for again, so the NEW wording reaches the doctor's phone before any patient. NOTHING IS SENT.
#    bash /tmp/s809kit/install_S809_WA_POST_VISIT_TEMPLATE.sh        DRY=1 writes nothing.   Undo: ... --undo
# =============================================================================
set -u
KIT="S809_WA_POST_VISIT_TEMPLATE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/portal/portal_wa.py"; FROM1=e8b27db968b378261014c27b7b46ca32; TO1=4b153e7d60c0af6271df1b5c8a39659a; BAK1="$F1.bak_S809_${FROM1:0:8}"
F2="$ROOT/portal/wa_ladder.py"; FROM2=5189a155cded969d0aa8fa75c29e0d47; TO2=c5e6a74cf6803f0de11912aefe12fb91; BAK2="$F2.bak_S809_${FROM2:0:8}"
N1="$ROOT/portal/wa_ladder_send.py"; SEND1=d8f16f00aecac80c9dd16971383d8163
WALK_WANT="WALK OK 7/7"
U_PAGE="http://127.0.0.1:$PPORT/portal/messages"
export FINANCE_DB="${FINANCE_DB:-$ROOT/finance/finance.db}" WA_LADDER_DB="${WA_LADDER_DB:-$ROOT/portal/wa_ladder.db}"
export WA_LADDER_INBOX_DB="${WA_LADDER_INBOX_DB:-$ROOT/wa/wa_inbox/inbox.db}" WA_LADDER_OLD_OPTOUT="${WA_LADDER_OLD_OPTOUT:-$ROOT/wa/wa_opt_outs.csv}"
export WA_LADDER_CONSOLE_DB="${WA_LADDER_CONSOLE_DB:-$ROOT/wa/console.db}" WA_LADDER_ALL_OFF="${WA_LADDER_ALL_OFF:-$ROOT/finance/_off/ALL_OFF}"
export WA_LADDER_PORTAL_CONFIG="${WA_LADDER_PORTAL_CONFIG:-$ROOT/portal/portal_config.py}" PORTAL_WA_DIR="${PORTAL_WA_DIR:-$ROOT/wa/wa_portal}"
export WA_LADDER_SEND_LOCK="${WA_LADDER_SEND_LOCK:-$ROOT/portal/wa_ladder_send.lock}" WA_LADDER_INGEST=0
RUNLOCK="$WA_LADDER_SEND_LOCK"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""; PB=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
pcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -H 'X-Messages: 1' -d '{"list":"post_visit","on":false}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${WAITS:-3}"; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
closed() { case "$1" in 302|303|401|403) return 0;; *) return 1;; esac; }
stale_mine() { local pid=""
  if [ -f "$LOCK/owner" ] && grep -q "^$KIT " "$LOCK/owner" 2>/dev/null; then
    pid=$(awk '{print $2}' "$LOCK/owner" 2>/dev/null)
    if [ -n "$pid" ] && [ "$pid" != "$$" ] && kill -0 "$pid" 2>/dev/null; then return 1; fi
    rm -rf "$LOCK"; echo "   (a lock left by an earlier, interrupted run of this kit was cleared)"
  fi
  if [ ! -e "$LOCK" ] && [ -f "$OFFSW" ] && grep -q "^$KIT " "$OFFSW" 2>/dev/null; then rm -f "$OFFSW"; echo "   (the pause switch left by an earlier, interrupted run of this kit was cleared)"; fi
  return 0; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
runfree() { command -v flock >/dev/null 2>&1 || return 0; [ -e "$RUNLOCK" ] || return 0; flock -w 180 "$RUNLOCK" true 2>/dev/null; }
runmod() { ( cd /tmp && PYTHONPATH="$ROOT/portal" timeout 60 "$VPY" -W ignore -B "$N1" "$@" 2>&1 | tail -1 ); }
# the "After today's visit" switch OFF and its test forgotten ($1 = 1), or only looked at ($1 = 0): prints "on=<0|1> tested=<0|1>"
postvisit() { ( cd /tmp && timeout 30 "$VPY" -W ignore -B -c '
import sqlite3, sys, time
c = sqlite3.connect(sys.argv[1], timeout=10)
have = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type=\"table\"")}
on = bool("send_switch" in have and c.execute("SELECT 1 FROM send_switch WHERE list=\"post_visit\" AND is_on<>0").fetchone())
ts = bool("send_test" in have and c.execute("SELECT 1 FROM send_test WHERE list=\"post_visit\"").fetchone())
if sys.argv[2] == "1" and (on or ts):
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 19800))
    c.execute("UPDATE send_switch SET is_on=0, at=?, by=\"S809\" WHERE list=\"post_visit\" AND is_on<>0", (now,))
    c.execute("DELETE FROM send_test WHERE list=\"post_visit\"")
    c.execute("INSERT INTO send_log(at, by, what, list, note) VALUES (?,\"S809\",\"new wording: switch off, test asked again\",\"post_visit\",\"\")", (now,))
    c.commit()
print("on=%d tested=%d" % (on, ts))
' "$WA_LADDER_DB" "$1" 2>&1 | tail -1 ); }
aftergates() { local c t0="$1" jl jr
  c=$(wait200 phz); [ "$c" = 200 ] || { echo "portal health $c"; return; }
  c=$(hcode "$U_PAGE"); closed "$c" || { echo "the page's door answers $c without a login"; return; }
  c=$(pcode "$U_PAGE/api/send/switch"); closed "$c" || { echo "the send door answers $c without a login -- it must be closed"; return; }
  sleep "${WAITS:-2}"
  jl="$("$JOURNALCTL" -u "$PSVC" --since "$t0" --no-pager 2>/dev/null)" || { echo "the portal's journal could not be read after the restart"; return; }
  jr="$(printf '%s\n' "$jl" | grep -v -i 'reentrant call' | grep -c -i -E 'NOT mounted|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
  [ "${jr:-0}" = 0 ] || echo "journal: $jr error line(s) since the restart"; }
putback() {
  runfree
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] && \cp -p "$BAK1" "$F1"
  [ -f "$BAK2" ] && [ "$(m5 "$BAK2")" = "$FROM2" ] && \cp -p "$BAK2" "$F2"
  rm -f "$F1.s809new" "$F2.s809new"
  find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && [ "$(m5 "$F2")" = "$FROM2" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting both files back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   portal_wa.py and wa_ladder.py are back byte-identically (as kit S808 left them)" || echo "   !! NOT back -- send a photo; the backups are $BAK1 and $BAK2"
  echo "   portal health $(wait200 phz). Nothing was sent to anyone. Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
if [ "${1:-}" = "--undo" ]; then
  { [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] && [ -f "$BAK2" ] && [ "$(m5 "$BAK2")" = "$FROM2" ]; } || stop "no good backups -- nothing to undo"
  L1=$(m5 "$F1"); L2=$(m5 "$F2")
  { [ "$L1" = "$TO1" ] || [ "$L1" = "$FROM1" ]; } && { [ "$L2" = "$TO2" ] || [ "$L2" = "$FROM2" ]; } || stop "a file has been changed since this kit (a later kit is on top) -- not undone"
  stale_mine || stop "an install of this kit is still running -- not undone"
  PV=$(postvisit 1); case "$PV" in on=*) ;; *) stop "the store could not be read ($PV) -- not undone";; esac
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && { echo "UNDONE: 'After today's visit' uses the OLD wording again (its switch is OFF and its test is asked for again); portal $(wait200 phz)."; exit 0; }
  echo "!! not back -- send a photo"; exit 1
fi
echo "[1/5] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1"); L2=$(m5 "$F2")
if [ "$L1" = "$TO1" ] && [ "$L2" = "$TO2" ]; then
  echo "-- ALREADY INSTALLED. No file written. portal $(phz)"
  stale_mine || { echo "   an install of this kit is still running -- wait for it to finish. Nothing done."; exit 0; }
  echo "   now: $(runmod --contract)"; exit 0
fi
[ "$L2" = "$FROM2" ] || stop "the live $F2 is not as kit S808 leaves it (live ${L2:0:8}, expected ${FROM2:0:8}) -- kit S808 goes in first"
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ "$(m5 "$N1")" = "$SEND1" ] || stop "the sending file $N1 is not kit S808's -- kit S808 goes in first"
SCR=$(mktemp -d /tmp/s809.XXXX) || stop "no scratch folder could be made in /tmp"
[ -n "$SCR" ] && [ -d "$SCR" ] || stop "no scratch folder could be made in /tmp"
chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live/portal"
"$APY" -B "$KDIR/make_s809.py" "$F1" "$F2" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal/portal_wa.py")" = "$TO1" ] && [ "$(m5 "$SCR/remake/portal/wa_ladder.py")" = "$TO2" ] \
  || stop "make_s809.py on the live bytes does not give the two files this kit was proven with"
for f in portal_wa.py wa_ladder.py; do
  "$APY" -W ignore -B -m py_compile "$SCR/remake/portal/$f" 2>/dev/null && "$VPY" -W ignore -B -m py_compile "$SCR/remake/portal/$f" 2>/dev/null || stop "$f does not compile"
done
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/5] the live portal_wa.py is ${FROM1:0:8} and wa_ladder.py is ${FROM2:0:8} (kit S808's); remade on the box they are ${TO1:0:8} and ${TO2:0:8}; both compile"
\cp -p "$F1" "$F2" "$SCR/live/portal/"
R=$(cd "$SCR" && TMPDIR="$SCR" S809_SEND="$ROOT/portal" S809_OLD_WA="$F1" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s809.py" "$SCR/remake" 2>&1 | tail -1)
[ "$R" = "$WALK_WANT" ] || { (cd "$SCR" && TMPDIR="$SCR" S809_SEND="$ROOT/portal" S809_OLD_WA="$F1" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s809.py" "$SCR/remake" 2>&1 | grep '^BAD' | head -5); stop "the S809 walk is not green ($R; wanted $WALK_WANT)"; }
R2=$(cd "$SCR" && TMPDIR="$SCR" S809_SEND="$ROOT/portal" S809_OLD_WA="$F1" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s809.py" "$SCR/live" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/5] the walk (made-up patients; the line to MyOperator is a recorder): $R | the live files: $R2"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
PB=$(hcode "$U_PAGE"); closed "$PB" || stop "the page's door answers $PB without a login before the install -- not as expected"
PV0=$(postvisit 0); case "$PV0" in on=*) ;; *) stop "the store could not be read ($PV0)";; esac
echo "[4/5] before: portal healthy | the page's door closed without a login ($PB) | 'After today's visit' now: $PV0"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
stale_mine || stop "an install of this kit is still running. Wait for it to finish"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
{ [ "$(m5 "$F1")" = "$FROM1" ] && [ "$(m5 "$F2")" = "$FROM2" ]; } || stop "the live files changed while this run was checking. Run the line once more"
if [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ]; then :; else { \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"; fi
if [ -f "$BAK2" ] && [ "$(m5 "$BAK2")" = "$FROM2" ]; then :; else { \cp -p "$F2" "$BAK2" && [ "$(m5 "$BAK2")" = "$FROM2" ]; } || stop "could not keep a backup of $F2"; fi
runfree                                   # no timed run in flight while the files change
PV=$(postvisit 1); case "$PV" in on=*) ;; *) stop "the 'After today's visit' switch could not be set OFF ($PV)";; esac
PLACED=1
for pair in "portal_wa.py:$F1:$TO1:$BAK1" "wa_ladder.py:$F2:$TO2:$BAK2"; do
  IFS=: read -r src dst to bak <<< "$pair"
  { \cp "$SCR/remake/portal/$src" "$dst.s809new" && [ "$(m5 "$dst.s809new")" = "$to" ] && chmod --reference="$bak" "$dst.s809new"; } || restore "$src could not be copied beside its place"
  chown --reference="$bak" "$dst.s809new" 2>/dev/null
  mv -f "$dst.s809new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$to" ] || restore "$src read-back did not match"
done
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
AG=$(aftergates "$T0"); [ -z "$AG" ] || restore "$AG"
S1=$(runmod --selftest); [ "$S1" = "selftest OK" ] || restore "the sending file's self-test with the new files ($S1)"
CN1=$(runmod --contract); case "$CN1" in "ok "*) ;; *) restore "the sending file and the portal's sender ($CN1)";; esac
ST1=$(runmod --status); case "$ST1" in "ok mode "*) ;; *) restore "after placing, not as expected: $ST1";; esac
PV1=$(postvisit 0); [ "$PV1" = "on=0 tested=0" ] || restore "'After today's visit' is not OFF and untested after placing ($PV1)"
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
echo "[5/5] placed (backups $BAK1, $BAK2); the portal restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): healthy; the doors closed without a login; journal clean; $CN1"
echo "      now: $ST1"
echo "      $KIT: DONE. 'After today's visit' now uses your new wording (copy_drmanoj_post_visit). Its switch is OFF and its test is asked for: send the test to your phone and read it before turning it on. Nothing was sent to anyone."
