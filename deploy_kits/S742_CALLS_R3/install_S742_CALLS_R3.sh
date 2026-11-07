#!/bin/bash
# =============================================================================
#  install_S742_CALLS_R3.sh . kit S742 (07-Nov-2026, session S397, the parent) . the Call Console to mock-up R3
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s742kit && cp -rp /root/deploy/repo/deploy_kits/S742_CALLS_R3 /tmp/s742kit && bash /tmp/s742kit/install_S742_CALLS_R3.sh
#  (DRY=1 before bash: every gate, the walk and the proof on the live stores; nothing written.)
#
#  /root/portal/calls_console.py  e0f9312a -> TO (the kit's copy, whole): WhatsApps in each timeline (D820's answer
#      rule), the follow-up list cleaned (one open row per patient; Today . Grace . Overdue . Lapsed . Came/closed;
#      F-1106), Call ke baad for the week, the arrow the way it happened, the R3 look (a one-line key, every section
#      folded with a coloured top line, two columns). Reads only.
#  /root/wa/portal_console.py     3317394c -> rebuilt by make_s742.py: + table fu_all (the whole Followups_Today feed,
#      today's rows included). The builder's own selftest must stay green. Takes effect at its next 10-minute run.
#  /root/portal/portal.py         5cf80f82 -> rebuilt by make_s742.py: the 'Follow-up WhatsApps' tile opens the cleaned
#      list on the Call Console (F-1107); the batch page stays at /portal/wa/followups.
#  ON THE BOX before anything is written: the walk (made-up data) on the new page = green and on the live page = red;
#      the proof on the LIVE stores, read-only, counts only: the call figures identical through the live and the new
#      page, every read under 20 s, the page renders.
#  Red after placing: the three files back byte-identically and clinic-portal restarted.
#  Undo:  for f in /root/portal/calls_console.py /root/portal/portal.py /root/wa/portal_console.py; do \cp -p $f.bak_S742 $f; done && systemctl restart clinic-portal
# =============================================================================
set -u
KIT="S742_CALLS_R3"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
PD="${PD:-/root/portal}"; WA="${WA:-/root/wa}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
CDB="${CDB:-$WA/console.db}"; IDB="${IDB:-$WA/wa_inbox/inbox.db}"; FDB="${FDB:-/root/finance/finance.db}"
LC="$PD/calls_console.py"; LB="$WA/portal_console.py"; LP="$PD/portal.py"
F_C=e0f9312a2fc9756fe595885e565c7d6c; F_B=3317394cdd9845690457182d2303fe0f; F_P=5cf80f8259efac4cbc88dcdc12729554
T_C=72f9769b6000e7ed91972eccdcc77574; T_B=a8d050ef8c9e78b57467b58a68789841; T_P=d52261a25791fb00bfdc6cbfcb44a124
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
  echo "!! RED after placing ($1) -- putting the three files back"
  local ok=1
  for f in "$LC" "$LP" "$LB"; do [ -f "$f.bak_S742" ] && \cp -p "$f.bak_S742" "$f"; done
  [ "$(m5 "$LC")" = "$F_C" ] && [ "$(m5 "$LP")" = "$F_P" ] && [ "$(m5 "$LB")" = "$F_B" ] || ok=0
  "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   the three files are back byte-identically" || echo "   !! a file is NOT back -- copy each *.bak_S742 back by hand"
  echo "   portal health $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/calls_console.py")" = "$T_C" ] || stop "the kit's calls_console.py is not the built one"
echo "[1/7] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
if [ "$(m5 "$LC")" = "$T_C" ] && [ "$(m5 "$LB")" = "$T_B" ] && [ "$(m5 "$LP")" = "$T_P" ]; then
  echo "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. portal health $(phz)"; exit 0; fi
[ "$(m5 "$LC")" = "$F_C" ] || stop "the live $LC changed since this kit was built (live $(m5 "$LC" | cut -c1-8), kit expects ${F_C:0:8})"
[ "$(m5 "$LB")" = "$F_B" ] || stop "the live $LB changed since this kit was built (live $(m5 "$LB" | cut -c1-8), kit expects ${F_B:0:8})"
[ "$(m5 "$LP")" = "$F_P" ] || stop "the live $LP changed since this kit was built (live $(m5 "$LP" | cut -c1-8), kit expects ${F_P:0:8})"
SCR=$(mktemp -d /tmp/s742.XXXX)
"$VPY" -B "$KDIR/make_s742.py" "$LB" "$LP" "$SCR" --expect >/dev/null || stop "make_s742.py refused the live files"
[ "$(m5 "$SCR/portal_console.py")" = "$T_B" ] && [ "$(m5 "$SCR/portal.py")" = "$T_P" ] || stop "the files rebuilt from the live ones are not the kit's"
\cp "$KDIR/calls_console.py" "$SCR/calls_console.py"
for f in calls_console.py portal_console.py portal.py; do "$VPY" -B -m py_compile "$SCR/$f" 2>/dev/null || stop "$f does not compile with $VPY"; done
echo "[2/7] the live files are the kit's FROM; rebuilt from them on the box = the kit's TO; all three compile"
R=$(cd "$SCR" && timeout 120 "$VPY" -B "$SCR/portal_console.py" --selftest 2>&1 | tail -1)
case "$R" in "SELFTEST PASSED"*) ;; *) stop "the builder's own selftest is not green ($R)";; esac
R=$(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s742.py" "$SCR" "$PD" "$SCR/portal_console.py" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the walk is not green ($R)";; esac
R2=$(mkdir -p "$SCR/live" && \cp "$LC" "$SCR/live/calls_console.py" && cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s742.py" "$SCR/live" "$PD" "$SCR/portal_console.py" --control 2>&1 | tail -1)
case "$R2" in "CONTROL:"*) ;; *) stop "the control on the live page did not go red ($R2)";; esac
echo "[3/7] the builder's selftest green; the walk on made-up data: $R; on the live page: $R2"
echo "[4/7] the proof on the LIVE stores (read-only, counts only):"
(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/proof_s742.py" "$SCR/calls_console.py" "$LC" "$PD" "$CDB" "$IDB" "$FDB") > "$SCR/proof.txt" 2>&1
sed 's/^/      /' "$SCR/proof.txt"
tail -1 "$SCR/proof.txt" | grep -q '^PROOF CLEAN' || stop "the proof on the live stores is not clean"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[5/7] the build lock taken; the doctor's auto-fix paused for the restart ($([ "$OFF_MINE" = 1 ] && echo 'by this kit' || echo 'it was already off -- left as it is'))"
for f in "$LC" "$LP" "$LB"; do \cp -p "$f" "$f.bak_S742" || stop "could not keep a backup of $f"; done
PLACED=1
for pair in "$LC:calls_console.py" "$LP:portal.py" "$LB:portal_console.py"; do
  dst="${pair%%:*}"; src="$SCR/${pair##*:}"
  \cp "$src" "$dst.s742new" && chmod --reference="$dst.bak_S742" "$dst.s742new" && mv -f "$dst.s742new" "$dst" || restore "$dst could not be placed"
done
[ "$(m5 "$LC")" = "$T_C" ] && [ "$(m5 "$LP")" = "$T_P" ] && [ "$(m5 "$LB")" = "$T_B" ] || restore "read-back did not match"
echo "[6/7] placed calls_console.py (${T_C:0:8}), portal.py (${T_P:0:8}), portal_console.py (${T_B:0:8}); read back; backups *.bak_S742"
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1"
c2=$(hcode "http://127.0.0.1:$PPORT/portal/console"); case "$c2" in 302|401|403|303) ;; *) restore "/portal/console answered $c2 without a login";; esac
c3=$(hcode "http://127.0.0.1:$PPORT/portal/"); case "$c3" in 200|302|303|401|403) ;; *) restore "/portal/ answered $c3";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null | awk '/Starting gunicorn|Listening at:/{f=1} f{print} END{if(!f)exit 9}')" || JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[7/7] $PSVC restarted at $T0: health $p1; /portal/console $c2 without a login (the gate); the new master's journal clean"
echo "      the follow-up list fills at the builder's next run (every 10 minutes, 07:00-22:50); until then it shows the older list"
echo ""
echo "$KIT: DONE. The Call Console now opens folded, with WhatsApps in each timeline, the cleaned follow-up list and Call ke baad."
