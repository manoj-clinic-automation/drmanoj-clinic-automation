#!/bin/bash
# rehearse_s980.sh -- the installer of kit S980_FILM_COUNT_RISE run on a MADE-UP root (temp), never the box: the service, the health
#   answers and the journal are stand-ins. Scenarios: dry . red@4 . red@5 . killed@4 . install . again . undo . undo again .
#   wrong FROM (xray_film) . kit altered. Last line "REHEARSAL n/n".  ONLY="1 2" runs those groups (a call cannot outlive
#   ~3 minutes on the build machine: F-1749).
#   bash rehearse_s980.sh <kit_dir> <a finance folder with the live files> <any folder (unused)> <a database copy> [python]
set -u
KIT_SRC="$(cd "$1" && pwd)"; FIN="$(cd "$2" && pwd)"; POR="$(cd "$3" && pwd)"; DBC="$4"; PY="${5:-python3}"
T="$(mktemp -d "${TMPDIR:-/tmp}/s980_reh.XXXXXX")"; chmod 700 "$T"; trap 'rm -rf "$T"' EXIT
P=0; N=0
want() { [ -z "${ONLY:-}" ] || case " $ONLY " in *" $1 "*) return 0;; *) return 1;; esac; }
chk() { N=$((N+1)); if eval "$2"; then P=$((P+1)); echo "  PASS  $1"; else echo "  FAIL  $1"; fi; }
m5() { [ -f "$1" ] && md5sum "$1" | awk '{print $1}' || echo ABSENT; }
cat > "$T/systemctl" <<'E'
#!/bin/bash
echo "systemctl $*" >> "$(dirname "$0")/svc.log"; exit 0
E
printf '#!/bin/bash\necho 200\n' > "$T/health"; printf '#!/bin/bash\necho 302\n' > "$T/door"; printf '#!/bin/bash\necho quiet\n' > "$T/log"
printf '#!/bin/bash\necho "LIVE stub (the dry run above ran the real one)"\necho "ALL PASS"\n' > "$T/live"
chmod +x "$T/systemctl" "$T/health" "$T/door" "$T/log" "$T/live"
FILES="finance/xray_film.py"
fresh() { rm -rf "$T/root" "$T/deploy" "$T/kit"; mkdir -p "$T/root/finance" "$T/root/portal" "$T/deploy/_off"
  \cp "$FIN"/*.py "$T/root/finance/"; for f in $FILES; do \cp "$KIT_SRC/from/$(basename $f)" "$T/root/$f"; done
  \cp "$DBC" "$T/root/finance/finance.db"; chmod 600 "$T/root/finance/finance.db"; : > "$T/svc.log"; \cp -rp "$KIT_SRC" "$T/kit"; }
is_from() { for f in $FILES; do [ "$(m5 "$T/root/$f")" = "$(m5 "$KIT_SRC/from/$(basename $f)")" ] || return 1; done; }
is_to() { for f in $FILES; do [ "$(m5 "$T/root/$f")" = "$(m5 "$KIT_SRC/to/$(basename $f)")" ] || return 1; done; }
run() { (cd "$T" && env ROOT="$T/root" VPY="$(command -v "$PY")" LOCK="$T/deploy/.lock" OFFSW="$T/deploy/_off/DOCTOR_AUTO_OFF" \
  SYSTEMCTL="$T/systemctl" HEALTH_CMD="$T/health" DOOR_CMD="$T/door" LOG_CMD="$T/log" NAP=0 NO_WAIT=1 \
  "$@" bash "$T/kit/install_S980_FILM_COUNT_RISE.sh" ${ARG:-} > "$T/out.txt" 2>&1); echo $?; }
if want 1; then fresh; rc=$(DRY=1 run); chk "dry: green to [3/6] (walk, control, live shape), nothing changed" "[ $rc = 0 ] && grep -q 'DRY ok' $T/out.txt && grep -q '^         the live shape' $T/out.txt && is_from"; [ $rc = 0 ] || tail -6 "$T/out.txt"; fi
export LIVE_CMD="$T/live"
if want 2; then fresh; rc=$(FORCE_RED_AT=4 run); chk "red at [4/6]: all put back, lock + switch gone" "[ $rc = 1 ] && is_from && [ ! -e $T/deploy/.lock ] && [ ! -e $T/deploy/_off/DOCTOR_AUTO_OFF ]"; fi
if want 2; then fresh; rc=$(FORCE_RED_AT=5 run); chk "red at [5/6] (after the restart): all put back, restarted again" "[ $rc = 1 ] && is_from && [ \$(grep -c 'restart clinic-finance' $T/svc.log) -ge 2 ]"; fi
if want 2; then fresh; rc=$(FORCE_KILL_AT=4 run); chk "killed at [4/6]: the exit trap puts all back" "[ $rc != 0 ] && is_from && grep -q 'ended before its proof' $T/out.txt"; fi
if want 3; then fresh; rc=$(run); chk "install: INSTALLED, the file TO" "[ $rc = 0 ] && grep -q 'INSTALLED' $T/out.txt && is_to"; [ $rc = 0 ] || tail -6 "$T/out.txt"; fi
if want 3; then rc=$(run); chk "again: ALREADY in place" "[ $rc = 0 ] && grep -q 'ALREADY in place' $T/out.txt && is_to"; fi
if want 3; then rc=$(ARG=--undo run); chk "undo: the file back" "[ $rc = 0 ] && grep -q 'UNDONE' $T/out.txt && is_from"; fi
if want 3; then rc=$(ARG=--undo run); chk "undo again: nothing to undo" "[ $rc = 0 ] && grep -q 'not installed; nothing to undo' $T/out.txt"; fi
if want 4; then fresh; echo "# a later change" >> "$T/root/finance/xray_film.py"; rc=$(run); chk "wrong FROM (xray_film.py changed): STOP at [2/6], nothing placed" "[ $rc = 1 ] && grep -q '\[2/6\].*xray_film.py' $T/out.txt"; fi
if want 4; then fresh; echo "x" >> "$T/kit/walk_s980.py"; rc=$(run); chk "a kit file altered: STOP at [1/6]" "[ $rc = 1 ] && grep -q '\[1/6\] SUMS' $T/out.txt && is_from"; fi
echo "REHEARSAL $P/$N"
[ "$P" = "$N" ]
