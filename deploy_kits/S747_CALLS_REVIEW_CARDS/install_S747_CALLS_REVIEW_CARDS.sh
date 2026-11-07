#!/bin/bash
# =============================================================================
#  install_S747_CALLS_REVIEW_CARDS.sh . kit S747 (07-Nov-2026, session S400, the parent) . D856, Build B part 2
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s747kit && cp -rp /root/deploy/repo/deploy_kits/S747_CALLS_REVIEW_CARDS /tmp/s747kit && bash /tmp/s747kit/install_S747_CALLS_REVIEW_CARDS.sh
#  (DRY=1 before bash: every gate, both walks and the proof on the live stores; nothing written.)
#
#  /root/portal/calls_console.py          40200409 (S745) -> TO: the owner's review buttons on each staff card's call (Ask to
#      log . Mark reviewed . Staff right . AI right . Note to staff . Undo), each call with its log line and transcript; the
#      staff's disputes with Accept / It stands; each person's own card for Aaj ka kaam (/portal/console/api/mycard, mytx,
#      dispute -- their own calls only); the reception mobile credited to the one phone staff member on duty (F-1168).
#  /root/finance/aaj_kaam.html            9f8fb9df -> TO: 'Mere calls', the person's own card in Hindi (read per request).
#  /root/state_backup/clinic_state_backup.py  37ed5524 (S719) -> TO: one line, /root/portal/call_review.db in the nightly.
#  /root/portal/call_review.db            NEW, created empty BEFORE the backup line is placed (an absent source = FATAL 41).
#  ON THE BOX before anything is written: the S747 walk green on the new page and red on the live one; S745's walk green on
#      the new page; the proof on the LIVE stores, read-only, counts only. After placing: clinic-portal restarted, health,
#      the gates, the journal; the backup's own preflight (nothing shipped).
#  Red after placing -- the restart, a gate, the journal or the backup's preflight: the three files back byte-identically,
#      clinic-portal restarted (the new empty store is left; harmless). A rerun then starts from the beginning.
#  Undo:  bash /tmp/s747kit/install_S747_CALLS_REVIEW_CARDS.sh --undo
# =============================================================================
set -u
KIT="S747_CALLS_REVIEW_CARDS"
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
F1="$PD/calls_console.py"; F2="$FIN/aaj_kaam.html"; F3="$SB/clinic_state_backup.py"
FROM1=4020040980d1557255b5c3b3527e3e6c; FROM2=9f8fb9df13e66773f6645dda321dedcb; FROM3=37ed5524ca4dffa96a19346bf6d3a012
TO1=df484c7d4fa37b2c0e29d18eb476ea0a; TO2=dc684e46126fcaa54bb0f88813172ef4; TO3=fd1647de19a20e908baa3d1f958ad07d
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
  for f in "$F1" "$F2" "$F3"; do [ -f "$f.bak_S747" ] && \cp -p "$f.bak_S747" "$f"; done
  [ "$(m5 "$F1")" = "$FROM1" ] || ok=0; [ "$(m5 "$F2")" = "$FROM2" ] || ok=0; [ "$(m5 "$F3")" = "$FROM3" ] || ok=0
  echo $ok
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the three files back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   the three files are back byte-identically" || echo "   !! a file is NOT back -- copy each *.bak_S747 back by hand"
  echo "   portal health $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 calls_console.py)" = "$TO1" ] && [ "$(m5 aaj_kaam.html)" = "$TO2" ] && [ "$(m5 clinic_state_backup.py)" = "$TO3" ] || stop "the kit's files are not the built ones"
if [ "${1:-}" = "--undo" ]; then
  for f in "$F1" "$F2" "$F3"; do [ -f "$f.bak_S747" ] || stop "no $f.bak_S747 -- nothing to undo"; done
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: the three files are back (S745's page, the old staff page, the backup without the store); portal health $(wait200)" || echo "!! a file is not back -- send a photo"
  exit 0
fi
echo "[1/8] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1"); L2=$(m5 "$F2"); L3=$(m5 "$F3")
if [ "$L1" = "$TO1" ] && [ "$L2" = "$TO2" ] && [ "$L3" = "$TO3" ]; then echo "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. portal health $(phz)"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not S745's (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ "$L2" = "$FROM2" ] || stop "the live $F2 changed since this kit was built (live ${L2:0:8}, kit expects ${FROM2:0:8})"
[ "$L3" = "$FROM3" ] || stop "the live $F3 changed since this kit was built (live ${L3:0:8}, kit expects ${FROM3:0:8})"
[ -f "$LB" ] || stop "$LB is not there (the walks read its build_fu_all, read only)"
SCR=$(mktemp -d /tmp/s747.XXXX); chmod 700 "$SCR"
\cp "$KDIR/calls_console.py" "$SCR/calls_console.py"
"$VPY" -B -m py_compile "$SCR/calls_console.py" 2>/dev/null || stop "calls_console.py does not compile with $VPY"
\cp "$KDIR/clinic_state_backup.py" "$SCR/csb.py"; "$VPY" -B -m py_compile "$SCR/csb.py" 2>/dev/null || stop "clinic_state_backup.py does not compile"
echo "[2/8] the live files are the ones the kit was built on (${FROM1:0:8} ${FROM2:0:8} ${FROM3:0:8}); the new ones compile"
R=$(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s747.py" "$SCR" "$PD" "$LB" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the S747 walk is not green ($R)";; esac
R2=$(mkdir -p "$SCR/live" && \cp "$F1" "$SCR/live/calls_console.py" && cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s747.py" "$SCR/live" "$PD" "$LB" --control 2>&1 | tail -1)
case "$R2" in "CONTROL:"*) ;; *) stop "the control on the live page did not go red ($R2)";; esac
R3=$(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/walk_s745.py" "$SCR" "$PD" "$LB" 2>&1 | tail -1)
case "$R3" in "WALK OK"*) ;; *) stop "S745's walk on the new page is not green ($R3)";; esac
echo "[3/8] the walk on made-up data: $R; on the live page: $R2; S745's walk on the new page: $R3"
echo "[4/8] the proof on the LIVE stores (read-only, counts only):"
(cd "$SCR" && timeout 300 "$VPY" -B "$KDIR/proof_s747.py" "$SCR/calls_console.py" "$F1" "$PD" "$CDB" "$IDB" "$FDB" "$SM" "$PU" "$RVDB") > "$SCR/proof.txt" 2>&1
sed 's/^/      /' "$SCR/proof.txt"
tail -1 "$SCR/proof.txt" | grep -q '^PROOF CLEAN' || stop "the proof on the live stores is not clean"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[5/8] the build lock taken; the doctor's auto-fix paused for the restart ($([ "$OFF_MINE" = 1 ] && echo 'by this kit' || echo 'it was already off -- left as it is'))"
"$VPY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import importlib.util as u; s=u.spec_from_file_location('c', sys.argv[2]); m=u.module_from_spec(s); s.loader.exec_module(m); m.rv_init(sys.argv[3])" "$SCR" "$SCR/calls_console.py" "$RVDB" \
  || stop "the review store $RVDB could not be made"
"$VPY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); sys.exit(0 if c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' else 1)" "$RVDB" \
  || stop "the review store does not pass its own integrity check"
chmod 600 "$RVDB"
echo "[6/8] the review store $RVDB is there, its tables made, integrity ok ($(du -k "$RVDB" | cut -f1) KB)"
for f in "$F1" "$F2" "$F3"; do \cp -p "$f" "$f.bak_S747" || stop "could not keep a backup of $f"; done
PLACED=1
for pair in "$F1:calls_console.py:$TO1" "$F2:aaj_kaam.html:$TO2" "$F3:clinic_state_backup.py:$TO3"; do
  dst=${pair%%:*}; rest=${pair#*:}; src=${rest%%:*}; want=${rest#*:}
  \cp "$KDIR/$src" "$dst.s747new" && chmod --reference="$dst.bak_S747" "$dst.s747new" && mv -f "$dst.s747new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$want" ] || restore "$src read-back did not match"
done
echo "[7/8] placed and read back: calls_console.py ${TO1:0:8}, aaj_kaam.html ${TO2:0:8}, clinic_state_backup.py ${TO3:0:8} (backups *.bak_S747)"
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
echo "      $PSVC restarted at $T0: health $p1; /portal/console $c2, mycard $c3, card $c4 without a login (the gates); the journal clean"
echo "[8/8] the backup's own preflight (every source, the encryption round trip -- nothing shipped)"
timeout 900 "$VPY" "$F3" preflight > "$SCR/pre.txt" 2>&1
PF=$?
grep -E "call_review|would include|WARNING: source not present|FATAL|round trip" "$SCR/pre.txt" | sed 's/^\[[^]]*\] /      /' | head -8
if [ "$PF" != 0 ] || grep -q "source not present: $RVDB" "$SCR/pre.txt"; then
  restore "the backup's preflight did not pass (exit $PF) -- tonight's backup runs as before"
fi
PLACED=0
echo "      preflight passed"
echo ""
echo "$KIT: DONE. Your buttons are on each staff call; each person's own card is on Aaj ka kaam; reception-mobile calls count to the one on duty."
