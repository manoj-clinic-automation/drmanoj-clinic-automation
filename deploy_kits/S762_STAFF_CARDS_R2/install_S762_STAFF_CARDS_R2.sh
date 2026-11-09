#!/bin/bash
# =============================================================================
#  install_S762_STAFF_CARDS_R2.sh . kit S762 (09-Nov-2026, session S415, the parent) . the owner's rulings 09:27 / 09:46 IST
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s762kit && cp -rp /root/deploy/repo/deploy_kits/S762_STAFF_CARDS_R2 /tmp/s762kit && bash /tmp/s762kit/install_S762_STAFF_CARDS_R2.sh
#  (DRY=1 before bash: every gate, the walks and the proof on the live stores; nothing written.)
#
#  /root/portal/calls_console.py   f233b851 (S748) -> TO: a call missed in a phone staff member's shift before she punches in
#      counts on her card ('before punch-in'); a call missed while two answer for it shows ONCE on his page ('Both on duty')
#      and stays on each one's own card; outcome codes in plain words; same-word 'mismatches' agree; lists newest first;
#      a link to each person's own card; a jump link to the staff cards; today's net missed for the staff's folded line.
#  /root/finance/aaj_kaam.html     791fbf8b (S748) -> TO: 'aaj abhi tak: N log' on the folded line, the reached-later
#      figure, 'punch se pehle' on a call. The Aaj / Kal / 7 din tabs unchanged (his word 09:32).
#  ON THE BOX before anything is written: the S762 walk green on the new page and red on the live one; S745's, S747's and
#      S748's walks on the new page red ONLY where EXPECTED_REDS.txt names (the rulings change those counts); the proof on
#      the LIVE stores (read-only, counts only).
#  Red after placing: both files back byte-identically and clinic-portal restarted.
#  Undo:  bash /tmp/s762kit/install_S762_STAFF_CARDS_R2.sh --undo
# =============================================================================
set -u
KIT="S762_STAFF_CARDS_R2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
PD="${PD:-/root/portal}"; WA="${WA:-/root/wa}"; FIN="${FIN:-/root/finance}"; SB="${SB:-/root/state_backup}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
CDB="${CDB:-$WA/console.db}"; IDB="${IDB:-$WA/wa_inbox/inbox.db}"; FDB="${FDB:-/root/finance/finance.db}"
SM="${SM:-/root/staff_master.csv}"; PU="${PU:-/root/punches.csv}"
RVDB="${RVDB:-$PD/call_review.db}"
LB="$WA/portal_console.py"
F1="$PD/calls_console.py"; F2="$FIN/aaj_kaam.html"
FROM1=f233b851ece87bacb643c4344e71d9be; FROM2=791fbf8b866d7294f8a1f859ff11c5b1
TO1=45b0373131411242839fecd940fc028c; TO2=e82f23d22fbd228a69b14096bb7b4869
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(phz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  local ok=1
  for f in "$F1" "$F2"; do [ -f "$f.bak_S762" ] && \cp -p "$f.bak_S762" "$f"; done
  [ "$(m5 "$F1")" = "$FROM1" ] || ok=0; [ "$(m5 "$F2")" = "$FROM2" ] || ok=0
  echo $ok
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the two files back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   the two files are back byte-identically" || echo "   !! a file is NOT back -- copy each *.bak_S762 back by hand"
  echo "   portal health $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 calls_console.py)" = "$TO1" ] && [ "$(m5 aaj_kaam.html)" = "$TO2" ] || stop "the kit's files are not the built ones"
if [ "${1:-}" = "--undo" ]; then
  for f in "$F1" "$F2"; do [ -f "$f.bak_S762" ] || stop "no $f.bak_S762 -- nothing to undo"; done
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: the two files are back (S748's); portal health $(wait200)" || echo "!! a file is not back -- send a photo"
  exit 0
fi
echo "[1/7] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1"); L2=$(m5 "$F2")
if [ "$L1" = "$TO1" ] && [ "$L2" = "$TO2" ]; then echo "-- ALREADY INSTALLED: the two files are the kit's. Nothing written. portal health $(phz)"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not S748's (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ "$L2" = "$FROM2" ] || stop "the live $F2 is not S748's (live ${L2:0:8}, kit expects ${FROM2:0:8})"
[ -f "$LB" ] || stop "$LB is not there (the walks read its build_fu_all, read only)"
SCR=$(mktemp -d /tmp/s762.XXXX); chmod 700 "$SCR"
\cp "$KDIR/calls_console.py" "$SCR/calls_console.py"
"$VPY" -B -m py_compile "$SCR/calls_console.py" 2>/dev/null || stop "calls_console.py does not compile with $VPY"
echo "[2/7] the live files are S748's (${FROM1:0:8} ${FROM2:0:8}); the new page compiles"
R=$(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s762.py" "$SCR" "$PD" "$LB" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the S762 walk is not green ($R)";; esac
R2=$(mkdir -p "$SCR/live" && \cp "$F1" "$SCR/live/calls_console.py" && cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s762.py" "$SCR/live" "$PD" "$LB" --control 2>&1 | tail -1)
case "$R2" in "CONTROL:"*) ;; *) stop "the control on the live page did not go red ($R2)";; esac
R3=$(cd "$SCR" && VPY="$VPY" bash "$KDIR/oldwalks_s762.sh" "$SCR" "$PD" "$LB" 2>&1 | tail -1)
case "$R3" in "OLD WALKS OK"*) ;; *) stop "the earlier walks on the new page are not as expected ($R3)";; esac
echo "[3/7] the walk on made-up data: $R; on the live page: $R2; $R3"
echo "[4/7] the proof on the LIVE stores (read-only, counts only):"
(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/proof_s762.py" "$SCR/calls_console.py" "$F1" "$PD" "$CDB" "$IDB" "$FDB" "$SM" "$PU" "$RVDB") > "$SCR/proof.txt" 2>&1
sed 's/^/      /' "$SCR/proof.txt"
tail -1 "$SCR/proof.txt" | grep -q '^PROOF CLEAN' || stop "the proof on the live stores is not clean"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[5/7] the build lock taken; the doctor's auto-fix paused for the restart ($([ "$OFF_MINE" = 1 ] && echo 'by this kit' || echo 'it was already off -- left as it is'))"
for f in "$F1" "$F2"; do \cp -p "$f" "$f.bak_S762" || stop "could not keep a backup of $f"; done
PLACED=1
for pair in "$F1:calls_console.py:$TO1" "$F2:aaj_kaam.html:$TO2"; do
  dst=${pair%%:*}; rest=${pair#*:}; src=${rest%%:*}; want=${rest#*:}
  \cp "$KDIR/$src" "$dst.s762new" && chmod --reference="$dst.bak_S762" "$dst.s762new" && mv -f "$dst.s762new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$want" ] || restore "$src read-back did not match"
done
echo "[6/7] placed and read back: calls_console.py ${TO1:0:8}, aaj_kaam.html ${TO2:0:8} (backups *.bak_S762)"
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1"
c2=$(hcode "http://127.0.0.1:$PPORT/portal/console"); case "$c2" in 302|401|403|303) ;; *) restore "/portal/console answered $c2 without a login";; esac
c3=$(hcode "http://127.0.0.1:$PPORT/portal/console/api/mycard"); case "$c3" in 302|401|403|303) ;; *) restore "/portal/console/api/mycard answered $c3 without a login (the staff route must sit behind the login)";; esac
c4=$(hcode "http://127.0.0.1:$PPORT/portal/console/api/card/x"); case "$c4" in 302|401|403|303) ;; *) restore "/portal/console/api/card answered $c4 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null | awk '/Starting gunicorn|Listening at:/{f=1} f{print} END{if(!f)exit 9}')" || JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[7/7] $PSVC restarted at $T0: health $p1; /portal/console $c2, mycard $c3, card $c4 without a login (the gates); the journal clean"
echo ""
echo "$KIT: DONE. Staff cards: before punch-in counted, 'Both on duty' once on your page, plain words, newest first; staff see today's net missed on their line."
