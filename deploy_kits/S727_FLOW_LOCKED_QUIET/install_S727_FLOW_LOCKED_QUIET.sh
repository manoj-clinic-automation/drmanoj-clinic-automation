#!/bin/bash
# =============================================================================
#  install_S727_FLOW_LOCKED_QUIET.sh . kit S727 (06-Nov-2026, session S390, the parent) . F-1128
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s727kit && cp -rp /root/deploy/repo/deploy_kits/S727_FLOW_LOCKED_QUIET /tmp/s727kit && bash /tmp/s727kit/install_S727_FLOW_LOCKED_QUIET.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s727kit/install_S727_FLOW_LOCKED_QUIET.sh --undo
#
#  /root/staff_register/staff_register.py  ffbe8db2 (S724) -> 18973ca9  (make_s727.py: 4 counted edits on the live bytes)
#    a LOCKED month's approvals are history: its flow page, sheet pages and lock desk never call them stale. Unlocked months
#    are as S724 made them. Restarts staff-register; red after placing: the old file back.
# =============================================================================
set -u
KIT="S727_FLOW_LOCKED_QUIET"
KDIR="$(cd "$(dirname "$0")" && pwd)"
REG="${REG:-/root/staff_register}"
VPY="${VPY:-}"; if [ -z "$VPY" ]; then for c in /root/wa/venv/bin/python3 /usr/bin/python3 "$(command -v python3)"; do [ -x "$c" ] && "$c" -c "import flask" 2>/dev/null && VPY="$c" && break; done; fi
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
RSVC="${RSVC:-staff-register}"; RPORT="${RPORT:-8044}"
LF="$REG/staff_register.py"; FROM=ffbe8db2e299c8ba224c72ed11a6272b; TO=18973ca92609519ed9aea819a66b9f68
WALK_OK="WALK OK 21/21"
HAVE_LOCK=0; PLACED=0; W=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$W" ] && rm -rf "$W"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
rhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$RPORT/register/health"; }
flowdoor() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$RPORT/register/salary/flow"; }
restart_ok() { "$SYSTEMCTL" restart "$RSVC"; h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(rhealth); [ "$h" = 200 ] && break; done; [ "$h" = 200 ]; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting staff_register.py back"
  \cp -p "$LF.bak_S727" "$LF"; restart_ok
  [ "$(m5 "$LF")" = "$FROM" ] && echo "   staff_register.py is back byte-identically" || echo "   !! copy $LF.bak_S727 back by hand"
  echo "   after the restore: the register $(rhealth). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
[ -n "$VPY" ] || stop "no python on this box can import flask for the walk"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/staff_register.py")" = "$TO" ] || stop "the kit's staff_register.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$LF.bak_S727" ] || stop "no backup $LF.bak_S727 -- nothing to undo"
  [ "$(m5 "$LF")" = "$TO" ] || stop "the live staff_register.py is not this kit's -- a later change would be undone; nothing done"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK)"; HAVE_LOCK=1
  \cp -p "$LF.bak_S727" "$LF"; restart_ok; echo "UNDONE: staff_register.py $(m5 "$LF" | cut -c1-8), the register $(rhealth)."; exit 0
fi
echo "1. kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST)"; fi
NOW=$(m5 "$LF")
if [ "$NOW" = "$TO" ]; then echo "-- ALREADY INSTALLED (staff_register.py ${TO:0:8})"; exit 0; fi
[ "$NOW" = "$FROM" ] || stop "the live staff_register.py changed since this kit was built (live ${NOW:0:8}, kit expects ${FROM:0:8})"
echo "2. the live staff_register.py is the one this kit was built from (${FROM:0:8})"
W=$(mktemp -d /tmp/s727w.XXXX); chmod 700 "$W"
"$VPY" -B "$KDIR/make_s727.py" "$LF" "$W/rebuilt.py" --expect "$TO" >/dev/null || stop "the kit's file is not exactly the live file plus this kit's edits"
echo "3. rebuilt from the live bytes on this box: the same file as the kit's (${TO:0:8})"
\cp "$KDIR/staff_register.py" "$W/kit.py"; \cp "$LF" "$W/live.py"
R=$(cd "$W" && "$VPY" -B "$KDIR/walk_s727.py" "$W/kit.py" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$W" && "$VPY" -B "$KDIR/walk_s727.py" "$W/kit.py" 2>&1 | grep FAIL | head); stop "the walk is not green ($R)"; }
echo "4. the walk (a made-up database, the file's own routes): $R"
R=$(cd "$W" && "$VPY" -B "$KDIR/walk_s727.py" "$W/live.py" 2>&1 | tail -1)
case "$R" in "WALK RED"*) echo "   control (the live file): $R -- red, as it must be";; *) stop "the control did not go red ($R)";; esac
[ "$(rhealth)" = 200 ] || stop "the staff register is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
[ "$(m5 "$LF")" = "$FROM" ] || stop "staff_register.py changed while this kit was checking -- run the line again"
\cp -p "$LF" "$LF.bak_S727" || stop "could not keep a backup"
echo "5. backup: staff_register.py.bak_S727"
PLACED=1
\cp "$KDIR/staff_register.py" "$LF.s727new" && chmod --reference="$LF.bak_S727" "$LF.s727new" && chown --reference="$LF.bak_S727" "$LF.s727new" && mv -f "$LF.s727new" "$LF" || restore "staff_register.py could not be placed"
[ "$(m5 "$LF")" = "$TO" ] || restore "read-back did not match"
echo "6. placed staff_register.py (${TO:0:8}), read back by md5"
restart_ok || restore "the register is not healthy after the restart"
D=$(flowdoor)
case "$D" in 200|302|303|401|403) ;; *) restore "the month-end flow answered $D";; esac
PLACED=0
echo "7. $RSVC restarted and healthy; the month-end flow answers ($D, signed out)"
echo ""
echo "$KIT: DONE. A locked month (October) no longer asks for its sheets to be approved again."
