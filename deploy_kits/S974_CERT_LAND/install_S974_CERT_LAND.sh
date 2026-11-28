#!/bin/bash
# =============================================================================
#  install_S974_CERT_LAND.sh . kit S974 (28-Nov-2026, session S541, the parent) . F-1731
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s974kit && \cp -rp /root/deploy/repo/deploy_kits/S974_CERT_LAND /tmp/s974kit && bash /tmp/s974kit/install_S974_CERT_LAND.sh
#  DRY=1 before bash: everything up to the LOOK; nothing placed.   NOW=1: a pending install runs now, not at 05:55 IST.
#  Undo:  bash /tmp/s974kit/install_S974_CERT_LAND.sh --undo
#
#  Places NEW /root/wa/cert_land.py (nightly 00:25 UTC = 05:55 IST, cron # S974_CERT_LAND) and one health leg
#  ("certificate lands") in /root/finance/freshness_legs.json (46 -> 47). Read-first: the walk on a made-up root with
#  a control that goes red, then the LOOK on the live sites (names, verdicts, days -- no key or certificate text).
# =============================================================================
set -u
KIT="S974_CERT_LAND"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
DST="${DST:-/root/wa/cert_land.py}"
LEGS="${LEGS:-/root/finance/freshness_legs.json}"
FRESH="${FRESH:-/root/finance/freshness.py}"
CRONBAK="${CRONBAK:-/root/crontab.bak_S974}"
LEGS_FROM="c5b667b4ee8cfbc9c055160870d4be59"
LEGS_TO="fd6b543a29b668460b7ea47d4def7b98"
CRONTAG="# S974_CERT_LAND"
CLLOCK="${CLLOCK:-/root/wa/cert_land.lock}"
CRONLINE="25 0 * * * /usr/bin/flock -n $CLLOCK $PY -B $DST >> /root/wa/cert_land.log 2>&1 $CRONTAG"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; HAVE_LOCK=0
release() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
md5() { md5sum "$1" 2>/dev/null | cut -d' ' -f1; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
TO="$(md5 "$KDIR/cert_land.py")"

if [ "${1:-}" = "--undo" ]; then
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK)"; HAVE_LOCK=1
  LU="$(md5 "$LEGS")"
  [ "$LU" = "$LEGS_TO" ] || [ "$LU" = "$LEGS_FROM" ] || stop "$LEGS has changed since this kit (md5 $LU) -- not putting the old one back"
  crontab -l > "$CRONBAK.undo" 2>/dev/null && [ -s "$CRONBAK.undo" ] || stop "could not read the crontab -- nothing was changed"
  [ -z "$(tail -c1 "$CRONBAK.undo")" ] || echo >> "$CRONBAK.undo"
  N0=$(wc -l < "$CRONBAK.undo"); NT=$(grep -c -F "$CRONTAG" "$CRONBAK.undo")
  grep -v -F "$CRONTAG" "$CRONBAK.undo" | crontab - || stop "could not write the crontab" "Its copy is $CRONBAK.undo."
  [ "$(crontab -l | wc -l)" = "$((N0 - NT))" ] || { crontab "$CRONBAK.undo"; stop "the crontab came back the wrong length -- put back from $CRONBAK.undo"; }
  [ "$LU" = "$LEGS_TO" ] && [ -f "$LEGS.bak_S974_$LEGS_FROM" ] && \cp -p "$LEGS.bak_S974_$LEGS_FROM" "$LEGS"
  [ -f "$DST" ] && mv "$DST" "$DST.removed_S974"
  echo "UNDONE: legs $(md5 "$LEGS") . cert_land.py set aside . cron line removed ($(crontab -l | grep -c -F "$CRONTAG") left)."
  echo "        Any certificate it installed stays (each site's .bak_S974_<date> pair is beside its files)."
  exit 0
fi

echo "[1/6] kit files: all match SUMS.md5"
command -v openssl >/dev/null || stop "openssl is not on this server"
[ -x "$PY" ] || stop "no python at $PY"
L="$(md5 "$LEGS")"
[ "$L" = "$LEGS_FROM" ] || [ "$L" = "$LEGS_TO" ] || stop "$LEGS is not the file this kit was built on (md5 $L)"
if [ -f "$DST" ] && [ "$(md5 "$DST")" != "$TO" ]; then stop "$DST already exists and is not this kit's"; fi
echo "[2/6] the box: legs $( [ "$L" = "$LEGS_TO" ] && echo "already this kit's" || echo "the expected FROM" ) . cert_land.py $( [ -f "$DST" ] && echo "already this kit's" || echo "new" ) . openssl $(openssl version | cut -d' ' -f2)"

rm -rf "$KDIR/_fresh" && mkdir -p "$KDIR/_fresh" && \cp -p "$FRESH" "$KDIR/_fresh/freshness.py" || stop "could not copy the health page's collector for the walk"
OUT="$("$PY" -B "$KDIR/walk_s974.py" "$KDIR/cert_land.py" 2>&1)"; RC=$?
echo "$OUT" | tail -1 | sed 's/^/      /'
[ "$RC" = 0 ] || { echo "$OUT" | grep FAIL | head -8; stop "the walk on a made-up root failed"; }
sed 's/^        if got and got\["fp"\] == fp:$/        if got:/' "$KDIR/cert_land.py" > "$KDIR/_fresh/mutant.py"
cmp -s "$KDIR/cert_land.py" "$KDIR/_fresh/mutant.py" && stop "the control copy could not be made (the read-back line was not found)"
"$PY" -B "$KDIR/walk_s974.py" "$KDIR/_fresh/mutant.py" > "$KDIR/_fresh/mutant.out" 2>&1 && stop "the control did NOT go red (a copy that does not compare what the site serves passed the walk)"
grep -q "^  FAIL noserve" "$KDIR/_fresh/mutant.out" || stop "the control went red for the wrong reason (no named read-back check failed)"
echo "[3/6] walk: green on the kit . control red (named checks) on a copy that does not compare what the site serves"

LOOK="$(CERT_LAND_STATE=/dev/null "$PY" -B "$KDIR/cert_land.py" --dry 2>&1)" || stop "the LOOK could not run: $(echo "$LOOK" | tail -1)"
echo "[4/6] the LOOK on the live sites (nothing changed; a fault is shown red on the health page from the first run):"
echo "$LOOK" | tail -n +2 | sed 's/^/    /'
NW="$(echo "$LOOK" | sed -n 's/.*would install: \([0-9]*\).*/\1/p')"
[ -n "$NW" ] || stop "the LOOK printed no count"
"$PY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import freshness as f; n = len(f.load_legs(sys.argv[2], {})); sys.exit(0 if n == 47 else 3)" "$KDIR/_fresh" "$KDIR/freshness_legs.json" >/dev/null 2>&1 || stop "the health page's own collector refuses the kit's legs file"
echo "      the health page's collector reads the kit's 47 legs"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: stopped after the LOOK; nothing placed."; exit 0; }

mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"; HAVE_LOCK=1
crontab -l > "$CRONBAK" 2>/dev/null && [ -s "$CRONBAK" ] || stop "could not read the crontab"
[ -z "$(tail -c1 "$CRONBAK")" ] || echo >> "$CRONBAK"           # a last job with no newline is never joined to ours
[ "$L" = "$LEGS_FROM" ] && { \cp -p "$LEGS" "$LEGS.bak_S974_$LEGS_FROM" || stop "could not back up $LEGS"; }
\cp "$KDIR/cert_land.py" "$DST.tmp_S974" && chmod 700 "$DST.tmp_S974" && mv "$DST.tmp_S974" "$DST" || stop "could not place $DST"
[ "$L" = "$LEGS_FROM" ] && { \cp "$KDIR/freshness_legs.json" "$LEGS.tmp_S974" && chmod --reference="$LEGS" "$LEGS.tmp_S974" && mv "$LEGS.tmp_S974" "$LEGS" || { \cp -p "$LEGS.bak_S974_$LEGS_FROM" "$LEGS"; stop "could not place the legs file" "The legs file was put back."; }; }
if ! grep -q -F "$CRONTAG" "$CRONBAK"; then
  N0=$(wc -l < "$CRONBAK")
  ( cat "$CRONBAK"; echo "$CRONLINE" ) | crontab - || stop "could not add the cron line" "cert_land.py and the leg are placed; the crontab copy is $CRONBAK."
  [ "$(crontab -l | wc -l)" = "$((N0 + 1))" ] || { crontab "$CRONBAK" && W="put back from $CRONBAK" || W="NOT put back -- run: crontab $CRONBAK"; stop "the crontab came back the wrong length -- $W" "cert_land.py and the leg are placed (unscheduled)."; }
fi
[ "$(md5 "$DST")" = "$TO" ] && [ "$(md5 "$LEGS")" = "$LEGS_TO" ] && [ "$(crontab -l | grep -c -F "$CRONTAG")" = 1 ] || stop "the read-back of the placed files does not match" "Files may be placed: run the line with --undo, then send a photo."
echo "[5/6] placed: $DST $TO . $LEGS $LEGS_TO (47 legs; backup .bak_S974_$LEGS_FROM) . cron 00:25 UTC = 05:55 IST"

if [ "$NW" = 0 ] || [ "${NOW:-0}" = 1 ]; then
  R="$(/usr/bin/flock -n "$CLLOCK" "$PY" -B "$DST" 2>&1)"; RC=$?
  echo "[6/6] first run: $(echo "$R" | head -1 | cut -d' ' -f2-)"
  echo "$R" | tail -n +2 | sed 's/^/      /'
  [ "$RC" = 0 ] || echo "      !! a site's renewal could not land or a pair is faulty -- the health page shows it red; Claude reads it next session."
else
  echo "[6/6] $NW site(s) will get their renewed certificate at 05:55 IST (NOW=1 does it now); the health leg turns green after that run."
fi
rm -rf "$KDIR/_fresh"
echo ""; echo "$KIT: INSTALLED."
