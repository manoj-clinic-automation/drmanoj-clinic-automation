#!/bin/bash
# rehearse_s895.sh -- the installer on a MADE-UP root (no live file). Six scenes; every one must end as said.
#   bash rehearse_s895.sh <kit_dir> <bundle_root (holds finance/ and wa/ at the FROM bytes)>
set -u
KIT="$(cd "$1" && pwd)"; BUNDLE="$(cd "$2" && pwd)"
R="$(mktemp -d /tmp/s895_reh.XXXXXX)"; fails=0
ok() { echo "  ok   $1"; }; bad() { echo "  FAIL $1"; fails=$((fails+1)); }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
mkroot() {   # a fresh made-up box
  rm -rf "$R/box"; mkdir -p "$R/box/finance/_off" "$R/box/wa" "$R/box/venv/bin" "$R/box/stubs" "$R/box/bin"
  cp -p "$BUNDLE/finance/docterz_ingest.py" "$R/box/finance/"; cp -p "$BUNDLE/wa/push_followups_vps.py" "$BUNDLE/wa/followup_receiver.py" "$R/box/wa/"
  echo "FU_UPLOAD_SECRET=made-up-secret-for-the-rehearsal" > "$R/box/wa/.env"; echo "PATIENT_FP_SALT=made-up-salt" > "$R/box/finance/patient_fp.env"
  echo '{"type":"service_account","made_up":true}' > "$R/box/wa/made-up-key.json"
  : > "$R/box/stubs/gspread.py"; : > "$R/box/stubs/flask.py"; : > "$R/box/stubs/requests.py"
  printf '#!/bin/bash\nexport PYTHONPATH="%s${PYTHONPATH:+:$PYTHONPATH}"\nexec /usr/bin/python3 "$@"\n' "$R/box/stubs" > "$R/box/venv/bin/python3"; chmod +x "$R/box/venv/bin/python3"
  printf '#!/bin/bash\necho "pip $*" >> "%s/pip.log"\n' "$R/box" > "$R/box/venv/bin/pip"; chmod +x "$R/box/venv/bin/pip"
  printf '#!/bin/bash\necho "systemctl $*" >> "%s/systemctl.log"; exit 0\n' "$R/box" > "$R/box/bin/systemctl"; chmod +x "$R/box/bin/systemctl"
  for i in $(seq 1 25); do echo "$i * * * * /bin/true # made-up line $i"; done > "$R/box/crontab.txt"
  printf '#!/bin/bash\nif [ "$1" = "-l" ]; then cat "%s/crontab.txt"; else cat "$1" > "%s/crontab.txt"; fi\n' "$R/box" "$R/box" > "$R/box/bin/crontab"; chmod +x "$R/box/bin/crontab"
}
run() {  # run the installer with the box's overrides; $1 = extra env, rest = args
  local extra="$1"; shift
  env FIN="$R/box/finance" WA="$R/box/wa" FUT="$R/box/followup_tracker" VENV="$R/box/venv" SYSTEMCTL="$R/box/bin/systemctl" CRONTAB="$R/box/bin/crontab" \
      PING_CMD="${PING_OK:-echo ok}" INGEST_DRY_CMD="echo read 0, skipped 0 unchanged, 0 with no Day Revenue sheet, failed 0; (rehearsal)" $extra \
      bash "$KIT/install_S895_TRACKER_SERVER_KIT.sh" "$@" > "$R/out.txt" 2>&1; echo $?
}
TO_ING="$(awk '$2=="finance/docterz_ingest.py"{print $1}' "$KIT/TO_PINS.md5")"
FROM_ING="$(m5 "$BUNDLE/finance/docterz_ingest.py")"

echo "== A · install on a clean box"
mkroot; rc=$(run "")
grep -q 'DONE (OFF)' "$R/out.txt" && [ "$rc" = 0 ] && ok "DONE (OFF), exit 0" || { bad "install: rc=$rc"; tail -3 "$R/out.txt"; }
[ "$(m5 "$R/box/finance/docterz_ingest.py")" = "$TO_ING" ] && ok "docterz_ingest at its TO pin" || bad "ingest not at TO"
[ -f "$R/box/finance/docterz_ingest.py.bak_S895_${FROM_ING:0:8}" ] && ok "bak kept beside it" || bad "no bak"
[ -f "$R/box/followup_tracker/OFF" ] && [ -f "$R/box/followup_tracker/processor.py" ] && ok "tracker folder placed, OFF present" || bad "tracker folder"
[ "$(grep -c 'S895_TRACKER' "$R/box/crontab.txt")" = 2 ] && [ "$(grep -c . "$R/box/crontab.txt")" = 27 ] && ok "two cron lines, 25 old lines kept" || bad "cron"
grep -q 'restart clinic-followup-receiver' "$R/box/systemctl.log" && ok "receiver restarted" || bad "no restart"
grep -q 'FU_UPLOAD_SECRET=' "$R/box/followup_tracker/fu_upload.env" && [ -L "$R/box/followup_tracker/patient_fp.env" ] && ok "secret file and salt link in place" || bad "env"
echo "== B · install again on the same box -> refused, nothing changed"
rc=$(run ""); grep -q 'STOP, nothing installed' "$R/out.txt" && [ "$rc" = 1 ] && ok "refused at [2/6]" || bad "second install not refused (rc=$rc)"
echo "== C · undo"
rc=$(run "" --undo); grep -q 'UNDONE' "$R/out.txt" && [ "$rc" = 0 ] && ok "UNDONE" || { bad "undo rc=$rc"; tail -2 "$R/out.txt"; }
[ "$(m5 "$R/box/finance/docterz_ingest.py")" = "$FROM_ING" ] && ok "ingest back at FROM" || bad "ingest not restored"
[ "$(grep -c 'S895_TRACKER' "$R/box/crontab.txt")" = 0 ] && [ "$(grep -c . "$R/box/crontab.txt")" = 25 ] && ok "cron lines out, 25 kept" || bad "cron undo"
[ ! -d "$R/box/followup_tracker" ] && ok "empty tracker folder removed" || bad "tracker folder left"
echo "== D · undo again -> nothing to undo"
rc=$(run "" --undo); grep -q 'nothing to undo' "$R/out.txt" && ok "says nothing to undo" || bad "undo again"
echo "== E · red rollback: the receiver stays silent after the restart"
mkroot; rc=$(PING_OK="echo dead" run "")
grep -q 'RED after placing' "$R/out.txt" && [ "$rc" = 1 ] && ok "went RED" || bad "no RED (rc=$rc)"
[ "$(m5 "$R/box/finance/docterz_ingest.py")" = "$FROM_ING" ] && [ ! -d "$R/box/followup_tracker" ] && [ "$(grep -c 'S895_TRACKER' "$R/box/crontab.txt")" = 0 ] && ok "everything back (files, folder, cron)" || bad "rollback incomplete"
echo "== F · a seeded folder survives an undo"
mkroot; run "" >/dev/null; mkdir -p "$R/box/followup_tracker/data"; echo "a,b" > "$R/box/followup_tracker/data/followup_ledger.csv"
rc=$(run "" --undo); [ -f "$R/box/followup_tracker/data/followup_ledger.csv" ] && [ -f "$R/box/followup_tracker/OFF" ] && ok "data kept, OFF set" || bad "seeded folder lost"
echo "== G · tampered kit -> SUMS gate"
cp -rp "$KIT" "$R/kit2"; echo "# x" >> "$R/kit2/server_runner.py"; mkroot
rc=$(env FIN="$R/box/finance" WA="$R/box/wa" FUT="$R/box/followup_tracker" VENV="$R/box/venv" SYSTEMCTL="$R/box/bin/systemctl" CRONTAB="$R/box/bin/crontab" bash "$R/kit2/install_S895_TRACKER_SERVER_KIT.sh" 2>&1 | grep -c 'SUMS.md5 gate failed')
[ "$rc" = 1 ] && [ "$(m5 "$R/box/finance/docterz_ingest.py")" = "$FROM_ING" ] && ok "refused, nothing installed" || bad "tamper not refused"
echo "== H · live file not at FROM -> refused before anything"
mkroot; echo "# drift" >> "$R/box/wa/followup_receiver.py"; rc=$(run ""); grep -q 'not 384e9ed8' "$R/out.txt" && [ ! -d "$R/box/followup_tracker" ] && ok "refused on the receiver's pin, nothing placed" || bad "drift not refused"
rm -rf "$R"
echo "REHEARSAL: $fails failure(s)"; exit $fails
