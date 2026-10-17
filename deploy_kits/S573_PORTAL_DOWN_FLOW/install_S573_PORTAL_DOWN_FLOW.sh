#!/bin/bash
# =============================================================================
#  install_S573_PORTAL_DOWN_FLOW.sh · kit S573 (17-Oct-2026, session S319)
#
#  Run on the server (the README's one line):
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s573kit && cp -rp /root/deploy/repo/deploy_kits/S573_PORTAL_DOWN_FLOW /tmp/s573kit && bash /tmp/s573kit/install_S573_PORTAL_DOWN_FLOW.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  Places two NEW files and edits nothing that exists:
#    /root/deploy/clinic_doctor.py      the repair command (checks, restarts only what is down, verdict, log)
#    /usr/local/bin/clinic-doctor       the one word the owner types
#  No service is restarted by this installer. At the end it runs `clinic-doctor --check` (read-only) once.
#  Housekeeping: removes old build scratch in /tmp (s554kit, s554probe, s562kit, s562probe, s564kit) if present.
#  Undo:  rm -f /usr/local/bin/clinic-doctor /root/deploy/clinic_doctor.py
# =============================================================================
set -u
KIT="S573_PORTAL_DOWN_FLOW"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
DEST="${DEST:-/root/deploy/clinic_doctor.py}"
BIN="${BIN:-/usr/local/bin/clinic-doctor}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
HOUSEKEEP="${HOUSEKEEP:-/tmp/s554kit /tmp/s554probe /tmp/s562kit /tmp/s562probe /tmp/s564kit}"
HAVE_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
"$PY" -B -m py_compile clinic_doctor.py || stop "clinic_doctor.py does not compile with $PY"
"$PY" -B -m py_compile walk_s573.py || stop "walk_s573.py does not compile"
echo "2. compiles with $("$PY" -V 2>&1)"
W=$("$PY" -B walk_s573.py "$KDIR/clinic_doctor.py" 2>&1 | tail -1)
case "$W" in *"22 of 22 green"*) echo "3. the walk on this server: $W";; *) echo "$W"; stop "the walk is not all green";; esac
KMD5=$(m5 "$KDIR/clinic_doctor.py")
WRAP='#!/bin/bash
# clinic-doctor -- kit S573. Checks the clinic portal, restarts only what is down, says ALL GOOD / FIXED / NOT FIXED.
exec /usr/bin/python3 -B /root/deploy/clinic_doctor.py "$@"'
if [ "$(m5 "$DEST")" = "$KMD5" ] && [ -x "$BIN" ] && [ "$(cat "$BIN")" = "$WRAP" ]; then
  echo "ALREADY INSTALLED ($DEST $KMD5)."
else
  [ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
  if [ -f "$DEST" ]; then \cp -p "$DEST" "$DEST.bak_S573_$(m5 "$DEST" | cut -c1-8)"; echo "   an older clinic_doctor.py was kept beside it"; fi
  \cp -p "$KDIR/clinic_doctor.py" "$DEST" && chmod 755 "$DEST"
  printf '%s\n' "$WRAP" > "$BIN" && chmod 755 "$BIN"
  [ "$(m5 "$DEST")" = "$KMD5" ] || stop "read-back of $DEST does not match"
  echo "4. placed: $DEST $KMD5 and $BIN"
fi
for d in $HOUSEKEEP; do [ -d "$d" ] && rm -rf "$d" && echo "   housekeeping: removed $d"; done
rm -rf "$LOCK"; HAVE_LOCK=0
echo "5. first run, read-only:"
"$BIN" --check
echo ""
echo "INSTALLED. From now on, when the portal will not open, type:  clinic-doctor"
