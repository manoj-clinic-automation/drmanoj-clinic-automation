#!/bin/bash
# rehearse_s890.sh -- the installer rehearsed on a made-up root (copies of the live folders from the bundle), fake systemctl / crontab /
# health. Nothing live. Usage: bash rehearse_s890.sh <kit folder> <live root holding assetapp/ portal/ shared/> <python with flask>
set -u
K="$(cd "$1" && pwd)"; L="$(cd "$2" && pwd)"; PY="${3:-python3}"
W="$(mktemp -d "${TMPDIR:-/tmp}/s890reh_XXXX")"; trap 'rm -rf "$W"' EXIT
R="$W/root"; mkdir -p "$R/deploy/_off" "$R/finance" "$W/bin"
cp -rp "$L/assetapp" "$R/assetapp"; cp -rp "$L/portal" "$R/portal"; cp -rp "$L/shared" "$R/shared"
rm -f "$R/assetapp"/*.bak* 2>/dev/null
# a made-up assets.db the app makes itself (the installer's --ensure needs a file): an empty sqlite file is enough for CREATE TABLE
"$PY" -c "import sqlite3,sys; sqlite3.connect(sys.argv[1]).execute('CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)')" "$R/assetapp/assets.db"
# fakes
cat > "$W/bin/systemctl" <<'EOF'
#!/bin/bash
echo "$*" >> "$FAKE_LOG"
case "$1" in show) case "$*" in *clinic-finance*Environment*--value*) [ "${FAKE_TOKEN:-}" = none ] || echo "FINANCE_RENEWALS_TOKEN=made-up-token-for-the-rehearsal OTHER=1";; esac;; esac
exit 0
EOF
cat > "$W/bin/crontab" <<'EOF'
#!/bin/bash
F="$FAKE_CRON"; touch "$F"
if [ "${1:-}" = "-l" ]; then cat "$F"; elif [ "${1:-}" = "-" ]; then cat > "$F"; fi
EOF
cat > "$W/bin/health" <<'EOF'
#!/bin/bash
# $1 port, $2 path -- what a live box would answer
[ -n "${FAKE_DOWN:-}" ] && { echo 000; exit 0; }
case "$2" in /healthz|/portal/health|/portal) echo 200;; /renewals) echo 302;; /renewals/one/api/count) echo 200;; /renewals/one/api/due) echo "${FAKE_DUE:-401}";; *) echo 404;; esac
EOF
chmod +x "$W/bin"/*
export FAKE_LOG="$W/fake.log" FAKE_CRON="$W/cron.txt"
run() { ROOT="$R" APY="$PY" VPY="$PY" SYSTEMCTL="$W/bin/systemctl" CRONTAB="$W/bin/crontab" HEALTH_CMD="$W/bin/health" LOCK="$R/deploy/.lock" OFFSW="$R/deploy/_off/DOCTOR_AUTO_OFF" NAP=0 TMPW="$W" bash "$K/install_S890_RENEWALS_ONE_LIST.sh" "$@"; }
m8() { md5sum "$1" | cut -c1-8; }
n=0; ok=0
chk() { n=$((n+1)); if eval "$2"; then ok=$((ok+1)); echo "GREEN R$n $1"; else echo "RED   R$n $1"; fi; }

echo "== A: DRY run"; OUT=$(DRY=1 run 2>&1); echo "$OUT" | tail -3
chk "DRY: every gate and both walks green, nothing placed" '[ "${OUT##*DRY RUN: every gate}" != "$OUT" ] && [ "$(m8 "$R/assetapp/asset_register.py")" = b668771c ] && [ ! -f "$R/assetapp/renewals_one.py" ]'
echo "== B: install"; OUT=$(run 2>&1); echo "$OUT" | tail -5
chk "install DONE: the three files at TO, token file 0600, cron line, both services restarted, lock released, doctor switch released" \
  '[ "${OUT##*: DONE.}" != "$OUT" ] && [ "$(md5sum "$R/assetapp/asset_register.py" | cut -c1-32)" = "$(awk '"'"'$2=="asset_register.py"{print $1}'"'"' "$K/TO_PINS.md5")" ] && [ -f "$R/assetapp/renewals_one.py" ] && [ "$(stat -c %a "$R/assetapp/renewals_one.token")" = 600 ] && grep -q S890_RENEWALS_STATE "$FAKE_CRON" && grep -q "restart assetapp" "$FAKE_LOG" && grep -q "restart clinic-portal" "$FAKE_LOG" && [ ! -d "$R/deploy/.lock" ] && [ ! -e "$R/deploy/_off/DOCTOR_AUTO_OFF" ]'
cat > "$W/count.py" <<'EOP'
import sqlite3, sys
print(len(sqlite3.connect(sys.argv[1]).execute("select name from sqlite_master where type='table' and name like 'renewal_%'").fetchall()))
EOP
TBL="$("$PY" "$W/count.py" "$R/assetapp/assets.db")"
chk "the three tables exist in the made-up assets.db ($TBL); the backups carry the FROM pins" \
  '[ "$TBL" = 3 ] && [ "$(m8 "$R/assetapp/asset_register.py.bak_S890_b668771c")" = b668771c ] && [ "$(m8 "$R/portal/portal.py.bak_S890_cb37c7fb")" = cb37c7fb ]'
chk "the token never printed by the installer" '! grep -q "made-up-token-for-the-rehearsal" <<< "$OUT"'
echo "== C: again"; OUT=$(run 2>&1); echo "$OUT" | tail -1
chk "a second run says ALREADY INSTALLED" '[ "${OUT##*ALREADY INSTALLED*}" != "$OUT" ]'
echo "== D: undo"; OUT=$(run --undo 2>&1); echo "$OUT" | tail -1
chk "undo: both files back at FROM, token file and cron line gone, renewals_one.py left inert, tables kept" \
  '[ "${OUT##*: UNDONE*}" != "$OUT" ] && [ "$(m8 "$R/assetapp/asset_register.py")" = b668771c ] && [ "$(m8 "$R/portal/portal.py")" = cb37c7fb ] && [ ! -f "$R/assetapp/renewals_one.token" ] && ! grep -q S890 "$FAKE_CRON" && [ -f "$R/assetapp/renewals_one.py" ]'
echo "== E: undo again"; OUT=$(run --undo 2>&1); echo "$OUT" | tail -1
chk "a second undo says not installed" '[ "${OUT##*not installed*}" != "$OUT" ]'
echo "== F: red rollback at [4/6]"; OUT=$(REHEARSE_RED_AT=4 run 2>&1); echo "$OUT" | tail -2
chk "a red after placing puts both files back (FROM), removes the token file and cron, releases the lock" \
  '[ "${OUT##*RED after placing*}" != "$OUT" ] && [ "$(m8 "$R/assetapp/asset_register.py")" = b668771c ] && [ "$(m8 "$R/portal/portal.py")" = cb37c7fb ] && [ ! -f "$R/assetapp/renewals_one.token" ] && ! grep -q S890 "$FAKE_CRON" && [ ! -d "$R/deploy/.lock" ]'
echo "== G: the due door answering 200 without a token is a red (rolled back)"; OUT=$(FAKE_DUE=200 run 2>&1); echo "$OUT" | tail -2
chk "an open due door rolls the install back" '[ "${OUT##*without a token answered 200*}" != "$OUT" ] && [ "$(m8 "$R/assetapp/asset_register.py")" = b668771c ]'
echo "== H: no token in finance's settings"; OUT=$(FAKE_TOKEN=none run 2>&1); echo "$OUT" | grep -E "^\[2/6\]|DONE" | cut -c1-160
chk "without a token the install still completes, says so, writes no token file" '[ "${OUT##*: DONE.}" != "$OUT" ] && [ "${OUT##*NO renewals token*}" != "$OUT" ] && [ ! -f "$R/assetapp/renewals_one.token" ]'
run --undo >/dev/null 2>&1
echo "== I: a drifted live file"; echo "# drift" >> "$R/portal/portal.py"; OUT=$(run 2>&1); echo "$OUT" | tail -1
chk "a live file that moved after the build stops the install at [2/6]" '[ "${OUT##*changed after this kit was built*}" != "$OUT" ] && [ ! -f "$R/assetapp/renewals_one.py.s890" ]'
cp -p "$R/portal/portal.py.bak_S890_cb37c7fb" "$R/portal/portal.py"
echo "== J: a tampered kit"; cp -rp "$K" "$W/kit2"; echo "#x" >> "$W/kit2/renewals_one.py"; OUT=$(ROOT="$R" APY="$PY" VPY="$PY" SYSTEMCTL="$W/bin/systemctl" CRONTAB="$W/bin/crontab" HEALTH_CMD="$W/bin/health" LOCK="$R/deploy/.lock" OFFSW="$R/deploy/_off/x" NAP=0 TMPW="$W" bash "$W/kit2/install_S890_RENEWALS_ONE_LIST.sh" 2>&1); echo "$OUT" | tail -1
chk "a tampered kit fails the SUMS gate" '[ "${OUT##*SUMS.md5 gate failed*}" != "$OUT" ]'
echo "== K: the lock held"; mkdir -p "$R/deploy/.lock"; OUT=$(run 2>&1); echo "$OUT" | tail -1; rmdir "$R/deploy/.lock"
chk "another build's lock refuses the install" '[ "${OUT##*another build holds the lock*}" != "$OUT" ]'
echo "REHEARSAL S890: $ok/$n green"
[ "$ok" = "$n" ]
