#!/bin/bash
# rehearse_s968.sh -- the installer of kit S968_REGISTER_PUSH run on a MADE-UP root (temp), never the box: the service, the
#   health answers, the journal and the crontab are stand-ins. Scenarios: dry . red@4 . red@5 . killed@4 . install . again .
#   undo . undo again . wrong FROM . kit altered. Last line "REHEARSAL n/n".
#   bash rehearse_s968.sh <kit_dir> <a finance folder with the live files> <a database copy> [python]
set -u
KIT_SRC="$(cd "$1" && pwd)"; FIN="$(cd "$2" && pwd)"; DBC="$3"; PY="${4:-python3}"
T="$(mktemp -d /tmp/s968_reh.XXXXXX)"; chmod 700 "$T"; trap 'rm -rf "$T"' EXIT
P=0; N=0
chk() { N=$((N+1)); if eval "$2"; then P=$((P+1)); echo "  PASS  $1"; else echo "  FAIL  $1"; fi; }
m5() { [ -f "$1" ] && md5sum "$1" | awk '{print $1}' || echo ABSENT; }
cat > "$T/systemctl" <<'E'
#!/bin/bash
echo "systemctl $*" >> "$(dirname "$0")/svc.log"; exit 0
E
cat > "$T/crontab" <<'E'
#!/bin/bash
f="$(dirname "$0")/crontab.txt"
if [ "${1:-}" = "-l" ]; then cat "$f"; else cat "$1" > "$f"; fi
E
printf '#!/bin/bash\necho 200\n' > "$T/health"; printf '#!/bin/bash\necho 302\n' > "$T/door"; printf '#!/bin/bash\necho quiet\n' > "$T/log"
chmod +x "$T/systemctl" "$T/crontab" "$T/health" "$T/door" "$T/log"
fresh() { rm -rf "$T/root" "$T/deploy" "$T/kit"; mkdir -p "$T/root/finance" "$T/root/portal" "$T/deploy/_off"
  \cp "$FIN"/*.py "$T/root/finance/"; rm -f "$T/root/finance/register_push.py"; echo "x" > "$T/root/portal/callback_clock.py"
  \cp "$DBC" "$T/root/finance/finance.db"; chmod 600 "$T/root/finance/finance.db"
  printf '0 3 * * * /bin/true # S443_DOCTERZ_PICKUP\n' > "$T/crontab.txt"; : > "$T/svc.log"; \cp -rp "$KIT_SRC" "$T/kit"; }
is_from() { [ "$(m5 "$T/root/finance/clinic_register.py")" = "$(m5 "$FIN/clinic_register.py")" ] && [ "$(m5 "$T/root/finance/day_check.py")" = "$(m5 "$FIN/day_check.py")" ] \
  && [ ! -f "$T/root/finance/register_push.py" ] && ! grep -q S968_REGISTER_PUSH "$T/crontab.txt"; }
is_to() { for n in clinic_register.py day_check.py register_push.py; do [ "$(m5 "$T/root/finance/$n")" = "$(m5 "$KIT_SRC/to/$n")" ] || return 1; done
  grep -q S968_REGISTER_PUSH "$T/crontab.txt" && [ "$(grep -c . "$T/crontab.txt")" = 2 ]; }
run() { (cd "$T" && env ROOT="$T/root" VPY="$(command -v "$PY")" LOCK="$T/deploy/.lock" OFFSW="$T/deploy/_off/DOCTOR_AUTO_OFF" \
  SYSTEMCTL="$T/systemctl" CRONTAB="$T/crontab" HEALTH_CMD="$T/health" DOOR_CMD="$T/door" LOG_CMD="$T/log" NAP=0 \
  "$@" bash "$T/kit/install_S968_REGISTER_PUSH.sh" ${ARG:-} > "$T/out.txt" 2>&1); echo $?; }

fresh; rc=$(DRY=1 run); chk "dry: green to [3/5] (walk, control, live shape), nothing changed" "[ $rc = 0 ] && grep -q 'DRY ok' $T/out.txt && grep -q '^         the live shape' $T/out.txt && is_from"
[ $rc = 0 ] || tail -6 "$T/out.txt"
fresh; rc=$(FORCE_RED_AT=4 run); chk "red at [4/5]: all put back, cron line out, lock + switch gone" "[ $rc = 1 ] && is_from && [ ! -e $T/deploy/.lock ] && [ ! -e $T/deploy/_off/DOCTOR_AUTO_OFF ]"
fresh; rc=$(FORCE_RED_AT=5 run); chk "red at [5/5] (after the restart): all put back, restarted again" "[ $rc = 1 ] && is_from && [ \$(grep -c 'restart clinic-finance' $T/svc.log) -ge 2 ]"
fresh; rc=$(FORCE_KILL_AT=4 run); chk "killed at [4/5]: the exit trap puts all back" "[ $rc != 0 ] && is_from && grep -q 'ended before its proof' $T/out.txt"
fresh; rc=$(run); chk "install: INSTALLED, the three files TO, the cron line in (old crontab + one), status ran" "[ $rc = 0 ] && grep -q 'INSTALLED' $T/out.txt && is_to && grep -q 'REGPUSH S968 1: ' $T/out.txt"
[ $rc = 0 ] || tail -6 "$T/out.txt"
rc=$(run); chk "again: ALREADY in place" "[ $rc = 0 ] && grep -q 'ALREADY in place' $T/out.txt && is_to"
rc=$(ARG=--undo run); chk "undo: both files back, register_push.py removed, the cron line out" "[ $rc = 0 ] && grep -q 'UNDONE' $T/out.txt && is_from"
rc=$(ARG=--undo run); chk "undo again: nothing to undo" "[ $rc = 0 ] && grep -q 'not installed; nothing to undo' $T/out.txt"
fresh; echo "# a later change" >> "$T/root/finance/day_check.py"; rc=$(run); chk "wrong FROM (day_check.py changed): STOP at [2/5], nothing placed" "[ $rc = 1 ] && grep -q '\[2/5\].*day_check.py' $T/out.txt && [ ! -f $T/root/finance/register_push.py ]"
fresh; echo "x" >> "$T/kit/walk_s968.py"; rc=$(run); chk "a kit file altered: STOP at [1/5]" "[ $rc = 1 ] && grep -q '\[1/5\] SUMS' $T/out.txt && is_from"
echo "REHEARSAL $P/$N"
[ "$P" = "$N" ]
