#!/bin/bash
# install_S943_SERVER_RECORD.sh -- S943 (the parent, S511, 24-Nov-2026): the nightly SERVER RECORD (roadmap S510 phase 0, A1).
#   NEW /root/finance/server_record.py + cron 02:50 (one JSON a night: disk by folder, RAM, load, the five biggest processes; 90 days;
#   warnings at disk 80 %, RAM < 1 GB, load at or above the CPUs) . owner_console.py cf7f8b09 -> TO (one 'Server:' health line in the
#   system section, read from LATEST.json) . freshness_legs.json f2ade687 -> TO (one leg, 26 h). Read-only on everything else.
#   [1/5] SUMS gate   [2/5] the ground: the three live pins (or already this kit's), the venv, finance healthz 200, the lock
#   [3/5] walk_s943 on made-up data (control red) + server_record --selftest under the venv
#   [4/5] the three files placed (.bak_S943_* beside), read back; the FIRST record written now and --check says RECORD OK;
#         clinic-finance restarted, healthz 200, /finance/console answers; the cron line in -- any red: everything back, restarted
#   [5/5] said: the record's one line.   DRY=1: gates, walk, selftest only.   --undo: files back, the new one moved aside, cron out.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s943kit && cp -rp /root/deploy/repo/deploy_kits/S943_SERVER_RECORD /tmp/s943kit && bash /tmp/s943kit/install_S943_SERVER_RECORD.sh
set -u
KIT="S943_SERVER_RECORD"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="${FIN:-$ROOT/finance}"; WA="${WA:-$ROOT/wa}"; APY="${APY:-$WA/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CRONTAB="${CRONTAB:-crontab}"; TAG="# S943_SERVER_RECORD"
CRONLINE="50 2 * * * [ -e $FIN/_off/ALL_OFF ] || flock -n /tmp/server_record.lock $APY -B $FIN/server_record.py >> $FIN/logs/server_record.log 2>&1 $TAG"
OC="owner_console.py"; LG="freshness_legs.json"; SR="server_record.py"
OC_FROM="cf7f8b09122306a893b229a4158449a1"; LG_FROM="f2ade68779b94c6b99cf3c3b0e00e7d6"
SCR="$(mktemp -d /tmp/s943_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OC_CHANGED=0; LG_CHANGED=0; SR_PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fget /finance/healthz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { release_lock; rm -rf "${SCR:?}" "$FIN/.$OC.s943" "$FIN/.$LG.s943" "$FIN/.$SR.s943"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYA_TIMEOUT:-600}" "$APY" -W ignore -B "$@" 2>&1); }
cron_has() { $CRONTAB -l 2>/dev/null | grep -qF "$TAG"; }
cron_out() { $CRONTAB -l 2>/dev/null | grep -vF "$TAG" | $CRONTAB -; }
OC_BAK="$FIN/$OC.bak_S943_${OC_FROM:0:8}"; LG_BAK="$FIN/$LG.bak_S943_${LG_FROM:0:8}"
restore() { say "!! RED ($1) - putting back"
  [ "$OC_CHANGED" = 1 ] && [ -f "$OC_BAK" ] && \cp -p "$OC_BAK" "$FIN/$OC"
  [ "$LG_CHANGED" = 1 ] && [ -f "$LG_BAK" ] && \cp -p "$LG_BAK" "$FIN/$LG"
  [ "$SR_PLACED" = 1 ] && [ -f "$FIN/$SR" ] && mv -f "$FIN/$SR" "$FIN/$SR.undone_S943"
  cron_has && cron_out
  if [ "$OC_CHANGED" = 1 ]; then "$SYSTEMCTL" restart "$FSVC" >/dev/null 2>&1 || true; h="$(wait200)"; else h="(not restarted)"; fi
  say "   restored: $OC $(m8 "$FIN/$OC") (expected ${OC_FROM:0:8}), $LG $(m8 "$FIN/$LG") (expected ${LG_FROM:0:8}), $SR moved aside, cron out; finance healthz $h. Tell Claude."
  release_lock; exit 1; }
if [ "${1:-}" = "--undo" ]; then
  n=0
  [ -f "$OC_BAK" ] && { [ "$(m5 "$FIN/$OC")" = "$(to_of $OC)" ] || stop "!! --undo: $OC is $(m8 "$FIN/$OC"), not S943's (a later kit?) - not undoing"; }
  [ -f "$LG_BAK" ] && { [ "$(m5 "$FIN/$LG")" = "$(to_of $LG)" ] || stop "!! --undo: $LG is $(m8 "$FIN/$LG"), not S943's (a later kit?) - not undoing"; }
  mkdir "$LOCK" 2>/dev/null || stop "!! --undo: another build holds $LOCK - try again in five minutes"; TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  [ -f "$LG_BAK" ] && { \cp -p "$LG_BAK" "$FIN/$LG"; n=$((n+1)); }
  [ -f "$FIN/$SR" ] && { mv -f "$FIN/$SR" "$FIN/$SR.undone_S943"; n=$((n+1)); }
  cron_has && { cron_out; n=$((n+1)); }
  if [ -f "$OC_BAK" ]; then \cp -p "$OC_BAK" "$FIN/$OC"; n=$((n+1)); "$SYSTEMCTL" restart "$FSVC"; h="$(wait200)"; [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - tell Claude"; exit 1; }; fi
  release_lock
  [ "$n" = 0 ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  say "$KIT: UNDONE ($n thing(s) back: $OC $(m8 "$FIN/$OC"), $LG $(m8 "$FIN/$LG"), $SR moved aside, cron $(cron_has && echo STILL THERE || echo out); the records folder kept)"; exit 0
fi
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
for n in $OC $LG $SR; do [ "$(m5 "$KDIR/$n")" = "$(to_of $n)" ] || stop "!! [1/5] the kit's $n is not as built - nothing installed"; done
say "   [1/5] kit sums ok"
[ -x "$APY" ] || stop "!! [2/5] $APY is not there - STOP. Tell Claude."
[ -f "$FIN/$OC" ] && [ -f "$FIN/$LG" ] && [ -d "$FIN/logs" ] || stop "!! [2/5] $FIN/$OC, $FIN/$LG or $FIN/logs missing - STOP. Tell Claude."
o="$(m5 "$FIN/$OC")"; g="$(m5 "$FIN/$LG")"; s="$(m5 "$FIN/$SR")"
if [ "$o" = "$(to_of $OC)" ] && [ "$g" = "$(to_of $LG)" ] && [ "$s" = "$(to_of $SR)" ] && cron_has; then say "-- $KIT is already installed. Nothing done."; exit 0; fi
[ "$o" = "$OC_FROM" ] || [ "$o" = "$(to_of $OC)" ] || stop "!! [2/5] $FIN/$OC is ${o:0:8}, not ${OC_FROM:0:8} (S911's) - it changed after this kit was built: STOP. Tell Claude."
[ "$g" = "$LG_FROM" ] || [ "$g" = "$(to_of $LG)" ] || stop "!! [2/5] $FIN/$LG is ${g:0:8}, not ${LG_FROM:0:8} (S897's) - STOP. Tell Claude."
[ -z "$s" ] || [ "$s" = "$(to_of $SR)" ] || stop "!! [2/5] $FIN/$SR exists and is not this kit's - STOP. Tell Claude."
for n in $OC $SR; do pya -m py_compile "$KDIR/$n" >/dev/null 2>&1 || stop "!! [2/5] the kit's $n does not compile under $APY - nothing installed"; done
f0=$(fget /finance/healthz); [ "$f0" = 200 ] || stop "!! [2/5] finance healthz $f0 before the install - nothing installed"
if [ "${DRY:-0}" = 1 ]; then say "   [2/5] DRY RUN: pins $OC ${o:0:8}, $LG ${g:0:8}, $SR ${s:-absent}; compile ok; healthz 200; no lock"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $$" > "$LOCK/owner"; TOOK_LOCK=1; say "   [2/5] pins $OC ${o:0:8}, $LG ${g:0:8}, $SR ${s:-absent}; compile ok; healthz 200; the build lock taken"
else stop "!! [2/5] another build holds $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - try again in five minutes"; fi
if [ "$g" = "$LG_FROM" ]; then LF="$FIN/$LG"; else LF="$LG_BAK"; fi        # re-entry: the legs already TO -> the FROM is its backup
W="$(LEGS_FROM="$LF" pya "$KDIR/walk_s943.py" "$KDIR" "$SCR/w943" | tail -1)"; case "$W" in "WALK 16/16") ;; *) stop "!! [3/5] walk_s943: $W - nothing installed";; esac
Wc="$(LEGS_FROM="$LF" OC_FROM="$FIN/$OC" pya "$KDIR/walk_s943.py" "$KDIR" "$SCR/w943c" --control | tail -1)"; [ "$Wc" != "WALK 16/16" ] || { [ "$o" = "$(to_of $OC)" ] || stop "!! [3/5] walk_s943's control did not go red - nothing installed"; }
ST="$(pya "$KDIR/$SR" --selftest | tail -1)"; [ "$ST" = "SELFTEST 10/10" ] || stop "!! [3/5] server_record --selftest: $ST - nothing installed"
say "   [3/5] walk $W (control $Wc); $ST"
[ "${DRY:-0}" = 1 ] && { say "-- DRY RUN: every gate, the walk and the selftest green; nothing live changed"; exit 0; }
if [ "$o" != "$(to_of $OC)" ]; then { \cp -p "$FIN/$OC" "$OC_BAK" && [ "$(m5 "$OC_BAK")" = "$OC_FROM" ]; } || stop "!! [4/5] could not write the backup of $OC - nothing placed"; fi
if [ "$g" != "$(to_of $LG)" ]; then { \cp -p "$FIN/$LG" "$LG_BAK" && [ "$(m5 "$LG_BAK")" = "$LG_FROM" ]; } || stop "!! [4/5] could not write the backup of $LG - nothing placed"; fi
for n in $OC $LG $SR; do { cat "$KDIR/$n" > "$FIN/.$n.s943" && chmod --reference="$FIN/$OC" "$FIN/.$n.s943" && chown --reference="$FIN/$OC" "$FIN/.$n.s943" && [ "$(m5 "$FIN/.$n.s943")" = "$(to_of $n)" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
[ "$s" = "$(to_of $SR)" ] || { mv -f "$FIN/.$SR.s943" "$FIN/$SR" || restore "placing $SR"; SR_PLACED=1; }
[ "$g" = "$(to_of $LG)" ] || { mv -f "$FIN/.$LG.s943" "$FIN/$LG" || restore "placing $LG"; LG_CHANGED=1; }
[ "$o" = "$(to_of $OC)" ] || { mv -f "$FIN/.$OC.s943" "$FIN/$OC" || restore "placing $OC"; OC_CHANGED=1; }
for n in $OC $LG $SR; do [ "$(m5 "$FIN/$n")" = "$(to_of $n)" ] || restore "read back of $n ($(m8 "$FIN/$n"), not its TO pin)"; done
R1="$(PYA_TIMEOUT=900 pya "$FIN/$SR" | grep -m1 "RECORD")"; case "$R1" in *"RECORD OK"*) ;; *) restore "the first record: $R1";; esac
CK="$(pya "$FIN/$SR" --check | head -1)"; case "$CK" in "RECORD OK"*) ;; *) restore "--check after the first record: $CK";; esac
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
if [ "$OC_CHANGED" = 1 ]; then
  "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
  c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
  pg=$(fget /finance/console); case "$pg" in 200|302|303|401|403) ;; *) restore "/finance/console answered $pg";; esac
else c1=200; pg="(not restarted)"; fi
$CRONTAB -l > "$SCR/cron_before.txt" 2>/dev/null || true
[ -s "$SCR/cron_before.txt" ] || restore "crontab -l came back empty - the crontab not touched"
{ grep -vF "$TAG" "$SCR/cron_before.txt"; echo "$CRONLINE"; } | $CRONTAB - || restore "the cron line"
cron_has || restore "the cron line did not read back"
release_lock
say "   [4/5] placed: $SR $(m8 "$FIN/$SR") (NEW), $OC $(m8 "$FIN/$OC"), $LG $(m8 "$FIN/$LG") (baks beside); $FSVC restarted, healthz $c1, console $pg; cron 02:50 in"
say "   [5/5] the first record: $CK"
pya "$FIN/$SR" --check | sed -n '2,6p' | sed 's/^/        /'
say "$KIT: DONE. Undo: bash $KDIR/install_$KIT.sh --undo"
exit 0
