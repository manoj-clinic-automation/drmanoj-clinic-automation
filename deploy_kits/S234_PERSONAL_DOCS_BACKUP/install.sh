#!/bin/bash
# =============================================================================
#  S234_PERSONAL_DOCS_BACKUP · install.sh · v1
#
#  THE THIRD PERSONAL BOOK. Detour item 2 of D432.
#
#  `PERSONAL_DOCS_ID` — the Personal Documents sheet the Janitor's Code.gs
#  updates, holding identity-document rows with expiry and lead-time columns.
#  PERSONAL_GOOGLE_PLANE_v1_S233 §4: "It has no backup, it is not in the S233
#  pull, and no census, brief or register had ever named it." It is the last of
#  the three personal books still with exactly one copy, in one account.
#
#  WHAT THIS DOES: adds that one book to the SHEETS list the S233 pull already
#  reads, so it rides the 01:45 pull and the 01:50 AES-256 bundle with the other
#  four. NO NEW MECHANISM, NO NEW JOB, NO NEW KEY, and not one line of
#  sheets_pull.py or clinic_state_backup.py is changed.
#
#  WHY IT IS A SECOND COPY AND NOT A PRETEND ONE: the book lives in the owner's
#  PERSONAL Google account; the encrypted bundle goes to the CLINIC account's
#  Drive. Different account, different credential, and encrypted in between —
#  which is the test S233 set when it ruled that a copy in the same account is
#  not a copy at all.
#
#  WHERE THE NUMBERS END UP, said plainly because they are identity documents:
#    * plaintext CSV at /root/state_backup/sheets/personal_docs/ on the VPS —
#      inside D429, the owner's own ruling that the VPS is a safe place for his
#      data, and on a box only he holds credentials for;
#    * inside the AES-256 bundle on the clinic Drive, never in plaintext there;
#    * NOWHERE ELSE. This kit writes nothing to git. D431 stands: the exports
#      and their books never enter the repository.
#
#  SAFETY: the conf is copied aside before it is touched, and ANY failure —
#  including the book simply not being shared yet — puts the original conf back
#  before exiting. A failed run leaves tonight's pull exactly as last night's.
#  Running it twice is safe; the second run says so and changes nothing.
# =============================================================================
set -u

CONF="${CONF:-/root/state_backup/clinic_state_backup.conf}"
export CONF
PULL="${PULL:-/root/state_backup/sheets_pull.py}"
BUNDLE="${BUNDLE:-/root/state_backup/clinic_state_backup.py}"
KIT_DIR="${KIT_DIR:-/root/deploy/repo/deploy_kits/S234_PERSONAL_DOCS_BACKUP}"
PY="${PY:-/root/wa/venv/bin/python3}"
SHEETS_ROOT="${SHEETS_ROOT:-/root/state_backup/sheets}"
STATE_JSON="${STATE_JSON:-/root/state_backup/clinic_state_backup.state.json}"
export SHEETS_ROOT STATE_JSON
LABEL="personal_docs"
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
  printf '   Tonight runs exactly as last night. Send me everything printed above.\n'
  exit 1
}

say "S234_PERSONAL_DOCS_BACKUP — install"

stage "the kit and the book id"
[ -f "$KIT_DIR/BOOK_ID.txt" ] || stop \
  "$KIT_DIR/BOOK_ID.txt is not there. The deploy clone was not pulled — run the first line again."
BOOK_ID=$(tr -d ' \t\r\n' < "$KIT_DIR/BOOK_ID.txt")
case "$BOOK_ID" in
  ????????????????????*) : ;;
  *) stop "BOOK_ID.txt does not hold a spreadsheet id." ;;
esac
say "    ok  a ${#BOOK_ID}-character id (not printed)"

stage "the S233 pull and bundle are where they should be"
[ -f "$CONF" ]   || stop "$CONF is not there."
[ -f "$PULL" ]   || stop "$PULL is not there — the S233 pull is not installed."
[ -f "$BUNDLE" ] || stop "$BUNDLE is not there — the S230 bundle is not installed."
[ -x "$PY" ]     || stop "$PY is not there or not executable."
say "    ok"

stage "is this book already in the list?"
if grep -q "$BOOK_ID" "$CONF"; then
  say "    it is already there. Nothing to do — this kit has already been run."
  say ""
  "$PY" "$PULL" list 2>/dev/null | sed -n '1,12p'
  exit 0
fi
N=$(grep -c '^SHEETS=' "$CONF")
[ "$N" = "1" ] || stop "expected exactly one SHEETS= line in the conf, found $N."
BEFORE=$(grep '^SHEETS=' "$CONF" | tr ',' '\n' | wc -l)
say "    not yet. The list holds $BEFORE book(s) today."

stage "keep a dated copy of the conf, so any failure is one copy back"
RESTORED="$CONF.bak_$(date +%Y%m%d_%H%M%S)"
\cp "$CONF" "$RESTORED" || stop "could not copy the conf aside."
say "    kept  $RESTORED"

stage "add the book to the list"
sed -i "s|^\(SHEETS=.*\)$|\1,$BOOK_ID:$LABEL|" "$CONF" || stop "could not edit the conf."
grep -q "$BOOK_ID:$LABEL" "$CONF" || stop "the edit did not take."
AFTER=$(grep '^SHEETS=' "$CONF" | tr ',' '\n' | wc -l)
[ "$AFTER" = "$((BEFORE + 1))" ] || stop \
  "the list should have gone from $BEFORE to $((BEFORE + 1)) books and reads $AFTER."
say "    ok  $BEFORE -> $AFTER books, one SHEETS= line"

stage "preflight — can the service account actually open it?"
if ! "$PY" "$PULL" preflight; then
  SA=$("$PY" - <<'PYEOF' 2>/dev/null
import json, os, re
conf = os.environ.get("CONF", "/root/state_backup/clinic_state_backup.conf")
sa = ""
for line in open(conf):
    m = re.match(r"\s*SA_JSON\s*=\s*(.+)", line)
    if m:
        sa = m.group(1).strip().strip('"').strip("'")
try:
    print(json.load(open(sa))["client_email"])
except Exception:
    print("(could not read the service-account address from %s)" % sa)
PYEOF
)
  say ""
  say "   The new book could not be opened. Almost always this means one thing:"
  say "   the sheet has not been SHARED with the service account yet."
  say ""
  say "   In Google, open your Personal Documents sheet, press Share, and give"
  say "   VIEWER access to exactly this address:"
  say ""
  say "       $SA"
  say ""
  say "   Then run this installer again. Nothing else is needed."
  stop "the new book is not reachable yet (the four existing books are unaffected)."
fi
say "    ok"

stage "the real pull, all books — about a minute, that is correct"
"$PY" "$PULL" run || stop "the pull did not finish cleanly. Its own words are above."

stage "the new book is on disk"
D="$SHEETS_ROOT/$LABEL"
[ -d "$D" ] || stop "$D was not written."
ROWS=$("$PY" - <<PYEOF
import json
m = json.load(open("$D/_BOOK.json"))
print(m.get("row_total", 0))
PYEOF
)
say "    ok  $D  ·  $ROWS row(s)"

stage "ship one bundle now, with it inside"
"$PY" "$BUNDLE" run || stop "the bundle run did not finish cleanly."
IN=$("$PY" - <<'PYX'
import json, os
s = json.load(open(os.environ["STATE_JSON"]))
mark = os.path.join(os.environ["SHEETS_ROOT"], "personal_docs") + os.sep
print(sum(1 for x in s["sources"] if mark in x))
PYX
)
[ "$IN" -ge 1 ] || stop "the bundle went out WITHOUT the new book's files in it."
say "    ok  $IN file(s) of the new book are inside the shipped bundle"

cat <<EOF

=============================================================================
DONE. Copy these three lines back to me and nothing else:
=============================================================================

books: $AFTER
rows:  $ROWS
inbundle: $IN

The nightly is unchanged — same 01:45 pull, same 01:50 bundle, one more book.

To undo: \cp $RESTORED $CONF
EOF
exit 0
