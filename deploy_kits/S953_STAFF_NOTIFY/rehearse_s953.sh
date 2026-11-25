#!/bin/bash
# rehearse_s953.sh -- S953_STAFF_NOTIFY: the installer on a MADE-UP root (stub systemctl / health / journal / the clock's live --dry), every path.
#   bash rehearse_s953.sh <kit dir> <dir holding the FROM calls_staff.py, callback_clock.py, calls_console.py, ring_outcome.py, ring_common.py> <python with flask>
set -u
KD="$(cd "$1" && pwd)"; FROMD="$(cd "$2" && pwd)"; PY="$3"
W="$(mktemp -d /tmp/s953_reh.XXXXXX)"; PASS=0; FAIL=0
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
ATO="$(awk '$2=="to/calls_staff.py"{print $1}' "$KD/TO_PINS.md5")"; BTO="$(awk '$2=="to/callback_clock.py"{print $1}' "$KD/TO_PINS.md5")"
AFR=1cb4941f3d387abba93f76e650d78fa1; BFR=70eb11972362eee87a9f7d056e04cae5
fresh() { rm -rf "$W/r"; mkdir -p "$W/r/portal" "$W/r/deploy/_off" "$W/bin"
  \cp "$FROMD"/calls_staff.py "$FROMD"/callback_clock.py "$FROMD"/calls_console.py "$FROMD"/ring_outcome.py "$FROMD"/ring_common.py "$W/r/portal/"
  chmod 644 "$W/r/portal/calls_staff.py"; chmod 755 "$W/r/portal/callback_clock.py"
  rm -rf "$W/kit"; \cp -rp "$KD" "$W/kit"
  printf '#!/bin/bash\necho "$@" >> %s/sysctl.log\n' "$W" > "$W/bin/sysctl"
  printf '#!/bin/bash\ncase "$1" in /portal/health) echo 200;; /portal/console/staff*) [ ! -e %s/r/STAFF404 ] && echo 302 || echo 404;; *) echo 302;; esac\n' "$W" > "$W/bin/hget"
  printf '#!/bin/bash\n[ -e %s/r/JOURNAL_BAD ] && echo "calls_staff NOT mounted: boom"; true\n' "$W" > "$W/bin/jr"
  printf '#!/bin/bash\nif [ -e %s/r/DRYBAD ]; then echo "DRY 2026-11-25 10:00: callers not spoken to 3; lists FAILED (ImportError) -- S796 rule; nothing sent"; else echo "DRY 2026-11-25 10:00: callers not spoken to 3 (unknown numbers 1); waiting 30+ duty minutes 2, 60+ 1; call again due 1; WhatsApp waiting 2; lists ok; judged as of 09:55; nothing sent, nothing written"; fi\n' "$W" > "$W/bin/cdry"
  printf '#!/bin/bash\nif [ -e %s/r/CRONBAD ]; then echo "*/5 8-21 * * * /opt/other/bin/python3 -B %s/r/portal/callback_clock.py"; else echo "*/5 8-21 * * * CC_CONSOLE_DB=x %s -B %s/r/portal/callback_clock.py >> log 2>&1"; fi\n' "$W" "$W" "$PY" "$W" > "$W/bin/cron"
  chmod +x "$W/bin/"*; : > "$W/sysctl.log"; }
run() { ROOT="$W/r" PD="$W/r/portal" APY="$PY" LOCK="$W/r/deploy/lock" OFFSW="$W/r/deploy/_off/DOCTOR_AUTO_OFF" SYSTEMCTL="$W/bin/sysctl" \
  HEALTH_CMD="$W/bin/hget" JOURNAL_CMD="$W/bin/jr" CLOCKDRY_CMD="$W/bin/cdry" CRON_CMD="$W/bin/cron" NAP=0 bash "$W/kit/install_S953_STAFF_NOTIFY.sh" "$@" 2>&1; }
chk() { if eval "$2"; then PASS=$((PASS+1)); echo "  ok   $1"; else FAIL=$((FAIL+1)); echo "  FAIL $1"; echo "$OUT" | tail -6 | sed 's/^/        /'; fi; }
isfrom() { [ "$(m5 "$W/r/portal/calls_staff.py")" = $AFR ] && [ "$(m5 "$W/r/portal/callback_clock.py")" = $BFR ]; }
isto() { [ "$(m5 "$W/r/portal/calls_staff.py")" = "$ATO" ] && [ "$(m5 "$W/r/portal/callback_clock.py")" = "$BTO" ]; }
clean() { [ ! -e "$W/r/deploy/lock" ] && [ ! -e "$W/r/deploy/_off/DOCTOR_AUTO_OFF" ] && [ -z "$(ls -A "$W/r/portal" | grep '\.s953$')" ] && [ -z "$(ls /tmp | grep '^s953_inst\.' )" ]; }
fresh; OUT="$(DRY=1 run)"; chk "DRY: runs [1]-[3], nothing changed" 'echo "$OUT" | grep -q "DRY ok" && isfrom && clean && [ ! -s "$W/sysctl.log" ]'
OUT="$(run)"; chk "install: INSTALLED, both TO, restarted" 'echo "$OUT" | grep -q "INSTALLED" && isto && grep -q "restart clinic-portal" "$W/sysctl.log" && clean'
chk "backups 0600 read as FROM, modes kept" '[ "$(m5 "$W/r/portal/calls_staff.py.bak_S953_1cb4941f")" = $AFR ] && [ "$(m5 "$W/r/portal/callback_clock.py.bak_S953_70eb1197")" = $BFR ] && [ "$(stat -c %a "$W/r/portal/calls_staff.py.bak_S953_1cb4941f")" = 600 ] && [ "$(stat -c %a "$W/r/portal/calls_staff.py")" = 644 ] && [ "$(stat -c %a "$W/r/portal/callback_clock.py")" = 755 ]'
OUT="$(run)"; chk "again: ALREADY" 'echo "$OUT" | grep -q "ALREADY" && isto && clean'
OUT="$(run --undo)"; chk "--undo: both back to FROM" 'echo "$OUT" | grep -q "UNDONE" && isfrom && clean'
OUT="$(run --undo)"; chk "--undo twice: not installed" 'echo "$OUT" | grep -q "not installed" && isfrom'
OUT="$(run)"; chk "re-install after undo" 'echo "$OUT" | grep -q "INSTALLED" && isto && clean'
echo x >> "$W/r/portal/calls_staff.py"; OUT="$(run --undo)"; chk "--undo refuses a later kit's file" 'echo "$OUT" | grep -q "not S953" && clean'
fresh; OUT="$(FORCE_RED_AT=4 run)"; chk "forced red at [4/5]: both put back, restarted" 'echo "$OUT" | grep -q "RED" && isfrom && grep -q restart "$W/sysctl.log" && clean'
fresh; OUT="$(FORCE_RED_AT=5 run)"; chk "forced red at [5/5]: both put back" 'echo "$OUT" | grep -q "RED" && isfrom && clean'
fresh; OUT="$(FORCE_KILL_AT=4 run)"; chk "killed mid-[4/5]: both put back" 'echo "$OUT" | grep -q "ended before its proof" && isfrom && clean'
fresh; touch "$W/r/JOURNAL_BAD"; OUT="$(run)"; chk "journal says NOT mounted: put back" 'echo "$OUT" | grep -q "NOT mounted" && isfrom && clean'
fresh; touch "$W/r/STAFF404"; OUT="$(run)"; chk "the staff page answers 404: put back" 'echo "$OUT" | grep -q "answered 404" && isfrom && clean'
fresh; touch "$W/r/DRYBAD"; OUT="$(run)"; chk "the clock's live --dry cannot read the lists: stops at [3/5], nothing changed" 'echo "$OUT" | grep -q "\[3/5\] the new clock" && isfrom && clean && [ ! -s "$W/sysctl.log" ]'
fresh; touch "$W/r/CRONBAD"; OUT="$(run)"; chk "the crontab runs another python: stops at [2/5], nothing changed" 'echo "$OUT" | grep -q "\[2/5\] the crontab line" && isfrom && clean && [ ! -s "$W/sysctl.log" ]'
fresh; mkdir "$W/r/deploy/lock"; OUT="$(run)"; chk "the build lock held: stops, nothing changed" 'echo "$OUT" | grep -q "another build holds" && isfrom && [ ! -e "$W/r/deploy/_off/DOCTOR_AUTO_OFF" ]'
fresh; echo "# drift" >> "$W/r/portal/calls_staff.py"; OUT="$(run)"; chk "a drifted calls_staff.py: stops at [2/5]" 'echo "$OUT" | grep -q "\[2/5\].*changed after" && clean'
fresh; echo "# drift" >> "$W/r/portal/callback_clock.py"; OUT="$(run)"; chk "a drifted callback_clock.py: stops at [2/5]" 'echo "$OUT" | grep -q "\[2/5\].*changed after" && clean'
fresh; \cp "$KD/to/calls_staff.py" "$W/r/portal/calls_staff.py"; OUT="$(run)"; chk "half installed (one file TO): stops at [2/5], nothing changed" 'echo "$OUT" | grep -q "\[2/5\]" && clean && [ ! -s "$W/sysctl.log" ]'
fresh; echo "# x" >> "$W/kit/to/callback_clock.py"; OUT="$(run)"; chk "a corrupt kit: stops at [1/5]" 'echo "$OUT" | grep -q "\[1/5\]" && isfrom'
rm -rf "$W"
echo "REHEARSAL: $PASS/$((PASS+FAIL)) $([ $FAIL = 0 ] && echo PASS || echo FAIL)"
[ $FAIL = 0 ]
