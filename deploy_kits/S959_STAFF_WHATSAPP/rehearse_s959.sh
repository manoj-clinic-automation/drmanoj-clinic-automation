#!/bin/bash
# rehearse_s959.sh -- S959_STAFF_WHATSAPP: the installer on a MADE-UP root (stub systemctl / health / journal), every path; the
#   walks run for real (on the made-up stores); the live-settings probe runs for real on a made-up portal_config.py.
#   bash rehearse_s959.sh <kit dir> <dir holding the FROM calls_staff.py, portal_inbox.py, calls_console.py and ring_outcome.py,
#        ring_common.py, callback_clock.py, presence.py, portal_wa.py, tile_grants.json> <python with flask>
set -u
KD="$(cd "$1" && pwd)"; FROMD="$(cd "$2" && pwd)"; PY="$3"
W="$(mktemp -d "${TMPDIR:-/tmp}/s959_reh.XXXXXX")"; PASS=0; FAIL=0
FK="made-up-not-a-key"   # the made-up key the rehearsal writes into its made-up portal_config.py (never real)
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
to_of() { awk -v f="to/$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
T1="$(to_of calls_staff.py)"; T2="$(to_of portal_inbox.py)"; T3="$(to_of calls_console.py)"
R1=a93cdc86b9870e6c6f92738cd95a2b22; R2=6abc6461846a408b47f7f4ceff493c21; R3=f484cbc23e85817c32cd7a6c9004dd3e
fresh() { rm -rf "$W/r"; mkdir -p "$W/r/portal" "$W/r/deploy/_off" "$W/bin"
  for f in calls_staff.py portal_inbox.py calls_console.py ring_outcome.py ring_common.py callback_clock.py presence.py portal_wa.py tile_grants.json; do \cp "$FROMD/$f" "$W/r/portal/"; done
  chmod 644 "$W/r/portal/calls_staff.py" "$W/r/portal/portal_inbox.py" "$W/r/portal/calls_console.py"
  printf 'PORTAL_WA_DRYRUN = "0"\nMYOP_AUTH_%s = "%s"\n' TOKEN "$FK" > "$W/r/portal/portal_config.py"; chmod 600 "$W/r/portal/portal_config.py"
  rm -rf "$W/kit"; \cp -rp "$KD" "$W/kit"
  printf '#!/bin/bash\necho "$@" >> %s/sysctl.log\n' "$W" > "$W/bin/sysctl"
  printf '#!/bin/bash\ncase "$1" in /portal/health) echo 200;; /portal/console/staff/api/wa/*) [ ! -e %s/r/WA404 ] && echo 302 || echo 404;; /portal/inbox*) [ ! -e %s/r/INBOX500 ] && echo 302 || echo 500;; *) echo 302;; esac\n' "$W" "$W" > "$W/bin/hget"
  printf '#!/bin/bash\n[ -e %s/r/JOURNAL_BAD ] && echo "calls_staff NOT mounted: boom"; true\n' "$W" > "$W/bin/jr"
  chmod +x "$W/bin/"*; : > "$W/sysctl.log"; }
run() { ROOT="$W/r" PD="$W/r/portal" APY="$PY" LOCK="$W/r/deploy/lock" OFFSW="$W/r/deploy/_off/DOCTOR_AUTO_OFF" SYSTEMCTL="$W/bin/sysctl" \
  HEALTH_CMD="$W/bin/hget" JOURNAL_CMD="$W/bin/jr" NAP=0 bash "$W/kit/install_S959_STAFF_WHATSAPP.sh" "$@" 2>&1; }
chk() { if eval "$2"; then PASS=$((PASS+1)); echo "  ok   $1"; else FAIL=$((FAIL+1)); echo "  FAIL $1"; echo "$OUT" | tail -6 | sed 's/^/        /'; fi; }
isfrom() { [ "$(m5 "$W/r/portal/calls_staff.py")" = $R1 ] && [ "$(m5 "$W/r/portal/portal_inbox.py")" = $R2 ] && [ "$(m5 "$W/r/portal/calls_console.py")" = $R3 ]; }
isto() { [ "$(m5 "$W/r/portal/calls_staff.py")" = "$T1" ] && [ "$(m5 "$W/r/portal/portal_inbox.py")" = "$T2" ] && [ "$(m5 "$W/r/portal/calls_console.py")" = "$T3" ]; }
clean() { [ ! -e "$W/r/deploy/lock" ] && [ ! -e "$W/r/deploy/_off/DOCTOR_AUTO_OFF" ] && [ -z "$(ls -A "$W/r/portal" | grep '\.s959$')" ] && [ -z "$(ls /tmp | grep '^s959_inst\.' )" ]; }
fresh; OUT="$(DRY=1 run)"; chk "DRY: runs [1]-[3], nothing changed; the live settings said in words, no value" 'echo "$OUT" | grep -q "DRY ok" && echo "$OUT" | grep -q "reply on . templates offered 1 (Enquiry acknowledgement) . templates LIVE . send key named yes" && ! echo "$OUT" | grep -q "$FK" && isfrom && clean && [ ! -s "$W/sysctl.log" ]'
OUT="$(run)"; chk "install: INSTALLED, all three TO, restarted" 'echo "$OUT" | grep -q "INSTALLED" && isto && grep -q "restart clinic-portal" "$W/sysctl.log" && clean'
chk "backups 0600 read as FROM, modes kept" '[ "$(m5 "$W/r/portal/calls_staff.py.bak_S959_a93cdc86")" = $R1 ] && [ "$(m5 "$W/r/portal/portal_inbox.py.bak_S959_6abc6461")" = $R2 ] && [ "$(m5 "$W/r/portal/calls_console.py.bak_S959_f484cbc2")" = $R3 ] && [ "$(stat -c %a "$W/r/portal/portal_inbox.py.bak_S959_6abc6461")" = 600 ] && [ "$(stat -c %a "$W/r/portal/portal_inbox.py")" = 644 ]'
OUT="$(run)"; chk "again: ALREADY" 'echo "$OUT" | grep -q "ALREADY" && isto && clean'
OUT="$(run --undo)"; chk "--undo: all three back to FROM" 'echo "$OUT" | grep -q "UNDONE" && isfrom && clean'
OUT="$(run --undo)"; chk "--undo twice: not installed" 'echo "$OUT" | grep -q "not installed" && isfrom'
OUT="$(run)"; chk "re-install after undo" 'echo "$OUT" | grep -q "INSTALLED" && isto && clean'
echo x >> "$W/r/portal/portal_inbox.py"; OUT="$(run --undo)"; chk "--undo refuses a later kit's file" 'echo "$OUT" | grep -q "not S959" && clean'
fresh; OUT="$(FORCE_RED_AT=4 run)"; chk "forced red at [4/5]: all put back, restarted" 'echo "$OUT" | grep -q "RED" && isfrom && grep -q restart "$W/sysctl.log" && clean'
fresh; OUT="$(FORCE_RED_AT=5 run)"; chk "forced red at [5/5]: all put back" 'echo "$OUT" | grep -q "RED" && isfrom && clean'
fresh; OUT="$(FORCE_KILL_AT=4 run)"; chk "killed mid-[4/5]: all put back" 'echo "$OUT" | grep -q "ended before its proof" && isfrom && clean'
fresh; touch "$W/r/JOURNAL_BAD"; OUT="$(run)"; chk "journal says NOT mounted: put back" 'echo "$OUT" | grep -q "NOT mounted" && isfrom && clean'
fresh; touch "$W/r/WA404"; OUT="$(run)"; chk "the new route answers 404: put back" 'echo "$OUT" | grep -q "not mounted" && isfrom && clean'
fresh; touch "$W/r/INBOX500"; OUT="$(run)"; chk "his Inbox answers 500: put back" 'echo "$OUT" | grep -q "/portal/inbox answered 500" && isfrom && clean'
fresh; printf 'PORTAL_STAFF_WA_SEND = "0"\n' > "$W/r/portal/portal_config.py"; OUT="$(DRY=1 run)"; chk "a live switch 0: said as 'reply OFF', no key named; nothing changed" 'echo "$OUT" | grep -q "reply OFF . templates offered 1" && echo "$OUT" | grep -q "templates TEST MODE . send key named NO" && isfrom && clean'
fresh; rm -f "$W/r/portal/portal_config.py"; OUT="$(DRY=1 run)"; chk "no portal_config: the probe still reads, DRY ok" 'echo "$OUT" | grep -q "DRY ok" && echo "$OUT" | grep -q "PROBE\|reply on" && isfrom && clean'
fresh; mkdir "$W/r/deploy/lock"; OUT="$(run)"; chk "the build lock held: stops, nothing changed" 'echo "$OUT" | grep -q "another build holds" && isfrom && [ ! -e "$W/r/deploy/_off/DOCTOR_AUTO_OFF" ]'
fresh; echo "# drift" >> "$W/r/portal/calls_staff.py"; OUT="$(run)"; chk "a drifted calls_staff.py: stops at [2/5]" 'echo "$OUT" | grep -q "\[2/5\].*changed after" && clean'
fresh; echo "# drift" >> "$W/r/portal/portal_inbox.py"; OUT="$(run)"; chk "a drifted portal_inbox.py: stops at [2/5]" 'echo "$OUT" | grep -q "\[2/5\].*changed after" && clean'
fresh; echo "# drift" >> "$W/r/portal/calls_console.py"; OUT="$(run)"; chk "a drifted calls_console.py: stops at [2/5]" 'echo "$OUT" | grep -q "\[2/5\].*changed after" && clean'
fresh; \cp "$KD/to/portal_inbox.py" "$W/r/portal/portal_inbox.py"; OUT="$(run)"; chk "half installed (one file TO): stops at [2/5], nothing changed" 'echo "$OUT" | grep -q "\[2/5\]" && clean && [ ! -s "$W/sysctl.log" ]'
fresh; echo "# x" >> "$W/kit/to/calls_staff.py"; OUT="$(run)"; chk "a corrupt kit: stops at [1/5]" 'echo "$OUT" | grep -q "\[1/5\]" && isfrom'
rm -rf "$W"
echo "REHEARSAL: $PASS/$((PASS+FAIL)) $([ $FAIL = 0 ] && echo PASS || echo FAIL)"
[ $FAIL = 0 ]
