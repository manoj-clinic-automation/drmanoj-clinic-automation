#!/bin/bash
# rehearse_s897.sh -- kit S897: the installer walked on a MADE-UP box (no live file, no patient). Every command the installer
# runs against the box is overridden: systemctl, crontab, the health probe, the seed and the replay. Scenes:
#   A dry run . B install green (no seed in Drive) . C install again refused . D undo . E undo again (nothing to undo)
#   F red at [4/7] -> everything restored . G tampered kit refused . H install with a seed in 'Drive' -> PLACED + Replay 2
#   I a seeded folder survives an undo . J wrong FROM pin refused . K the switch flag present -> refused
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d /tmp/s897reh.XXXXXX)"; chmod 700 "$T"
FAILS=0; N=0
ok() { N=$((N+1)); echo "PASS $1"; }
bad() { N=$((N+1)); FAILS=$((FAILS+1)); echo "FAIL $1 -- $2"; }
expect() { local name="$1" want="$2" got="$3"; if echo "$got" | grep -qF -- "$want"; then ok "$name"; else bad "$name" "wanted '$want' in: $(echo "$got" | tail -3 | tr '\n' '|')"; fi; }
mkbox() {
  rm -rf "$T/box"; mkdir -p "$T/box/root/finance" "$T/box/root/followup_tracker/logs" "$T/box/root/wa/followup-inbox" "$T/box/root/deploy" "$T/box/bin"
  cp "$KDIR/../live/owner_console.py" "$T/box/root/finance/owner_console.py" 2>/dev/null || cp "${LIVE_DIR:?set LIVE_DIR}/owner_console.py" "$T/box/root/finance/"
  for f in freshness_legs.json docterz_pickup.py freshness.py; do cp "${LIVE_DIR:-$KDIR/../live}/$f" "$T/box/root/finance/$f"; done
  echo "# stub" > "$T/box/root/finance/docterz_ingest.py"
  echo "# engine" > "$T/box/root/followup_tracker/processor.py"; echo "# runner" > "$T/box/root/followup_tracker/server_runner.py"
  : > "$T/box/root/followup_tracker/OFF"
  for i in $(seq 1 22); do echo "$i * * * * echo line$i"; done > "$T/box/cron.txt"
  cat > "$T/box/bin/crontab" <<'EOS'
#!/bin/bash
F="$CRON_FILE"; if [ "${1:-}" = "-l" ]; then cat "$F"; else cat "$1" > "$F"; fi
EOS
  cat > "$T/box/bin/systemctl" <<'EOS'
#!/bin/bash
echo "$@" >> "$SYSTEMCTL_LOG"; exit 0
EOS
  cat > "$T/box/bin/health" <<'EOS'
#!/bin/bash
case "$1" in /finance/healthz) echo 200;; /finance/console/docterz-reports*) [ -f "$HEALTH_DOOR" ] && echo 302 || echo 404;; *) echo 302;; esac
EOS
  cat > "$T/box/bin/seed_none" <<'EOS'
#!/bin/bash
echo "no TRACKER_SEED_*.zip in the Drive folder (3 file(s) seen) -- has the PC's outputs folder synced?"; exit 1
EOS
  cat > "$T/box/bin/seed_yes" <<'EOS'
#!/bin/bash
mkdir -p "$FUT/data"; echo "A,B" > "$FUT/data/visit_ledger.csv"; echo "2026-11-20 18:00:00 seed 20261120-175900 (since 2026-10-19): ledgers 12, snapshots 33, uploads 90, archive files 160" > "$FUT/SEEDED_AT"
echo "seed: TRACKER_SEED_20261120-175900.zip (Drive)"; echo "sha256 agrees; manifest 300 files, all agree"; echo "PLACED: ledgers 12, snapshots 33, uploads 90, archive files 160; runner still OFF"; exit 0
EOS
  cat > "$T/box/bin/replay_ok" <<'EOS'
#!/bin/bash
echo "REPLAY 2 (S897.1, on the box) -- now -- 33 run(s) logged since 2026-10-19"; echo "#1 x SKIP (an earlier run of the day)"; echo "#2 y PASS (code current)"; echo "RESULT: 22 pass, 0 fail, 11 skipped of 33"; exit 0
EOS
  chmod +x "$T/box/bin/"*
  : > "$T/box/systemctl.log"
}
ENVS() { echo "ROOT=$T/box/root FIN=$T/box/root/finance FUT=$T/box/root/followup_tracker WA=$T/box/root/wa LOCK=$T/box/root/deploy/.lock APY=$(command -v python3) VPY=$(command -v python3) SYSTEMCTL=$T/box/bin/systemctl CRONTAB=$T/box/bin/crontab HEALTH_CMD=$T/box/bin/health NAP=0 TMPW=$T CRON_FILE=$T/box/cron.txt SYSTEMCTL_LOG=$T/box/systemctl.log HEALTH_DOOR=$T/box/root/finance/docterz_door.py"; }
run() { env $(ENVS) "$@" bash "$KDIR/install_S897_TRACKER_SEED_REPLAY.sh" 2>&1; }
undo() { env $(ENVS) bash "$KDIR/install_S897_TRACKER_SEED_REPLAY.sh" --undo 2>&1; }
OC_FROM="$(md5sum "${LIVE_DIR:-$KDIR/../live}/owner_console.py" | cut -c1-8)"

mkbox
out="$(run DRY=1)"; expect "A dry run green, nothing changed" "DRY RUN: every gate and proof green" "$out"
[ ! -f "$T/box/root/finance/docterz_door.py" ] && ok "A dry run placed nothing" || bad "A dry run placed nothing" "door present"

out="$(run SEED_CMD="$T/box/bin/seed_none")"; expect "B install green, seed NOT YET" "DONE (the runner stays OFF; nothing switched). Seed: NOT YET" "$out"
expect "B the door placed and the console line" "placed and read back at their TO pins: docterz_door.py" "$out"
expect "B the watcher's cron line and first check" "first check: ok  not switched yet" "$out"
grep -q "S897_PC_UPLOAD_WATCH" "$T/box/cron.txt" && ok "B cron line in the crontab" || bad "B cron line in the crontab" "absent"
[ "$(grep -c . "$T/box/cron.txt")" = 23 ] && ok "B the other 22 cron lines kept" || bad "B cron lines" "$(grep -c . "$T/box/cron.txt")"
grep -q "restart clinic-finance" "$T/box/systemctl.log" && ok "B finance restarted" || bad "B finance restarted" "no restart"
[ -f "$T/box/root/finance/owner_console.py.bak_S897_$OC_FROM" ] && ok "B backup beside owner_console.py" || bad "B backup" "none"
[ "$(md5sum "$T/box/root/finance/owner_console.py" | cut -c1-32)" = "$(awk '$2=="finance/owner_console.py"{print $1}' "$KDIR/TO_PINS.md5")" ] && ok "B owner_console.py at its TO pin" || bad "B owner_console.py pin" "x"
[ -f "$T/box/root/followup_tracker/pc_upload_watch.state.json" ] && ok "B the watcher's state written" || bad "B watcher state" "none"
[ -e "$T/box/root/followup_tracker/OFF" ] && ok "B the runner still OFF" || bad "B OFF" "gone"

out="$(run)"; expect "C install again: already installed, nothing done" "is already installed" "$out"

out="$(undo)"; expect "D undo" "UNDONE (two files back, the door set aside" "$out"
[ "$(md5sum "$T/box/root/finance/owner_console.py" | cut -c1-8)" = "$OC_FROM" ] && ok "D owner_console.py back at FROM" || bad "D owner_console" "x"
! grep -q "S897_PC_UPLOAD_WATCH" "$T/box/cron.txt" && ok "D cron line out" || bad "D cron line out" "still there"
[ ! -f "$T/box/root/followup_tracker/pc_upload_watch.py" ] && ok "D the FUT files out" || bad "D FUT files" "still there"
out="$(undo)"; expect "E undo again: nothing to undo" "not installed; nothing to undo" "$out"

mkbox
out="$(run REHEARSE_RED_AT=4 SEED_CMD="$T/box/bin/seed_none")"; expect "F red at [4/7] -> restored" "restored: owner_console.py $OC_FROM" "$out"
[ "$(md5sum "$T/box/root/finance/owner_console.py" | cut -c1-8)" = "$OC_FROM" ] && [ ! -f "$T/box/root/finance/docterz_door.py" ] && ok "F files back, door set aside" || bad "F restore" "x"
! grep -q "S897_PC_UPLOAD_WATCH" "$T/box/cron.txt" && ok "F no cron line after the red" || bad "F cron" "line left"

mkbox; cp -r "$KDIR" "$T/kit_t"; echo "# tampered" >> "$T/kit_t/docterz_door.py"
out="$(env $(ENVS) bash "$T/kit_t/install_S897_TRACKER_SEED_REPLAY.sh" 2>&1)"; expect "G tampered kit refused by SUMS" "SUMS.md5 gate failed" "$out"; rm -rf "$T/kit_t"

mkbox
out="$(run SEED_CMD="$T/box/bin/seed_yes" REPLAY_CMD="$T/box/bin/replay_ok")"
expect "H install with a seed: PLACED" "Seed: PLACED" "$out"; expect "H Replay 2 counted" "REPLAY 2 on the box: RESULT: 22 pass, 0 fail, 11 skipped of 33" "$out"
out="$(undo)"; expect "I undo keeps the seed" "the seed in $T/box/root/followup_tracker stays" "$out"
[ -f "$T/box/root/followup_tracker/data/visit_ledger.csv" ] && ok "I the seeded ledger survives the undo" || bad "I seed" "gone"
out="$(run SEED_CMD="$T/box/bin/seed_yes" REPLAY_CMD="$T/box/bin/replay_ok")"; expect "I install again after the undo: already seeded, kept" "already seeded:" "$out"

mkbox; echo "# moved" >> "$T/box/root/finance/owner_console.py"
out="$(run)"; expect "J a moved live file refused at [2/7]" "not $OC_FROM (the 20-Nov bundle) - STOP" "$out"
mkbox; echo "2026-11-25 20:30:00" > "$T/box/root/followup_tracker/SWITCHED_AT"
out="$(run)"; expect "K SWITCHED_AT present -> refused" "this kit is for BEFORE the switch" "$out"
mkbox; rm -f "$T/box/root/followup_tracker/OFF"
out="$(run)"; expect "K2 OFF absent -> refused" "the runner is not off" "$out"

rm -rf "$T"
echo "rehearse_s897: $N scenes, $FAILS failure(s)"
exit $((FAILS > 0))
