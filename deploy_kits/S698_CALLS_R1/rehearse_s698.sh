#!/bin/bash
# rehearse_s698.sh -- the S698 installer on a MADE-UP root (no live file, no service, no sheet): dry . install . again .
# changed FROM . half placed . corrupt kit . someone else's switch . journal red . forced red at [9/9] . the repair's fail branch.
# usage: bash rehearse_s698.sh <kit folder> <src folder with the FROM files: portal.py portal_console.py call_hook_capture.py>
set -u
KDIR="$(cd "$1" && pwd)"; SRC="$(cd "$2" && pwd)"
R="$(mktemp -d /tmp/s698reh_XXXX)"; export TMPW="$R/tmp"; mkdir -p "$TMPW"
PY="$(command -v python3)"
fresh() {  # a made-up root with the FROM files
  rm -rf "$R/root" "$R/bin" "$R/deploy"; mkdir -p "$R/root/portal" "$R/root/wa/call-hook" "$R/root/wa/logs" "$R/bin" "$R/deploy/_off"
  cp -p "$SRC/portal.py" "$R/root/portal/portal.py"; cp -p "$SRC/portal_console.py" "$R/root/wa/portal_console.py"; cp -p "$SRC/call_hook_capture.py" "$R/root/wa/call-hook/call_hook_capture.py"
  "$PY" - "$R/root/wa/console.db" <<'PYX'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.executescript("CREATE TABLE calls(id INTEGER PRIMARY KEY, client_ref_id TEXT, ref_id TEXT, session_id TEXT, category TEXT, status TEXT, direction TEXT, answered INTEGER, total_duration TEXT, customer_result TEXT, customer_talk_duration TEXT, customer_ring_duration TEXT, recording_filename TEXT, ended_at_ist TEXT, captured_at_ist TEXT, source_event TEXT, phone10 TEXT, join_key TEXT); CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT); INSERT INTO meta VALUES('built_at','2026-11-02T10:00:00');")
for i in range(3):
    c.execute("INSERT INTO calls(client_ref_id,ref_id,session_id,category,status,direction,answered,ended_at_ist,source_event,phone10) VALUES (?,?,?,?,?,?,?,?,?,?)", ("IN-x%d"%i,"u%d"%i,"x%d"%i,"incoming","missed","In",0,"2026-11-01T10:0%d:00+05:30"%i,"call.end","5000000001"))
    c.execute("INSERT INTO calls(client_ref_id,ref_id,session_id,category,status,direction,answered,ended_at_ist,source_event,phone10) VALUES (?,?,?,?,?,?,?,?,?,?)", ("IN-x%d"%i,"u%d"%i,"x%d"%i,"incoming","missed","In",0,"2026-11-01T10:0%d:00+05:30"%i,"call.summary","5000000001"))
c.commit()
PYX
  printf '%s\n' '# made-up crontab' '*/10 9-21 * * * /usr/bin/flock -n /root/wa/console_cron.lock /root/wa/venv/bin/python3 /root/wa/portal_console.py --build >> /root/wa/logs/console_cron.log 2>&1' '0 3 * * * echo other' > "$R/crontab.txt"
  # shims
  cat > "$R/bin/systemctl" <<'SH'
#!/bin/bash
echo "systemctl $*" >> "$REH_LOG"; exit 0
SH
  cat > "$R/bin/journalctl" <<'SH'
#!/bin/bash
case "$*" in
  *call-hook*) echo "Nov 02 10:00:00 box gunicorn[1]: [call_hook_capture] Phase B receiver v3.2 (dual-key + incoming capture; the verified row, S698). raw logs: x"; echo "Nov 02 10:00:01 box gunicorn[1]: [call_hook_capture] connected to 'Call_Durations' (key=k.json) - 2123 rows known";;
  *) echo "Nov 02 10:00:02 box systemd[1]: Starting gunicorn"; echo "Nov 02 10:00:03 box gunicorn[2]: Listening at: http://127.0.0.1:8099"; [ "${REH_JOURNAL_RED:-0}" = 1 ] && echo "Nov 02 10:00:04 box gunicorn[2]: Traceback (most recent call last): calls_console";;
esac
exit 0
SH
  cat > "$R/bin/crontab" <<'SH'
#!/bin/bash
if [ "$1" = "-l" ]; then cat "$REH_CRON"; elif [ "$1" = "-" ]; then cat > "$REH_CRON"; fi
SH
  cat > "$R/bin/curl" <<'SH'
#!/bin/bash
url="${@: -1}"
case "$url" in
  *:8098/) echo "call_hook_capture alive";;
  */portal/health) printf '200';;
  */portal/console/api/call) printf '405';;
  */portal/console*) printf '302';;
  *) printf '000';;
esac
SH
  chmod +x "$R/bin/"*
  printf 'VERIFIED fake\n' > /dev/null
  cat > "$R/repair_ok.py" <<'PYX'
import sys
print("REPAIR S698 (APPLY): fake"); print("  VERIFIED: 2000 data rows now; no key twice; every raw-log call of the region present.")
PYX
  cat > "$R/repair_bad.py" <<'PYX'
import sys
print("REPAIR S698 (APPLY): fake"); print("  !! VERIFY FAILED: 1 key(s) twice"); print("  RESTORED the region's rows"); sys.exit(1)
PYX
}
run() {  # name, then env assignments
  local name="$1"; shift
  export REH_LOG="$R/log_$name.txt"; : > "$REH_LOG"; export REH_CRON="$R/crontab.txt"
  env PATH="$R/bin:$PATH" APY="$PY" VPY="$PY" ROOT="$R/root" LOCK="$R/deploy/.lock" OFFSW="$R/deploy/_off/DOCTOR_AUTO_OFF" SKIP_WINDOW=1 CRON_LOCK="$R/cron.lock" "$@" bash "$KDIR/install_S698_CALLS_R1.sh" > "$R/out_$name.txt" 2>&1
  echo "== $name: exit $?: $(tail -1 "$R/out_$name.txt" | cut -c1-150)"
}
fresh; run dry DRY=1 REPAIR_PY="$R/repair_ok.py"; grep -c "^\[" "$R/out_dry.txt" | sed 's/^/   steps printed: /'; grep -q "NOTHING written" "$R/out_dry.txt" && echo "   dry: nothing written" ; [ "$(md5sum "$R/root/portal/portal.py" | cut -c1-8)" = 4ff31351 ] && echo "   dry: portal.py untouched"
run install REPAIR_PY="$R/repair_ok.py"; grep -E "^\[[0-9]/9\]|DONE|VERIFIED|cron now" "$R/out_install.txt" | cut -c1-160; [ -f "$R/root/portal/calls_console.py" ] && echo "   placed: calls_console.py there"; grep -c "7-22" "$R/crontab.txt" | sed 's/^/   crontab lines with 7-22: /'; grep -c "systemctl restart" "$R/log_install.txt" | sed 's/^/   restarts: /'; [ -e "$R/deploy/_off/DOCTOR_AUTO_OFF" ] && echo "   !! OFF left" || echo "   OFF cleared"; [ -d "$R/deploy/.lock" ] && echo "   !! lock left" || echo "   lock released"
run again REPAIR_PY="$R/repair_ok.py"
fresh; cp "$R/root/wa/portal_console.py" "$R/x"; echo "# changed" >> "$R/root/wa/portal_console.py"; run changed REPAIR_PY="$R/repair_ok.py"
fresh; cp -p "$KDIR/calls_console.py" "$R/root/portal/calls_console.py"; run half REPAIR_PY="$R/repair_ok.py"
fresh; mkdir -p "$R/kitc"; cp -rp "$KDIR/." "$R/kitc/"; echo "#x" >> "$R/kitc/calls_console.py"; export REH_LOG="$R/log_corrupt.txt"; : > "$REH_LOG"; (env PATH="$R/bin:$PATH" APY="$PY" VPY="$PY" ROOT="$R/root" LOCK="$R/deploy/.lock" OFFSW="$R/deploy/_off/DOCTOR_AUTO_OFF" SKIP_WINDOW=1 bash "$R/kitc/install_S698_CALLS_R1.sh" > "$R/out_corrupt.txt" 2>&1; echo "== corrupt: exit $?: $(tail -1 "$R/out_corrupt.txt" | cut -c1-120)")
fresh; echo "OTHER_KIT 2026-11-02" > "$R/deploy/_off/DOCTOR_AUTO_OFF"; run otheroff REPAIR_PY="$R/repair_ok.py"; [ "$(head -c 9 "$R/deploy/_off/DOCTOR_AUTO_OFF")" = "OTHER_KIT" ] && echo "   someone else's switch kept"
fresh; run journalred REPAIR_PY="$R/repair_ok.py" REH_JOURNAL_RED=1; [ "$(md5sum "$R/root/portal/portal.py" | cut -c1-8)" = 4ff31351 ] && [ ! -e "$R/root/portal/calls_console.py" ] && echo "   restored: portal.py at FROM, the new file removed"; [ -d "$R/deploy/.lock" ] && echo "   !! lock left" || echo "   lock released"
fresh; run red9 REPAIR_PY="$R/repair_ok.py" REHEARSE_RED_AT=9; [ "$(md5sum "$R/root/wa/call-hook/call_hook_capture.py" | cut -c1-8)" = b8a1a293 ] && echo "   restored: the hook at FROM"; grep -c "systemctl restart" "$R/log_red9.txt" | sed 's/^/   restarts (incl. the restore): /'
fresh; run repairbad REPAIR_PY="$R/repair_bad.py"; grep -q "THE REPAIR DID NOT VERIFY" "$R/out_repairbad.txt" && echo "   the repair's failure said loudly, the install went on" ; grep -q "DONE" "$R/out_repairbad.txt" && echo "   DONE still reached"
fresh; run skiprepair SKIP_REPAIR=1; grep -q "SKIPPED at your word" "$R/out_skiprepair.txt" && echo "   repair skipped on SKIP_REPAIR=1"
echo "rehearsal root: $R (outputs out_*.txt)"
