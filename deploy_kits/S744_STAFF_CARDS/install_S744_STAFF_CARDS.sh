#!/bin/bash
# =============================================================================
#  install_S744_STAFF_CARDS.sh . kit S744 (07-Nov-2026, session S397, the parent) . the Call Console's staff cards
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s744kit && cp -rp /root/deploy/repo/deploy_kits/S744_STAFF_CARDS /tmp/s744kit && bash /tmp/s744kit/install_S744_STAFF_CARDS.sh
#  (DRY=1 before bash: every gate, the walk and the proof on the live stores; nothing written.)
#
#  /root/portal/calls_console.py  72f9769b (S742) -> TO (the kit's copy, whole): + the Staff performance section --
#      one folded line per call-handling staff member with the summary on the top line and its colour; duty from
#      /root/staff_master.csv (times only) and the morning punch from /root/punches.csv, both read-only; inside, the
#      calls behind each figure. Nothing else on the page changes; it reads only.
#  ON THE BOX before anything is written: the walk (made-up data) green on the new page and red on the live page; the
#      proof on the LIVE stores, read-only, counts only: calls, the follow-up list and Call ke baad identical through
#      the live and the new page; every read under 20 s; the page renders with the section.
#  Red after placing: calls_console.py back byte-identically and clinic-portal restarted.
#  Undo:  \cp -p /root/portal/calls_console.py.bak_S744 /root/portal/calls_console.py && systemctl restart clinic-portal
# =============================================================================
set -u
KIT="S744_STAFF_CARDS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
PD="${PD:-/root/portal}"; WA="${WA:-/root/wa}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
CDB="${CDB:-$WA/console.db}"; IDB="${IDB:-$WA/wa_inbox/inbox.db}"; FDB="${FDB:-/root/finance/finance.db}"
SM="${SM:-/root/staff_master.csv}"; PU="${PU:-/root/punches.csv}"
LC="$PD/calls_console.py"; LB="$WA/portal_console.py"
FROM=72f9769b6000e7ed91972eccdcc77574; TO=df484ee523a14611bbb7420995738317
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
  \cp -p "$LC.bak_S744" "$LC"; "$SYSTEMCTL" restart "$PSVC" || true
  [ "$(m5 "$LC")" = "$FROM" ] && echo "   calls_console.py is back byte-identically (${FROM:0:8})" || echo "   !! $LC is NOT ${FROM:0:8} -- copy $LC.bak_S744 back by hand"
  echo "   portal health $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/calls_console.py")" = "$TO" ] || stop "the kit's calls_console.py is not the built one"
echo "[1/7] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L=$(m5 "$LC")
if [ "$L" = "$TO" ]; then echo "-- ALREADY INSTALLED: calls_console.py is the kit's (${TO:0:8}). Nothing written. portal health $(phz)"; exit 0; fi
[ -n "$L" ] || stop "$LC is not there"
[ "$L" = "$FROM" ] || stop "the live $LC changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
[ -f "$LB" ] || stop "$LB is not there (the walk reads its build_fu_all, read only)"
SCR=$(mktemp -d /tmp/s744.XXXX)
\cp "$KDIR/calls_console.py" "$SCR/calls_console.py"
"$VPY" -B -m py_compile "$SCR/calls_console.py" 2>/dev/null || stop "calls_console.py does not compile with $VPY"
echo "[2/7] the live calls_console.py is S742's (${FROM:0:8}); the kit's copy (${TO:0:8}) compiles"
R=$(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s744.py" "$SCR" "$PD" "$LB" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the walk is not green ($R)";; esac
R2=$(mkdir -p "$SCR/live" && \cp "$LC" "$SCR/live/calls_console.py" && cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s744.py" "$SCR/live" "$PD" "$LB" --control 2>&1 | tail -1)
case "$R2" in "CONTROL:"*) ;; *) stop "the control on the live page did not go red ($R2)";; esac
echo "[3/7] the walk on made-up data: $R; on the live page: $R2"
echo "[4/7] the proof on the LIVE stores (read-only, counts only):"
(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/proof_s744.py" "$SCR/calls_console.py" "$LC" "$PD" "$CDB" "$IDB" "$FDB" "$SM" "$PU") > "$SCR/proof.txt" 2>&1
sed 's/^/      /' "$SCR/proof.txt"
tail -1 "$SCR/proof.txt" | grep -q '^PROOF CLEAN' || stop "the proof on the live stores is not clean"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[5/7] the build lock taken; the doctor's auto-fix paused for the restart ($([ "$OFF_MINE" = 1 ] && echo 'by this kit' || echo 'it was already off -- left as it is'))"
\cp -p "$LC" "$LC.bak_S744" || stop "could not keep a backup of $LC"
PLACED=1
\cp "$SCR/calls_console.py" "$LC.s744new" && chmod --reference="$LC.bak_S744" "$LC.s744new" && mv -f "$LC.s744new" "$LC" || restore "the file could not be placed"
[ "$(m5 "$LC")" = "$TO" ] || restore "read-back did not match"
echo "[6/7] placed calls_console.py (${TO:0:8}), read back; backup calls_console.py.bak_S744"
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1"
c2=$(hcode "http://127.0.0.1:$PPORT/portal/console"); case "$c2" in 302|401|403|303) ;; *) restore "/portal/console answered $c2 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null | awk '/Starting gunicorn|Listening at:/{f=1} f{print} END{if(!f)exit 9}')" || JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[7/7] $PSVC restarted at $T0: health $p1; /portal/console $c2 without a login (the gate); the new master's journal clean"
echo ""
echo "$KIT: DONE. The Call Console now carries the staff cards: one folded line per person, its colour saying open me."
