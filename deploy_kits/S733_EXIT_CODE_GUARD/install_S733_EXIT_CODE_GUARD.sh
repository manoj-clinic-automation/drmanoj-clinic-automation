#!/bin/bash
# =============================================================================
#  install_S733_EXIT_CODE_GUARD.sh . kit S733 (06-Nov-2026, session S394, the parent) . F-1147
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s733kit && cp -rp /root/deploy/repo/deploy_kits/S733_EXIT_CODE_GUARD /tmp/s733kit && bash /tmp/s733kit/install_S733_EXIT_CODE_GUARD.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s733kit/install_S733_EXIT_CODE_GUARD.sh --undo
#
#  /root/finance/joiner_app.py  6305b05d -> be2bf7e5  (make_s733.py: 7 counted edits on the live bytes)
#    an exit finds the leaver's machine code when it is opened; the 'removed from the biometric
#    device' tick retires that code, is REFUSED when there is none, and never moves the date of
#    a code already retired. Joining is untouched. Restarts clinic-finance; red after placing:
#    the old file back.
# =============================================================================
set -u
KIT="S733_EXIT_CODE_GUARD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN="${FIN:-/root/finance}"
FDB="${FDB:-$FIN/finance.db}"
VPY="${VPY:-}"; if [ -z "$VPY" ]; then for c in /root/wa/venv/bin/python3 /usr/bin/python3 "$(command -v python3)"; do [ -x "$c" ] && "$c" -c "import flask" 2>/dev/null && VPY="$c" && break; done; fi
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
LF="$FIN/joiner_app.py"; FROM=6305b05dccf0d915924c9f698eddc94e; TO=be2bf7e539c409cf52e525bbd86e8aba
WALK_OK="WALK OK 36/36"
HAVE_LOCK=0; PLACED=0; W=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$W" ] && rm -rf "$W"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }
door() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/staff/api/healthz"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$SVC" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }
restart_ok() {
  local since old jl p; since=$(date '+%Y-%m-%d %H:%M:%S'); old="$(pids_of | tr '\n' ' ')"
  "$SYSTEMCTL" restart "$SVC"; h=000
  for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
  [ "$h" = 200 ] || return 1
  if command -v "$JOURNALCTL" >/dev/null 2>&1; then
    # F-1135: the stopping master's shutdown noise is not this install's -- the old PIDs' lines are left out
    jl="$("$JOURNALCTL" -u "$SVC" --since "$since" --no-pager -o short 2>/dev/null)"
    for p in $old; do jl="$(printf '%s\n' "$jl" | grep -v -E "\[$p\]:")"; done
    printf '%s\n' "$jl" | grep -q "joiner_app NOT mounted" && return 2
    printf '%s\n' "$jl" | grep -q -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError' && return 3
  fi
  return 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting joiner_app.py back"
  \cp -p "$LF.bak_S733" "$LF"; find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; restart_ok
  [ "$(m5 "$LF")" = "$FROM" ] && echo "   joiner_app.py is back byte-identically" || echo "   !! copy $LF.bak_S733 back by hand"
  echo "   after the restore: finance $(health). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
[ -n "$VPY" ] || stop "no python on this box can import flask for the walk"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/joiner_app.py")" = "$TO" ] || stop "the kit's joiner_app.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$LF.bak_S733" ] || stop "no backup $LF.bak_S733 -- nothing to undo"
  [ "$(m5 "$LF")" = "$TO" ] || stop "the live joiner_app.py is not this kit's -- a later change would be undone; nothing done"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK)"; HAVE_LOCK=1
  \cp -p "$LF.bak_S733" "$LF"; find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  restart_ok || { echo "!! UNDONE but the finance app is NOT healthy after the restart ($(health)). Send a photo of this screen to Claude."; exit 1; }
  echo "UNDONE: joiner_app.py $(m5 "$LF" | cut -c1-8), finance $(health)."; exit 0
fi
echo "1. kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST)"; fi
NOW=$(m5 "$LF")
if [ "$NOW" = "$TO" ]; then echo "-- ALREADY INSTALLED (joiner_app.py ${TO:0:8})"; exit 0; fi
[ "$NOW" = "$FROM" ] || stop "the live joiner_app.py changed since this kit was built (live ${NOW:0:8}, kit expects ${FROM:0:8})"
echo "2. the live joiner_app.py is the one this kit was built from (${FROM:0:8})"
[ -f "$FIN/joiner_schema.sql" ] || stop "no $FIN/joiner_schema.sql for the walk"
W=$(mktemp -d /tmp/s733w.XXXX); chmod 700 "$W"
"$VPY" -B "$KDIR/make_s733.py" "$LF" "$W/rebuilt.py" --expect "$TO" >/dev/null || stop "the kit's file is not exactly the live file plus this kit's edits"
echo "3. rebuilt from the live bytes on this box: the same file as the kit's (${TO:0:8})"
mkdir -p "$W/kit" "$W/live"
\cp "$KDIR/joiner_app.py" "$W/kit/joiner_app.py"; \cp "$LF" "$W/live/joiner_app.py"
\cp "$FIN/joiner_schema.sql" "$W/kit/"; \cp "$FIN/joiner_schema.sql" "$W/live/"
R=$(cd "$W" && TMPDIR="$W" "$VPY" -B "$KDIR/walk_s733.py" "$W/kit/joiner_app.py" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$W" && TMPDIR="$W" "$VPY" -B "$KDIR/walk_s733.py" "$W/kit/joiner_app.py" 2>&1 | grep FAIL | head); stop "the walk is not green ($R)"; }
echo "4. the walk (a made-up register, the file's own routes): $R"
R=$(cd "$W" && TMPDIR="$W" "$VPY" -B "$KDIR/walk_s733.py" "$W/live/joiner_app.py" 2>&1 | tail -1)
case "$R" in "WALK RED"*) echo "   control (the live file): $R -- red, as it must be";; *) stop "the control did not go red ($R)";; esac
[ -f "$FDB" ] || stop "no finance database at $FDB"
"$VPY" -B -c "import sqlite3,sys; s=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True,timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$FDB" "$W/copy.db" || stop "could not take a read-only copy of the finance database"
R=$(cd "$W" && TMPDIR="$W" "$VPY" -B "$KDIR/live_shape_s733.py" "$W/kit/joiner_app.py" "$W/copy.db" 2>&1)
rm -f "$W/copy.db"
printf '%s\n' "$R" | grep -E "exit |open exits|AMBIGUOUS|FAIL" | sed 's/^/   /'
[ "$(printf '%s\n' "$R" | tail -1)" = "LIVE-SHAPE OK" ] || stop "the live-shape read on a copy of today's register is not green"
echo "5. live shape on a copy of today's register: every live code found from its own name; each open exit's tick retires only a code the register gives to that leaver (copy deleted)"
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
[ "$(m5 "$LF")" = "$FROM" ] || stop "joiner_app.py changed while this kit was checking -- run the line again"
\cp -p "$LF" "$LF.bak_S733" || stop "could not keep a backup"
[ "$(m5 "$LF.bak_S733")" = "$FROM" ] || stop "the backup did not read back"
echo "6. backup: joiner_app.py.bak_S733"
PLACED=1
\cp "$KDIR/joiner_app.py" "$LF.s733new" && chmod --reference="$LF.bak_S733" "$LF.s733new" && chown --reference="$LF.bak_S733" "$LF.s733new" && mv -f "$LF.s733new" "$LF" || restore "joiner_app.py could not be placed"
[ "$(m5 "$LF")" = "$TO" ] || restore "read-back did not match"
find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "7. placed joiner_app.py (${TO:0:8}), read back by md5"
restart_ok; rc=$?
case "$rc" in 0) ;; 1) restore "the finance app is not healthy after the restart";; 2) restore "the journal says the joiner register did not mount";; *) restore "the journal shows an error from the new processes";; esac
D=$(door)
case "$D" in 200|302|303|401|403) ;; *) restore "the joiner register answered $D";; esac
PLACED=0
echo "8. $SVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST') and healthy; the joiner register answers ($D, signed out); journal clean"
echo ""
echo "$KIT: DONE. An exit now carries the leaver's machine code, and ticking 'removed from the biometric device' retires it -- never a date already set."
