#!/bin/bash
# =============================================================================
#  install_S639_PARCHI_DESK.sh · kit S639 (24-Oct-2026, session S347) · D775
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s639kit && cp -rp /root/deploy/repo/deploy_kits/S639_PARCHI_DESK /tmp/s639kit && bash /tmp/s639kit/install_S639_PARCHI_DESK.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  /root/finance/parchi_desk.py  NEW                  99b7e43b   the parchi desk: OPD, X-ray/Proc, Blood test on one page
#  /root/finance/slip_log.py     2419c536 -> 93103944  7 counted edits (make_s639.py): mounts the desk; the room's Paid/Done no
#                                                        longer asked (report, reminder, badge); the desk in the menu and the report;
#                                                        a chhoot line on today's list no longer takes the menu down (TypeError)
#  No data step, no new table. ONE restart of clinic-finance.
#  Red after placing: the old file back byte-identically, parchi_desk.py set aside, restart, healthz.
#  Undo:  \cp -p /root/finance/slip_log.py.bak_S639_2419c536 /root/finance/slip_log.py && mv /root/finance/parchi_desk.py /root/finance/parchi_desk.py.off_S639 && systemctl restart clinic-finance
# =============================================================================
set -u
KIT="S639_PARCHI_DESK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N="slip_log.py"; FROM=2419c5360570a307cad9cf1094cebe68; TO=93103944a60cbce13ec4dde462626bf6
D="parchi_desk.py"; D_TO=99b7e43b95a034398962269dc6ce84fa
BAK="$FIN/$N.bak_S639_${FROM:0:8}"
HAVE_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }
restore() { \cp -p "$BAK" "$FIN/$N"; [ -f "$FIN/$D" ] && mv "$FIN/$D" "$FIN/$D.off_S639"; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
[ "$(m5 "$KDIR/$N")" = "$TO" ] || stop "the kit's $N is not the built file"
[ "$(m5 "$KDIR/$D")" = "$D_TO" ] || stop "the kit's $D is not the built file"
LIVE=$(m5 "$FIN/$N"); LD=$(m5 "$FIN/$D")
if [ "$LIVE" = "$TO" ] && [ "$LD" = "$D_TO" ]; then echo "ALREADY INSTALLED."; exit 0; fi
[ "$LIVE" = "$FROM" ] || stop "the live $N changed since this kit was built (live ${LIVE:0:8}, kit expects ${FROM:0:8})"
[ -e "$FIN/$D" ] && stop "$FIN/$D already exists - this kit does not overwrite it"
echo "2. the live file is the one this kit was built from; $D is new"
for f in "$N" "$D" walk_s639.py; do "$PY" -B -m py_compile "$KDIR/$f" || stop "$f does not compile with $PY"; done
R=$("$PY" -B walk_s639.py "$KDIR" "$FIN" 2>&1 | tail -1); case "$R" in "27 of 27 green") echo "3. walk: $R";; *) "$PY" -B walk_s639.py "$KDIR" "$FIN" 2>&1 | grep RED; stop "the walk is not green ($R)";; esac
R=$("$PY" -B walk_s639.py "$FIN" "$FIN" --old 2>&1 | tail -1); case "$R" in *" 0 older red · "*) echo "   control on the live file: $R";; *) echo "$R"; stop "the control on the live file did not go as expected";; esac
R=$("$PY" -B walk_s639.py "$KDIR" "$FIN" --no-desk 2>&1 | tail -1); case "$R" in *" 0 older red · "*) echo "   the new slip_log without the desk: $R";; *) echo "$R"; stop "the new slip_log does not stand without parchi_desk.py";; esac
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
\cp -p "$FIN/$N" "$BAK" || stop "could not keep a backup"
\cp "$KDIR/$D" "$FIN/$D" && chmod --reference="$BAK" "$FIN/$D" 2>/dev/null
\cp "$KDIR/$N" "$FIN/$N" && chmod --reference="$BAK" "$FIN/$N" 2>/dev/null
if [ "$(m5 "$FIN/$N")" != "$TO" ] || [ "$(m5 "$FIN/$D")" != "$D_TO" ]; then restore; stop "read-back did not match; the old file is back"; fi
echo "4. placed $FIN/$D $D_TO · $FIN/$N $TO (backup ${BAK##*/})"
"$SYSTEMCTL" restart "$SVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
if [ "$h" != 200 ]; then
  echo "!! RED after placing (healthz $h) - putting the old file back"
  restore; "$SYSTEMCTL" restart "$SVC"
  h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  echo "   after the restore: healthz $h2. Send a photo of this screen to Claude."; exit 1
fi
journalctl -u "$SVC" --since "-60 s" --no-pager 2>/dev/null | grep -q "parchi_desk NOT mounted" && echo "   NOTE: the log says the desk did not mount - tell Claude."
echo "5. $SVC restarted; healthz 200"
echo ""
echo "INSTALLED. The parchi desk: https://followup.dr-manoj.in/finance/slips/desk"
