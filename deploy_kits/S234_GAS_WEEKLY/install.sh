#!/bin/bash
# =============================================================================
#  S234_GAS_WEEKLY · install.sh · v1
#
#  Puts gas_export.py on the box, adds the GAS= line to the conf the S230
#  bundle and S233 pull already use, proves it against Google, runs it once,
#  and only then switches on the weekly schedule.
#
#  ANY failure puts the conf back byte for byte. A failed run leaves the
#  nightly and the weekly exactly as they were.
#
#  It exports and never writes to Google: no project edited, no trigger read
#  or changed, no Script Property touched. And the Clinic Callback Tracker is
#  DENYLISTED IN THE CODE — HOLD 2 says "no re-export", and a hold that lives
#  only in a document is one config edit away from being broken.
# =============================================================================
set -u

CONF="${CONF:-/root/state_backup/clinic_state_backup.conf}"
export CONF
DEST="${DEST:-/root/state_backup}"
KIT_DIR="${KIT_DIR:-/root/deploy/repo/deploy_kits/S234_GAS_WEEKLY}"
PY="${PY:-/root/wa/venv/bin/python3}"
GAS_DIR="${GAS_DIR:-/root/state_backup/gas}"
CRON_ON="${CRON_ON:-1}"
LOG="${LOG:-/root/state_backup/gas_export.log}"
export GAS_DIR

TARGET="$DEST/gas_export.py"
STAGE=0
RESTORED=""

say()  { printf '%s\n' "$*"; }
stage(){ STAGE=$((STAGE+1)); printf '\n[%d] %s\n' "$STAGE" "$*"; }

restore() {
  if [ -n "$RESTORED" ] && [ -f "$RESTORED" ]; then
    \cp "$RESTORED" "$CONF" && say "   the conf has been put back exactly as it was."
  fi
}

stop() {
  printf '\n!! STOPPED at stage %d: %s\n' "$STAGE" "$1"
  restore
  if [ -n "${2:-}" ]; then printf '   To put things back:\n   %s\n' "$2"; fi
  printf '   Nothing was scheduled. Send me everything printed above.\n'
  exit 1
}

say "S234_GAS_WEEKLY — install"

stage "the kit is where it should be"
[ -f "$KIT_DIR/gas_export.py" ] || stop \
  "$KIT_DIR/gas_export.py is not there. The deploy clone was not pulled — run the first line again."
[ -f "$KIT_DIR/GAS_LINE.txt" ] || stop "$KIT_DIR/GAS_LINE.txt is not there."
say "    ok"

stage "python and the google libraries this box already has"
[ -x "$PY" ] || stop "$PY is not there or not executable."
"$PY" -c 'from google.oauth2 import service_account; import google.auth.transport.requests' 2>/dev/null \
  || stop "$PY cannot import the google auth libraries. Use /root/wa/venv/bin/python3 — the system python does not have them."
say "    ok  $($PY -V 2>&1)"

stage "the conf, and the S230/S233 jobs it belongs to"
[ -f "$CONF" ] || stop "$CONF is not there."
grep -q '^SA_JSON=' "$CONF" || stop "the conf has no SA_JSON= line."
say "    ok"

stage "the script's own selftest, before it is installed anywhere"
OUT=$("$PY" "$KIT_DIR/gas_export.py" selftest 2>&1) || stop \
  "the selftest did not pass. It is printed above."
printf '%s\n' "$OUT" | tail -2
printf '%s\n' "$OUT" | grep -q ', 0 failures' || stop "the selftest reported failures."

stage "put the script in place"
if [ -f "$TARGET" ]; then
  \cp "$TARGET" "$TARGET.bak_$(date +%Y%m%d_%H%M%S)" || stop "could not copy $TARGET aside."
  say "    kept a dated copy of the previous one"
fi
\cp "$KIT_DIR/gas_export.py" "$TARGET" || stop "could not copy into $DEST."
chmod 0700 "$TARGET"
say "    ok  $TARGET"
say "    md5 $(md5sum "$TARGET" | cut -d' ' -f1)"

stage "the GAS= line in the conf"
if grep -q '^GAS=' "$CONF"; then
  say "    already there — left exactly as it is."
else
  RESTORED="$CONF.bak_$(date +%Y%m%d_%H%M%S)"
  \cp "$CONF" "$RESTORED" || stop "could not copy the conf aside."
  say "    kept  $RESTORED"
  cat "$KIT_DIR/GAS_LINE.txt" >> "$CONF" || stop "could not append to the conf."
  N=$(grep -c '^GAS=' "$CONF")
  [ "$N" = "1" ] || stop "expected exactly one GAS= line, found $N."
  say "    added, one GAS= line, $(grep '^GAS=' "$CONF" | tr ',' '\n' | wc -l) project(s)"
fi

stage "preflight — can the service account open each project?"
if ! "$PY" "$TARGET" preflight; then
  SA=$("$PY" - <<'PYX' 2>/dev/null
import json, os, re
sa = ""
for line in open(os.environ["CONF"]):
    m = re.match(r"\s*SA_JSON\s*=\s*(.+)", line)
    if m:
        sa = m.group(1).strip().strip('"').strip("'")
try:
    print(json.load(open(sa))["client_email"])
except Exception:
    print("(could not read the service-account address)")
PYX
)
  say ""
  say "   A project could not be opened. The line above says which one and"
  say "   whether it was a PERMISSION refusal or a RATE refusal."
  say ""
  say "   If it says PERMISSION: in Google, open that script project, press"
  say "   Share, and give VIEWER access to exactly this address:"
  say ""
  say "       $SA"
  say ""
  say "   If it says RATE LIMIT: the sharing is fine, change nothing, and run"
  say "   the installer again in a few minutes."
  stop "not every project is reachable yet."
fi

stage "the first real export, and the two drift checks"
"$PY" "$TARGET" run || stop "the export did not finish cleanly. Its own words are above." \
  "rm -f $TARGET"

stage "what is on disk now"
"$PY" "$TARGET" list || stop "the export list could not be read back."

if [ "$CRON_ON" = "1" ]; then
  stage "the weekly schedule — Sunday 02:20, after the 01:45 pull and the 01:50 bundle"
  ( crontab -l 2>/dev/null | grep -v 'gas_export.py'
    echo "20 2 * * 0 $PY $TARGET run >> $LOG 2>&1" ) | crontab - \
    || stop "could not write the crontab." "rm -f $TARGET"
  crontab -l | grep -q 'gas_export.py' || stop "the cron line did not stick."
  say "    ok  $(crontab -l | grep gas_export.py)"
else
  stage "schedule skipped (CRON_ON=0)"
fi

cat <<EOF

=============================================================================
DONE. Copy these three lines back to me and nothing else:
=============================================================================

md5:      $(md5sum "$TARGET" | cut -d' ' -f1)
projects: $(grep '^GAS=' "$CONF" | tr ',' '\n' | wc -l)
cron:     $(crontab -l 2>/dev/null | grep gas_export.py || echo 'not scheduled')

The exports land in $GAS_DIR and ride the 01:50 bundle already.

To undo:
  crontab -l | grep -v gas_export.py | crontab -
  sed -i '/^GAS=/d' $CONF
  rm -f $TARGET
EOF
exit 0
