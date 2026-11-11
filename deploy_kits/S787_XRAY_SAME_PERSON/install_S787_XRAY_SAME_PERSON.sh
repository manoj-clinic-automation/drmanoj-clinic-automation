#!/bin/bash
# =============================================================================
#  install_S787_XRAY_SAME_PERSON.sh . kit S787 (11-Nov-2026, session S428, the parent) . the owner 08:38 IST: RESMA shown several times
#  (her 5-Nov photos added again on 9-Nov); SACHIN AGRAWAL not registered in Docterz -- "no flow for him also. Do the needful."
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s787kit && cp -rp /root/deploy/repo/deploy_kits/S787_XRAY_SAME_PERSON /tmp/s787kit && bash /tmp/s787kit/install_S787_XRAY_SAME_PERSON.sh
#  /root/finance/check_screens.py c259e6a2 -> TO . /root/finance/records.py 794cb87f -> TO (finance restarted once).
#  claude_code_briefs/DUTY_MAP.json v23 arrives with the git pull (reception's X-ray line leaves 'not in Docterz' out).
#  Undo:  bash /tmp/s787kit/install_S787_XRAY_SAME_PERSON.sh --undo
# =============================================================================
set -u
KIT="S787_XRAY_SAME_PERSON"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
REPO="${REPO:-/root/deploy/repo}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/finance/check_screens.py"; FROM1=c259e6a258c19f1222820b47e9e9ad34; TO1=597dd8c941408172a6dd6bbcfadd7c4c; BAK1="$F1.bak_S787_${FROM1:0:8}"
F2="$ROOT/finance/records.py";       FROM2=794cb87f64afb89742e6bf0b04114b8e; TO2=a2481f74ee0054c45cef06a9e8fa923e; BAK2="$F2.bak_S787_${FROM2:0:8}"
DM="$REPO/claude_code_briefs/DUTY_MAP.json"; DM23=0113d6e4f4d0e3e66a0f43a7e84abe7d
DB="${FINANCE_DB:-$ROOT/finance/finance.db}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
fhz() { hcode "http://127.0.0.1:$FIN_PORT/finance/healthz"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() { [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; [ -f "$BAK2" ] && \cp -p "$BAK2" "$F2"; find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; [ "$(m5 "$F1")" = "$FROM1" ] && [ "$(m5 "$F2")" = "$FROM2" ] && echo 1 || echo 0; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting both files back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "   check_screens.py and records.py are back byte-identically" || echo "   !! NOT back -- copy $BAK1 and $BAK2 back by hand"
  echo "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 check_screens.py)" = "$TO1" ] && [ "$(m5 records.py)" = "$TO2" ] && [ "$(m5 DUTY_MAP.json.s787)" = "$DM23" ] || stop "the kit's files are not the built ones"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ -f "$BAK2" ] || stop "no backups -- nothing to undo"
  ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: check_screens.py (${FROM1:0:8}) and records.py (${FROM2:0:8}) are back; finance $(wait200 fhz). (The answers already given stay.)" || echo "!! not back -- send a photo"
  exit 0
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1"); L2=$(m5 "$F2")
[ "$L1" = "$TO1" ] && [ "$L2" = "$TO2" ] && { echo "-- ALREADY INSTALLED. Nothing written. finance $(fhz)"; exit 0; }
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ "$L2" = "$FROM2" ] || stop "the live $F2 is not the expected one (live ${L2:0:8}, kit expects ${FROM2:0:8})"
[ "$(m5 "$DM")" = "$DM23" ] || stop "the duty map in $DM is not v23 (${DM23:0:8}) -- run the git pull part of the line first"
SCR=$(mktemp -d /tmp/s787.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live"
"$APY" -B "$KDIR/make_s787.py" "$F1" "$F2" "$KDIR/DUTY_MAP.json.v22" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/check_screens.py")" = "$TO1" ] \
  && [ "$(m5 "$SCR/remake/records.py")" = "$TO2" ] && [ "$(m5 "$SCR/remake/DUTY_MAP.json.s787")" = "$DM23" ] || stop "make_s787.py on the live bytes does not give the kit's files"
for f in check_screens.py records.py; do
  "$APY" -W ignore -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $APY"
done
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/6] the live files are ${FROM1:0:8} and ${FROM2:0:8}; the kit's are those + the S787 edits (remade on the box); both compile; the duty map is v23"
"$APY" -c "import sqlite3; s=sqlite3.connect('file:$DB?mode=ro', uri=True); d=sqlite3.connect('$SCR/f.db'); s.backup(d); d.close(); s.close()" 2>/dev/null || stop "could not copy finance.db for the walk"
\cp -p "$F1" "$F2" "$SCR/live/"; \cp -p "$KDIR/DUTY_MAP.json.v22" "$SCR/live/DUTY_MAP.json"
R=$(cd "$SCR" && TMPDIR="$SCR" S787_ANY=1 S787_LIBS="$ROOT/finance" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s787.py" "$KDIR" "$SCR/f.db" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the S787 walk on a copy of today's database is not green ($R)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" S787_LIBS="$ROOT/finance" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s787.py" "$SCR/live" "$SCR/f.db" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($R2)";; esac
rm -f "$SCR/f.db"; find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/6] the walk (a copy of today's finance.db): $R | the live files: $R2"
[ "$(fhz)" = 200 ] || stop "finance is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[4/6] the build lock taken; the doctor's auto-fix paused for the restart"
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
{ \cp -p "$F2" "$BAK2" && [ "$(m5 "$BAK2")" = "$FROM2" ]; } || stop "could not keep a backup of $F2"
PLACED=1
for pair in "check_screens.py:$F1:$BAK1:$TO1" "records.py:$F2:$BAK2:$TO2"; do
  IFS=: read -r src dst bak to <<< "$pair"
  \cp "$KDIR/$src" "$dst.s787new" && chmod --reference="$bak" "$dst.s787new" && chown --reference="$bak" "$dst.s787new" 2>/dev/null; mv -f "$dst.s787new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$to" ] || restore "$src read-back did not match"
done
find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(hcode "http://127.0.0.1:$FIN_PORT/finance/records/xray-check"); case "$c2" in 302|401|403|303) ;; *) restore "his X-ray page answered $c2 without a login";; esac
c3=$(hcode "http://127.0.0.1:$FIN_PORT/finance/checks"); case "$c3" in 302|401|403|303) ;; *) restore "Check karein answered $c3 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'check_screens|records\.py|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'check|records|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[5/6] placed (backups $BAK1, $BAK2); restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): finance $c1; both pages' doors closed without a login ($c2, $c3); journal clean"
echo "[6/6] $KIT: DONE. The next filing run gives a same-name photo of a patient filed that day his ID; your X-ray page has the 'Not in Docterz' tile."
