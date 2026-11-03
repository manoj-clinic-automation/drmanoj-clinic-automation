#!/bin/bash
# =============================================================================
#  install_S703_CALLS_PLAYER.sh . kit S703 (03-Nov-2026, session S382, the parent) . the Call Console's recording player
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s703kit && cp -rp /root/deploy/repo/deploy_kits/S703_CALLS_PLAYER /tmp/s703kit && bash /tmp/s703kit/install_S703_CALLS_PLAYER.sh
#  (DRY=1 before bash: every gate and the render check; nothing written.)
#
#  /root/portal/calls_console.py  a0f58fec -> see TO below   rebuilt on the box by make_s703.py from the live file (must
#      equal the kit's copy): a player bar at the foot of the screen while a recording plays -- Loading..., a progress bar,
#      time played / length, pause and play, tap the bar to jump, a plain message when the recording cannot be fetched;
#      the row's button shows the time and fills. Nothing else on the page; no route changes. Restarts clinic-portal.
#  ON THE BOX: the page rendered through the live and the new module on S698's made-up data -- the new one carries the
#      player, and with the four S703 pieces taken out it is the live page byte for byte.
#  Red after placing: calls_console.py back byte-identically and clinic-portal restarted.
#  Undo:  \cp -p /root/portal/calls_console.py.bak_S703 /root/portal/calls_console.py && systemctl restart clinic-portal
# =============================================================================
set -u
KIT="S703_CALLS_PLAYER"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
PD="${PD:-/root/portal}"; WA="${WA:-/root/wa}"; REPO="${REPO:-/root/deploy/repo}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
LP="$PD/calls_console.py"; PCF="$WA/portal_console.py"; W698="$REPO/deploy_kits/S698_CALLS_R1/walk_s698.py"
FROM=a0f58fec929be96d02cfc278776bd631; TO=e0f9312a2fc9756fe595885e565c7d6c
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(phz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting calls_console.py back"
  \cp -p "$LP.bak_S703" "$LP"; "$SYSTEMCTL" restart "$PSVC" || true
  [ "$(m5 "$LP")" = "$FROM" ] && echo "   calls_console.py is back byte-identically (${FROM:0:8})" || echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S703 back by hand"
  echo "   portal health $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/calls_console.py")" = "$TO" ] || stop "the kit's calls_console.py is not the built one"
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L=$(m5 "$LP")
if [ "$L" = "$TO" ]; then echo "-- ALREADY INSTALLED: calls_console.py is the kit's (${TO:0:8}). Nothing written. portal health $(phz)"; exit 0; fi
[ "$L" = "$FROM" ] || stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
[ -f "$PCF" ] && [ -f "$W698" ] || stop "$PCF or $W698 is not there (the render check needs both, read only)"
SCR=$(mktemp -d /tmp/s703.XXXX)
"$VPY" -B "$KDIR/make_s703.py" "$LP" "$SCR/calls_console.py" >/dev/null || stop "make_s703.py refused the live file"
[ "$(m5 "$SCR/calls_console.py")" = "$TO" ] || stop "the file rebuilt from the live one is not the kit's copy"
"$VPY" -B -m py_compile "$SCR/calls_console.py" || stop "the new file does not compile with $VPY"
echo "[2/6] the live calls_console.py is S698's (${FROM:0:8}); rebuilt from it on the box = the kit's copy (${TO:0:8}); compiles"
R=$(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/render_s703.py" "$LP" "$SCR/calls_console.py" "$PCF" "$W698" "$KDIR/make_s703.py" 2>&1 | tail -1)
case "$R" in "RENDER OK"*) ;; *) stop "the render check is not green ($R)";; esac
echo "[3/6] the page rendered on made-up data through the live and the new module: $R"
R=$(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/render_s703.py" "$LP" "$LP" "$PCF" "$W698" "$KDIR/make_s703.py" 2>&1 | tail -1)
case "$R" in "RENDER RED"*) ;; *) stop "the control (the live module twice) did not go red ($R)";; esac
echo "      control (the live module in place of the new): red, as it must be"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[4/6] the build lock taken; the doctor's auto-fix paused for the restart ($([ "$OFF_MINE" = 1 ] && echo 'by this kit' || echo 'it was already off -- left as it is'))"
\cp -p "$LP" "$LP.bak_S703" || stop "could not keep a backup of $LP"
PLACED=1
\cp "$SCR/calls_console.py" "$LP.s703new" && chmod --reference="$LP.bak_S703" "$LP.s703new" && mv -f "$LP.s703new" "$LP" || restore "the file could not be placed"
[ "$(m5 "$LP")" = "$TO" ] || restore "read-back did not match"
echo "[5/6] placed calls_console.py (${TO:0:8}), read back; backup calls_console.py.bak_S703"
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1"
c2=$(hcode "http://127.0.0.1:$PPORT/portal/console"); case "$c2" in 302|401|403|303) ;; *) restore "/portal/console answered $c2 without a login";; esac
c3=$(hcode "http://127.0.0.1:$PPORT/portal/rec/1_1"); case "$c3" in 302|401|403|303) ;; *) restore "/portal/rec answered $c3 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null | awk '/Starting gunicorn|Listening at:/{f=1} f{print} END{if(!f)exit 9}')" || JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -c -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[6/6] $PSVC restarted at $T0: health $p1; /portal/console $c2 and /portal/rec $c3 without a login (the gate); the new master's journal clean"
echo ""
echo "$KIT: DONE. On the Call Console a recording now plays in a player at the foot of the screen, with a progress bar and its time."
