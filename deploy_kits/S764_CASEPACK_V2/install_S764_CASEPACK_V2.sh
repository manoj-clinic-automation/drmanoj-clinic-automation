#!/bin/bash
# =============================================================================
#  install_S764_CASEPACK_V2.sh . kit S764 (09-Nov-2026, session S418, the parent) . D880 -- the owner's word 13:32 IST: build in a fresh session, as ONE kit
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s764kit && cp -rp /root/deploy/repo/deploy_kits/S764_CASEPACK_V2 /tmp/s764kit && bash /tmp/s764kit/install_S764_CASEPACK_V2.sh
#  (DRY=1 before bash: every gate, the walk and the control; nothing written.)
#
#  /root/portal/casepack_portal.py          cbbd392d (S385) -> a8774eef  registers casepack_v2 behind the same owner-only guard; nothing else changes
#  /root/portal/casepack_v2.py              (new)           -> da09b6c5  the stores (cp_packages / cp_rates / cp_estimates / cp_settings in /root/wa/casepack,
#                                                                         the PHI store, in the encrypted nightly), the routes, the fracture catalogue, the arithmetic
#  /root/wa/casepack/casepack_page.html     f95d186d (S685) -> 333f7825  the Enquiry stage v2: search first; the server's packages; DTH rates fold; Build an estimate;
#                                                                         every line a fold; Next: Consent -> . Estimates given . Manage packages; 1-2-3-4 all live
#  /root/wa/casepack/casepack_seed.html     (new)           -> 76f16159  the seeding page /portal/casepack/seed (charge groups, suggestions, his net)
#  ON THE BOX before anything is written: make_s764.py remakes the two changed files from the LIVE bytes (byte-identical to the kit);
#      the modules compile under the venv python; the walk on a made-up store (45 checks) green on the kit's files and red on the live ones.
#  Nothing is seeded by the installer: the first GET /portal/casepack/packages by the owner writes cp_packages.json from his 15 live packages.
#  Red after placing: every file back byte-identically (the two new files removed), clinic-portal restarted.
#  Undo:  bash /tmp/s764kit/install_S764_CASEPACK_V2.sh --undo
# =============================================================================
set -u
KIT="S764_CASEPACK_V2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
PD="${PD:-/root/portal}"; CP="${CP:-/root/wa/casepack}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
ROWS="$PD/casepack_portal.py|casepack_portal.py|cbbd392d849f7bc5824197d25830cf05|a8774eef5301cb74fe13739336e735c8
$PD/casepack_v2.py|casepack_v2.py|absent|da09b6c53e019903f4d756c7ada11a43
$CP/casepack_page.html|casepack_page.html|f95d186d66ed44b391f3ea4ac2f8428f|333f7825e5ba97018fcd1b2acefa74ab
$CP/casepack_seed.html|casepack_seed.html|absent|76f1615921a9d9a8f3cf04190e4132fb"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(phz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  local bad=0
  while IFS='|' read -r LP KF FROM TO; do
    if [ "$FROM" = absent ]; then rm -f "$LP"; [ -e "$LP" ] && bad=1
    else [ -f "$LP.bak_S764" ] && \cp -p "$LP.bak_S764" "$LP"; [ "$(m5 "$LP")" = "$FROM" ] || { echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S764 back by hand"; bad=1; }; fi
  done <<< "$ROWS"
  find "$PD" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  echo "$bad"
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting every file back"
  local bad; bad=$(putback | tail -1); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$bad" = 0 ] && echo "   every file is back byte-identically; casepack_v2.py and casepack_seed.html removed"
  echo "   portal health $(wait200). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$KDIR/$KF")" = "$TO" ] || stop "the kit's $KF is not the built file"; done <<< "$ROWS"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$PD/casepack_portal.py.bak_S764" ] || stop "no backups (*.bak_S764) -- nothing to undo"
  while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$TO" ] || stop "$LP is no longer this kit's (a later change) -- undo refused, so that change is not lost"; done <<< "$ROWS"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
  HAVE_LOCK=1
  bad=$(putback | tail -1); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$bad" = 0 ] && echo "UNDONE: every file is back; portal health $(wait200). The cp_* stores in $CP are kept (nothing of his is deleted)." || echo "!! not every file is back -- send a photo"
  exit 0
fi
echo "[1/7] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
ALL_TO=1
while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$TO" ] || ALL_TO=0; done <<< "$ROWS"
[ "$ALL_TO" = 1 ] && { echo "-- ALREADY INSTALLED: every file is the kit's. Nothing written. portal health $(phz)"; exit 0; }
while IFS='|' read -r LP KF FROM TO; do
  if [ "$FROM" = absent ]; then [ -e "$LP" ] && stop "$LP is already there (the kit expects it absent)"
  else L=$(m5 "$LP"); [ "$L" = "$FROM" ] || stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"; fi
done <<< "$ROWS"
SCR=$(mktemp -d /tmp/s764.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/live" "$SCR/remake" "$SCR/walk" "$SCR/ctl"
\cp "$PD/casepack_portal.py" "$CP/casepack_page.html" "$SCR/live/"
"$VPY" -B "$KDIR/make_s764.py" "$SCR/live" "$SCR/remake" >/dev/null 2>&1 || stop "make_s764.py did not run on the live bytes"
[ "$(m5 "$SCR/remake/casepack_portal.py")" = "a8774eef5301cb74fe13739336e735c8" ] || stop "make_s764.py on the live bytes does not give the kit's casepack_portal.py"
[ "$(m5 "$SCR/remake/casepack_page.html")" = "333f7825e5ba97018fcd1b2acefa74ab" ] || stop "make_s764.py on the live bytes does not give the kit's casepack_page.html"
for f in casepack_portal.py casepack_v2.py; do "$VPY" -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $VPY"; done
"$VPY" -B -c "import sys; sys.path.insert(0,'$KDIR'); import casepack_v2 as v; assert len(v.C)==54 and len(v.LIVE15)==15 and len(v.GROUPS_SEED)==8; c=v.calc({'surgery':20000,'implant':6000,'grade':'eco','stay':2,'room':'gen','anaesthesia':5000,'otMeds':3000,'wardMeds':2500,'admission':1200,'carm':4000,'investigations':2000}, v.RATES_SEED, 50); assert (c['total'],c['shareable'],c['my_net'])==(54700,35000,17500), c" 2>/dev/null \
  || stop "casepack_v2 does not import in the venv, or the worked example (54,700 / 35,000 / 17,500) does not hold"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/7] the live files are the ones this kit was built from; remade on the box byte-identically; the modules compile; the worked example holds"
\cp "$KDIR/casepack_portal.py" "$KDIR/casepack_v2.py" "$KDIR/casepack_page.html" "$KDIR/casepack_seed.html" "$SCR/walk/"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s764.py" "$SCR/walk" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the walk is not green ($R)";; esac
\cp "$PD/casepack_portal.py" "$CP/casepack_page.html" "$KDIR/casepack_v2.py" "$KDIR/casepack_seed.html" "$SCR/ctl/"
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s764.py" "$SCR/ctl" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/7] the walk on a made-up store (no live file read or written): $R; the live files: $R2"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ -d "$CP" ] || stop "$CP is not there"
echo "[4/7] portal health 200; $CP is there (the stores are written there on the owner's first open, never by this installer)"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[5/7] the build lock taken; the doctor's auto-fix paused for the restart"
while IFS='|' read -r LP KF FROM TO; do
  [ "$FROM" = absent ] && continue
  { \cp -p "$LP" "$LP.bak_S764" && [ "$(m5 "$LP.bak_S764")" = "$FROM" ]; } || stop "could not keep a backup of $LP"
done <<< "$ROWS"
PLACED=1
while IFS='|' read -r LP KF FROM TO; do
  REF="$LP.bak_S764"
  if [ "$FROM" = absent ]; then case "$LP" in "$PD"/*) REF="$PD/casepack_portal.py.bak_S764";; *) REF="$CP/casepack_page.html.bak_S764";; esac; fi
  \cp "$KDIR/$KF" "$LP.s764new" && chmod --reference="$REF" "$LP.s764new" && { chown --reference="$REF" "$LP.s764new" 2>/dev/null; true; } \
    && mv -f "$LP.s764new" "$LP" || restore "$LP could not be placed"
  [ "$(m5 "$LP")" = "$TO" ] || restore "$LP read-back did not match"
done <<< "$ROWS"
find "$PD" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[6/7] placed and read back: 4 files (backups *.bak_S764)"
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c1=$(wait200); [ "$c1" = 200 ] || restore "portal health $c1"
for door in /portal/casepack /portal/casepack/packages /portal/casepack/rates /portal/casepack/estimates /portal/casepack/templates /portal/casepack/seed; do
  c=$(hcode "http://127.0.0.1:$PPORT$door"); case "$c" in 302|401|403|303) ;; *) restore "$door answered $c without a login";; esac
done
c5=$(hcode "http://127.0.0.1:$PPORT/portal/casepack/v2/calc"); case "$c5" in 302|401|403|303|405) ;; *) restore "/portal/casepack/v2/calc answered $c5 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -v -E '"(GET|POST|HEAD) ' | grep -c -i -E 'casepack_v2|casepack_portal|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -v -E '"(GET|POST|HEAD) ' | grep -i -E 'casepack|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
PLACED=0
echo "[7/7] $PSVC restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): health $c1; without a login every Case Pack door refuses; the journal clean"
echo ""
echo "$KIT: DONE. Open https://followup.dr-manoj.in/portal/casepack -- your 15 packages are on the server from the first open; Manage packages is the seeding page."
