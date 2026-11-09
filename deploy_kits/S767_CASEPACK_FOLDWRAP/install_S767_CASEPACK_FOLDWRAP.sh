#!/bin/bash
# =============================================================================
#  install_S767_CASEPACK_FOLDWRAP.sh . kit S767 (09-Nov-2026, session S418, the parent) . the live read of S764, 18:0x IST
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s767kit && cp -rp /root/deploy/repo/deploy_kits/S767_CASEPACK_FOLDWRAP /tmp/s767kit && bash /tmp/s767kit/install_S767_CASEPACK_FOLDWRAP.sh
#  /root/wa/casepack/casepack_page.html  333f7825 (S764) -> 71565ab9  one CSS selector: the nowrap rule reaches the two box titles only,
#      so a long fold label inside the Build card wraps instead of running into its figure. Nothing else changes; no restart needed
#      (the page is read from disk on every request).
#  Undo:  bash /tmp/s767kit/install_S767_CASEPACK_FOLDWRAP.sh --undo
# =============================================================================
set -u
KIT="S767_CASEPACK_FOLDWRAP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
CP="${CP:-/root/wa/casepack}"; LP="$CP/casepack_page.html"
PPORT="${PPORT:-8099}"
FROM=333f7825e5ba97018fcd1b2acefa74ab; TO=71565ab919b519a684dd686c92c6ac1f
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/casepack_page.html")" = "$TO" ] || stop "the kit's page is not the built file"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$LP.bak_S767" ] || stop "no backup ($LP.bak_S767) -- nothing to undo"
  [ "$(m5 "$LP")" = "$TO" ] || stop "the live page is no longer this kit's (a later change) -- undo refused"
  \cp -p "$LP.bak_S767" "$LP" && [ "$(m5 "$LP")" = "$FROM" ] && echo "UNDONE: the page is back at ${FROM:0:8}" || echo "!! not back -- send a photo"
  exit 0
fi
echo "[1/4] kit files: all match SUMS.md5"
[ "$(m5 "$LP")" = "$TO" ] && { echo "-- ALREADY INSTALLED: the page is the kit's. Nothing written."; exit 0; }
L=$(m5 "$LP"); [ "$L" = "$FROM" ] || stop "the live page changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
SCR=$(mktemp -d /tmp/s767.XXXX); mkdir -p "$SCR/live" "$SCR/remake"; \cp "$LP" "$SCR/live/"
"$VPY" -B "$KDIR/make_s767.py" "$SCR/live" "$SCR/remake" >/dev/null 2>&1 || { rm -rf "$SCR"; stop "make_s767.py did not run on the live bytes"; }
[ "$(m5 "$SCR/remake/casepack_page.html")" = "$TO" ] || { rm -rf "$SCR"; stop "make_s767.py on the live bytes does not give the kit's page"; }
R=$("$VPY" -B "$KDIR/walk_s767.py" "$KDIR" 2>&1 | tail -1); case "$R" in "WALK OK"*) ;; *) rm -rf "$SCR"; stop "the walk is not green ($R)";; esac
R2=$("$VPY" -B "$KDIR/walk_s767.py" "$SCR/live" --control 2>&1 | tail -1); case "$R2" in "CONTROL: red"*) ;; *) rm -rf "$SCR"; stop "the control on the live page did not go red ($R2)";; esac
rm -rf "$SCR"
echo "[2/4] the live page is S764's; remade on the box byte-identically; walk $R; live: $R2"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
{ \cp -p "$LP" "$LP.bak_S767" && [ "$(m5 "$LP.bak_S767")" = "$FROM" ]; } || stop "could not keep a backup"
\cp "$KDIR/casepack_page.html" "$LP.s767new" && chmod --reference="$LP.bak_S767" "$LP.s767new" && { chown --reference="$LP.bak_S767" "$LP.s767new" 2>/dev/null; true; } && mv -f "$LP.s767new" "$LP" || { \cp -p "$LP.bak_S767" "$LP"; stop "could not place the page (put back)"; }
[ "$(m5 "$LP")" = "$TO" ] || { \cp -p "$LP.bak_S767" "$LP"; stop "read-back did not match (put back)"; }
echo "[3/4] placed and read back (backup $LP.bak_S767); no restart -- the portal reads the page from disk"
c=$(hcode "http://127.0.0.1:$PPORT/portal/casepack"); case "$c" in 302|401|403|303) ;; *) echo "!! /portal/casepack answered $c without a login"; \cp -p "$LP.bak_S767" "$LP"; stop "put back";; esac
echo "[4/4] /portal/casepack still refuses without a login ($c)"
echo ""
echo "$KIT: DONE. Reload the Case Pack page once (Ctrl+F5)."
