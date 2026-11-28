#!/bin/bash
# rehearse_s977.sh -- the installer of kit S977_MORNING_REVENUE_MATCH run on a MADE-UP root (temp), never the box: the service, the
#   health answers and the journal are stand-ins. Scenarios: dry . red@4 . red@5 . killed@4 . install . again . undo .
#   undo again . wrong FROM . kit altered. Last line "REHEARSAL n/n".
#   bash rehearse_s977.sh <kit_dir> <a finance folder with the live files> <a database copy> [python]
set -u
KIT_SRC="$(cd "$1" && pwd)"; FIN="$(cd "$2" && pwd)"; DBC="$3"; PY="${4:-python3}"
T="$(mktemp -d /tmp/s977_reh.XXXXXX)"; chmod 700 "$T"; trap 'rm -rf "$T"' EXIT
P=0; N=0
want() { [ -z "${ONLY:-}" ] || case " $ONLY " in *" $1 "*) return 0;; *) return 1;; esac; }   # ONLY="1 2" runs those groups
chk() { N=$((N+1)); if eval "$2"; then P=$((P+1)); echo "  PASS  $1"; else echo "  FAIL  $1"; fi; }
m5() { [ -f "$1" ] && md5sum "$1" | awk '{print $1}' || echo ABSENT; }
cat > "$T/systemctl" <<'E'
#!/bin/bash
echo "systemctl $*" >> "$(dirname "$0")/svc.log"; exit 0
E
printf '#!/bin/bash\necho 200\n' > "$T/health"; printf '#!/bin/bash\necho 302\n' > "$T/door"; printf '#!/bin/bash\necho quiet\n' > "$T/log"
printf '#!/bin/bash\necho "LIVE stub (the dry run above ran the real one)"\necho "ALL PASS"\n' > "$T/live"
chmod +x "$T/systemctl" "$T/health" "$T/door" "$T/log" "$T/live"
fresh() { rm -rf "$T/root" "$T/deploy" "$T/kit"; mkdir -p "$T/root/finance" "$T/deploy/_off"
  \cp "$FIN"/*.py "$T/root/finance/"; \cp "$KIT_SRC/from/day_check.py" "$KIT_SRC/from/register_push.py" "$KIT_SRC/from/docterz_pickup.py" "$T/root/finance/"
  \cp "$DBC" "$T/root/finance/finance.db"; chmod 600 "$T/root/finance/finance.db"; : > "$T/svc.log"; \cp -rp "$KIT_SRC" "$T/kit"; }
is_from() { for n in day_check.py register_push.py docterz_pickup.py; do [ "$(m5 "$T/root/finance/$n")" = "$(m5 "$KIT_SRC/from/$n")" ] || return 1; done; }
is_to() { for n in day_check.py register_push.py docterz_pickup.py; do [ "$(m5 "$T/root/finance/$n")" = "$(m5 "$KIT_SRC/to/$n")" ] || return 1; done; }
run() { (cd "$T" && env ROOT="$T/root" VPY="$(command -v "$PY")" LOCK="$T/deploy/.lock" OFFSW="$T/deploy/_off/DOCTOR_AUTO_OFF" \
  SYSTEMCTL="$T/systemctl" HEALTH_CMD="$T/health" DOOR_CMD="$T/door" LOG_CMD="$T/log" NAP=0 NO_WAIT=1 \
  "$@" bash "$T/kit/install_S977_MORNING_REVENUE_MATCH.sh" ${ARG:-} > "$T/out.txt" 2>&1); echo $?; }

if want 1; then fresh; rc=$(DRY=1 run); chk "dry: green to [3/6] (walk, control, live shape), nothing changed" "[ $rc = 0 ] && grep -q 'DRY ok' $T/out.txt && grep -q '^         the live shape' $T/out.txt && is_from"; fi
if want 1; then [ $rc = 0 ] || tail -6 "$T/out.txt"; fi
export LIVE_CMD="$T/live"            # the dry run above ran the real live shape; the rest use a stand-in
if want 2; then fresh; rc=$(FORCE_RED_AT=4 run); chk "red at [4/6]: all put back, lock + switch gone" "[ $rc = 1 ] && is_from && [ ! -e $T/deploy/.lock ] && [ ! -e $T/deploy/_off/DOCTOR_AUTO_OFF ]"; fi
if want 3; then fresh; rc=$(FORCE_RED_AT=5 run); chk "red at [5/6] (after the restart): all put back, restarted again" "[ $rc = 1 ] && is_from && [ \$(grep -c 'restart clinic-finance' $T/svc.log) -ge 2 ]"; fi
if want 4; then fresh; rc=$(FORCE_KILL_AT=4 run); chk "killed at [4/6]: the exit trap puts all back" "[ $rc != 0 ] && is_from && grep -q 'ended before its proof' $T/out.txt"; fi
if want 5; then fresh; rc=$(run); chk "install: INSTALLED, three files TO, quiet sweep + status ran" "[ $rc = 0 ] && grep -q 'INSTALLED' $T/out.txt && is_to && grep -q 'REGPUSH S977 1: ' $T/out.txt && grep -q 'the quiet sweep' $T/out.txt"; fi
if want 5; then [ $rc = 0 ] || tail -6 "$T/out.txt"; fi
if want 5; then rc=$(run); chk "again: ALREADY in place" "[ $rc = 0 ] && grep -q 'ALREADY in place' $T/out.txt && is_to"; fi
if want 5; then rc=$(ARG=--undo run); chk "undo: three files back" "[ $rc = 0 ] && grep -q 'UNDONE' $T/out.txt && is_from"; fi
if want 5; then rc=$(ARG=--undo run); chk "undo again: nothing to undo" "[ $rc = 0 ] && grep -q 'not installed; nothing to undo' $T/out.txt"; fi
if want 6; then fresh; echo "# a later change" >> "$T/root/finance/day_check.py"; rc=$(run); chk "wrong FROM (day_check.py changed): STOP at [2/6], nothing placed" "[ $rc = 1 ] && grep -q '\[2/6\].*day_check.py' $T/out.txt && [ \"\$(m5 $T/root/finance/register_push.py)\" = \"\$(m5 $KIT_SRC/from/register_push.py)\" ]"; fi
if want 7; then fresh; echo "# later" >> "$T/root/finance/docterz_pickup.py"; rc=$(run); chk "wrong FROM (docterz_pickup.py changed): STOP at [2/6], nothing placed" "[ $rc = 1 ] && grep -q '\\[2/6\\].*docterz_pickup.py' $T/out.txt && [ \"\$(m5 $T/root/finance/day_check.py)\" = \"\$(m5 $KIT_SRC/from/day_check.py)\" ]"; fi
if want 8; then fresh; echo "x" >> "$T/kit/walk_s977.py"; rc=$(run); chk "a kit file altered: STOP at [1/6]" "[ $rc = 1 ] && grep -q '\[1/6\] SUMS' $T/out.txt && is_from"; fi
echo "REHEARSAL $P/$N"
[ "$P" = "$N" ]
