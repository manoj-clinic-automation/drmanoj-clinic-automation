#!/bin/bash
# =============================================================================
#  install_S721_PHYSIO_BACKFILL_RECEPTION.sh . kit S721_PHYSIO_BACKFILL_RECEPTION (06-Nov-2026, session S390, the parent)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s721kit && cp -rp /root/deploy/repo/deploy_kits/S721_PHYSIO_BACKFILL_RECEPTION /tmp/s721kit && bash /tmp/s721kit/install_S721_PHYSIO_BACKFILL_RECEPTION.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s721kit/install_S721_PHYSIO_BACKFILL_RECEPTION.sh --undo
#
#  The owner, 08:11 IST 06-Nov: "bhati home visit backfill option required for october mth, reception shd be able to do
#  physiotherapy clinic slips entries also".
#  /root/finance/physio_book.py  a085fee7 -> new   a home patient's page gains "Purane visit ek saath (backfill)": every day
#      from the floor (01-Oct) as a tick box, one press writes one visit per ticked day, never twice on a day for that patient;
#      the start moves back to the earliest ticked day. A maker not named in physio_book.home_makers (default bhati) writes
#      CLINIC slips only: no Ghar tab, every home route refused.
#  finance.db unit_role  seed_s721.py: physiobook maker for alisha, shivani, reception; physio viewer for reception (the
#      front gate's own row). Only where absent; --undo takes back exactly these.
#  /root/portal/tile_grants.json  v42 -> v43: the 'Physiotherapy' tile to alisha, shivani and reception (display only; its page
#      carries the 'Patient-wise register' button for a register role). Restarts clinic-finance and clinic-portal.
# =============================================================================
set -u
KIT="S721_PHYSIO_BACKFILL_RECEPTION"
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN="${FIN:-/root/finance}"
DB="${DB:-/root/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
MOD="physio_book"
LF="$FIN/$MOD.py"; FROM=a085fee79c2b0346e4417798cd9808f5; TO=9c3442d6e328fe0d8bd751762c1ee4d6
WALK_OK="WALK OK 43/43"
HAVE_LOCK=0; PLACED=0; W=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$W" ] && rm -rf "$W"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }
restart_ok() {
  local since; since=$(date '+%Y-%m-%d %H:%M:%S')
  "$SYSTEMCTL" restart "$SVC"; h=000
  for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
  [ "$h" = 200 ] || return 1
  "$JOURNALCTL" -u "$SVC" --since "$since" --no-pager 2>/dev/null | grep -q "$MOD NOT mounted" && return 2
  return 0
}
seed() { "$PYS" -B "$KDIR/seed_s721.py" "$DB" "$@"; }
PYS=/usr/bin/python3; [ -x "$PYS" ] || PYS=/root/wa/venv/bin/python3
GL="${GRANTS:-/root/portal/tile_grants.json}"; GFROM=64305c5fae3476586d96ba0d71eb3362; GTO=f2dad1579505c672de4270ed7fecb224; GF=""
grants_check() { GF=$(m5 "$GL"); [ "$GF" = "$GFROM" ] || [ "$GF" = "$GTO" ]; }
grants_place() {
  GF=$(m5 "$GL")
  if [ "$GF" = "$GTO" ]; then echo "8. tile_grants.json already v43"; return 0; fi
  if [ "$GF" != "$GFROM" ]; then echo "8. !! tile_grants.json changed since the check (${GF:0:8}) -- NOT placed; the register works, the tile waits. Send a photo to Claude."; return 0; fi
  "$PYS" -c "import json,sys; json.load(open(sys.argv[1]))" "$KDIR/tile_grants.json" || { echo "8. !! the kit's tile_grants.json is not JSON -- not placed"; return 0; }
  \cp -p "$GL" "$GL.bak_S721" && \cp "$KDIR/tile_grants.json" "$GL.s721new" && chmod --reference="$GL.bak_S721" "$GL.s721new" && chown --reference="$GL.bak_S721" "$GL.s721new" && mv -f "$GL.s721new" "$GL"
  if [ "$(m5 "$GL")" = "$GTO" ]; then echo "8. tile_grants.json v42 -> v43 (the Physiotherapy tile to alisha, shivani, reception; read on every request, no restart)"
  else [ -f "$GL.bak_S721" ] && \cp -p "$GL.bak_S721" "$GL"; echo "8. !! tile_grants.json did not read back -- v42 put back"; fi
}
grants_undo() { [ "$(m5 "$GL")" = "$GTO" ] && [ -f "$GL.bak_S721" ] && \cp -p "$GL.bak_S721" "$GL" && echo "   tile_grants.json v42 put back"; return 0; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting $MOD.py back"
  seed --undo 2>&1 | sed 's/^/   /'; grants_undo
  \cp -p "$LF.bak_S721" "$LF"; restart_ok; r=$?
  [ "$(m5 "$LF")" = "$FROM" ] && echo "   $MOD.py is back byte-identically" || echo "   !! copy $LF.bak_S721 back by hand"
  echo "   after the restore: finance $(health). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/$MOD.py")" = "$TO" ] || stop "the kit's $MOD.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$LF.bak_S721" ] || stop "no backup $LF.bak_S721 -- nothing to undo"
  [ "$(m5 "$LF")" = "$TO" ] || stop "the live $MOD.py is not this kit's (${TO:0:8}) -- a later change would be undone; nothing done"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK)"; HAVE_LOCK=1
  seed --undo 2>&1 | sed 's/^/   /'; grants_undo
  \cp -p "$LF.bak_S721" "$LF"; restart_ok; echo "UNDONE: $MOD.py $(m5 "$LF" | cut -c1-8), finance $(health)."; exit 0
fi
echo "1. kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
NOW=$(m5 "$LF")
if [ "$NOW" = "$TO" ]; then echo "-- ALREADY INSTALLED ($MOD.py ${TO:0:8})"; R=$(seed 2>&1); echo "   the roles step (safe to repeat): $R"; grants_place; exit 0; fi
[ "$NOW" = "$FROM" ] || stop "the live $MOD.py changed since this kit was built (live ${NOW:0:8}, kit expects ${FROM:0:8})"
echo "2. the live $MOD.py is the one this kit was built from (${FROM:0:8})"
PYF=""; for c in /usr/bin/python3 /root/wa/venv/bin/python3 /root/finance/venv/bin/python3 "$(command -v python3)"; do [ -x "$c" ] && "$c" -c "import flask" 2>/dev/null && PYF="$c" && break; done
[ -n "$PYF" ] || stop "no python on this box can import flask for the walk"
W=$(mktemp -d /tmp/s721w.XXXX); \cp "$LF" "$W/live.py"; \cp "$KDIR/$MOD.py" "$W/kit.py"
"$PYF" -B -m py_compile "$W/kit.py" || stop "$MOD.py does not compile with $PYF"
R=$(cd "$W" && "$PYF" -B "$KDIR/walk_s721.py" "$W/kit.py" "$W/live.py" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$W" && "$PYF" -B "$KDIR/walk_s721.py" "$W/kit.py" "$W/live.py" 2>&1 | grep -E 'FAIL|Error' | head); stop "the walk is not green ($R)"; }
echo "3. the walk on a made-up database, against the live file: $R"
R=$(cd "$W" && "$PYF" -B "$KDIR/walk_s721.py" "$W/live.py" "$W/live.py" 2>&1 | tail -1)
case "$R" in "WALK RED"*) echo "   control (the live file in the kit's place): $R -- red, as it must be";; *) stop "the control did not go red ($R)";; esac
R=$(seed --dry 2>&1) || stop "the roles step's DRY run did not pass ($R)"; echo "   the roles, DRY on the live database: $R"
grants_check || stop "the live tile_grants.json is not v42 (${GF:0:8}) -- not the file this kit was built on"
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
[ "$(m5 "$LF")" = "$FROM" ] || stop "the live $MOD.py changed while this kit was checking -- run the line again"
\cp -p "$LF" "$LF.bak_S721" || stop "could not keep a backup of $MOD.py"
echo "4. backup: $MOD.py.bak_S721"
PLACED=1
\cp "$KDIR/$MOD.py" "$LF.s721new" && chmod --reference="$LF.bak_S721" "$LF.s721new" && chown --reference="$LF.bak_S721" "$LF.s721new" && mv -f "$LF.s721new" "$LF" || restore "$MOD.py could not be placed"
[ "$(m5 "$LF")" = "$TO" ] || restore "read-back did not match"
echo "5. placed $MOD.py (${TO:0:8}), read back by md5"
restart_ok; RR=$?
[ "$RR" = 0 ] || restore "finance $(health); the journal says $MOD NOT mounted: $([ "$RR" = 2 ] && echo yes || echo no)"
echo "6. $SVC restarted and healthy; $MOD mounted (no 'NOT mounted' line since the restart)"
R=$(seed 2>&1) || restore "the roles step failed ($R)"; echo "7. $R"
grants_place
PLACED=0
echo ""
echo "$KIT: DONE. Bhati can tick his October home visits in one go, and reception can write the physiotherapy clinic slips (Physiotherapy tile, then Patient-wise register)."
