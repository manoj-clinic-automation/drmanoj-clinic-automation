#!/bin/bash
# =============================================================================
#  install_S734_PACKS_HEAD_STOP.sh . kit S734 (06-Nov-2026, session S394, the parent) . F-1148
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s734kit && cp -rp /root/deploy/repo/deploy_kits/S734_PACKS_HEAD_STOP /tmp/s734kit && bash /tmp/s734kit/install_S734_PACKS_HEAD_STOP.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s734kit/install_S734_PACKS_HEAD_STOP.sh --undo
#
#  /root/finance/packs.py  fb987b27 (S729) -> 7dc8c39a  (make_s734.py: 1 counted edit on the live bytes)
#    a statement's head also ends at an ICICI 'serial + date' row, an SBI 'd Mon yyyy' row and an HDFC 'dd/mm/yy' row
#    (a line ending in an amount, with words, not a period line), so a narration never reaches the holder words. Before placing: every readable paper on the live shelf is
#    identified and placed by the old and the new file and must come out the same (counts only are printed).
#    Restarts clinic-finance; red after placing: the old file back.
# =============================================================================
set -u
KIT="S734_PACKS_HEAD_STOP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN="${FIN:-/root/finance}"
FDB="${FDB:-$FIN/finance.db}"
VPY="${VPY:-}"; if [ -z "$VPY" ]; then for c in /root/wa/venv/bin/python3 /usr/bin/python3 "$(command -v python3)"; do [ -x "$c" ] && "$c" -c "import flask" 2>/dev/null && VPY="$c" && break; done; fi
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
LF="$FIN/packs.py"; FROM=fb987b271f9b99dec2c696590501b19d; TO=7dc8c39a83965b5839cac46138bb1d63
WALK_OK="WALK OK 15/15"
HAVE_LOCK=0; PLACED=0; W=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$W" ] && rm -rf "$W"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }
door() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/packs"; }
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
    printf '%s\n' "$jl" | grep -q "packs NOT mounted" && return 2
    printf '%s\n' "$jl" | grep -q -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError' && return 3
  fi
  return 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting packs.py back"
  \cp -p "$LF.bak_S734" "$LF"; find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; restart_ok
  [ "$(m5 "$LF")" = "$FROM" ] && echo "   packs.py is back byte-identically" || echo "   !! copy $LF.bak_S734 back by hand"
  echo "   after the restore: finance $(health). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
[ -n "$VPY" ] || stop "no python on this box can import flask for the walk"
command -v pdftotext >/dev/null 2>&1 || stop "pdftotext is not on this box"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/packs.py")" = "$TO" ] || stop "the kit's packs.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$LF.bak_S734" ] || stop "no backup $LF.bak_S734 -- nothing to undo"
  [ "$(m5 "$LF")" = "$TO" ] || stop "the live packs.py is not this kit's -- a later change would be undone; nothing done"
  [ "$(m5 "$LF.bak_S734")" = "$FROM" ] || stop "the backup $LF.bak_S734 is not the file this kit replaced (${FROM:0:8}); nothing done"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK)"; HAVE_LOCK=1
  \cp -p "$LF.bak_S734" "$LF"; find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  restart_ok || { echo "!! UNDONE but the finance app is NOT healthy after the restart ($(health)). Send a photo of this screen to Claude."; exit 1; }
  echo "UNDONE: packs.py $(m5 "$LF" | cut -c1-8), finance $(health)."; exit 0
fi
echo "1. kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST)"; fi
NOW=$(m5 "$LF")
if [ "$NOW" = "$TO" ]; then echo "-- ALREADY INSTALLED (packs.py ${TO:0:8})"; exit 0; fi
[ "$NOW" = "$FROM" ] || stop "the live packs.py changed since this kit was built (live ${NOW:0:8}, kit expects ${FROM:0:8})"
echo "2. the live packs.py is the one this kit was built from (${FROM:0:8})"
[ -f "$FIN/stmt_shelf.py" ] || stop "$FIN/stmt_shelf.py not found"
W=$(mktemp -d /tmp/s734w.XXXX); chmod 700 "$W"
"$VPY" -B "$KDIR/make_s734.py" "$LF" "$W/rebuilt.py" --expect "$TO" >/dev/null || stop "the kit's file is not exactly the live file plus this kit's edit"
echo "3. rebuilt from the live bytes on this box: the same file as the kit's (${TO:0:8})"
\cp "$KDIR/packs.py" "$W/kit.py"; \cp "$LF" "$W/live.py"
R=$(cd "$W" && TMPDIR="$W" "$VPY" -B "$KDIR/walk_s734.py" "$W/kit.py" "$W/live.py" "$FIN/stmt_shelf.py" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$W" && TMPDIR="$W" "$VPY" -B "$KDIR/walk_s734.py" "$W/kit.py" "$W/live.py" "$FIN/stmt_shelf.py" 2>&1 | grep -E 'FAIL|Error' | head); stop "the walk is not green ($R)"; }
echo "4. the walk (papers laid out like the real ones, made-up names and numbers): $R"
R=$(cd "$W" && TMPDIR="$W" "$VPY" -B "$KDIR/walk_s734.py" "$W/live.py" "$W/live.py" "$FIN/stmt_shelf.py" 2>&1 | tail -1)
case "$R" in "WALK RED"*) echo "   control (the live file): $R -- red, as it must be";; *) stop "the control did not go red ($R)";; esac
[ -f "$FDB" ] || stop "no finance database at $FDB"
"$VPY" -B -c "import sqlite3,sys; s=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True,timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$FDB" "$W/copy.db" || stop "could not take a read-only copy of the finance database"
R=$(cd "$W" && TMPDIR="$W" "$VPY" -B "$KDIR/shelf_s734.py" "$W/kit.py" "$W/live.py" "$FIN/stmt_shelf.py" "$W/copy.db" 2>&1)
rm -f "$W/copy.db"
printf '%s\n' "$R" | grep -E "^  " | sed 's/^/ /'
[ "$(printf '%s\n' "$R" | tail -1)" = "SHELF OK" ] || stop "a paper on the shelf would be read or placed differently"
echo "5. the whole shelf, old file against new: every readable paper read and placed the same (copy deleted)"
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
[ "$(m5 "$LF")" = "$FROM" ] || stop "packs.py changed while this kit was checking -- run the line again"
\cp -p "$LF" "$LF.bak_S734" || stop "could not keep a backup"
[ "$(m5 "$LF.bak_S734")" = "$FROM" ] || stop "the backup did not read back"
echo "6. backup: packs.py.bak_S734"
PLACED=1
\cp "$KDIR/packs.py" "$LF.s734new" && chmod --reference="$LF.bak_S734" "$LF.s734new" && chown --reference="$LF.bak_S734" "$LF.s734new" && mv -f "$LF.s734new" "$LF" || restore "packs.py could not be placed"
[ "$(m5 "$LF")" = "$TO" ] || restore "read-back did not match"
find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "7. placed packs.py (${TO:0:8}), read back by md5"
restart_ok; rc=$?
case "$rc" in 0) ;; 1) restore "the finance app is not healthy after the restart";; 2) restore "the journal says packs did not mount";; *) restore "the journal shows an error from the new processes";; esac
D=$(door)
case "$D" in 200|302|303|401|403) ;; *) restore "the packs page answered $D";; esac
PLACED=0
echo "8. $SVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST') and healthy; the packs page answers ($D, signed out); journal clean"
echo ""
echo "$KIT: DONE. A bank statement's head now ends at its first row, so a narration can no longer be taken for the holder or the bank."
