#!/bin/bash
# rehearse_s966.sh -- the installer of kit S966_WA_BSUID run on a MADE-UP root (temp), never the box: the services, the health
#   answers and the journal are stand-ins. Scenarios: dry . red@4 . red@5 . killed@4 . receiver silent . install . again .
#   undo . wrong FROM. Each says PASS or FAIL; the last line is "REHEARSAL n/n" (all green = n/n).
#   bash rehearse_s966.sh <kit_dir> <from_dir with the four live files> [python]
set -u
KIT_SRC="$(cd "$1" && pwd)"; FROMD="$(cd "$2" && pwd)"; PY="${3:-python3}"
T="$(mktemp -d /tmp/s966_reh.XXXXXX)"; trap 'rm -rf "$T"' EXIT
P=0; N=0
chk() { N=$((N+1)); if eval "$2"; then P=$((P+1)); echo "  PASS  $1"; else echo "  FAIL  $1"; fi; }
m5() { md5sum "$1" | awk '{print $1}'; }
F="wa/wa_receiver.py wa/wa_alert.py portal/portal_inbox.py finance/records.py portal/calls_console.py"
fresh() { rm -rf "$T/root" "$T/deploy" "$T/kit"; mkdir -p "$T/root/wa" "$T/root/portal" "$T/root/finance" "$T/deploy/_off"
  \cp "$FROMD/wa_receiver.py" "$FROMD/wa_alert.py" "$T/root/wa/"; \cp "$FROMD/portal_inbox.py" "$FROMD/calls_console.py" "$T/root/portal/"; \cp "$FROMD/records.py" "$T/root/finance/"
  mkdir -p "$T/root/wa/wa_logs"; "$PY" - "$T/root/wa/wa_logs/2026-11-26.jsonl" <<'PYE'
import json, sys
with open(sys.argv[1], "w") as fh:                       # made-up pushes, numbers built here (none written in this file)
    for i in range(20):
        n = "91" + "9" + str(10 ** 8 + i)
        b = {"event_type": "message.received", "customer_identifier": n, "timestamp": str(1764200000 + i),
             "payload": {"id": "r%d" % i, "data": {"type": "text", "context": {"body": "made-up %d" % i}}}}
        fh.write(json.dumps({"at": "2026-11-26T10:00:00+05:30", "body": b}) + "\n")
    b = {"event_type": "message.received", "customer_identifier": "91" + "9" + str(10 ** 8 + 99), "id": "nots", "message": "no time"}
    fh.write(json.dumps({"at": "2026-11-26T10:05:00+05:30", "body": b}) + "\n")   # no timestamp of its own (second look)
    fh.write('{"at": "2026-11-26T10:06:00+05:30", "body": {"event_type": "message.rec')    # a half-written last line
PYE

  \cp -rp "$KIT_SRC" "$T/kit"; }
all_is() { local w="$1" f; for f in $F; do
    if [ "$w" = from ]; then [ "$(m5 "$T/root/$f")" = "$(m5 "$FROMD/$(basename "$f")")" ] || return 1
    else [ "$(m5 "$T/root/$f")" = "$(m5 "$KIT_SRC/to/$(basename "$f")")" ] || return 1; fi; done; return 0; }
cat > "$T/systemctl" <<'E'
#!/bin/bash
echo "systemctl $*" >> "$(dirname "$0")/svc.log"; exit 0
E
chmod +x "$T/systemctl"
printf '#!/bin/bash\necho 200\n' > "$T/health"; chmod +x "$T/health"
run() { (cd "$T" && env ROOT="$T/root" APY="$(command -v "$PY")" LOCK="$T/deploy/.lock" OFFSW="$T/deploy/_off/DOCTOR_AUTO_OFF" \
  SYSTEMCTL="$T/systemctl" HEALTH_CMD="$T/health" RX_CMD="${RXC:-echo wa_receiver alive}" JOURNAL_CMD="echo quiet" NAP=0 QUIET_TRIES=1 QUIET_NAP=0 \
  RAWLOG="$T/root/wa/wa_logs" "$@" bash "$T/kit/install_S966_WA_BSUID.sh" ${ARG:-} > "$T/out.txt" 2>&1); echo $?; }

fresh; rc=$(DRY=1 run); chk "dry: green to [3/5], nothing changed" "[ $rc = 0 ] && grep -q 'DRY ok' $T/out.txt && all_is from && grep -q '\[3/5\] walk ALL PASS' $T/out.txt"
[ $rc = 0 ] || tail -5 "$T/out.txt"
fresh; rc=$(FORCE_RED_AT=4 run); chk "red at [4/5]: all five put back, lock and switch gone" "[ $rc = 1 ] && all_is from && [ ! -e $T/deploy/.lock ] && [ ! -e $T/deploy/_off/DOCTOR_AUTO_OFF ]"
fresh; rc=$(FORCE_RED_AT=5 run); chk "red at [5/5] (after the restarts): all five put back, services restarted again" "[ $rc = 1 ] && all_is from && [ \$(grep -c 'restart wa-receiver' $T/svc.log) -ge 2 ]"
fresh; rc=$(FORCE_KILL_AT=4 run); chk "killed at [4/5]: the exit trap puts all five back" "[ $rc != 0 ] && all_is from && grep -q 'ended before its proof' $T/out.txt"
fresh; rc=$(RXC="echo nothing" run); chk "the receiver silent after its restart: all five put back" "[ $rc = 1 ] && all_is from && grep -q 'receiver did not answer' $T/out.txt"
fresh; rc=$(run); chk "install: INSTALLED, all five are the TO, five backups, the real-push replay read 21 (one with no time, a half line)" "[ $rc = 0 ] && grep -q 'INSTALLED' $T/out.txt && all_is to && [ \$(ls $T/root/*/*.bak_S966_* | wc -l) = 5 ] && grep -q 'real pushes: 1 files, 21 pushes' $T/out.txt"
[ $rc = 0 ] || tail -8 "$T/out.txt"
rc=$(run); chk "again: ALREADY in place, nothing done" "[ $rc = 0 ] && grep -q 'ALREADY in place' $T/out.txt && all_is to"
rc=$(ARG=--undo run); chk "undo: all five back to the FROM" "[ $rc = 0 ] && grep -q 'UNDONE' $T/out.txt && all_is from"
rc=$(ARG=--undo run); chk "undo again: nothing to undo" "[ $rc = 0 ] && grep -q 'not installed; nothing to undo' $T/out.txt"
fresh; echo "# a later change" >> "$T/root/finance/records.py"; rc=$(run); chk "wrong FROM (records.py changed since the build): STOP at [2/5], nothing changed" "[ $rc = 1 ] && grep -q '\[2/5\].*records.py' $T/out.txt && [ \$(ls $T/root/*/*.bak_S966_* 2>/dev/null | wc -l) = 0 ]"
fresh; echo "x" >> "$T/kit/walk_s966.py"; rc=$(run); chk "a kit file altered: STOP at [1/5]" "[ $rc = 1 ] && grep -q '\[1/5\] SUMS' $T/out.txt && all_is from"
fresh; "$PY" - "$T/root/wa/wa_logs/2026-11-26.jsonl" <<'PYE'
import json, sys
with open(sys.argv[1], "a") as fh:
    fh.write("\n" + json.dumps({"at": "x", "body": {"event_type": "message.received", "customer_identifier": "tel:+91" + "9" + str(10 ** 8),
                                            "payload": {"id": "odd", "data": {"type": "text", "context": {"body": "odd"}}}}}) + "\n")
PYE
rc=$(DRY=1 run); chk "a real push with an unknown lettered number: STOP at [3/5], nothing changed" "[ $rc = 1 ] && grep -q 'REAL pushes' $T/out.txt && all_is from"
echo "REHEARSAL $P/$N"
[ "$P" = "$N" ]
