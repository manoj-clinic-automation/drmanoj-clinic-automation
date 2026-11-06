#!/bin/bash
# =============================================================================
#  install_S726_PURCHASE_RULES.sh · kit S726 (06-Nov-2026, Sanjeevni session 393) · D839 D840 F-1140 F-1141 F-1142 F-1143: a scan pairs
#  with its Marg bill on bill number and date first; the amount-only auto-link only in the bill's month, with no other bill of the
#  supplier at that amount and nothing read differing (else reception's one-tap question); the wrong AUTO links of a counted month undone
#  at each pass (never a September-only one); every rupee shown; Second look; Paired, nothing read; the owner's step view /page/check.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s726kit && cp -rp /root/deploy/repo/deploy_kits/S726_PURCHASE_RULES /tmp/s726kit && bash /tmp/s726kit/install_S726_PURCHASE_RULES.sh
#  (DRY=1 before bash: every gate, the walk, the control and the proof -- printed whole; nothing written.)
#   /root/finance/scan_register.py  904f07b1 -> TO
#   /root/finance/purchase_app.py   2e1e9023 -> TO
#   /root/finance/porders.py        8326dfc5 -> TO
#  Gates: SUMS, KIT_ID, the window, the live pins, the rebuild to the TO pins, the walk on the rebuilt files, the control on the live
#  files, the proof on this box's own databases (read only, printed whole). After placing: restart, health, the new page refuses a
#  stranger, the journal (F-1135: only the NEW master's and its workers' lines are counted), the walk again; then ONE matching pass by
#  the nightly's own crontab line (59 23 * * *: cd /root/finance && FINANCE_DB=... /root/wa/venv/bin/python3 -B purchase_app.py rematch
#  >> scan_rematch.log 2>&1) and a one-line summary of what it did, read from the audit rows it wrote.
# =============================================================================
set -u
KIT="S726_PURCHASE_RULES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
ADB="${ADB:-$ROOT/assetapp/assets.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDIT="finance/scan_register.py finance/purchase_app.py finance/porders.py"
FILES="$EDIT"
declare -A FROM=( [finance/scan_register.py]=904f07b1c7c6ce2291632586b7ddf279 [finance/purchase_app.py]=2e1e9023d7cd2887fefee3aa80276a93 [finance/porders.py]=8326dfc53a668689e7098bfdcb7ddfc0 )
declare -A TO
for f in $FILES; do TO[$f]="$(awk -v f="$f" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s726_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="walk_s726: 0 check(s) failed (0 of them S726 checks)"
CONTROL="walk_s726: 74 check(s) failed (74 of them S726 checks)"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S726_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s726"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { for f in $FILES; do rm -f "$(stg "$f")"; done; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && S726_SCHEMA_DIR="$ROOT/finance" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s726.py" "$1" 2>&1); }   # the schema file: beside the files, else the live folder
proof() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 1200 "$VPY" -W ignore -B "$KDIR/proof_s726.py" "$ROOT/finance" "$SCR/proof/finance" "$DB" "$ADB" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  PLACED=2
  for f in $EDIT; do \cp -p "$(bak "$f")" "$ROOT/$f" || say "   !! could not put back $ROOT/$f"; rm -f "$(stg "$f")"; done
  find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  for f in $EDIT; do say "   $ROOT/$f $(m5 "$ROOT/$f" | cut -c1-8) (expected ${FROM[$f]:0:8})"; done
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$FSVC" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep ln; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ -n "${TO[$f]}" ] || { say "!! [1/8] TO_PINS.md5 does not name $f - nothing installed"; exit 1; }; done
for f in $EDIT; do [ -f "$ROOT/$f" ] || { say "!! [1/8] $ROOT/$f is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$ROOT/finance/purchase_schema.sql" ] || { say "!! [1/8] $DB, $ADB or purchase_schema.sql is missing - nothing installed"; exit 1; }
mkdir -p "$SCR/built/finance" "$SCR/pyc" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/8] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
for f in $EDIT; do C=$(m5 "$ROOT/$f"); [ "$C" = "${FROM[$f]}" ] || stop_unlocked "!! [2/8] $ROOT/$f is ${C:0:8}, expected ${FROM[$f]:0:8} - it changed after this kit was built: STOP, nothing installed"; done
say "[2/8] live pins exact: scan_register ${FROM[finance/scan_register.py]:0:8} · purchase_app ${FROM[finance/purchase_app.py]:0:8} · porders ${FROM[finance/porders.py]:0:8}"

"$APY" -B make_s726.py "$ROOT/finance" "$SCR/built/finance" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused a live file - nothing installed"; }
for f in $FILES; do
  [ "$(m5 "$SCR/built/$f")" = "${TO[$f]}" ] || stop_unlocked "!! [3/8] rebuilt, $f is $(m5 "$SCR/built/$f" | cut -c1-8), not ${TO[$f]:0:8} - nothing installed"
  for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/8] $f does not compile on $py - nothing installed"; done
done
mkdir -p "$SCR/new/finance"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql; do [ -f "$f" ] && cp -p "$f" "$SCR/new/finance/"; done
for f in $FILES; do cp -p "$SCR/built/$f" "$SCR/new/finance/$(basename "$f")"; done
mkdir -p "$SCR/proof/finance"                                  # the proof's NEW side: the live folder by links, the three files real
for e in "$ROOT"/finance/*; do ln -s "$e" "$SCR/proof/finance/$(basename "$e")"; done
for f in $FILES; do rm -f "$SCR/proof/finance/$(basename "$f")"; cp -p "$SCR/built/$f" "$SCR/proof/finance/$(basename "$f")"; done
say "[3/8] rebuilt here from this box's live bytes: the three files at their TO pins; each compiles under both pythons"

R=$(walk "$SCR/new/finance" | tail -1)
[ "$R" = "$GREEN" ] || { walk "$SCR/new/finance" | grep -E 'FAIL|Error' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk "$ROOT/finance" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live files is not as expected ($R0) - nothing installed (kept in $SCR)"; }
say "[4/8] the walk: $R; the control on the live files: $R0"
proof > "$SCR/proof.txt"
P=$(tail -1 "$SCR/proof.txt")
say "---------------------------------------------------------------- the proof (read only) -- paste all of it to Claude"
sed 's/^/   /' "$SCR/proof.txt"
say "----------------------------------------------------------------"
echo "$P" | grep -q -E '^PROOF S726: [0-9]+ bills change \(Sep [0-9]+, Oct [0-9]+, Nov [0-9]+\)$' || { PLACED=2; stop_unlocked "!! [4/8] the proof on this box's databases: $P - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] $P (both databases opened read-only); finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the proof green; NOTHING written"; exit 0; fi

for f in $EDIT; do { \cp -p "$ROOT/$f" "$(bak "$f")" && [ "$(m5 "$(bak "$f")")" = "${FROM[$f]}" ]; } || stop_unlocked "!! [5/8] could not write the backup $(bak "$f") - nothing placed"; done
for f in $FILES; do { cat "$SCR/built/$f" > "$(stg "$f")" && [ "$(m5 "$(stg "$f")")" = "${TO[$f]}" ]; } || stop_unlocked "!! [5/8] could not stage $f - nothing placed"; done
for f in $EDIT; do chmod --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; chown --reference="$ROOT/$f" "$(stg "$f")" 2>/dev/null; done
OLDPIDS="$(pids_of | tr '\n' ' ')"
PLACED=1
for f in $FILES; do mv -f "$(stg "$f")" "$ROOT/$f" || restore "the rename of $f"; done
for f in $FILES; do [ "$(m5 "$ROOT/$f")" = "${TO[$f]}" ] || restore "read back of $f"; done
find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/8] placed and read back: scan_register ${TO[finance/scan_register.py]:0:8} · purchase_app ${TO[finance/purchase_app.py]:0:8} · porders ${TO[finance/porders.py]:0:8} (backups *.bak_S726_*)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/purchase/page/check); case "$c2" in 302|401|403) ;; *) restore "the new page answered $c2 without a login (expected 302, 401 or 403)";; esac
c3=$(fhealth /finance/purchase/page/scans); case "$c3" in 302|401|403) ;; *) restore "the register page answered $c3 without a login (expected 302, 401 or 403)";; esac
NEWPIDS="$(pids_of | tr '\n' ' ')"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  # F-1135: the stopping master's shutdown noise is not this install's fault -- count only lines of PIDs that are not the old ones
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|Logging error')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) from the new master ($NEWPIDS) since the restart"; }
fi
say "[6/8] $FSVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c1; without a login the new page $c2, the register $c3; journal clean (old PIDs $OLDPIDS left out, F-1135)"
R=$(walk "$ROOT/finance" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/8]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
say "[7/8] the walk on the placed files: $R"
# [8/8] ONE pass, exactly as the nightly runs it (crontab: 59 23 * * * cd /root/finance && FINANCE_DB=/root/finance/finance.db
# /root/wa/venv/bin/python3 -B /root/finance/purchase_app.py rematch >> /root/finance/scan_rematch.log 2>&1); ASSETS_DB is the
# nightly's own default (/root/assetapp/assets.db) on the box -- named only so a rehearsal root can point elsewhere.
A0=$("$VPY" -c 'import sqlite3,sys; c=sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); print(c.execute("SELECT COALESCE(MAX(id),0) FROM purchase_audit").fetchone()[0])' "$DB" 2>/dev/null)
[ -n "$A0" ] || restore "the audit could not be read before the pass"
(cd "$ROOT/finance" && FINANCE_DB="$DB" ASSETS_DB="$ADB" timeout 900 "$VPY" -B "$ROOT/finance/purchase_app.py" rematch >> "$ROOT/finance/scan_rematch.log" 2>&1)
RC=$?
[ "${REHEARSE_RED_AT:-}" = 8 ] && RC=99
[ "$RC" = 0 ] || restore "the pass (purchase_app.py rematch) ended $RC -- see $ROOT/finance/scan_rematch.log"
SUMLINE=$("$VPY" -c '
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
n = dict(c.execute("SELECT action, COUNT(*) FROM purchase_audit WHERE id > ? GROUP BY action", (int(sys.argv[2]),)).fetchall())
made = n.get("scan_link", 0) + n.get("auto_link", 0)
print("%d AUTO link(s) undone (S726) · %d link(s) made (%d by number / verified, %d by itself) · %d stale link(s) dropped · %d second scan(s) marked · S726 faults %d"
      % (n.get("auto_link_undone", 0), made, n.get("scan_link", 0), n.get("auto_link", 0), n.get("scan_unlink", 0), n.get("scan_dup", 0),
         n.get("s726_setup_error", 0) + n.get("auto_link_undo_error", 0)))
' "$DB" "$A0" 2>&1 | tail -1)
FAULTS=$(printf '%s\n' "$SUMLINE" | sed -n 's/.*S726 faults \([0-9][0-9]*\)$/\1/p')
[ "${REHEARSE_FAULT:-}" = 1 ] && FAULTS=1
[ "$FAULTS" = 0 ] || restore "the pass wrote ${FAULTS:-unknown} S726 fault row(s) (s726_setup_error / auto_link_undo_error): $SUMLINE"
say "[8/8] one pass by the nightly's own line: $SUMLINE"
say "      its log line: $(tail -1 "$ROOT/finance/scan_rematch.log" 2>/dev/null | cut -c1-220)"
release_lock
say "undo (one line): $(for f in $EDIT; do printf '\\cp -p %s %s && ' "$(bak "$f")" "$ROOT/$f"; done)$SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Your step view: https://followup.dr-manoj.in/finance/purchase/page/check"
exit 0
