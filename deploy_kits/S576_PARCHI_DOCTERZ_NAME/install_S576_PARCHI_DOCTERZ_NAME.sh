#!/bin/bash
# =============================================================================
#  install_S576_PARCHI_DOCTERZ_NAME.sh · kit S576 (18-Oct-2026, session S319)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s576kit && cp -rp /root/deploy/repo/deploy_kits/S576_PARCHI_DOCTERZ_NAME /tmp/s576kit && bash /tmp/s576kit/install_S576_PARCHI_DOCTERZ_NAME.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  /root/finance/slip_log.py   87f07d57 -> 2419c536   2 counted edits (make_s576.py)
#  The parchi (and every page that asks slip_log.patient) shows Docterz's newest name for a clinic ID when it differs
#  from the patient master; the master's last-4 stays. No data step. ONE restart of clinic-finance.
#  Red after placing: the old file back byte-identically, restart, healthz.
#  Undo:  \cp -p /root/finance/slip_log.py.bak_S576_87f07d57 /root/finance/slip_log.py && systemctl restart clinic-finance
# =============================================================================
set -u
KIT="S576_PARCHI_DOCTERZ_NAME"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N="slip_log.py"
FROM=87f07d57f61a5c0e031d6ff0f01585d0; TO=2419c5360570a307cad9cf1094cebe68
BAK="$FIN/$N.bak_S576_${FROM:0:8}"
HAVE_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
[ "$(m5 "$KDIR/$N")" = "$TO" ] || stop "the kit's $N is not the built file"
LIVE=$(m5 "$FIN/$N")
if [ "$LIVE" = "$TO" ]; then echo "ALREADY INSTALLED ($FIN/$N $TO)."; exit 0; fi
[ "$LIVE" = "$FROM" ] || stop "the live $N changed since this kit was built (live ${LIVE:0:8}, kit expects ${FROM:0:8})"
echo "2. the live file is the one this kit was built from"
"$PY" -B -m py_compile "$KDIR/$N" || stop "$N does not compile with $PY"
R=$("$PY" -B walk_s576.py "$KDIR/$N" 2>&1 | tail -1); case "$R" in *"8 of 8 green"*) echo "3. walk: $R";; *) echo "$R"; stop "the walk is not green";; esac
R=$("$PY" -B walk_s576.py "$FIN/$N" --old 2>&1 | tail -1); case "$R" in *"1 S576 check(s) red"*"0 older"*) echo "   control on the live file: $R";; *) echo "$R"; stop "the control on the live file did not go red";; esac
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
\cp -p "$FIN/$N" "$BAK" || stop "could not keep a backup"
\cp "$KDIR/$N" "$FIN/$N" && chmod --reference="$BAK" "$FIN/$N" 2>/dev/null
[ "$(m5 "$FIN/$N")" = "$TO" ] || { \cp -p "$BAK" "$FIN/$N"; stop "read-back did not match; the old file is back"; }
echo "4. placed $FIN/$N $TO (backup $BAK)"
"$SYSTEMCTL" restart "$SVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
if [ "$h" != 200 ]; then
  echo "!! RED after placing (healthz $h) - putting the old file back"
  \cp -p "$BAK" "$FIN/$N"; "$SYSTEMCTL" restart "$SVC"
  h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  echo "   after the restore: healthz $h2. Send a photo of this screen to Claude."; exit 1
fi
echo "5. $SVC restarted; healthz 200"
echo ""
echo "INSTALLED. The parchi now shows Docterz's newest name for each clinic ID."
