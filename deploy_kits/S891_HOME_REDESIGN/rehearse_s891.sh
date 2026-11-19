#!/bin/bash
# rehearse_s891.sh -- the installer rehearsed on a made-up root (a copy of the live portal folder from the bundle), fake systemctl /
# health. Nothing live. Usage: bash rehearse_s891.sh <kit folder> <live root holding portal/> <python with flask>
set -u
K="$(cd "$1" && pwd)"; L="$(cd "$2" && pwd)"; PY="${3:-python3}"
W="$(mktemp -d "${TMPDIR:-/tmp}/s891reh_XXXX")"; trap 'rm -rf "$W"' EXIT
R="$W/root"; mkdir -p "$R/deploy/_off" "$W/bin"
cp -rp "$L/portal" "$R/portal"; rm -f "$R/portal"/*.bak* 2>/dev/null
cat > "$W/bin/systemctl" <<'EOT'
#!/bin/bash
echo "$*" >> "$FAKE_LOG"; exit 0
EOT
cat > "$W/bin/health" <<'EOT'
#!/bin/bash
[ -n "${FAKE_DOWN:-}" ] && { echo 000; exit 0; }
case "$2" in /portal/health) echo 200;; /portal) echo "${FAKE_PORTAL:-302}";; *) echo 404;; esac
EOT
chmod +x "$W/bin"/*
export FAKE_LOG="$W/fake.log"
run() { ROOT="$R" VPY="$PY" SYSTEMCTL="$W/bin/systemctl" HEALTH_CMD="$W/bin/health" LOCK="$R/deploy/.lock" OFFSW="$R/deploy/_off/DOCTOR_AUTO_OFF" NAP=0 TMPW="$W" bash "$K/install_S891_HOME_REDESIGN.sh" "$@"; }
m8() { md5sum "$1" | cut -c1-8; }
TO8="$(awk '$2=="portal.py"{print substr($1,1,8)}' "$K/TO_PINS.md5")"
n=0; ok=0
chk() { n=$((n+1)); if eval "$2"; then ok=$((ok+1)); echo "GREEN R$n $1"; else echo "RED   R$n $1"; fi; }
echo "== A: DRY run"; OUT=$(DRY=1 run 2>&1); echo "$OUT" | tail -2
chk "DRY: every gate and the walk green, nothing placed" '[ "${OUT##*DRY RUN: every gate}" != "$OUT" ] && [ "$(m8 "$R/portal/portal.py")" = 9da49bd1 ]'
echo "== B: install"; OUT=$(run 2>&1); echo "$OUT" | tail -3
chk "install DONE: portal.py at TO, backup at FROM, the portal restarted, lock and doctor switch released" \
  '[ "${OUT##*: DONE.}" != "$OUT" ] && [ "$(m8 "$R/portal/portal.py")" = "$TO8" ] && [ "$(m8 "$R/portal/portal.py.bak_S891_9da49bd1")" = 9da49bd1 ] && grep -q "restart clinic-portal" "$FAKE_LOG" && [ ! -d "$R/deploy/.lock" ] && [ ! -e "$R/deploy/_off/DOCTOR_AUTO_OFF" ]'
echo "== C: again"; OUT=$(run 2>&1); echo "$OUT" | tail -1
chk "a second run says ALREADY INSTALLED" '[ "${OUT##*ALREADY INSTALLED*}" != "$OUT" ]'
echo "== D: undo"; OUT=$(run --undo 2>&1); echo "$OUT" | tail -1
chk "undo: portal.py back at FROM, the portal restarted" '[ "${OUT##*: UNDONE*}" != "$OUT" ] && [ "$(m8 "$R/portal/portal.py")" = 9da49bd1 ]'
echo "== E: undo again"; OUT=$(run --undo 2>&1); echo "$OUT" | tail -1
chk "a second undo says not installed" '[ "${OUT##*not installed*}" != "$OUT" ]'
echo "== F: red rollback at [4/5]"; OUT=$(REHEARSE_RED_AT=4 run 2>&1); echo "$OUT" | tail -2
chk "a red after placing puts portal.py back (FROM) and releases the lock" '[ "${OUT##*RED after placing*}" != "$OUT" ] && [ "$(m8 "$R/portal/portal.py")" = 9da49bd1 ] && [ ! -d "$R/deploy/.lock" ]'
echo "== G: /portal answering 500 after the restart"; OUT=$(FAKE_PORTAL=500 run 2>&1); echo "$OUT" | tail -2
chk "a broken home rolls the install back" '[ "${OUT##*/portal answered 500*}" != "$OUT" ] && [ "$(m8 "$R/portal/portal.py")" = 9da49bd1 ]'
echo "== H: a drifted live file"; echo "# drift" >> "$R/portal/portal.py"; OUT=$(run 2>&1); echo "$OUT" | tail -1
chk "a live file that moved after the build stops the install at [2/5]" '[ "${OUT##*changed after this kit was built*}" != "$OUT" ] && [ ! -f "$R/portal/.portal.py.s891" ]'
cp -p "$R/portal/portal.py.bak_S891_9da49bd1" "$R/portal/portal.py"
echo "== I: a tampered kit"; cp -rp "$K" "$W/kit2"; echo "#x" >> "$W/kit2/portal.py"; OUT=$(ROOT="$R" VPY="$PY" SYSTEMCTL="$W/bin/systemctl" HEALTH_CMD="$W/bin/health" LOCK="$R/deploy/.lock" OFFSW="$R/deploy/_off/x" NAP=0 TMPW="$W" bash "$W/kit2/install_S891_HOME_REDESIGN.sh" 2>&1); echo "$OUT" | tail -1
chk "a tampered kit fails the SUMS gate" '[ "${OUT##*SUMS.md5 gate failed*}" != "$OUT" ]'
echo "== J: the lock held"; mkdir -p "$R/deploy/.lock"; OUT=$(run 2>&1); echo "$OUT" | tail -1; rmdir "$R/deploy/.lock"
chk "another build's lock refuses the install" '[ "${OUT##*another build holds the lock*}" != "$OUT" ]'
echo "== K: health down before"; OUT=$(FAKE_DOWN=1 run 2>&1); echo "$OUT" | tail -1
chk "a portal already down refuses the install, nothing placed" '[ "${OUT##*health before the install*}" != "$OUT" ] && [ "$(m8 "$R/portal/portal.py")" = 9da49bd1 ]'
echo "REHEARSAL S891: $ok/$n green"
[ "$ok" = "$n" ]
