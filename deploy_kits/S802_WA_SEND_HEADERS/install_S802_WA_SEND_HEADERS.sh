#!/bin/bash
# =============================================================================
#  install_S802_WA_SEND_HEADERS.sh . kit S802 (12-Nov-2026, session S437, the parent) . F-1031 (MyOperator ticket 691386).
#  urllib re-cases header names on the wire ("X-MYOP-COMPANY-ID" leaves as "X-Myop-Company-Id"); MyOperator's gateway refuses that
#  form at its authorizer unless a properly-cased request with the same key has just been let through. The two senders' ONE
#  request moves from urllib to http.client, which sends header names as written (as the tracker's relay always has):
#    /root/portal/portal_inbox.py 06e2c28e -> TO (myop_send)   .   /root/portal/portal_wa.py 34994b23 -> TO (send)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s802kit && cp -rp /root/deploy/repo/deploy_kits/S802_WA_SEND_HEADERS /tmp/s802kit && bash /tmp/s802kit/install_S802_WA_SEND_HEADERS.sh
#  FIRST it is PROVEN on the live gateway -- NOTHING SENT: fresh made-up keys (no earlier request can help them), and the real key
#  only with an empty number and empty text. Placed ONLY on PROVEN. DRY=1 runs the gates and the proof, and changes nothing.
#  Undo:  bash /tmp/s802kit/install_S802_WA_SEND_HEADERS.sh --undo
# =============================================================================
set -u
KIT="S802_WA_SEND_HEADERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/portal/portal_inbox.py"; FROM1=06e2c28e412ca1b2359182d16ff0cf65; TO1=973cc74f1603ecd2594ac69f52c543df; BAK1="$F1.bak_S802_${FROM1:0:8}"
F2="$ROOT/portal/portal_wa.py";    FROM2=34994b235c95a7c611996738ab14bdd1; TO2=e8b27db968b378261014c27b7b46ca32; BAK2="$F2.bak_S802_${FROM2:0:8}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; [ -f "$BAK2" ] && \cp -p "$BAK2" "$F2"; rm -f "$F1.s802new" "$F2.s802new"
  find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && [ "$(m5 "$F2")" = "$FROM2" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting both files back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   portal_inbox.py and portal_wa.py are back byte-identically" || echo "   !! NOT all back -- copy $BAK1 and $BAK2 back by hand"
  echo "   portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP
probe_installed() { ( cd /tmp && S802_CONFIG_DIR="$ROOT/portal" timeout 200 "$VPY" -W ignore -B "$KDIR/prove_s802.py" "$ROOT/portal" --installed 2>&1 | tail -1 ); }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
# The kit carries NO copy of the two files (portal_wa.py holds the clinic's number in its page text -- no number goes into the
# repository, F-185): make_s802.py makes them on this box from the live bytes and the result is checked against the pins below.
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] && [ -f "$BAK2" ] && [ "$(m5 "$BAK2")" = "$FROM2" ] || stop "no good backups -- nothing to undo"
  L1=$(m5 "$F1"); L2=$(m5 "$F2")
  { [ "$L1" = "$TO1" ] || [ "$L1" = "$FROM1" ]; } && { [ "$L2" = "$TO2" ] || [ "$L2" = "$FROM2" ]; } || stop "one of the two files has been changed since this kit (a later kit is on top) -- not undone"
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && { echo "UNDONE: both files are back as before; portal $(wait200 phz)"; exit 0; }
  echo "!! not back -- send a photo"; exit 1
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1"); L2=$(m5 "$F2")
if [ "$L1" = "$TO1" ] && [ "$L2" = "$TO2" ]; then
  echo "-- ALREADY INSTALLED. Nothing written. portal $(phz)"; echo "   $(probe_installed)"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ "$L2" = "$FROM2" ] || stop "the live $F2 is not the expected one (live ${L2:0:8}, kit expects ${FROM2:0:8})"
SCR=$(mktemp -d /tmp/s802.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live/portal"
"$APY" -B "$KDIR/make_s802.py" "$F1" "$F2" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal/portal_inbox.py")" = "$TO1" ] \
  && [ "$(m5 "$SCR/remake/portal/portal_wa.py")" = "$TO2" ] || stop "make_s802.py on the live bytes does not give the two pinned files"
for f in "$SCR/remake/portal/portal_inbox.py" "$SCR/remake/portal/portal_wa.py" "$KDIR/prove_s802.py"; do
  "$APY" -W ignore -B -m py_compile "$f" 2>/dev/null || stop "$(basename "$f") does not compile with $APY"
  "$VPY" -W ignore -B -m py_compile "$f" 2>/dev/null || stop "$(basename "$f") does not compile with $VPY"
done
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/6] the live files are ${FROM1:0:8} and ${FROM2:0:8}; the kit's are those with the one request moved to http.client (remade on the box); all compile"
\cp -p "$F1" "$SCR/live/portal/portal_inbox.py"; \cp -p "$F2" "$SCR/live/portal/portal_wa.py"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s802.py" "$SCR/remake" "$KDIR" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s802.py" "$SCR/remake" "$KDIR" 2>&1 | grep '^BAD' | head -6); stop "the S802 walk is not green ($R)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s802.py" "$SCR/live" "$KDIR" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/6] the walk (a stand-in gateway on this machine, nothing leaves it): $R | the live files: $R2"
echo "[4/6] the proof on MyOperator's gateway -- NOTHING SENT:"
( cd /tmp && S802_CONFIG_DIR="$ROOT/portal" timeout 300 "$VPY" -W ignore -B "$KDIR/prove_s802.py" "$SCR/remake/portal" > "$SCR/prove.txt" 2>&1 )
find "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
sed 's/^/      /' "$SCR/prove.txt" | head -14
V=$(grep '^PROVE: ' "$SCR/prove.txt" | tail -1 | awk '{print $2}')
[ -n "$V" ] || stop "the proof gave no result"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: the proof says $V; nothing written."; exit 0; }
if [ "$V" != "PROVEN" ]; then
  echo "[5/6] NOT APPLIED -- the proof says $V: the table above does not show that header names as written get through."
  echo "[6/6] $KIT: NOTHING CHANGED. Send a photo of this screen to Claude -- the lines above are what is needed."
  exit 0
fi
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
{ \cp -p "$F2" "$BAK2" && [ "$(m5 "$BAK2")" = "$FROM2" ]; } || stop "could not keep a backup of $F2"
PLACED=1
for pair in "portal/portal_inbox.py:$F1:$BAK1:$TO1" "portal/portal_wa.py:$F2:$BAK2:$TO2"; do
  IFS=: read -r src dst ref to <<< "$pair"
  \cp "$SCR/remake/$src" "$dst.s802new" && chmod --reference="$ref" "$dst.s802new" && chown --reference="$ref" "$dst.s802new" 2>/dev/null; mv -f "$dst.s802new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$to" ] || restore "$src read-back did not match"
done
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c2=$(wait200 phz); [ "$c2" = 200 ] || restore "portal health $c2"
c3=$(hcode "http://127.0.0.1:$PPORT/portal/inbox"); case "$c3" in 302|303|401|403) ;; *) restore "the Inbox answered $c3 without a login";; esac
c4=$(hcode "http://127.0.0.1:$PPORT/portal/inbox/health"); [ "$c4" = 200 ] || restore "the Inbox's health answered $c4"
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'portal_inbox|portal_wa|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'inbox|portal_wa|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PI=$(probe_installed)
case "$PI" in *"let through"*) ;; *) restore "the installed Inbox sender is not let through ($PI)";; esac
PLACED=0
echo "[5/6] placed (backups *.bak_S802_*); the portal restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): health $c2; the Inbox's door closed without a login ($c3), its health $c4; journal clean"
echo "      $PI"
echo "[6/6] $KIT: DONE. The Inbox's replies and the portal's templates now reach MyOperator with the header names as written. Replies still waiting in the queue go out by themselves at their next try."
