#!/bin/bash
# =============================================================================
#  install_S578_PORTAL_SELF_REPAIR.sh · kit S578 (18-Oct-2026, session S325, D734)
#
#  Run on the server (the README's one line):
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s578kit && cp -rp /root/deploy/repo/deploy_kits/S578_PORTAL_SELF_REPAIR /tmp/s578kit && bash /tmp/s578kit/install_S578_PORTAL_SELF_REPAIR.sh
#  (DRY=1 before bash: every gate, the walk and the control, nothing written.)
#
#  Changes on the server:
#    /root/deploy/clinic_doctor.py   af696c77 -> 2.0 (adds --auto; the manual run is unchanged except that it no longer
#                                    restarts the web server when the fault is a part behind it). Backup beside it.
#    /etc/systemd/system/clinic-watchdog.service.d/s578-doctor-first.conf   NEW: the repair runs just before the
#                                    watchman, on the watchman's own 5-minute timer. The watchman's files are not edited.
#    /root/deploy/_off/              NEW empty folder: touch /root/deploy/_off/DOCTOR_AUTO_OFF stops the automatic repair.
#  No service is restarted by this installer. At the end it runs one read-only check and one watchman round.
#  Housekeeping: removes /tmp/s573kit and /tmp/s576kit if present.
#  Undo (README): rm -f the drop-in, systemctl daemon-reload, put the .bak_S578_af696c77 copy back.
# =============================================================================
set -u
KIT="S578_PORTAL_SELF_REPAIR"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
DEST="${DEST:-/root/deploy/clinic_doctor.py}"
BIN="${BIN:-/usr/local/bin/clinic-doctor}"
UNITFILE="${UNITFILE:-/etc/systemd/system/clinic-watchdog.service}"
DROPDIR="${DROPDIR:-/etc/systemd/system/clinic-watchdog.service.d}"
DROP="$DROPDIR/s578-doctor-first.conf"
OFFDIR="${OFFDIR:-/root/deploy/_off}"
STATUS="${STATUS:-/root/deploy/clinic_doctor_status.json}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
HOUSEKEEP="${HOUSEKEEP:-/tmp/s573kit /tmp/s576kit}"
OLD_DOC="af696c7776ee4ba1fd8a9e49163c22dd"     # the live S573 file (live_pins_S319close)
WRAP_PIN="e22da9c93abc6de33fba4d435b9d9a39"    # /usr/local/bin/clinic-doctor (unchanged by this kit)
UNIT_PIN="b3021bd1afa2d5a3f82a6c15b5cfac7a"    # clinic-watchdog.service (read, never edited; the 18-Oct bundle)
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
"$PY" -B -m py_compile walk_s578.py || stop "walk_s578.py does not compile"
echo "2. compiles with $("$PY" -V 2>&1)"
W=$("$PY" -B walk_s578.py "$KDIR/clinic_doctor.py" 2>&1 | tail -1)
case "$W" in *"55 of 55 green"*) echo "3. the walk on this server: $W";; *) echo "$W"; stop "the walk is not all green";; esac
KMD5=$(m5 "$KDIR/clinic_doctor.py")
LIVE=$(m5 "$DEST")
[ "$(m5 "$BIN")" = "$WRAP_PIN" ] || stop "$BIN is not the pinned S573 wrapper"
[ "$(m5 "$UNITFILE")" = "$UNIT_PIN" ] || stop "the watchman's unit file changed since this kit was built ($UNITFILE)"
echo "4. pins: the wrapper and the watchman's unit file are as pinned"
if [ -d "$DROPDIR" ] && [ -n "$(ls -A "$DROPDIR" 2>/dev/null | grep -vx 's578-doctor-first.conf')" ]; then
  stop "$DROPDIR already holds other settings: $(ls -A "$DROPDIR" | tr '\n' ' ')"
fi
if [ "$LIVE" = "$KMD5" ] && [ -f "$DROP" ] && [ "$(m5 "$DROP")" = "$(m5 "$KDIR/s578-doctor-first.conf")" ]; then
  echo "ALREADY INSTALLED ($DEST $KMD5, $DROP)."
  rm -rf "$LOCK"; HAVE_LOCK=0
  exit 0
fi
if [ "$LIVE" != "$KMD5" ]; then
  [ "$LIVE" = "$OLD_DOC" ] || stop "$DEST is $LIVE, not the pinned $OLD_DOC"
  C=$("$PY" -B walk_s578.py "$DEST" 2>&1 | tail -1)
  case "$C" in *"55 of 55 green"*) stop "the control did not go red: the walk cannot tell the live file from the new one";; esac
  echo "5. the control: the same walk on the live file goes red ($C)"
fi
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }

BAK="$DEST.bak_S578_$(echo "$OLD_DOC" | cut -c1-8)"
if [ "$LIVE" != "$KMD5" ]; then
  \cp -p "$DEST" "$BAK" || stop "could not keep a backup of $DEST"
  \cp -p "$KDIR/clinic_doctor.py" "$DEST" && chmod 755 "$DEST"
  if [ "$(m5 "$DEST")" != "$KMD5" ]; then \cp -p "$BAK" "$DEST"; stop "read-back of $DEST did not match; the old file is back"; fi
  echo "6. placed: $DEST $KMD5 (the old one kept as $BAK)"
fi
mkdir -p "$OFFDIR" "$DROPDIR"
\cp "$KDIR/s578-doctor-first.conf" "$DROP" && chmod 644 "$DROP"
if [ "$(m5 "$DROP")" != "$(m5 "$KDIR/s578-doctor-first.conf")" ] || ! "$SYSTEMCTL" daemon-reload; then
  rm -f "$DROP"; "$SYSTEMCTL" daemon-reload; [ -f "$BAK" ] && \cp -p "$BAK" "$DEST"
  stop "the timer hook could not be placed; everything is put back as it was"
fi
"$SYSTEMCTL" show clinic-watchdog.service -p ExecStartPre 2>/dev/null | grep -q "clinic-doctor" \
  || { rm -f "$DROP"; "$SYSTEMCTL" daemon-reload; [ -f "$BAK" ] && \cp -p "$BAK" "$DEST"; stop "systemd did not take the hook; everything is put back as it was"; }
echo "7. the repair now runs first on the watchman's 5-minute timer ($DROP)"
for d in $HOUSEKEEP; do [ -d "$d" ] && rm -rf "$d" && echo "   housekeeping: removed $d"; done
rm -rf "$LOCK"; HAVE_LOCK=0                      # released BEFORE the live round: the automatic run waits while it exists
echo "8. read-only check:"
"$BIN" --check | tail -4
echo "9. one watchman round now (the automatic repair first, then the watchman):"
"$SYSTEMCTL" start clinic-watchdog.service
"$PY" -B -c "import json,sys; s=json.load(open(sys.argv[1])); print('   last run: %s  mode %s  verdict %s' % (s.get('at'), s.get('mode'), s.get('verdict')))" "$STATUS" 2>/dev/null \
  || echo "   (no status file yet -- it is written at the next round)"
echo ""
echo "INSTALLED. The server now repairs its own stuck parts every 5 minutes (at most once an hour each)"
echo "and tells your phone only when it fixed something or could not. clinic-doctor still works by hand as before."
