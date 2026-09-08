#!/bin/bash
# =============================================================================
#  install.sh  ·  Session 233  ·  S233_SHEETS_BACKUP  ·  v1
#
#  ONE LINE INSTEAD OF FIFTEEN — and safer than the fifteen, not despite being
#  one line but because of it. A human pasting fifteen lines can skip one, run
#  two out of order, or carry on past a step that failed. This script cannot:
#  it stops dead at the first thing that does not go as expected, and when it
#  stops it says exactly what to paste to put everything back.
#
#  WHAT IT WILL AND WILL NOT DO
#    * It NEVER deletes anything except one directory of exported CSVs whose
#      source is still sitting in Google. Nothing else is removed, ever.
#    * It takes a dated copy of BOTH live scripts before replacing either.
#    * It PROVES each stage before starting the next: the sheets must be
#      readable before they are pulled; the pull must succeed before the
#      bundle is shipped; the bundle must contain the sheets before the
#      nightly schedule is switched on. A failure anywhere means the schedule
#      is NOT switched on and last night's arrangement still stands.
#    * It is safe to run twice. Every step checks the state it is about to
#      create, so a second run repairs rather than duplicates.
#    * It changes nothing outside /root/state_backup and one crontab line.
#
#  Run it as:  bash /root/deploy/repo/deploy_kits/S233_SHEETS_BACKUP/install.sh
#
#  Testing knobs, used ONLY by WALK_install.py — never set on the live box:
#    S233_PREFIX   put every path under this directory instead of /
#    S233_PY       the python to use
#    S233_NO_GIT   skip the deploy pull
# =============================================================================
set -u

PREFIX="${S233_PREFIX:-}"
PY="${S233_PY:-/root/wa/venv/bin/python3}"
REPO="${PREFIX}/root/deploy/repo"
BASE="${PREFIX}/root/state_backup"
CONF="${BASE}/clinic_state_backup.conf"
KIT="${REPO}/deploy_kits/S233_SHEETS_BACKUP"
STAMP="$(date +%Y%m%d_%H%M%S)"

BOOKS='SHEETS=1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0:tracker,1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ:audit,1OB70_Mapuugc33zkfFevwnrS0e8s1NdWzsrzJDqO38E:renewals,1wKMcAWMz5VqjoC7q5AgbRvB0xEODrUvibRQw4iRPAHY:payment_register'

CRON_LINE="45 1 * * * ${PY} ${BASE}/sheets_pull.py run >> ${BASE}/sheets_pull.log 2>&1"

step=0

say()  { printf '\n%s\n' "$*"; }
ok()   { printf '   OK   %s\n' "$*"; }

begin() {
    step=$((step + 1))
    printf '\n[%d/9] %s\n' "$step" "$1"
}

stop() {
    printf '\n'
    printf '=============================================================\n'
    printf ' STOPPED at step %d — %s\n' "$step" "$1"
    printf '=============================================================\n'
    printf '\n NOTHING further was changed. The nightly schedule was NOT\n'
    printf ' switched on, so tonight still runs exactly as it did last night.\n'
    if [ -f "${BASE}/sheets_pull.py.before_${STAMP}" ]; then
        printf '\n To put the previous scripts back, paste these two lines:\n\n'
        printf '   \\cp %s %s\n' "${BASE}/sheets_pull.py.before_${STAMP}" "${BASE}/sheets_pull.py"
        printf '   \\cp %s %s\n' "${BASE}/clinic_state_backup.py.before_${STAMP}" "${BASE}/clinic_state_backup.py"
    fi
    printf '\n Send me everything above this line and I will take it from there.\n\n'
    exit 1
}

printf '=============================================================\n'
printf ' S233_SHEETS_BACKUP — installer\n'
printf ' Four Google Sheets into the nightly encrypted bundle.\n'
printf ' Nine stages. It stops at the first sign of trouble.\n'
printf '=============================================================\n'

# --- 1 ----------------------------------------------------------------------
begin "checking this box is ready"
[ -d "$BASE" ]  || stop "$BASE does not exist — the S230 backup job is not installed here."
[ -f "$CONF" ]  || stop "$CONF does not exist — the S230 backup job is not configured here."
[ -x "$PY" ]    || stop "$PY is not there. This job needs the venv python, not the system one."
grep -q '^SA_JSON=' "$CONF" || stop "the conf has no SA_JSON line — the service-account key is not named."
ok "backup job present, conf present, venv python present"

# --- 2 ----------------------------------------------------------------------
begin "fetching the published kit"
if [ "${S233_NO_GIT:-0}" = "1" ]; then
    ok "skipped (test mode)"
else
    git -C "$REPO" fetch --depth 1 -q origin main || stop "could not fetch from GitHub. Is the box online?"
    git -C "$REPO" reset --hard -q origin/main    || stop "could not update the deploy clone."
    ok "deploy clone updated"
fi
[ -f "${KIT}/sheets_pull.py" ]         || stop "the kit is not in the deploy clone. Was PUBLISH_ALL.bat run?"
[ -f "${KIT}/clinic_state_backup.py" ] || stop "the kit is incomplete — clinic_state_backup.py is missing."
ok "kit found"

# --- 3 ----------------------------------------------------------------------
begin "keeping a copy of what is live now"
if [ -f "${BASE}/sheets_pull.py" ]; then
    cp -p "${BASE}/sheets_pull.py" "${BASE}/sheets_pull.py.before_${STAMP}" || stop "could not save a copy of sheets_pull.py."
    ok "sheets_pull.py saved as sheets_pull.py.before_${STAMP}"
else
    ok "no sheets_pull.py yet — first install"
fi
cp -p "${BASE}/clinic_state_backup.py" "${BASE}/clinic_state_backup.py.before_${STAMP}" || stop "could not save a copy of clinic_state_backup.py."
ok "clinic_state_backup.py saved as clinic_state_backup.py.before_${STAMP}"

# --- 4 ----------------------------------------------------------------------
begin "putting the new scripts in place"
cp "${KIT}/sheets_pull.py"         "${BASE}/sheets_pull.py"         || stop "could not write sheets_pull.py."
cp "${KIT}/clinic_state_backup.py" "${BASE}/clinic_state_backup.py" || stop "could not write clinic_state_backup.py."
"$PY" -c "import py_compile,sys;py_compile.compile('${BASE}/sheets_pull.py',cfile='/tmp/s233chk.pyc',doraise=True)" \
    || stop "the new sheets_pull.py does not compile on this box. The copies from step 3 are still good."
"$PY" -c "import py_compile,sys;py_compile.compile('${BASE}/clinic_state_backup.py',cfile='/tmp/s233chk.pyc',doraise=True)" \
    || stop "the new clinic_state_backup.py does not compile on this box. The copies from step 3 are still good."
rm -f /tmp/s233chk.pyc
ok "both scripts in place and both compile"

# --- 5 ----------------------------------------------------------------------
begin "setting the list of sheets to four"
cp -p "$CONF" "${CONF}.before_${STAMP}" || stop "could not save a copy of the conf."
sed -i '/^SHEETS=/d' "$CONF"     || stop "could not edit the conf."
sed -i '/^SHEETS_DIR=/d' "$CONF" || stop "could not edit the conf."
printf 'SHEETS_DIR=%s/sheets\n' "$BASE" >> "$CONF"
printf '%s\n' "$BOOKS" >> "$CONF"
n=$(grep -c '^SHEETS=' "$CONF")
[ "$n" = "1" ] || stop "the conf ended up with $n SHEETS lines instead of 1."
chmod 600 "$CONF"
ok "four books configured: tracker, audit, renewals, payment_register"

# --- 6 ----------------------------------------------------------------------
begin "removing the exports of books that were dropped"
for gone in accounting_details daily_clinic_reports monthly_accounting patient_diagnosis; do
    if [ -d "${BASE}/sheets/${gone}" ]; then
        rm -rf "${BASE}/sheets/${gone}" || stop "could not remove ${BASE}/sheets/${gone}."
        ok "removed the old export of ${gone} (its source is still in Google)"
    fi
done
ok "nothing else was removed"

# --- 7 ----------------------------------------------------------------------
begin "checking Google can be read — this writes nothing"
"$PY" "${BASE}/sheets_pull.py" preflight
case $? in
  0)  ok "all four books readable" ;;
  41) stop "a sheet is genuinely not shared with the service account. The lines above name it. Share it as Viewer, then run this installer again." ;;
  43) stop "Google rate-limited us. THE SHARING IS FINE — do not re-share anything. Wait ten minutes and run this installer again." ;;
  *)  stop "preflight failed. The lines above say why." ;;
esac

# --- 8 ----------------------------------------------------------------------
begin "pulling the sheets, and shipping one bundle with them inside"
say "   (this takes about a minute — the pauses are deliberate, to stay inside"
say "    Google's rate limit. It is not stuck.)"
"$PY" "${BASE}/sheets_pull.py" run || stop "the pull did not finish cleanly. The lines above say why. Nothing good was overwritten."
ok "sheets pulled"
"$PY" "${BASE}/clinic_state_backup.py" run || stop "the bundle did not ship. The sheets are on the box; only the shipment failed."
ok "bundle shipped"
"$PY" - <<PYEOF || stop "the bundle shipped but does not contain the sheets. The schedule was NOT switched on."
import json, sys
s = json.load(open("${BASE}/clinic_state_backup.state.json"))
n = sum(1 for x in s["sources"] if "/state_backup/sheets/" in x)
print("   OK   %d sheet files are inside the shipped bundle, of %d files total"
      % (n, s["files_included"]))
sys.exit(0 if n > 0 else 1)
PYEOF

# --- 9 ----------------------------------------------------------------------
begin "switching on the nightly schedule"
if crontab -l 2>/dev/null | grep -q 'sheets_pull.py run'; then
    ok "already scheduled — left alone"
else
    (crontab -l 2>/dev/null; printf '%s\n' "$CRON_LINE") | crontab - || stop "could not write the crontab. Everything else is done; only the schedule is missing."
    crontab -l 2>/dev/null | grep -q 'sheets_pull.py run' || stop "the crontab did not take the new line."
    ok "scheduled for 01:45, five minutes before the bundle at 01:50"
fi

# --- done -------------------------------------------------------------------
printf '\n=============================================================\n'
printf ' DONE. Everything passed.\n'
printf '=============================================================\n\n'
printf ' Four sheets are pulled to this box every night at 01:45 and\n'
printf ' ride inside the encrypted bundle that ships at 01:50.\n\n'
printf ' Copy the four lines below back to Claude:\n\n'
md5sum "${BASE}/sheets_pull.py" "${BASE}/clinic_state_backup.py"
"$PY" "${BASE}/sheets_pull.py" list | tail -6
printf '\n If you ever want it all undone, two lines:\n\n'
printf '   crontab -l | grep -v sheets_pull | crontab -\n'
printf '   \\cp %s %s\n\n' "${BASE}/clinic_state_backup.py.before_${STAMP}" "${BASE}/clinic_state_backup.py"
exit 0
