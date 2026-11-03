#!/bin/bash
# =============================================================================
#  install_S701_WA_KEY_SWAP.sh . kit S701 (03-Nov-2026, session S382, the parent) . the WhatsApp fix
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s701kit && cp -rp /root/deploy/repo/deploy_kits/S701_WA_KEY_SWAP /tmp/s701kit && bash /tmp/s701kit/install_S701_WA_KEY_SWAP.sh
#  (DRY=1 before bash: every gate, both walks and the read-only list of the key's holders; nothing written.)
#  (UNDO=1 before bash: the key's files put back as before the last swap; the inbox file is not touched.)
#
#  PART 1  /root/portal/portal_inbox.py  58d5318e -> f89ad282  a send refused at MyOperator's authorizer is retried until the
#          patient's 24-hour window closes (every 2 min in the first hour, every 10 after), not 60 minutes only; a photo /
#          PDF / voice note's link is renewed before each retry (it lives 6 h).
#          Rebuilt on the box by make_s701.py from the live file (must equal the kit's copy). Restarts clinic-portal.
#  PART 2  /root/wa/swap_key_s701.py  NEW  the key swap: asks for the NEW key (hidden), asks MyOperator, writes it BY VALUE in
#          every live file that holds the old one (backups in /root/s701_backup, mode 600), reloads systemd if a unit
#          file changed, restarts the services that read the key only at start, checks no live holder keeps the old key.
#          Every check runs BEFORE it says "NOW press Regenerate"; Enter alone at the question = the key is left as it is.
#  Red after placing PART 1: portal_inbox.py back byte-identically and clinic-portal restarted.
#  Undo PART 1:  \cp -p /root/portal/portal_inbox.py.bak_S701 /root/portal/portal_inbox.py && systemctl restart clinic-portal
# =============================================================================
set -u
KIT="S701_WA_KEY_SWAP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
PORTAL="${PORTAL:-/root/portal}"; WA="${WA:-/root/wa}"
LOCKF="${LOCKF:-/root/wa/wa_inbox/retry.lock}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-portal}"; PORT="${PORT:-8099}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LP="$PORTAL/portal_inbox.py"; LR="$PORTAL/inbox_retry.py"; LS="$WA/swap_key_s701.py"
FROM=58d5318eff3e880112d26d2f30c3c910; TO=f89ad282bf81982af7f5e8b15cb238ac; RTO=d6718b9af9e30f75005aa5f42ac2efe0
STO=d74a9021a1294c6e2ffe88f8512bfc2f
WALK_OK="32 of 32 green"; CONTROL="8 S701 check(s) red · 0 older red · 24 green"; SWALK_OK="31 of 31 green"
HAVE_LOCK=0; WN=""; WO=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$WN" ] && rm -rf "$WN" "$WO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -m 8 "http://127.0.0.1:$PORT/portal/inbox/health" 2>/dev/null; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/portal_inbox.py")" = "$TO" ] && [ "$(m5 "$KDIR/swap_key_s701.py")" = "$STO" ] || stop "the kit's files are not the built ones"
echo "1. kit files: all match SUMS.md5"

if [ "${UNDO:-0}" = 1 ]; then
  [ -f "$LS" ] || stop "$LS is not there -- no swap was made by this kit"
  "$PY" -B "$LS" undo; exit $?
fi

H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
"$PY" -c "import flask" 2>/dev/null || stop "$PY has no flask (the walk loads the inbox)"
[ -x "$VPY" ] || stop "$VPY (the runner's python) is not there"
[ "$(m5 "$LR")" = "$RTO" ] || stop "$LR is not S666's runner (d6718b9a)"

L=$(m5 "$LP")
if [ "$L" = "$TO" ]; then
  PART1=already; echo "2. PART 1 (the inbox retries until the window closes): ALREADY INSTALLED. $(health)"
elif [ "$L" = "$FROM" ]; then
  PART1=todo
  WN=$(mktemp -d /tmp/s701new.XXXX); WO=$(mktemp -d /tmp/s701old.XXXX); mkdir -p "$WN/portal" "$WO/portal"
  "$PY" -B "$KDIR/make_s701.py" "$LP" "$WN/portal/portal_inbox.py" >/dev/null || stop "make_s701.py refused the live file"
  [ "$(m5 "$WN/portal/portal_inbox.py")" = "$TO" ] || stop "the file rebuilt from the live one is not the kit's copy"
  \cp "$LR" "$WN/portal/"; \cp "$LP" "$LR" "$WO/portal/"
  for py in "$PY" "$VPY"; do "$py" -B -m py_compile "$WN/portal/portal_inbox.py" || stop "the new file does not compile with $py"; done
  echo "2. the live portal_inbox.py is the one this kit was built from; rebuilt from it on the box = the kit's copy (${TO:0:8})"
  R=$(cd /tmp && timeout 600 "$PY" -B "$KDIR/walk_s701.py" "$WN" 2>&1 | tail -1)
  [ "$R" = "$WALK_OK" ] || { (cd /tmp && timeout 600 "$PY" -B "$KDIR/walk_s701.py" "$WN" 2>&1 | grep -E 'RED|Error' | head); stop "the walk is not green ($R)"; }
  echo "3. the inbox walk with a stand-in MyOperator (made-up numbers, temp store): $R"
  R=$(cd /tmp && timeout 600 "$PY" -B "$KDIR/walk_s701.py" "$WO" --old 2>&1 | tail -1)
  [ "$R" = "$CONTROL" ] || stop "the control on the live file is not as expected ($R)"
  echo "   control on the live file: $R"
  health | grep -q '"inbox"' || stop "the inbox is not answering before the install"
else
  stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
fi
SW=$(mktemp -d /tmp/s701sw.XXXX); mkdir -p "$SW/portal"; \cp "$KDIR/portal_inbox.py" "$LR" "$SW/portal/"
R=$(cd /tmp && timeout 600 "$PY" -B "$KDIR/walk_swap_s701.py" "$KDIR/swap_key_s701.py" "$SW" 2>&1 | tail -1); rm -rf "$SW"
[ "$R" = "$SWALK_OK" ] || stop "the key swap's walk is not green ($R)"
echo "4. the key swap's walk (a made-up server in /tmp, made-up keys, stand-in MyOperator): $R"
if [ "${DRY:-0}" = 1 ]; then
  echo "   the key's holders now (read-only):"; "$PY" -B "$KDIR/swap_key_s701.py" find | sed 's/^/   /'
  echo "DRY=1: every gate green; nothing written."; exit 0
fi
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1

if [ "$PART1" = todo ]; then
  restore() {
    \cp -p "$LP.bak_S701" "$LP"; "$SYSTEMCTL" restart "$SVC"; sleep 6
    [ "$(m5 "$LP")" = "$FROM" ] && echo "   the old portal_inbox.py is back byte-identically" || echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S701 back by hand"
    echo "   after the restore: $(health). Send a photo of this screen to Claude."; exit 1
  }
  \cp -p "$LP" "$LP.bak_S701" || stop "could not keep a backup of $LP"
  \cp "$WN/portal/portal_inbox.py" "$LP" && chmod --reference="$LP.bak_S701" "$LP" 2>/dev/null
  [ "$(m5 "$LP")" = "$TO" ] || { echo "!! read-back did not match"; restore; }
  "$SYSTEMCTL" restart "$SVC"
  h=""; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); echo "$h" | grep -q '"S701"' && break; done
  echo "$h" | grep -q '"S701"' || { echo "!! RED after placing: the inbox did not come back as S701 ($h)"; restore; }
  R=$(cd /tmp && /usr/bin/flock -w 60 "$LOCKF" "$VPY" -B "$LR" 2>&1; echo "rc=$?")
  echo "$R" | grep -q "rc=0" || { echo "!! RED: the runner failed on the box: $R"; restore; }
  echo "5. PART 1 DONE: portal_inbox.py placed (backup portal_inbox.py.bak_S701), $SVC restarted, inbox health S701, the runner ran once (rc 0)"
fi

\cp "$KDIR/swap_key_s701.py" "$LS" && chmod 700 "$LS"
[ "$(m5 "$LS")" = "$STO" ] || { echo "!! $LS did not read back"; exit 1; }
echo "6. PART 2 -- the key (do NOT press Regenerate until the lines below say NOW)."
"$PY" -B "$LS" apply
RC=$?
echo ""
if [ "$RC" = 0 ]; then echo "$KIT: DONE. The new WhatsApp key is in every live place; a refused send now keeps retrying until the patient's window closes."
elif [ "$RC" = 3 ]; then echo "$KIT: the new key is written everywhere but MyOperator has not yet confirmed it. Send a photo of this screen to Claude."
elif [ "$RC" = 2 ]; then echo "$KIT: PART 1 DONE; the key was left as it is. Run the same line again when you have the new key."
else echo "$KIT: see the lines above (Send a photo of this screen to Claude)."; fi
exit $RC
