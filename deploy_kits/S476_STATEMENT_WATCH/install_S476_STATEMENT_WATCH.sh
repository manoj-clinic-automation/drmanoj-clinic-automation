#!/bin/bash
# =============================================================================
# install_S476_STATEMENT_WATCH.sh -- session 294, 04-Oct-2026 -- F-723, F-725, F-243
#  WHAT IT IS FOR. On 1-Oct the owner's personal Google scripts lost their authorisation; the relay that files the banks'
#  statements into Drive stopped, its failure mail reached his personal inbox only, and the shelf simply saw nothing until he
#  asked on 4-Oct why the pack was empty. This kit makes the road say so itself, and takes three stores into the nightly.
#  EDITS, by apply_s476.py (exact anchors on the real bytes: the 04-Oct 01:35 bundle + S471 ... S475's own applies, each
#  reproducing its S293 pin; every anchor found exactly once; all four verified before any is written):
#   /root/finance/packs.py                     6099b525 -> 1bc18b26   statement_road() and its health row; the owner's text door
#   /root/finance/packs.html                   1349b37b -> 73ff8c2f   the road's line above the summary card
#   /root/finance/finance_app.py               56eb421b -> 47a83382   ONE guarded health row, straight after the Reception PC row
#   /root/state_backup/clinic_state_backup.py  3bf7caea -> be57fe75   clinic_users.json (F-243) as a file; the hand-over photos
#                                                                    and the spine's order snapshots as trees
#  THE WATCH: from the 3rd of a month, AMBER while no bank statement has reached the shelf this month and last month's cells
#  are still empty or partial (it stays amber until one arrives); from the 3rd to the 10th a grey note when some came and then
#  none for three days; quiet otherwise. On the packs page and as 'Bank statements reaching Drive' on /finance/health.
#  THE DOOR: GET /finance/packs/api/text/<id> -- the owner only -- the text the readers see of one shelf file (F-725: the
#  bank's monthly e-mailed statement is a layout neither Yes Bank reader knows; its reader is built from that text).
#  NOT TOUCHED: the readers, stmt_shelf.py, the tables' shape, the checklist page, every other health row, the backup's
#  tar, key and slot files. No statement is re-read; nothing is sent anywhere.
# Walked first, on this box, hermetically (F-709): the four files copied to /tmp (old / new), an empty database, made-up
# files and logins; SHOWN absent on the old, present on the new. Then, before anything is placed, the three new backup
# sources are MEASURED on this box (a count and a size; nothing copied) -- no login store, or over 200 MB together, and nothing
# is installed. Restarts clinic-finance (about 8 seconds). Red after placing -> all four files are put back and the service
# restarted; a road that 'could not be read' on the live database is a red. Run again on an installed box, it repeats every
# after-placing check and says so if one is red. DRY=1 places nothing. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S476_STATEMENT_WATCH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; SB="$ROOT/state_backup"
DB="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
MAX_NEW_MB="${MAX_NEW_MB:-200}"
declare -A DIR=( [packs.py]="$FIN" [packs.html]="$FIN" [finance_app.py]="$FIN" [clinic_state_backup.py]="$SB" )
declare -A FROM=( [packs.py]=6099b5255374fc0bd0d27555cc009054 [packs.html]=1349b37b2a952ee4566376a577541e31 [finance_app.py]=56eb421b8d57a846e969b362e25b2c94 [clinic_state_backup.py]=3bf7caea3828c4e2a58227e161feec36 )
declare -A TO=( [packs.py]=1bc18b263af7e652a8d093e29e018ea8 [packs.html]=73ff8c2f06a6e070c0ff293afb2e3ff6 [finance_app.py]=47a83382595c59f42b80d2f72831837d [clinic_state_backup.py]=be57fe75f04b8b9020fcfd465b733578 )
FILES="packs.py packs.html finance_app.py clinic_state_backup.py"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s476_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR"; for f in $FILES; do rm -f "${DIR[$f]}/.$f.s476"; done; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/7] $SPY lacks flask (the walk mounts the packs page) - nothing installed"; exit 1; }
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/7] kit gates green (SUMS, KIT_ID, flask); the build lock is taken"

road_now() {
  ( cd "$FIN" && "$SPY" -B - "$DB" <<'PY'
import sqlite3, sys
import packs
con = sqlite3.connect(sys.argv[1], timeout=60); con.row_factory = sqlite3.Row
r = packs.statement_road(con)
print("   the road says: %s | %s" % (r["state"], r["text"]))
PY
  ) 2>&1 | tail -1 | cut -c1-300
}

T0=""
post_checks() {
  # every check made after placing; RED carries the first reason. Runs in this shell (never in a subshell), so the caller decides.
  RED=""
  systemctl is-active --quiet clinic-finance || { RED="clinic-finance not active"; return 1; }
  c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || { RED="finance healthz $c1"; return 1; }
  c2=$(health "$FINURL/finance/packs"); case "$c2" in 302|401) ;; *) RED="/finance/packs answered $c2 without a login"; return 1;; esac
  c3=$(health "$FINURL/finance/packs/api/text/1"); case "$c3" in 302|401|403) ;; *) RED="the text door answered $c3 without a login"; return 1;; esac
  c4=$(health "$FINURL/finance/health"); case "$c4" in 302|401|403) ;; *) RED="/finance/health answered $c4 without a login"; return 1;; esac
  D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
  echo "$D1" | grep -q '"NOT_YOU"' || { RED="the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"; return 1; }
  if [ -n "$T0" ]; then
    if journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted"; then RED="a module NOT mounted"; return 1; fi
    JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
    [ "${JR:-0}" = 0 ] || { RED="clinic-finance journal: $JR error line(s)"; return 1; }
  fi
  "$SPY" -B -c "import importlib.util as u; s=u.spec_from_file_location('csb','$SB/clinic_state_backup.py'); m=u.module_from_spec(s); s.loader.exec_module(m); assert m.SRC_FILES[-1]=='/root/portal/clinic_users.json' and m.SRC_TREES[-2:]==['/root/finance/statements/packs/handover','/root/finance/spine/orders']" 2>/dev/null || { RED="the placed clinic_state_backup.py does not load with the new sources"; return 1; }
  R1="$(road_now)"
  echo "$R1" | grep -q "the road says: \(ok\|info\|warn\) | ." || { RED="the road gave no answer on the live database: $(echo "$R1" | cut -c1-200)"; return 1; }
  if echo "$R1" | grep -q "could not be read"; then RED="the road could not be read on the live database: $(echo "$R1" | cut -c1-200)"; return 1; fi
  return 0
}

ALL=1; ANY=0; for f in $FILES; do if [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ]; then ANY=1; else ALL=0; fi; done
if [ "$ALL" = 1 ]; then
  say "-- ALREADY INSTALLED: all four files at the kit's pins. The after-placing checks, again:"
  post_checks || { say "!! installed, but a check is RED: $RED"; say "   Nothing was changed by this run. Tell the assistant; the undo line is in the kit's README."; exit 1; }
  say "   clinic-finance active · healthz 200 · /finance/packs $c2, the text door $c3 and /finance/health $c4 (the login gate) · the heartbeat door as before · the backup script loads with its new sources"
  echo "$R1"
  exit 0
fi
[ "$ANY" = 0 ] || { say "!! [2/7] some of the four files are at this kit's pins and some are not - a half state. Nothing installed; tell the assistant."; for f in $FILES; do say "   $f $(m5 "${DIR[$f]}/$f")"; done; exit 1; }
for f in $FILES; do
  H="$(m5 "${DIR[$f]}/$f")"
  [ "$H" = "${FROM[$f]}" ] || { say "!! [2/7] ${DIR[$f]}/$f is $H, not ${FROM[$f]} - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
done
[ -f "$DB" ] || { say "!! [2/7] $DB is not there - nothing installed"; exit 1; }
say "[2/7] all four files at the pins this kit was built on; the database in place"

mkdir -p "$SCR" && for f in $FILES; do \cp -p "${DIR[$f]}/$f" "$SCR/$f" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }; done
"$SPY" -B apply_s476.py "$SCR/packs.py" "$SCR/packs.html" "$SCR/finance_app.py" "$SCR/clinic_state_backup.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
for f in $FILES; do [ "$(m5 "$SCR/$f")" = "${TO[$f]}" ] || { say "!! [3/7] the edited scratch copy of $f is not its predicted bytes - nothing installed"; clean; exit 1; }; done
"$SPY" -m py_compile apply_s476.py walk_s476.py "$SCR/packs.py" "$SCR/finance_app.py" "$SCR/clinic_state_backup.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the twelve edits apply to scratch copies and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 600 "$SPY" -B "$KDIR/walk_s476.py" --apply "$KDIR/apply_s476.py" --finance "$FIN" --backup "$SB" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  note|^WALK_S476' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S476 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
for f in $FILES; do [ "$(m5 "${DIR[$f]}/$f")" = "${FROM[$f]}" ] || { say "!! [4/7] $f changed during the walk - nothing installed"; clean; exit 1; }; done
MEAS="$( "$SPY" -B - "$SCR/clinic_state_backup.py" "$ROOT" "$MAX_NEW_MB" <<'PY'
import importlib.util as u, os, sys
s = u.spec_from_file_location("csb_s476", sys.argv[1]); m = u.module_from_spec(s); s.loader.exec_module(m)
root, cap = sys.argv[2], float(sys.argv[3])
def here(p):                                   # ROOT is /root on the box; a rehearsal points it elsewhere
    return os.path.join(root, os.path.relpath(p, "/root"))
total = 0
p = here(m.SRC_FILES[-1])
assert m.SRC_FILES[-1] == "/root/portal/clinic_users.json"
have_store = os.path.isfile(p)
if have_store:
    total += os.path.getsize(p); print("   the login store: %d bytes" % os.path.getsize(p))
else:
    print("   the login store: NOT THERE (%s)" % m.SRC_FILES[-1])
for d in m.SRC_TREES[-2:]:
    q = here(d)
    if os.path.isdir(q):
        found, sec = m._walk_tree(q); b = sum(os.path.getsize(f) for f, _ in found); total += b
        dbs = sum(1 for f, _ in found if m.is_sqlite(f))
        print("   %s: %d file(s), %.2f MB%s%s" % (d, len(found), b / 1048576.0, (", %d secret-named file(s) left out" % sec) if sec else "",
                                               (", %d of them a database (integrity-checked each night)" % dbs) if dbs else ""))
    else:
        print("   %s: not there yet -- taken from the night it exists" % d)
print("MEASURE %s %.2f MB" % ("NO-LOGIN-STORE" if not have_store else ("OK" if total <= cap * 1048576 else "TOO-BIG"), total / 1048576.0))
PY
)"
echo "$MEAS" | grep -v '^MEASURE' | cut -c1-300
echo "$MEAS" | tail -1 | grep -q "^MEASURE OK" || { say "!! [4/7] the new backup sources: the login store is not where the script names it, or they are over $MAX_NEW_MB MB together, or they could not be measured ($(echo "$MEAS" | tail -1 | cut -c1-200)) - nothing installed; tell the assistant"; clean; exit 1; }
say "[4/7] walk green on this box (the road, the text door, the page, the health hook, the backup's own gather on made-up folders); the new backup sources measured: $(echo "$MEAS" | tail -1 | cut -d' ' -f3-)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

declare -A BAK
for f in $FILES; do
  B="${DIR[$f]}/$f.bak_S476_$(echo "${FROM[$f]}" | cut -c1-8)"
  \cp -p "${DIR[$f]}/$f" "$B" && [ "$(m5 "$B")" = "${FROM[$f]}" ] || { say "!! [5/7] the backup of $f failed - nothing placed"; clean; exit 1; }
  BAK[$f]="$B"
done
say "[5/7] backups: $(for f in $FILES; do echo -n "${BAK[$f]} "; done)"
restore() {
  say "!! RED after placing ($1) - restoring all four"
  for f in $FILES; do \cp -p "${BAK[$f]}" "${DIR[$f]}/$f"; done
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  for f in $FILES; do
    if [ "$(m5 "${DIR[$f]}/$f")" = "${FROM[$f]}" ]; then say "   $f back at ${FROM[$f]}"; else say "   !! $f is $(m5 "${DIR[$f]}/$f"), NOT its old ${FROM[$f]} - put ${BAK[$f]} back by hand"; fi
  done
  say "   finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
for f in $FILES; do
  \cp -p "${DIR[$f]}/$f" "${DIR[$f]}/.$f.s476" && cat "$SCR/$f" > "${DIR[$f]}/.$f.s476" && [ "$(m5 "${DIR[$f]}/.$f.s476")" = "${TO[$f]}" ] || { say "!! [6/7] could not stage $f - nothing placed"; clean; exit 1; }
done
for f in $FILES; do mv -f "${DIR[$f]}/.$f.s476" "${DIR[$f]}/$f" || restore "placing $f"; done
for f in $FILES; do [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
post_checks || restore "$RED"
say "[6/7] placed, md5 read back = the kit's pins · clinic-finance active · healthz 200 · /finance/packs $c2, the text door $c3 and /finance/health $c4 (the login gate) · the heartbeat door answers as before · every part mounted · journal clean · the backup script loads with its new sources"
say "[7/7] the road, read on this box as the page reads it:"
echo "$R1"
clean
say "all green -- $KIT: DONE. Tonight's 01:50 backup is the first with the new sources, as measured at [4/7]."
for f in $FILES; do md5sum "${DIR[$f]}/$f"; done
