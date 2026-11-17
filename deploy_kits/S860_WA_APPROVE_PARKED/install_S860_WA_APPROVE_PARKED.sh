#!/bin/bash
# =============================================================================
#  install_S860_WA_APPROVE_PARKED.sh . kit S860 (17-Nov-2026, session S478, the parent) . F-1364 / D964
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s860kit && cp -rp /root/deploy/repo/deploy_kits/S860_WA_APPROVE_PARKED /tmp/s860kit && bash /tmp/s860kit/install_S860_WA_APPROVE_PARKED.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s860kit/install_S860_WA_APPROVE_PARKED.sh --undo
#
#  THE GAP: the wa-approve service (the old WhatsApp approvals page, port 8101) still runs although its tile was retired by
#  S816, and two tools still expect it: clinic-doctor lists it (it would restart it) and the key swap (S701) names it a reader.
#  THE CHANGE: those two rows out (clinic_doctor.py, swap_key_s701.py), then the service STOPPED and DISABLED -- its unit
#  file, its code and its settings stay on disk (kept, not removed). If anything is red, the files go back and the service is
#  enabled and started again.
# =============================================================================
set -u
KIT="S860_WA_APPROVE_PARKED"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CRONTAB="${CRONTAB:-crontab}"
UNITDIR="${UNITDIR:-/etc/systemd}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s860_backup}"
F1="${F1:-/root/deploy/clinic_doctor.py}";  FROM1=45de587b982c9e5b12c8b9f1c3b2ee3f; TO1=32c4a916861d48676e09e7f9723cc326
F2="${F2:-/root/wa/swap_key_s701.py}";      FROM2=d74a9021a1294c6e2ffe88f8512bfc2f; TO2=7125a3b7298d9f05d87c77d918d9a3ab
UNIT="wa-approve"
UNITFILE="${UNITFILE:-/etc/systemd/system/wa-approve.service}"
WALK_OK="WALK OK 8/8"
W=""; HAVE_LOCK=0; P1=0; P2=0; STOPPED=0; DISABLED=0; WAS_ACTIVE=""; WAS_ENABLED=""
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
on_exit() { [ -n "$W" ] && rm -rf "$W"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
isact() { "$SYSTEMCTL" is-active "$UNIT" 2>/dev/null | head -1; }
isen()  { "$SYSTEMCTL" is-enabled "$UNIT" 2>/dev/null | head -1; }
back() {
  local ok=1
  [ "$P1" = 1 ] && { \cp -fp "$BK/clinic_doctor.py.bak_S860" "$F1"; [ "$(m5 "$F1")" = "$FROM1" ] || { ok=0; echo "   !! clinic_doctor.py DID NOT GO BACK -- copy $BK/clinic_doctor.py.bak_S860 over $F1"; }; }
  [ "$P2" = 1 ] && { \cp -fp "$BK/swap_key_s701.py.bak_S860" "$F2"; [ "$(m5 "$F2")" = "$FROM2" ] || { ok=0; echo "   !! swap_key_s701.py DID NOT GO BACK -- copy $BK/swap_key_s701.py.bak_S860 over $F2"; }; }
  [ "$DISABLED" = 1 ] && [ "$WAS_ENABLED" = "enabled" ] && "$SYSTEMCTL" enable "$UNIT" >/dev/null 2>&1
  [ "$STOPPED" = 1 ] && [ "$WAS_ACTIVE" = "active" ] && "$SYSTEMCTL" start "$UNIT" >/dev/null 2>&1
  if [ "$STOPPED" = 1 ] && [ "$WAS_ACTIVE" = "active" ]; then sleep 2; [ "$(isact)" = "active" ] || { ok=0; echo "   !! $UNIT DID NOT START AGAIN -- systemctl start $UNIT"; }; fi
  [ "$ok" = 1 ] && echo "   everything went back: both files as before, $UNIT $(isact) / $(isen)"
  BACK_OK=$ok
}
red() { echo "!! RED: $1"; back; echo "!! STOPPED: $1"; echo "   Send a photo of this screen to Claude."; exit 1; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 clinic_doctor.py)" = "$TO1" ] && [ "$(m5 swap_key_s701.py)" = "$TO2" ] || stop "the kit's files are not the built ones"

if [ "${1:-}" = "--undo" ]; then
  [ "${DRY:-0}" = 1 ] && stop "DRY=1 and --undo were given together -- nothing done"
  for p in "$F1:$FROM1:$TO1:clinic_doctor.py" "$F2:$FROM2:$TO2:swap_key_s701.py"; do
    IFS=: read -r f fr to b <<< "$p"
    L=$(m5 "$f"); { [ "$L" = "$to" ] || [ "$L" = "$fr" ]; } || stop "$b has been changed since this kit (a later kit is on top) -- not undone"
  done
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
  HAVE_LOCK=1
  for p in "$F1:$FROM1:clinic_doctor.py" "$F2:$FROM2:swap_key_s701.py"; do
    IFS=: read -r f fr b <<< "$p"
    if [ "$(m5 "$f")" != "$fr" ]; then
      [ "$(m5 "$BK/$b.bak_S860")" = "$fr" ] || stop "no good S860 backup of $b in $BK -- not undone"
      \cp -fp "$BK/$b.bak_S860" "$f"; [ "$(m5 "$f")" = "$fr" ] || stop "$b did not go back"
    fi
  done
  "$SYSTEMCTL" enable "$UNIT" >/dev/null 2>&1; "$SYSTEMCTL" start "$UNIT" >/dev/null 2>&1; sleep 2
  [ "$(isact)" = "active" ] || stop "$UNIT did not start" "Both files are back."
  echo "UNDONE: both files put back; $UNIT enabled and running again ($(isact) / $(isen))."
  exit 0
fi

echo "1. kit files: all match SUMS.md5"
N1=$(m5 "$F1"); N2=$(m5 "$F2"); WAS_ACTIVE=$(isact); WAS_ENABLED=$(isen)
if [ "$N1" = "$TO1" ] && [ "$N2" = "$TO2" ] && [ "$WAS_ACTIVE" != "active" ] && [ "$WAS_ENABLED" = "disabled" ]; then
  echo "-- ALREADY INSTALLED (both files placed; $UNIT $WAS_ACTIVE / $WAS_ENABLED)"; exit 0
fi
[ "$N1" = "$FROM1" ] || [ "$N1" = "$TO1" ] || stop "clinic_doctor.py is not the file this kit was built on (${N1:0:8})"
[ "$N2" = "$FROM2" ] || [ "$N2" = "$TO2" ] || stop "swap_key_s701.py is not the file this kit was built on (${N2:0:8})"
[ -f "$UNITFILE" ] || stop "the unit file $UNITFILE is not on the box"
echo "2. the live files are the ones this kit was built on; $UNIT is $WAS_ACTIVE / $WAS_ENABLED"
# the cold review's gate (S478): nothing else on the box may need wa-approve -- no unit that Requires/BindsTo/Wants it, no cron
# line, no other unit file naming it or its port. Read only.
RD=$("$SYSTEMCTL" list-dependencies --reverse --plain --no-legend "$UNIT" 2>/dev/null | sed 's/^[^a-zA-Z0-9]*//' | grep -v -E "^$UNIT(\.service)?$" | grep -v -E '\.target$' | grep -c . || true)
[ "${RD:-0}" = 0 ] || stop "another unit depends on $UNIT ($("$SYSTEMCTL" list-dependencies --reverse --plain --no-legend "$UNIT" 2>/dev/null | grep -v -E '\.target$' | head -3 | tr '\n' ' ')) -- not stopped"
CR=$("$CRONTAB" -l 2>/dev/null | grep -v '^#' | grep -c -E 'wa-approve|wa_approve|:8101' || true)
[ "${CR:-0}" = 0 ] || stop "the crontab names $UNIT or its port -- not stopped"
UR=$(grep -rlE 'wa-approve|wa_approve|:8101' "$UNITDIR" 2>/dev/null | grep -v -E '/wa-approve\.service$|/multi-user\.target\.wants/wa-approve\.service$' | head -3)
[ -z "$UR" ] || stop "another systemd file names $UNIT or its port ($UR) -- not stopped"
echo "   nothing else depends on it: no unit needs it, no cron line, no other unit file names it"
"$PY" -B -c "import sys; [compile(open(p, encoding='utf-8').read(), p, 'exec') for p in sys.argv[1:]]" "$KDIR/clinic_doctor.py" "$KDIR/swap_key_s701.py" 2>/dev/null || stop "the kit's files do not compile with $PY"
W=$(mktemp -d /tmp/s860w.XXXX) || stop "no scratch folder could be made in /tmp"
chmod 700 "$W"; \cp -f "$F1" "$W/cd_live.py"; \cp -f "$F2" "$W/sk_live.py"
[ "$(m5 "$W/cd_live.py")" = "$FROM1" ] || \cp -f "$BK/clinic_doctor.py.bak_S860" "$W/cd_live.py" 2>/dev/null
[ "$(m5 "$W/sk_live.py")" = "$FROM2" ] || \cp -f "$BK/swap_key_s701.py.bak_S860" "$W/sk_live.py" 2>/dev/null
R=$(cd "$W" && "$PY" -B "$KDIR/walk_s860.py" "$W/cd_live.py" "$KDIR/clinic_doctor.py" "$W/sk_live.py" "$KDIR/swap_key_s701.py" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || stop "the walk is not green ($R)"
R2=$(cd "$W" && "$PY" -B "$KDIR/walk_s860.py" "$W/cd_live.py" "$W/cd_live.py" "$W/sk_live.py" "$W/sk_live.py" 2>&1 | tail -1)
case "$R2" in "WALK RED"*) ;; *) stop "the control (the live files in the kit's place) did not go red ($R2)";; esac
echo "3. the walk: $R | control: $R2"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }

mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
mkdir -p "$BK"; chmod 700 "$BK"
if [ "$N1" = "$FROM1" ]; then
  \cp -fp "$F1" "$BK/clinic_doctor.py.bak_S860" && [ "$(m5 "$BK/clinic_doctor.py.bak_S860")" = "$FROM1" ] || stop "could not keep a backup of clinic_doctor.py"
  P1=1; \cp -f "$KDIR/clinic_doctor.py" "$F1.s860new" && mv -f "$F1.s860new" "$F1" && [ "$(m5 "$F1")" = "$TO1" ] || red "clinic_doctor.py did not land byte-exact"
fi
if [ "$N2" = "$FROM2" ]; then
  \cp -fp "$F2" "$BK/swap_key_s701.py.bak_S860" && [ "$(m5 "$BK/swap_key_s701.py.bak_S860")" = "$FROM2" ] || red "could not keep a backup of swap_key_s701.py"
  P2=1; \cp -f "$KDIR/swap_key_s701.py" "$F2.s860new" && mv -f "$F2.s860new" "$F2" && [ "$(m5 "$F2")" = "$TO2" ] || red "swap_key_s701.py did not land byte-exact"
fi
chmod 600 "$BK"/* 2>/dev/null
echo "4. placed clinic_doctor.py ${FROM1:0:8} -> ${TO1:0:8} and swap_key_s701.py ${FROM2:0:8} -> ${TO2:0:8} (copies in $BK)"
"$PY" -B -c "import sys; [compile(open(p, encoding='utf-8').read(), p, 'exec') for p in sys.argv[1:]]" "$F1" "$F2" 2>/dev/null || red "the placed files do not compile"
if [ "$WAS_ACTIVE" = "active" ]; then STOPPED=1; "$SYSTEMCTL" stop "$UNIT" >/dev/null 2>&1; fi
if [ "$WAS_ENABLED" = "enabled" ]; then DISABLED=1; "$SYSTEMCTL" disable "$UNIT" >/dev/null 2>&1; fi
sleep 1
A=$(isact); E=$(isen)
[ "$A" != "active" ] || red "$UNIT is still running after the stop"
[ "$E" = "disabled" ] || red "$UNIT is not disabled ($E)"
[ -f "$UNITFILE" ] || red "the unit file went missing"
echo "5. $UNIT stopped and disabled ($A / $E); its unit file, code and settings are kept on disk"
echo ""
echo "$KIT: DONE. The old WhatsApp approvals service is switched off and kept; clinic-doctor and the key swap no longer expect it. Nothing on any page changes."
