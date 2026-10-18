#!/bin/bash
# =============================================================================
#  install_S586_PORTAL_TILE_GROUPS.sh · kit S586 (session S326, 18-Oct-2026) · D739
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s586kit && cp -rp /root/deploy/repo/deploy_kits/S586_PORTAL_TILE_GROUPS /tmp/s586kit && bash /tmp/s586kit/install_S586_PORTAL_TILE_GROUPS.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  THE OWNER, 18-Oct 15:24-15:48 IST (D739): the portal home regrouped -- for him ten group tiles, each opening a submenu;
#  the Sanjeevni tiles untouched behind one tile; eight old Google-Sheet / Apps-Script / clinic-PC tiles retired; Renewals
#  on the server; Dr Bhawna down to seven tiles (Patient records and Check karein off, a Staff folder on). Display only.
#   /root/portal/portal.py          963911cc -> PO_TO   18 counted edits (make_s586.py), rebuilt from the live bytes on the box
#   /root/portal/tile_grants.json   merged in place (merge_grants_s586.py, additive): manoj folders, bhawna folders/only/mask,
#                                   staff section order, version + 1
#  No database step. Restarts clinic-portal only. Housekeeping: /tmp/s578kit, /tmp/s581kit if present (Runbook §2A item 10).
#  Red after placing: both files put back byte-identically, clinic-portal restarted.
# =============================================================================
set -u
KIT="S586_PORTAL_TILE_GROUPS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"             # the portal's python
POR="${POR:-/root/portal}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
POR_PORT="${POR_PORT:-8099}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
HOUSEKEEP="${HOUSEKEEP:-/tmp/s578kit /tmp/s581kit}"
PO_FROM=963911cc41eac1ef98677b54e1a17291; PO_TO=25cb73e7869813a56df1f0bef6c0dce5
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s586_inst_$STAMP"
HAVE_LOCK=0
B_PO="$POR/portal.py.bak_S586_${PO_FROM:0:8}"; B_TG="$POR/tile_grants.json.bak_S586_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "!! STOPPED: $1"; say "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"); [ "$h" = "$2" ] && break; done; echo "$h"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting both files back"
  [ -f "$B_PO" ] && \cp -p "$B_PO" "$POR/portal.py"
  [ -f "$B_TG" ] && \cp -p "$B_TG" "$POR/tile_grants.json"
  rm -f "$POR"/.*.s586
  "$SYSTEMCTL" restart clinic-portal || true
  say "   portal $(m5 "$POR/portal.py") (expected $PO_FROM) · grants $(m5 "$POR/tile_grants.json") (expected $(m5 "$B_TG"))"
  say "   health: portal $(health "http://127.0.0.1:$POR_PORT/portal/login" 200)"
  say "   Send a photo of this screen to Claude."
  exit 1
}

say "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
say "[1/7] kit files: all match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
mkdir -p "$SCR/built" "$SCR/g" || stop "no scratch folder"

if [ "$(m5 "$POR/portal.py")" = "$PO_TO" ] && grep -q '"folders"' "$POR/tile_grants.json"; then
  say "ALREADY INSTALLED (portal ${PO_TO:0:8}, the grants carry folders)."
  exit 0
fi
[ "$(m5 "$POR/portal.py")" = "$PO_FROM" ] || stop "$POR/portal.py is $(m5 "$POR/portal.py"), not the pinned $PO_FROM"
"$VPY" -c "import json,sys; d=json.load(open(sys.argv[1])); assert isinstance(d.get('users'),dict) and 'manoj' in d['users'] and 'bhawna' in d['users']" "$POR/tile_grants.json" 2>/dev/null \
  || stop "$POR/tile_grants.json does not read as the grants file (users manoj and bhawna)"
say "[2/7] pins: portal ${PO_FROM:0:8} · grants file readable"

PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -m py_compile make_s586.py merge_grants_s586.py walk_s586.py || stop "the kit's python does not compile on $VPY"
"$VPY" -B make_s586.py "$POR/portal.py" "$SCR/built" >/dev/null || stop "the builder refused the live file"
[ "$(m5 "$SCR/built/portal.py")" = "$PO_TO" ] || stop "rebuilt portal.py is $(m5 "$SCR/built/portal.py"), not $PO_TO"
PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -m py_compile "$SCR/built/portal.py" || stop "rebuilt portal.py does not compile on $VPY"
say "[3/7] compiled; rebuilt from the live bytes (18 counted edits) to portal ${PO_TO:0:8}"

\cp -p "$POR/tile_grants.json" "$SCR/g/before.json" && \cp -p "$POR/tile_grants.json" "$SCR/g/after.json" || stop "no scratch copy of the grants"
"$VPY" -B merge_grants_s586.py "$SCR/g/after.json" >/dev/null || stop "the grants merge failed on a copy"
"$VPY" -B merge_grants_s586.py "$SCR/g/after.json" | grep -q "already merged" || stop "the grants merge is not idempotent on a copy"
W="$( cd "$SCR" && PYTHONPATH="$POR" timeout 600 "$VPY" -B "$KDIR/walk_s586.py" "$POR/portal.py" "$SCR/built/portal.py" "$SCR/g/before.json" "$SCR/g/after.json" 2>&1 | tail -1 )"
echo "$W" | grep -Eq '^[0-9]+ checks, 0 FAIL$' || stop "the walk is not all green ($W)"
R="$( cd "$SCR" && PYTHONPATH="$POR" timeout 600 "$VPY" -B "$KDIR/walk_s586.py" "$POR/portal.py" "$SCR/built/portal.py" "$SCR/g/before.json" "$SCR/g/after.json" --expect-red 2>&1 | tail -1 )"
echo "$R" | grep -Eq ', 0 wrongly green$' || stop "the control did not go red on the live file ($R)"
say "[4/7] the walk on the box, against the live grants: $W · control: $R"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

\cp -p "$POR/portal.py" "$B_PO" && \cp -p "$POR/tile_grants.json" "$B_TG" || stop "a file backup failed"
[ "$(m5 "$B_PO")" = "$PO_FROM" ] || stop "the portal backup is not the live file"
say "[5/7] backups: $(basename "$B_PO"), $(basename "$B_TG")"

\cp -p "$SCR/built/portal.py" "$POR/.portal.py.s586" && mv -f "$POR/.portal.py.s586" "$POR/portal.py" || restore "placing portal.py"
[ "$(m5 "$POR/portal.py")" = "$PO_TO" ] || restore "portal.py did not land at its md5"
TG="$("$VPY" -B merge_grants_s586.py "$POR/tile_grants.json" 2>&1)" || restore "the grants merge"
chmod --reference="$B_TG" "$POR/tile_grants.json" 2>/dev/null
"$VPY" -c "import json,sys; json.load(open(sys.argv[1]))" "$POR/tile_grants.json" || restore "the merged grants file does not read"
say "[6/7] placed; md5 read back: portal $(m5 "$POR/portal.py") · $TG"

"$SYSTEMCTL" restart clinic-portal || restore "restart clinic-portal"
c2=$(health "http://127.0.0.1:$POR_PORT/portal/login" 200)
"$SYSTEMCTL" is-active --quiet clinic-portal || restore "clinic-portal is not active"
[ "$c2" = 200 ] || restore "health portal $c2"
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$POR_PORT/portal/")
case "$c3" in 200|302) ;; *) restore "the home page answers $c3";; esac
for d in $HOUSEKEEP; do [ -d "$d" ] && rm -rf "$d" && say "   housekeeping: removed $d"; done
say "[7/7] clinic-portal restarted and active - login $c2 - home $c3"
say ""
say "INSTALLED. Open your portal: ten tiles, each opens its submenu; the back button closes it."
say "Dr Bhawna's phone shows her seven. Staff screens are unchanged."
say "undo: see the README (portal.py.bak_S586_${PO_FROM:0:8} and the grants .bak beside the files)"
