#!/bin/bash
# =============================================================================
#  install_S757_XRAY_LAB_CHECK.sh . kit S757 (09-Nov-2026, session S413, the parent) . D875 -- the owner's FINAL 06:39 IST
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s757kit && cp -rp /root/deploy/repo/deploy_kits/S757_XRAY_LAB_CHECK /tmp/s757kit && bash /tmp/s757kit/install_S757_XRAY_LAB_CHECK.sh
#  (DRY=1 before bash: every gate, both walks and the proof on the live database; nothing written.)
#
#  /root/finance/records.py          a6ec1052 -> d86f2ada  Check karein drawn by check_screens (old list = fallback, ?list=1); his way in
#  /root/finance/check_screens.py    (new)    -> ce7d248d  the photo / lab-report screens, Shavez's queue, his page /finance/records/xray-check
#  /root/finance/parchi_desk.py      fb405c12 -> 5ec8aebc  the Check karein strip; a lab report's blood slip written on the visit day
#  /root/finance/owner_console.py    f2ab5deb -> 7dd1a858  his console's line for the four tiles
#  /root/finance/aaj_seed.py         dc7050d5 -> 6f4784ae  Shavez's morning line 'Check karein: X-ray photo aur lab report dekhiye'
#  /root/finance/aaj_duties.json     c5c80c37 -> 90233998  its fetch duty (shipped as aaj_duties.json.kit)
#  /root/portal/tile_grants.json     f2dad157 -> e486f3de  F-1185: Marg Purchases on his home; v44 (shipped as tile_grants.json.kit)
#  ON THE BOX before anything is written: make_s757.py remakes every file from the LIVE bytes; all compile under both pythons; the
#      walk (a made-up clinic on the live schema, no row copied) green on the kit's files and red on the live ones; the proof on the
#      LIVE database (a read-only copy; counts only).
#  Red after placing: every file back byte-identically (check_screens.py removed), clinic-finance restarted.
#  Undo:  bash /tmp/s757kit/install_S757_XRAY_LAB_CHECK.sh --undo
# =============================================================================
set -u
KIT="S757_XRAY_LAB_CHECK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; PORTAL="$ROOT/portal"; DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
ROWS="$FIN/records.py|records.py|a6ec1052937e1aee99b515e07e13a853|d86f2adae16afa32afc4443042e5aacc
$FIN/check_screens.py|check_screens.py|absent|ce7d248de626660586b6a5caa064b5d6
$FIN/parchi_desk.py|parchi_desk.py|fb405c1233c7f5c808aefb7e67c57a2f|5ec8aebce77f6b631884956b51e36066
$FIN/owner_console.py|owner_console.py|f2ab5deb9c5f284b5257a10d4735fce8|7dd1a85872c31d90e9fe65a8bdf70f92
$FIN/aaj_seed.py|aaj_seed.py|dc7050d5de882cb65af843beb8110b07|6f4784ae945d8daba2c4296334aa669e
$FIN/aaj_duties.json|aaj_duties.json.kit|c5c80c37e5868864a5e6f58ea7c75112|90233998dd41fb86d8e65448227a5f44
$PORTAL/tile_grants.json|tile_grants.json.kit|f2dad1579505c672de4270ed7fecb224|e486f3de51dfc8e0c330e5e874a35bf2"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { hcode /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  local bad=0
  while IFS='|' read -r LP KF FROM TO; do
    if [ "$FROM" = absent ]; then rm -f "$LP"; [ -e "$LP" ] && bad=1
    else [ -f "$LP.bak_S757" ] && \cp -p "$LP.bak_S757" "$LP"; [ "$(m5 "$LP")" = "$FROM" ] || { echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S757 back by hand"; bad=1; }; fi
  done <<< "$ROWS"
  find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  echo "$bad"
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting every file back"
  local bad; bad=$(putback | tail -1); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$bad" = 0 ] && echo "   every file is back byte-identically; check_screens.py removed"
  echo "   finance healthz $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$KDIR/$KF")" = "$TO" ] || stop "the kit's $KF is not the built file"; done <<< "$ROWS"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$FIN/records.py.bak_S757" ] || stop "no backups (*.bak_S757) -- nothing to undo"
  while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$TO" ] || stop "$LP is no longer this kit's (a later change) -- undo refused, so that change is not lost"; done <<< "$ROWS"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
  HAVE_LOCK=1
  bad=$(putback | tail -1); "$SYSTEMCTL" restart "$FSVC" || true
  [ "$bad" = 0 ] && echo "UNDONE: every file is back; finance healthz $(wait200)" || echo "!! not every file is back -- send a photo"
  exit 0
fi
echo "[1/7] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
ALL_TO=1
while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$TO" ] || ALL_TO=0; done <<< "$ROWS"
[ "$ALL_TO" = 1 ] && { echo "-- ALREADY INSTALLED: every file is the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
while IFS='|' read -r LP KF FROM TO; do
  if [ "$FROM" = absent ]; then [ -e "$LP" ] && stop "$LP is already there (the kit expects it absent)"
  else L=$(m5 "$LP"); [ "$L" = "$FROM" ] || stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"; fi
done <<< "$ROWS"
SCR=$(mktemp -d /tmp/s757.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/live" "$SCR/remake"
\cp "$FIN/records.py" "$FIN/parchi_desk.py" "$FIN/owner_console.py" "$FIN/aaj_seed.py" "$FIN/aaj_duties.json" "$PORTAL/tile_grants.json" "$SCR/live/"
"$APY" -B "$KDIR/make_s757.py" "$SCR/live" "$SCR/remake" >/dev/null 2>&1 || stop "make_s757.py did not run on the live bytes"
while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$SCR/remake/$KF")" = "$TO" ] || stop "make_s757.py on the live bytes does not give the kit's $KF"; done <<< "$ROWS"
for f in records.py check_screens.py parchi_desk.py owner_console.py aaj_seed.py; do
  "$APY" -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $APY"
  "$VPY" -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $VPY"
done
"$APY" -c "import json,sys; [json.load(open(p)) for p in sys.argv[1:]]" "$KDIR/aaj_duties.json.kit" "$KDIR/tile_grants.json.kit" || stop "a .json.kit is not valid JSON"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/7] the live files are the ones this kit was built from; remade on the box byte-identically; all compile under both pythons"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/walk_s757.py" "$KDIR" "$FIN" "$DB" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the walk is not green ($R)";; esac
\cp "$KDIR/walk_s757.py" "$SCR/live/"
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$SCR/live/walk_s757.py" "$SCR/live" "$FIN" "$DB" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($R2)";; esac
echo "[3/7] the walk on a made-up clinic (the live schema, no row copied): $R; the live files: $R2"
echo "[4/7] the proof on the LIVE database (a read-only copy; counts only) -- what the screens would show today:"
(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$APY" -W ignore -B "$KDIR/proof_s757.py" "$KDIR" "$DB") > "$SCR/proof.txt" 2>&1
sed 's/^/      /' "$SCR/proof.txt"
tail -1 "$SCR/proof.txt" | grep -q '^PROOF DONE' || stop "the proof did not finish"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
[ "$(fhz)" = 200 ] || stop "finance is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[5/7] the build lock taken; the doctor's auto-fix paused for the restart"
while IFS='|' read -r LP KF FROM TO; do
  [ "$FROM" = absent ] && continue
  { \cp -p "$LP" "$LP.bak_S757" && [ "$(m5 "$LP.bak_S757")" = "$FROM" ]; } || stop "could not keep a backup of $LP"
done <<< "$ROWS"
PLACED=1
while IFS='|' read -r LP KF FROM TO; do
  REF="$LP.bak_S757"; [ "$FROM" = absent ] && REF="$FIN/records.py.bak_S757"
  \cp "$KDIR/$KF" "$LP.s757new" && chmod --reference="$REF" "$LP.s757new" && { chown --reference="$REF" "$LP.s757new" 2>/dev/null; true; } \
    && mv -f "$LP.s757new" "$LP" || restore "$LP could not be placed"
  [ "$(m5 "$LP")" = "$TO" ] || restore "$LP read-back did not match"
done <<< "$ROWS"
find "$FIN" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[6/7] placed and read back: 7 files (backups *.bak_S757)"
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1"
( cd "$FIN" && "$APY" -B -c "import records,sys; sys.exit(0 if getattr(records, '_s757', None) is not None and hasattr(records._s757, 'answer') else 3)" ) >/dev/null 2>&1 \
  || restore "records.py did not take check_screens' doors on (the screens would silently stay the old list)"
for door in /finance/checks /finance/checks/api/mine /finance/records/xray-check /finance/slips/desk /finance/console; do
  c=$(hcode "$door"); case "$c" in 302|401|403|303) ;; *) restore "$door answered $c without a login";; esac
done
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'records\.py|check_screens|parchi_desk|owner_console|aaj_seed|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'records|check_screens|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[7/7] $FSVC restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): healthz $c1; without a login every new door refuses; the journal clean"
echo ""
echo "$KIT: DONE. Check karein shows the photos; Shavez's PC carries the lab reports; your page is /finance/records/xray-check."
