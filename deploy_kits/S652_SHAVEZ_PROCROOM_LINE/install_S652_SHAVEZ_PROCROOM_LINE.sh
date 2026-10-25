#!/bin/bash
# =============================================================================
#  install_S652_SHAVEZ_PROCROOM_LINE.sh . kit S652 (25-Oct-2026, session S354, the parent) . Shavez's 'Kal ke procedures' line
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s652kit && cp -rp /root/deploy/repo/deploy_kits/S652_SHAVEZ_PROCROOM_LINE /tmp/s652kit && bash /tmp/s652kit/install_S652_SHAVEZ_PROCROOM_LINE.sh
#  (DRY=1 before bash: every gate and both walks, nothing written.)
#
#  /root/finance/aaj_duties.json  90219853 -> 1d085d58  1 counted edit: the fetch line shavez.procroom_morning (shipped as .json.kit)
#  /root/finance/aaj_seed.py      64d9a607 -> 2121947f  1 counted edit: his line, first section
#  No data step. Restarts clinic-finance. Red after placing: both old files back byte-identically, restart.
#  Undo:  \cp -p /root/finance/aaj_duties.json.bak_S652 /root/finance/aaj_duties.json; \cp -p /root/finance/aaj_seed.py.bak_S652 /root/finance/aaj_seed.py; systemctl restart clinic-finance
# =============================================================================
set -u
KIT="S652_SHAVEZ_PROCROOM_LINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
MAPF="${DUTY_MAP_JSON:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"; export DUTY_MAP_JSON="$MAPF"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
MAPMD5=78b5f07ef7cdd48b1a76d78db52107fc
ROWS="$FIN/aaj_duties.json|aaj_duties.json.kit|90219853b4a25b051fa3f53f6c09d74d|1d085d5873d97beff138b01e15e11577
$FIN/aaj_seed.py|aaj_seed.py|64d9a607fda40b34a96ed72fa688979b|2121947f27ce6c5e024b30b0926a898d"
HAVE_LOCK=0; WN=""; WO=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$WN" ] && rm -rf "$WN" "$WO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
ALL_TO=1
while IFS='|' read -r LP KF FROM TO; do
  [ "$(m5 "$KDIR/$KF")" = "$TO" ] || stop "the kit's $KF is not the built file"
  [ "$(m5 "$LP")" = "$TO" ] || ALL_TO=0
done <<< "$ROWS"
[ "$ALL_TO" = 1 ] && { echo "ALREADY INSTALLED."; exit 0; }
while IFS='|' read -r LP KF FROM TO; do
  L=$(m5 "$LP"); [ "$L" = "$FROM" ] || stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
done <<< "$ROWS"
[ "$(m5 "$MAPF")" = "$MAPMD5" ] || stop "the duty map $MAPF is not v20 (78b5f07e) -- it moved since this kit was built"
echo "2. the two live files and the duty map are the ones this kit was built from"
DB=$("$SYSTEMCTL" show -p Environment "$SVC" 2>/dev/null | sed 's/^Environment=//' | tr ' ' '\n' | sed -n 's/^FINANCE_DB=//p' | head -1); [ -n "$DB" ] || DB="$FIN/finance.db"
[ -f "$DB" ] || stop "the finance database was not found ($DB)"
WN=$(mktemp -d /tmp/s652new.XXXX); WO=$(mktemp -d /tmp/s652old.XXXX)
\cp "$KDIR/aaj_seed.py" "$WN/"; \cp "$KDIR/aaj_duties.json.kit" "$WN/aaj_duties.json"; \cp "$FIN/aaj_seed.py" "$FIN/aaj_duties.json" "$WO/"
"$PY" -B -m py_compile "$WN/aaj_seed.py" || stop "aaj_seed.py does not compile with $PY"
"$PY" -c "import json,sys; json.load(open(sys.argv[1]))" "$WN/aaj_duties.json" || stop "aaj_duties.json is not valid JSON"
R=$("$PY" -B walk_s652.py "$WN" "$FIN" --db "$DB" --map "$MAPF" --base "$WO" 2>&1 | tail -1)
[ "$R" = "3 of 3 green" ] || { "$PY" -B walk_s652.py "$WN" "$FIN" --db "$DB" --map "$MAPF" --base "$WO" 2>&1 | grep -E 'RED|Error'; stop "the walk is not green ($R)"; }
echo "3. walk on the live books: $R"
R=$("$PY" -B walk_s652.py "$WO" "$FIN" --db "$DB" --map "$MAPF" --base "$WO" --old 2>&1 | tail -1)
[ "$R" = "1 S652 check(s) red · 0 older red · 2 green" ] || { echo "$R"; stop "the control on the live files is not as expected ($R)"; }
echo "   control on the live files: $R"
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
restore() {
  while IFS='|' read -r LP KF FROM TO; do [ -f "$LP.bak_S652" ] && \cp -p "$LP.bak_S652" "$LP"; done <<< "$ROWS"
  "$SYSTEMCTL" restart "$SVC"; h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  bad=0; while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$FROM" ] || { echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S652 back by hand"; bad=1; }; done <<< "$ROWS"
  [ "$bad" = 0 ] && echo "   both old files are back byte-identically"
  echo "   after the restore: finance $h2. Send a photo of this screen to Claude."; exit 1
}
while IFS='|' read -r LP KF FROM TO; do \cp -p "$LP" "$LP.bak_S652" || stop "could not keep a backup of $LP"; done <<< "$ROWS"
while IFS='|' read -r LP KF FROM TO; do \cp "$KDIR/$KF" "$LP" && chmod --reference="$LP.bak_S652" "$LP" 2>/dev/null; done <<< "$ROWS"
ok=1; while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$TO" ] || ok=0; done <<< "$ROWS"
[ "$ok" = 1 ] || { echo "!! read-back did not match"; restore; }
echo "4. placed both files (backups *.bak_S652), read back by md5"
"$SYSTEMCTL" restart "$SVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
R=$("$PY" -B walk_s652.py "$FIN" "$FIN" --db "$DB" --map "$MAPF" --base "$WO" 2>&1 | tail -1)
if [ "$h" != 200 ] || [ "$R" != "3 of 3 green" ]; then echo "!! RED after placing (finance $h; walk on the placed files: $R)"; restore; fi
echo "5. $SVC restarted and healthy; the walk on the placed files: $R"
echo ""
echo "INSTALLED. Shavez's list now carries 'Kal ke procedures' whenever days wait on his morning page."
