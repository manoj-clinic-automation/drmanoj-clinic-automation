#!/bin/bash
# rehearse_s949.sh -- the installer on a made-up root (stub systemctl / journal / health / crontab / Sheet). The stub
# restart LOADS the hook in the made-up root (gspread blocked) so the table is created exactly as on the box.
#   bash rehearse_s949.sh <kit dir> <FROM hook> <FROM legs>        last line: REHEARSAL n/m
set -u
KD="$(cd "$1" && pwd)"; FROMH="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"; FROML="$(cd "$(dirname "$3")" && pwd)/$(basename "$3")"
T="$(mktemp -d /tmp/r949.XXXXXX)"; R="$T/root"; HK="$R/wa/call-hook"; FIN="$R/finance"; PASS=0; FAIL=0
mkdir -p "$HK" "$FIN" "$T/bin" "$T/stub/gspread" "$T/tmp" "$T/off"
ok() { if [ "$2" = 0 ]; then PASS=$((PASS+1)); echo "  ok   $1"; else FAIL=$((FAIL+1)); echo "  RED  $1"; fi; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cat > "$T/stub/gspread/__init__.py" <<'PY'
import json, os
class _WS:
    def get_all_values(self):
        return json.load(open(os.environ["STUB_SHEET"]))
class _SH:
    def worksheet(self, tab): return _WS()
class _C:
    def open_by_key(self, k): return _SH()
def service_account(filename=None): return _C()
PY
printf 'class WorksheetNotFound(Exception):\n    pass\n' > "$T/stub/gspread/exceptions.py"
echo '{"type": "service_account", "client_email": "made-up"}' > "$T/sa.json"
cat > "$T/bin/vpy" <<SH
#!/bin/bash
PYTHONPATH="$T/stub" exec python3 "\$@"
SH
cat > "$T/bin/systemctl" <<SH
#!/bin/bash
case "\$1" in
  is-active) [ -e "$T/svc_down" ] && exit 3; exit 0;;
  restart) [ -e "$T/no_journal" ] && exit 0
           (cd "$HK" && CALLHOOK_RAW_LOG_DIR="$T/raw" CALLHOOK_REJECT_DIR="$T/rej" CALLHOOK_QUEUE_DIR="$T/q" python3 -c "import sys; sys.modules['gspread']=None; sys.path.insert(0,'.'); import call_hook_capture" >> "$T/journal.txt" 2>&1); exit 0;;
esac
exit 0
SH
cat > "$T/bin/crontab" <<SH
#!/bin/bash
if [ "\$1" = "-l" ]; then [ -s "$T/cron.txt" ] && cat "$T/cron.txt"; exit 0; fi
cat > "$T/cron.txt"
SH
cat > "$T/bin/health" <<SH
#!/bin/bash
cat "$T/health"
SH
cat > "$T/bin/journal" <<SH
#!/bin/bash
cat "$T/journal.txt" 2>/dev/null
SH
cat > "$FIN/freshness.py" <<'PY'
import json, sys
legs = json.load(open(sys.argv[0].rsplit("/", 1)[0] + "/freshness_legs.json"))["legs"]
print("%d leg(s) declared in freshness_legs.json . 0 parked" % len(legs))
PY
chmod +x "$T/bin/"*
reset() { rm -rf "$HK"/* "$FIN"/freshness_legs.json* "$R/wa/calls.db"* "$T/lock" "$T/journal.txt" "$T/svc_down" "$T/no_journal"
  cp "$FROMH" "$HK/call_hook_capture.py"; cp "$FROML" "$FIN/freshness_legs.json"; echo 200 > "$T/health"
  printf '0 1 * * * /bin/true # an existing line\n5 2 * * * /bin/true # another\n' > "$T/cron.txt"; echo '[["h"]]' > /dev/null
  python3 -c "import json,sys; sys.path.insert(0,'$KD'); import call_log_db as c; json.dump([c.HEADER], open('$T/sheet.json','w'))"; }
export ROOT="$R" VPY="$T/bin/vpy" SYSTEMCTL="$T/bin/systemctl" CRONTAB="$T/bin/crontab" HEALTH_CMD="$T/bin/health" JOURNAL_CMD="$T/bin/journal"
export LOCK="$T/lock" OFFSW="$T/off/DOCTOR_AUTO_OFF" TMPW="$T/tmp" NAP=0 REHEARSE_CLOCK=2200 REHEARSE_DOW=2
export CALLHOOK_DB="$R/wa/calls.db" CALLHOOK_SA_KEY="$T/sa.json" STUB_SHEET="$T/sheet.json" CALL_LOG_COMPARE_STATE="$HK/call_log_compare.state.json"
I="$KD/install_S949_CALL_LOG_TABLE.sh"
TO_H=$(awk '$2=="call_hook_capture.py"{print $1}' "$KD/TO_PINS.md5"); TO_L=$(awk '$2=="freshness_legs.json"{print $1}' "$KD/TO_PINS.md5")
FROM_H=$(m5 "$FROMH"); FROM_L=$(m5 "$FROML")
untouched() { [ "$(m5 "$HK/call_hook_capture.py")" = "$FROM_H" ] && [ "$(m5 "$FIN/freshness_legs.json")" = "$FROM_L" ] && [ ! -f "$HK/call_log_db.py" ] && [ ! -f "$HK/call_log_compare.py" ] && ! grep -q S949 "$T/cron.txt" && [ ! -e "$T/lock" ] && [ ! -e "$T/off/DOCTOR_AUTO_OFF" ]; }
installed() { [ "$(m5 "$HK/call_hook_capture.py")" = "$TO_H" ] && [ "$(m5 "$FIN/freshness_legs.json")" = "$TO_L" ] && [ -f "$HK/call_log_db.py" ] && [ -f "$HK/call_log_compare.py" ] && [ "$(grep -c S949_CALL_LOG_COMPARE "$T/cron.txt")" = 1 ] && [ "$(wc -l < "$T/cron.txt")" = 3 ] && [ ! -e "$T/lock" ] && [ ! -e "$T/off/DOCTOR_AUTO_OFF" ]; }

reset; O=$(DRY=1 bash "$I" 2>&1); echo "$O" | grep -q "DRY RUN: every gate" && untouched; ok "R1 DRY: every gate green, nothing changed" $?
O=$(bash "$I" 2>&1); echo "$O" | grep -q "S949_CALL_LOG_TABLE: DONE" && installed && [ "$(stat -c %a "$R/wa/calls.db")" = 600 ] && grep -q '"verdict": "EQUAL"' "$CALL_LOG_COMPARE_STATE"; ok "R2 install: four files at TO, cron in (one line added), table 0600, first compare EQUAL, lock and pause released" $?
echo "$O" | grep -q "receiver v3.4" ; ok "R3 the install says the log showed receiver v3.4" $?
O=$(bash "$I" 2>&1); echo "$O" | grep -q "ALREADY INSTALLED"; ok "R4 again: ALREADY INSTALLED" $?
O=$(bash "$I" --undo 2>&1); echo "$O" | grep -q "UNDONE" && [ "$(m5 "$HK/call_hook_capture.py")" = "$FROM_H" ] && [ "$(m5 "$FIN/freshness_legs.json")" = "$FROM_L" ] && [ -f "$HK/call_log_db.py.undone_S949" ] && ! grep -q S949 "$T/cron.txt" && [ -f "$R/wa/calls.db" ]; ok "R5 undo: hook and legs back, scripts aside, cron out, the table kept" $?
O=$(bash "$I" --undo 2>&1); echo "$O" | grep -q "not installed"; ok "R6 undo again: not installed" $?
O=$(REHEARSE_CLOCK=1100 bash "$I" 2>&1); echo "$O" | grep -q "inside duty hours" && [ "$(m5 "$HK/call_hook_capture.py")" = "$FROM_H" ] && [ ! -e "$T/lock" ]; ok "R7 at 11:00 on a weekday: refused, nothing changed" $?
O=$(REHEARSE_CLOCK=1100 REHEARSE_DOW=7 bash "$I" 2>&1); echo "$O" | grep -q "Sunday" ; ok "R8 at 11:00 on a Sunday: refused" $?
O=$(REHEARSE_CLOCK=1500 REHEARSE_DOW=7 bash "$I" 2>&1); echo "$O" | grep -q "DONE" && installed && echo "$O" | grep -q "an older table kept as" && ls "$R/wa/" | grep -q "calls.db.before_S949_"; ok "R9 Sunday 15:00 after an undo: installs, the old table set aside (kept)" $?
bash "$I" --undo >/dev/null 2>&1
reset; O=$(REHEARSE_RED_AT=4 bash "$I" 2>&1); echo "$O" | grep -q "RED (rehearsal: a forced red at \[4/6\])" && untouched; ok "R10 forced red at [4/6]: everything back" $?
reset; O=$(REHEARSE_RED_AT=5 bash "$I" 2>&1); echo "$O" | grep -q "forced red at \[5/6\]" && untouched; ok "R11 forced red at [5/6]: everything back, cron out" $?
reset; python3 -c "import json,sys; sys.path.insert(0,'$KD'); import call_log_db as c; r=['']*14; r[0]='IN-x'; r[11]='2099-01-01T00:00:00+05:30'; json.dump([c.HEADER, r], open('$T/sheet.json','w'))"
O=$(bash "$I" 2>&1); echo "$O" | grep -q "the first compare: COMPARE DIFFER" && untouched; ok "R12 the first compare not EQUAL (a Sheet row the table lacks): everything back" $?
reset; printf '' > "$T/cron.txt"; O=$(bash "$I" 2>&1); echo "$O" | grep -q "crontab -l came back empty" && untouched; ok "R13 crontab empty: everything back, the crontab not touched" $?
reset; echo 500 > "$T/health"; O=$(bash "$I" 2>&1); echo "$O" | grep -q "health 500 before" && untouched; ok "R14 health 500 before: nothing installed" $?
reset; touch "$T/no_journal"; O=$(bash "$I" 2>&1); echo "$O" | grep -q "does not show receiver v3.4" && untouched; ok "R15 the log never shows v3.4: everything back" $?
reset; mkdir "$T/lock"; echo other > "$T/lock/owner"; O=$(bash "$I" 2>&1); echo "$O" | grep -q "another build holds the lock" && [ -d "$T/lock" ]; ok "R16 the build lock held: refused, the other lock untouched" $?
rm -rf "$T/lock"
reset; echo "# drift" >> "$HK/call_hook_capture.py"; O=$(bash "$I" 2>&1); echo "$O" | grep -q "changed after this kit was built" && [ ! -f "$HK/call_log_db.py" ]; ok "R17 a drifted live hook: STOP, nothing installed" $?
reset; cp -rp "$KD" "$T/kit2"; echo "# x" >> "$T/kit2/call_log_compare.py"; O=$(bash "$T/kit2/install_S949_CALL_LOG_TABLE.sh" 2>&1); echo "$O" | grep -q "SUMS.md5 gate failed" && untouched; ok "R18 a tampered kit: refused" $?
reset; touch "$T/svc_down"; O=$(bash "$I" 2>&1); echo "$O" | grep -q "not active before" && untouched; ok "R19 the service down before: nothing installed" $?
rm -rf "$T"
echo "REHEARSAL $PASS/$((PASS+FAIL))"
