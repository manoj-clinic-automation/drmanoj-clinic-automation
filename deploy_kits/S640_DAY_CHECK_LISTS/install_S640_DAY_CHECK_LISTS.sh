#!/bin/bash
# =============================================================================
#  install_S640_DAY_CHECK_LISTS.sh · kit S640 (24-Oct-2026, session S347) · D776 stage 3
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s640kit && cp -rp /root/deploy/repo/deploy_kits/S640_DAY_CHECK_LISTS /tmp/s640kit && bash /tmp/s640kit/install_S640_DAY_CHECK_LISTS.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  /root/finance/day_check.py     f223cbf6 -> 332bc8d4  4 counted edits: the staff's door, 'not fixed', 'Re-export <day> from Docterz'
#  /root/finance/aaj_seed.py      a97cd07b -> ab6e4b14  2 counted edits: two new lines (reception, Shavez) -- they arrive OFF on his panel
#  /root/finance/aaj_kaam.html    b58d8f76 -> 9f8fb9df  1 counted edit: a door's line may carry its own words (the patients' names)
#  /root/finance/aaj_duties.json  fa5cfac5 -> 1c49af35  1 counted edit: the two lines read the day check's own door
#  No data step. ONE restart of clinic-finance. Red after placing: all four back byte-identically, restart, healthz.
#  Undo:  for f in day_check.py aaj_seed.py aaj_kaam.html aaj_duties.json; do \cp -p /root/finance/$f.bak_S640 /root/finance/$f; done; systemctl restart clinic-finance
# =============================================================================
set -u
KIT="S640_DAY_CHECK_LISTS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="day_check.py aaj_seed.py aaj_kaam.html aaj_duties.json"
declare -A FROM=( [day_check.py]=f223cbf68450fe2043068d6698d68a3a [aaj_seed.py]=a97cd07bfc7270184c62c16dff4dff48 [aaj_kaam.html]=b58d8f76880b08ff94edeb2f76e01e55 [aaj_duties.json]=fa5cfac53ee1cd3dc1721a00a9cc3dde )
declare -A TO=( [day_check.py]=332bc8d42d51cc3b829de29e71b510ef [aaj_seed.py]=ab6e4b14f83e665400efe91e2f3050e1 [aaj_kaam.html]=9f8fb9df13e66773f6645dda321dedcb [aaj_duties.json]=1c49af3585c63beeeceef8803f112fca )
declare -A SRC=( [day_check.py]=day_check.py [aaj_seed.py]=aaj_seed.py [aaj_kaam.html]=aaj_kaam.html [aaj_duties.json]=aaj_duties.json.kit )
HAVE_LOCK=0; STAGE=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$STAGE" ] && rm -rf "$STAGE"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }
restore() { for n in $NAMES; do \cp -p "$FIN/$n.bak_S640" "$FIN/$n"; done; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
all_to=1
for n in $NAMES; do
  [ "$(m5 "$KDIR/${SRC[$n]}")" = "${TO[$n]}" ] || stop "the kit's ${SRC[$n]} is not the built file"
  L=$(m5 "$FIN/$n"); [ "$L" = "${TO[$n]}" ] || all_to=0
done
[ "$all_to" = 1 ] && { echo "ALREADY INSTALLED."; exit 0; }
for n in $NAMES; do L=$(m5 "$FIN/$n"); [ "$L" = "${FROM[$n]}" ] || stop "the live $n changed since this kit was built (live ${L:0:8}, kit expects ${FROM[$n]:0:8})"; done
echo "2. the four live files are the ones this kit was built from"
STAGE=$(mktemp -d /tmp/s640new.XXXX); for n in $NAMES; do \cp "$KDIR/${SRC[$n]}" "$STAGE/$n"; done
for f in day_check.py aaj_seed.py; do "$PY" -B -m py_compile "$STAGE/$f" || stop "$f does not compile with $PY"; done
"$PY" -c "import json,sys; json.load(open(sys.argv[1]))" "$STAGE/aaj_duties.json" || stop "aaj_duties.json is not valid JSON"
R=$("$PY" -B walk_s640.py "$STAGE" "$FIN" 2>&1 | tail -1); case "$R" in "17 of 17 green") echo "3. walk: $R";; *) "$PY" -B walk_s640.py "$STAGE" "$FIN" 2>&1 | grep RED; stop "the walk is not green ($R)";; esac
R=$("$PY" -B walk_s640.py "$FIN" "$FIN" --old 2>&1 | tail -1); case "$R" in "15 S640 check(s) red · 0 older red · 2 green") echo "   control on the live files: $R";; *) echo "$R"; stop "the control on the live files did not go red as expected";; esac
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
for n in $NAMES; do \cp -p "$FIN/$n" "$FIN/$n.bak_S640" || stop "could not keep a backup of $n"; done
for n in $NAMES; do \cp "$STAGE/$n" "$FIN/$n" && chmod --reference="$FIN/$n.bak_S640" "$FIN/$n" 2>/dev/null; done
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || { restore; stop "read-back of $n did not match; the old files are back"; }; done
echo "4. placed the four files (backups *.bak_S640)"
"$SYSTEMCTL" restart "$SVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
if [ "$h" != 200 ]; then
  echo "!! RED after placing (healthz $h) - putting the old files back"
  restore; "$SYSTEMCTL" restart "$SVC"
  h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  echo "   after the restore: healthz $h2. Send a photo of this screen to Claude."; exit 1
fi
echo "5. $SVC restarted; healthz 200"
echo ""
echo "INSTALLED. Two new lines wait on your Aaj ka kaam panel, switched off: 'Din ki galtiyan' for Reception and for Shavez."
