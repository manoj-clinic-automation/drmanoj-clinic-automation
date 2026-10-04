#!/bin/bash
# =============================================================================
# install_S472_MAHINE_KA_KAAM.sh -- session 293, 04-Oct-2026 -- Shavez's "Mahine ka kaam", a better flow (the owner's word)
#  CHAINED ON S471_PACKS_SEPTEMBER (refuses on the pin otherwise).
#  EDITS, by apply_s472.py (exact anchors on the real bytes; every anchor found exactly once):
#   /root/finance/packs.py                6738d65d (S471) -> 6099b525  a due day per item (column packs_item.due_day, seeded by
#                                          kind: Docterz the 1st, statements/scans the 5th, NEFT the 7th, hand-overs and the
#                                          accountant's things the 10th, the petty book the 3rd; the owner's own day wins);
#                                          late / due-today on every row; the tile's line (/finance/packs/api/checklist/line);
#                                          a hand-over ticked with a photo (multipart, jpeg/png, 8 MB, kept under the packs
#                                          folder; the photo door /finance/packs/handover/<month>/<name>); the owner's rename
#                                          carries a due day
#   /root/finance/packs_checklist.html    12ac3f27 -> 74598ba7  'Aaj ka kaam' first; 'N tak' on every row, late in red;
#                                          'Ho gaya — tick karein'; for a hand-over 'Photo ke saath ho gaya' (camera) and
#                                          'bina photo' behind a confirmation; 'photo ✓' on a done row
#   /root/portal/portal.py                1a9fb99d (S450) -> d9b7685f  the 'Mahine ka kaam' tile carries the live line
#                                          'N kaam baaki · M late · aaj: ...' (fail-soft: the static text stands)
#  NO WhatsApp: a staff message outside a patient's window needs an approved template and there is none for this; the tile
#  is where he already looks every day.  NOT TOUCHED: the owner's packs page (its Shavez section reads the same API and
#  gains the late/due words by it), the send, the shelf, the Sanjeevni files, every other tile.
# Walked first, on this box, hermetically (F-709): packs.py beside the box's readers in /tmp, an EMPTY database, a scratch
# packs folder, a throwaway Flask app with a made-up staff login; SHOWN on the old file that the checklist knew no due day.
# Restarts clinic-finance and clinic-portal (about 12 seconds); red after placing -> all three files are put back.
# DRY=1 places nothing. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S472_MAHINE_KA_KAAM"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; POR="$ROOT/portal"
FINURL="${FINURL:-http://127.0.0.1:8106}"; PORURL="${PORURL:-http://127.0.0.1:8099}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
PY_FROM=6738d65dacd26b3f308fe8fd688b806a; PY_TO=6099b5255374fc0bd0d27555cc009054; PY_S470=23fda41a19a6d4be398922e906d06702
CH_FROM=12ac3f27f532e9604b77f8affd47c742; CH_TO=74598ba70bd8ad8a24b142114dde81e5
PO_FROM=1a9fb99dfab46621a91c3fa041e37b50; PO_TO=d9b7685f75926164df34a10eca5dcb77
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s472_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.packs.py.s472" "$FIN/.packs_checklist.html.s472" "$POR/.portal.py.s472"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/7] $SPY lacks flask - nothing installed"; exit 1; }
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/7] kit gates green (SUMS, KIT_ID, flask); the build lock is taken"

H1="$(m5 "$FIN/packs.py")"; H2="$(m5 "$FIN/packs_checklist.html")"; H3="$(m5 "$POR/portal.py")"
if [ "$H1" = "$PY_TO" ] && [ "$H2" = "$CH_TO" ] && [ "$H3" = "$PO_TO" ]; then
  say "-- ALREADY INSTALLED: all three files at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null) · clinic-portal $(systemctl is-active clinic-portal 2>/dev/null)"; exit 0; fi
if [ "$H1" = "$PY_S470" ]; then say "!! [2/7] $FIN/packs.py is still the 04-Oct file - S471_PACKS_SEPTEMBER goes in first; nothing installed"; exit 1; fi
[ "$H1" = "$PY_FROM" ] || { say "!! [2/7] $FIN/packs.py is $H1, not $PY_FROM (S471's result) - another kit changed it. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
[ "$H2" = "$CH_FROM" ] || { say "!! [2/7] $FIN/packs_checklist.html is $H2, not $CH_FROM - nothing installed; tell the assistant"; exit 1; }
[ "$H3" = "$PO_FROM" ] || { say "!! [2/7] $POR/portal.py is $H3, not $PO_FROM (S450) - nothing installed; tell the assistant"; exit 1; }
say "[2/7] packs.py at S471's pin, packs_checklist.html and portal.py at their pins"

mkdir -p "$SCR" && \cp -p "$FIN/packs.py" "$FIN/packs_checklist.html" "$SCR/" && \cp -p "$POR/portal.py" "$SCR/portal.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s472.py "$SCR/packs.py" "$SCR/packs_checklist.html" "$SCR/portal.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/packs.py")" = "$PY_TO" ] && [ "$(m5 "$SCR/packs_checklist.html")" = "$CH_TO" ] && [ "$(m5 "$SCR/portal.py")" = "$PO_TO" ] || { say "!! [3/7] the edited scratch copies are not their predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s472.py walk_s472.py "$SCR/packs.py" "$SCR/portal.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the 13 edits apply to scratch copies and give the predicted bytes; compiles"

WOUT="$( cd /tmp && PACKS_TODAY=2026-10-04 timeout 900 "$SPY" -B "$KDIR/walk_s472.py" --apply "$KDIR/apply_s472.py" --finance "$FIN" --portal "$POR" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^WALK_S472' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S472 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/packs.py")" = "$PY_FROM" ] && [ "$(m5 "$POR/portal.py")" = "$PO_FROM" ] || { say "!! [4/7] a file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green on this box: the due days by kind; late / due today; the tile's line; a hand-over ticked with a photo through the real door (kept, shown, served; a .txt refused; a tick without a photo still works); the owner's day wins; SHOWN on the old file that the checklist knew no due day"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

B1="$FIN/packs.py.bak_S472_$(echo "$PY_FROM" | cut -c1-8)"; B2="$FIN/packs_checklist.html.bak_S472_$(echo "$CH_FROM" | cut -c1-8)"; B3="$POR/portal.py.bak_S472_$(echo "$PO_FROM" | cut -c1-8)"
\cp -p "$FIN/packs.py" "$B1" && \cp -p "$FIN/packs_checklist.html" "$B2" && \cp -p "$POR/portal.py" "$B3" && [ "$(m5 "$B1")" = "$PY_FROM" ] && [ "$(m5 "$B2")" = "$CH_FROM" ] && [ "$(m5 "$B3")" = "$PO_FROM" ] || { say "!! [5/7] the backups failed - nothing placed"; clean; exit 1; }
say "[5/7] backups: $B1 · $B2 · $B3"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$B1" "$FIN/packs.py"; \cp -p "$B2" "$FIN/packs_checklist.html"; \cp -p "$B3" "$POR/portal.py"
  systemctl restart clinic-finance 2>/dev/null || true; systemctl restart clinic-portal 2>/dev/null || true; sleep 7
  say "   packs.py $(m5 "$FIN/packs.py") · portal.py $(m5 "$POR/portal.py") · finance healthz $(health "$FINURL/finance/healthz") · portal health $(health "$PORURL/portal/health")"
  clean; exit 1
}
for pair in "$FIN/packs.py:$PY_TO:packs.py" "$FIN/packs_checklist.html:$CH_TO:packs_checklist.html" "$POR/portal.py:$PO_TO:portal.py"; do
  dst="${pair%%:*}"; rest="${pair#*:}"; want="${rest%%:*}"; name="${rest#*:}"; stage="$(dirname "$dst")/.$name.s472"
  \cp -p "$dst" "$stage" && cat "$SCR/$name" > "$stage" && [ "$(m5 "$stage")" = "$want" ] || { say "!! [6/7] could not stage $name - nothing placed"; clean; exit 1; }
done
mv -f "$FIN/.packs.py.s472" "$FIN/packs.py" || restore "placing packs.py"
mv -f "$FIN/.packs_checklist.html.s472" "$FIN/packs_checklist.html" || restore "placing packs_checklist.html"
mv -f "$POR/.portal.py.s472" "$POR/portal.py" || restore "placing portal.py"
[ "$(m5 "$FIN/packs.py")" = "$PY_TO" ] && [ "$(m5 "$FIN/packs_checklist.html")" = "$CH_TO" ] && [ "$(m5 "$POR/portal.py")" = "$PO_TO" ] || restore "md5 read-back"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
systemctl restart clinic-portal || restore "restart clinic-portal"
sleep 10
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || restore "$s not active"; done
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/packs/checklist"); case "$c2" in 302|401) ;; *) restore "/finance/packs/checklist answered $c2 without a login";; esac
c3=$(health "$FINURL/finance/packs/api/checklist/line"); case "$c3" in 401|403|302) ;; *) restore "the line door answered $c3 without a login";; esac
c4=$(health "$FINURL/finance/packs/handover/2026-09/1_x.jpg"); case "$c4" in 401|403|302|404) ;; *) restore "the photo door answered $c4 without a login";; esac
p1=$(health "$PORURL/portal/health"); [ "$p1" = 200 ] || restore "portal /portal/health $p1"
p2=$(health "$PORURL/portal/login"); case "$p2" in 200|302) ;; *) restore "portal /portal/login $p2";; esac
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
for s in clinic-finance clinic-portal; do
  journalctl -u "$s" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "$s: a module NOT mounted"
  JR="$(journalctl -u "$s" --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
  [ "${JR:-0}" = 0 ] || restore "$s journal: $JR error line(s)"
done
say "[6/7] placed, md5 read back = the kit's pins · both services active · finance healthz 200 · the checklist $c2, its line door $c3, the photo door $c4 (the login gate) · portal health $p1, login $p2 · the heartbeat door answers as before · journals clean"
mkdir -p "$FIN/statements/packs/handover" 2>/dev/null || true
say "[7/7] the photo folder exists: $FIN/statements/packs/handover"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/packs.py" "$FIN/packs_checklist.html" "$POR/portal.py"
