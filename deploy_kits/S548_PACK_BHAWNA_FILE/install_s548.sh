#!/bin/bash
# install_s548.sh -- S548_PACK_BHAWNA_FILE (D721): Dr Bhawna's personal expenses become the accountants' pack's own item 8.3;
# item 8.2, Dr Manoj's expense file, keeps only Dr MK's. One file: /root/finance/packs.py (THE PARENT'S; its PLANNED line is on
# the board, v397). No database change. Safe before S544: without the scan app's pe_who column the pack is as today.
# BUILD_NORM_v1 s3 order: gates -> the build lock -> pin -> rebuild -> walk + control -> backup -> place -> restart
#                         clinic-finance only -> health -> words -> undo.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S548_PACK_BHAWNA_FILE/install_s548.sh
set -u
KIT="S548_PACK_BHAWNA_FILE"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIN="${S548_FIN_DIR:-/root/finance}"
PY="${S548_PYTHON:-/usr/bin/python3}"
SVC="${S548_SERVICE:-clinic-finance}"
HEALTH="${S548_HEALTH_URL:-http://127.0.0.1:8106/finance/healthz}"
RESTART="${S548_RESTART_CMD:-systemctl restart $SVC}"
ACTIVE="${S548_ACTIVE_CMD:-systemctl is-active --quiet $SVC}"
LOCK="${S548_LOCK:-/root/deploy/.claude_code_build.lock}"
F="packs.py"
FROM="ada0860ad0b64e95836b24880927071f"
TO="$(tr -d ' \n' < "$HERE/PIN_TO_packs.txt" 2>/dev/null)"
HAVE_LOCK=0
WORK="$(mktemp -d "${HOME:-/root}/s548_install_XXXX")" && [ -n "$WORK" ] && [ -d "$WORK" ] || { echo "REFUSED: no temporary folder"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
trap 'rm -rf "$WORK"; rm -f "$FIN/$F.tmp"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"' EXIT
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }

log "gates"
[ -n "$TO" ] || die "PIN_TO_packs.txt missing"
[ -f "$FIN/$F" ] || die "$FIN/$F missing"
command -v "$PY" >/dev/null || die "no $PY"
for k in make_s548.py walk_s548.py; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pin -- the live bytes must be the ones this kit was built on"
L="$(md5 "$FIN/$F")"
if [ "$L" = "$TO" ]; then echo "$KIT: ALREADY INSTALLED ($F at the kit's pin ${TO:0:8})"; exit 0; fi
[ "$L" = "$FROM" ] || die "$F is ${L:0:8}, not the pinned ${FROM:0:8} -- the parent moved it; rebuild S548 on the new bytes"
echo "    $F ${L:0:8} ok"

log "rebuild on the box, from the live bytes"
cp "$FIN/$F" "$WORK/live_packs.py"
"$PY" "$HERE/make_s548.py" "$WORK/live_packs.py" "$WORK/packs.py" >/dev/null || die "the builder refused"
B="$(md5 "$WORK/packs.py")"; [ "$B" = "$TO" ] || die "the rebuilt file is ${B:0:8}, the kit says ${TO:0:8}"
"$PY" -m py_compile "$WORK/packs.py" || die "the built file does not compile"
echo "    rebuilt ${B:0:8} = the kit's pin"

log "walk (made-up scan rows only; the program files copied under the session's home, removed after) -- and the control on the live file"
( cd "$WORK" && HOME="$WORK" "$PY" -B "$HERE/walk_s548.py" "$WORK/packs.py" "$FIN" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^(RED|GREEN)|checks' "$WORK/walk.txt"; die "the walk is RED on the built file"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
( cd "$WORK" && HOME="$WORK" "$PY" -B "$HERE/walk_s548.py" "$WORK/live_packs.py" "$FIN" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live file"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live file, must be red): /'

log "backup beside the live file"
cp -p "$FIN/$F" "$FIN/$F.bak_S548_${FROM:0:8}" || die "backup failed"
echo "    $F.bak_S548_${FROM:0:8}"

restore(){
  echo "RESTORING $F from its backup"
  cp -p "$FIN/$F.bak_S548_${FROM:0:8}" "$FIN/$F.tmp" && mv -f "$FIN/$F.tmp" "$FIN/$F"
  eval "$RESTART" || true
  [ "$(md5 "$FIN/$F")" = "$FROM" ] || { echo "RESTORE FAILED -- run the UNDO line in the README"; exit 2; }
  echo "$KIT: NOT INSTALLED (restored; $F is back at ${FROM:0:8})"; exit 1
}

log "place"
if ! { cp "$WORK/packs.py" "$FIN/$F.tmp" && mv -f "$FIN/$F.tmp" "$FIN/$F"; }; then rm -f "$FIN/$F.tmp"; [ "$(md5 "$FIN/$F")" = "$FROM" ] || restore; die "could not place $F"; fi
[ "$(md5 "$FIN/$F")" = "$TO" ] || restore
echo "    placed at the kit's pin"

log "restart $SVC only, then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 20); do sleep 2; HC="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$HEALTH" || true)"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing} for 40 s"; restore; }
eval "$ACTIVE" || { echo "    $SVC is not active"; restore; }
echo "    healthz 200 . $SVC active"
echo
echo "$KIT: DONE."
echo "  PIN (read back): $F $(md5 "$FIN/$F") . RELEASED to the parent: build on packs.py only from this byte."
echo "  WHAT THE OWNER SEES on the accountants' pack page: a new line 8.3 'Scanned bills: Dr Bhawna's expense-file bills'; 8.2,"
echo "  Dr Manoj's expense-file bills, now carries only Dr MK's personal expenses. Until a paper is marked Dr Bhawna (the scan app's"
echo "  Personal expense, S544), 8.3 reads 'not ready'. The mail to the accountants carries 8.3 as its own PDF when it is ready."
echo "  UNDO (one line): cp -p $FIN/$F.bak_S548_${FROM:0:8} $FIN/$F && systemctl restart $SVC"
exit 0
