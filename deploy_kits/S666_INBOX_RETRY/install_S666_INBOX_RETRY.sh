#!/bin/bash
# =============================================================================
#  install_S666_INBOX_RETRY.sh . kit S666 (27-Oct-2026, session S358, the parent) . the WhatsApp Inbox retries MyOperator's gateway refusal
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s666kit && cp -rp /root/deploy/repo/deploy_kits/S666_INBOX_RETRY /tmp/s666kit && bash /tmp/s666kit/install_S666_INBOX_RETRY.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  /root/portal/portal_inbox.py  e25bed25 -> 58d5318e  only HTTP 500 + x-amzn-ErrorType AuthorizerConfigurationException is kept and tried
#                                again (every 2 min, up to 60 min, while the 24-h window is open); any other failure as before, never retried
#  /root/portal/inbox_retry.py   NEW d6718b9a          the runner
#  crontab: one line, marked # S666_INBOX_RETRY:  */2 * * * * flock ... /root/portal/inbox_retry.py >> /root/wa/wa_inbox/retry.log
#  Restarts clinic-portal only. The queue table is made by the module itself on first use (additive).
#  Red after placing: portal_inbox.py back byte-identically, inbox_retry.py removed, the crontab line removed, restart.
#  Undo:  \cp -p /root/portal/portal_inbox.py.bak_S666 /root/portal/portal_inbox.py && crontab -l > /root/portal/crontab.now && grep -vF S666_INBOX_RETRY /root/portal/crontab.now > /root/portal/crontab.new && crontab /root/portal/crontab.new && rm -f /root/portal/inbox_retry.py && systemctl restart clinic-portal
# =============================================================================
set -u
KIT="S666_INBOX_RETRY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
LOCKF="${LOCKF:-/root/wa/wa_inbox/retry.lock}"; LOGF="${LOGF:-/root/wa/wa_inbox/retry.log}"; EXPECT_DB="${EXPECT_DB:-/root/wa/wa_inbox/inbox.db}"
PORTAL="${PORTAL:-/root/portal}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-portal}"; PORT="${PORT:-8099}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; CRONTAB="${CRONTAB:-crontab}"
LP="$PORTAL/portal_inbox.py"; LR="$PORTAL/inbox_retry.py"
FROM=e25bed25d025d84b57180f388c653a8b; TO=58d5318eff3e880112d26d2f30c3c910; RTO=d6718b9af9e30f75005aa5f42ac2efe0
MARK="# S666_INBOX_RETRY"
CRONLINE="*/2 * * * * /usr/bin/flock -n $LOCKF $VPY -B $LR >> $LOGF 2>&1 $MARK"
WALK_OK="23 of 23 green"; CONTROL="19 S666 check(s) red · 0 older red · 4 green"
HAVE_LOCK=0; WN=""; WO=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$WN" ] && rm -rf "$WN" "$WO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -m 8 "http://127.0.0.1:$PORT/portal/inbox/health" 2>/dev/null; }
has_cron() { "$CRONTAB" -l 2>/dev/null | grep -qF "$MARK"; }
CBAK="$PORTAL/crontab.bak_S666"
cron_add() {     # never pipes a failed listing into crontab: the copy is taken, counted, and put back on any mismatch
  "$CRONTAB" -l > "$CBAK" 2>/dev/null || return 1
  local n0 n1; n0=$(grep -c '' "$CBAK"); [ "$n0" -ge 1 ] || return 1
  { cat "$CBAK"; [ -n "$(tail -c1 "$CBAK")" ] && echo; echo "$CRONLINE"; } > "$CBAK.new" && "$CRONTAB" "$CBAK.new" || { "$CRONTAB" "$CBAK"; return 1; }
  n1=$("$CRONTAB" -l 2>/dev/null | grep -c '')
  if [ "$n1" = "$((n0 + 1))" ] && has_cron; then rm -f "$CBAK.new"; return 0; fi
  "$CRONTAB" "$CBAK"; return 1
}

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/portal_inbox.py")" = "$TO" ] && [ "$(m5 "$KDIR/inbox_retry.py")" = "$RTO" ] || stop "the kit's files are not the built ones"
echo "1. kit files: all match SUMS.md5"
if [ "$(m5 "$LP")" = "$TO" ] && [ "$(m5 "$LR")" = "$RTO" ] && has_cron; then echo "ALREADY INSTALLED. $(health)"; exit 0; fi
L=$(m5 "$LP"); [ "$L" = "$FROM" ] || stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
[ -e "$LR" ] && stop "$LR already exists and is not this kit's"
has_cron && stop "the crontab already carries $MARK but the files are not this kit's"
"$PY" -c "import flask" 2>/dev/null || stop "$PY has no flask (the walk loads the inbox)"
[ -x "$VPY" ] || stop "$VPY (the runner's python) is not there"
"$SYSTEMCTL" show "$SVC" -p Environment 2>/dev/null | grep -q "INBOX_" && stop "$SVC sets INBOX_ settings of its own -- the runner would not see the same store"
MPID=$("$SYSTEMCTL" show "$SVC" -p MainPID --value 2>/dev/null)
if [ -n "$MPID" ] && [ "$MPID" != 0 ] && [ -r "/proc/$MPID/environ" ]; then tr '\0' '\n' < "/proc/$MPID/environ" | grep -q "^INBOX_" && stop "$SVC runs with INBOX_ settings (from its environment file) -- the runner would not see the same store"; fi
echo "2. the live file is the one this kit was built from; no runner, no cron line yet"
WN=$(mktemp -d /tmp/s666new.XXXX); WO=$(mktemp -d /tmp/s666old.XXXX); mkdir -p "$WN/portal" "$WO/portal"
\cp "$KDIR/portal_inbox.py" "$KDIR/inbox_retry.py" "$WN/portal/"; \cp "$LP" "$WO/portal/"
for py in "$PY" "$VPY"; do "$py" -B -m py_compile "$WN/portal/portal_inbox.py" "$WN/portal/inbox_retry.py" || stop "a file does not compile with $py"; done
R=$(cd /tmp && timeout 300 "$PY" -B "$KDIR/walk_s666.py" "$WN" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd /tmp && timeout 300 "$PY" -B "$KDIR/walk_s666.py" "$WN" 2>&1 | grep -E 'RED|Error' | head); stop "the walk is not green ($R)"; }
echo "3. the walk with a stand-in MyOperator (made-up numbers, temp store): $R"
R=$(cd /tmp && timeout 300 "$PY" -B "$KDIR/walk_s666.py" "$WO" --old 2>&1 | tail -1)
[ "$R" = "$CONTROL" ] || stop "the control on the live file is not as expected ($R)"
echo "   control on the live file: $R"
health | grep -q '"inbox"' || stop "the inbox is not answering before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
rm -f "$CBAK" "$CBAK.new"                     # no older copy can ever be put back
restore() {
  \cp -p "$LP.bak_S666" "$LP"; rm -f "$LR"
  [ -s "$CBAK" ] && "$CRONTAB" "$CBAK"
  "$SYSTEMCTL" restart "$SVC"; sleep 6
  [ "$(m5 "$LP")" = "$FROM" ] && echo "   the old portal_inbox.py is back byte-identically" || echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S666 back by hand"
  has_cron && echo "   !! the cron line is still there -- remove it by hand" || echo "   the cron line is removed"
  echo "   after the restore: $(health). Send a photo of this screen to Claude."; exit 1
}
\cp -p "$LP" "$LP.bak_S666" || stop "could not keep a backup of $LP"
echo "4. backup: portal_inbox.py.bak_S666 (the crontab is copied when its line is added)"
\cp "$KDIR/portal_inbox.py" "$LP" && chmod --reference="$LP.bak_S666" "$LP" 2>/dev/null
\cp "$KDIR/inbox_retry.py" "$LR" && chmod 700 "$LR"
[ "$(m5 "$LP")" = "$TO" ] && [ "$(m5 "$LR")" = "$RTO" ] || { echo "!! read-back did not match"; restore; }
echo "5. placed portal_inbox.py and inbox_retry.py, read back by md5"
"$SYSTEMCTL" restart "$SVC"
h=""; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); echo "$h" | grep -q '"S666"' && break; done
echo "$h" | grep -q '"S666"' || { echo "!! RED after placing: the inbox did not come back as S666 ($h)"; restore; }
K=$(cd /tmp && "$VPY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import inbox_retry, portal_inbox as P; print(bool(P._token(inbox_retry.cfg_get)), P.DB_PATH)" "$PORTAL" 2>&1 | tail -1)
[ "$K" = "True $EXPECT_DB" ] || { echo "!! RED: under $VPY the runner does not find the send key and the inbox store ($K)"; restore; }
R=$(cd /tmp && /usr/bin/flock -n "$LOCKF" "$VPY" -B "$LR" 2>&1; echo "rc=$?")
echo "$R" | grep -q "rc=0" || { echo "!! RED: the runner failed on the box: $R"; restore; }
cron_add || { echo "!! RED: the cron line could not be added safely (the crontab is as it was)"; restore; }
echo "6. $SVC restarted (inbox health says S666); under $VPY the runner finds the key and $EXPECT_DB; it ran once (rc 0); the cron line added (every 2 minutes; crontab $(grep -c '' "$CBAK") -> $("$CRONTAB" -l | grep -c '') lines)"
echo ""
echo "$KIT: DONE. A send MyOperator's gateway refuses now shows 'MyOperator busy — retrying' and goes through by itself when they accept."
