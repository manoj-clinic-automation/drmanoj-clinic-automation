#!/bin/bash
# =============================================================================
#  S234_PAYMENT_REGISTER · install.sh · v1
#
#  Puts payments_register.py on the box, proves it against the box's own pulled
#  copy of the sheet, and only then switches on the 02:05 schedule.
#
#  It is safe to run twice. It is safe to stop. It stops dead at the first
#  thing that does not go as expected, and when it stops it has changed
#  nothing that matters and it prints the line that puts things back.
#
#  IT NEVER TOUCHES AN EXISTING TABLE. Everything it creates in finance.db is
#  new and named payment_register*; no existing table, view or row is read for
#  writing, altered or dropped. If this whole kit were deleted tomorrow the
#  books would be exactly as they are today.
#
#  Roots are overridable so the walk can drive this script in a sandbox.
# =============================================================================
set -u

FIN_ROOT="${FIN_ROOT:-/root/finance}"
SHEETS_ROOT="${SHEETS_ROOT:-/root/state_backup/sheets}"
KIT_DIR="${KIT_DIR:-/root/deploy/repo/deploy_kits/S234_PAYMENT_REGISTER}"
PY="${PY:-/root/wa/venv/bin/python3}"
CRON_ON="${CRON_ON:-1}"
LOG="${LOG:-/root/finance/payments_register.log}"

TARGET="$FIN_ROOT/payments_register.py"
BOOK="$SHEETS_ROOT/payment_register"
STAGE=0

say()  { printf '%s\n' "$*"; }
stage(){ STAGE=$((STAGE+1)); printf '\n[%d] %s\n' "$STAGE" "$*"; }
stop() {
  printf '\n!! STOPPED at stage %d: %s\n' "$STAGE" "$1"
  printf '   Nothing was scheduled. Send me everything printed above.\n'
  if [ -n "${2:-}" ]; then printf '   To put things back:\n   %s\n' "$2"; fi
  exit 1
}

say "S234_PAYMENT_REGISTER — install"
say "  finance root  $FIN_ROOT"
say "  sheets root   $SHEETS_ROOT"
say "  kit           $KIT_DIR"

stage "the kit is where it should be"
[ -f "$KIT_DIR/payments_register.py" ] || stop \
  "$KIT_DIR/payments_register.py is not there. The deploy clone was not pulled — run the first line again."
say "    ok"

stage "python is the one this box uses"
[ -x "$PY" ] || stop "$PY is not there or not executable."
"$PY" -c 'import sqlite3,csv,json,hashlib' 2>/dev/null || stop \
  "$PY cannot import the standard modules this script needs."
say "    ok  $($PY -V 2>&1)"

stage "the finance directory and its database"
[ -d "$FIN_ROOT" ] || stop "$FIN_ROOT does not exist."
if [ -f "$FIN_ROOT/finance.db" ]; then
  say "    ok  finance.db is there ($(du -h "$FIN_ROOT/finance.db" | cut -f1))"
else
  say "    note: no finance.db yet — it will be created on first ingest"
fi

stage "the nightly pull has produced a copy of the Payment Register"
[ -d "$BOOK" ] || stop \
  "$BOOK does not exist. This table is fed by sheets_pull.py; that job must have run for the payment_register book at least once. Run: $PY /root/state_backup/sheets_pull.py run"
CSV_COUNT=$(find "$BOOK" -maxdepth 1 -name '*.csv' | wc -l)
[ "$CSV_COUNT" -ge 1 ] || stop "$BOOK holds no CSV."
say "    ok  $CSV_COUNT csv in $BOOK"

stage "the script's own selftest, before it is installed anywhere"
OUT=$("$PY" "$KIT_DIR/payments_register.py" selftest 2>&1) || stop \
  "the selftest did not pass. It is printed above."
printf '%s\n' "$OUT" | tail -2
printf '%s\n' "$OUT" | grep -q ', 0 failures' || stop \
  "the selftest reported failures."

stage "a dated copy of whatever is already in place"
if [ -f "$TARGET" ]; then
  BK="$TARGET.bak_$(date +%Y%m%d_%H%M%S)"
  \cp "$TARGET" "$BK" || stop "could not copy $TARGET aside."
  say "    kept  $BK"
else
  say "    nothing to keep — this is a first install"
fi

stage "put the script in place"
\cp "$KIT_DIR/payments_register.py" "$TARGET" || stop "could not copy into $FIN_ROOT."
chmod 0700 "$TARGET"
say "    ok  $TARGET"
say "    md5 $(md5sum "$TARGET" | cut -d' ' -f1)"

stage "a rehearsal against a THROWAWAY database — the real one is not touched"
TMPDB=$(mktemp -d)/rehearse.db
"$PY" "$TARGET" ingest --db "$TMPDB" --sheets-dir "$SHEETS_ROOT" || stop \
  "the rehearsal refused. The reason is printed above; the real database was never opened."
REH=$("$PY" "$TARGET" status --db "$TMPDB" | sed -n '2,3p')
say "$REH"
rm -rf "$(dirname "$TMPDB")"

stage "the real ingest into finance.db"
"$PY" "$TARGET" ingest --db "$FIN_ROOT/finance.db" --sheets-dir "$SHEETS_ROOT" || stop \
  "the real ingest refused. The reason is printed above. Nothing was written; the cron was not added." \
  "rm -f $TARGET"

stage "what the table now holds"
"$PY" "$TARGET" status --db "$FIN_ROOT/finance.db" || stop "status could not read the table back."

if [ "$CRON_ON" = "1" ]; then
  stage "the 02:05 schedule — twenty minutes after the 01:45 pull"
  ( crontab -l 2>/dev/null | grep -v 'payments_register.py'
    echo "5 2 * * * $PY $TARGET ingest >> $LOG 2>&1" ) | crontab - \
    || stop "could not write the crontab." "rm -f $TARGET"
  crontab -l | grep -q 'payments_register.py' || stop "the cron line did not stick."
  say "    ok  $(crontab -l | grep payments_register.py)"
else
  stage "schedule skipped (CRON_ON=0)"
fi

cat <<EOF

=============================================================================
DONE. Copy these three lines back to me and nothing else:
=============================================================================

md5:   $(md5sum "$TARGET" | cut -d' ' -f1)
rows:  $("$PY" "$TARGET" status --db "$FIN_ROOT/finance.db" 2>/dev/null | sed -n 's/^  rows *//p')
cron:  $(crontab -l 2>/dev/null | grep payments_register.py || echo 'not scheduled')

To undo everything this kit did:
  crontab -l | grep -v payments_register.py | crontab -
  rm -f $TARGET
The payment_register tables can be left where they are — they are derived from
the sheet and hold nothing that is not also in Google.
EOF
exit 0
