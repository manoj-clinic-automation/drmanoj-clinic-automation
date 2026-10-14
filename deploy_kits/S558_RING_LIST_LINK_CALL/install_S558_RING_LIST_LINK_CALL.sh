#!/bin/bash
# =============================================================================
# install_S558_RING_LIST_LINK_CALL.sh -- session 317, 14-Oct-2026 -- D726, F-896
#  THE OWNER, 14-Oct, on /portal/ring/list: "the patients, they call from a different number. The new ones. And then they
#  register themselves with a different number ... Secondly, there should be a click to call link to IVR number as the
#  callback tracker does. For the no shows". Then "1 any staff . 2 yes".
#  REBUILT ON THIS BOX by counted anchored edits on the live bytes (make_s558.py), each gated on its md5:
#     /root/portal/ring_outcome.py  7cb60aad -> the fold 'Shayad yeh aaye?' (suggestions + search + 'Haan, yahi hai') on a
#                                              new number's line; the link supplies the visit (THE RULE unchanged);
#                                              'Galat link -- hatao'; 'IVR se call karein' on each Nahi aaye line; the
#                                              owner's two toggles. Installed OFF (kv link_on = call_on = 0).
#     /root/portal/ring_common.py   4344b592 -> lookup_caller also reads the live links (the second number remembered).
#  READ-ONLY, must be unchanged: /root/wa/call_api.py 930b42c4 (never edited), /root/portal/portal.py f8b059f6.
#  The ring store (ring_outcomes.db) gains one table, appt_link, and the two keys -- nothing in it is changed. finance.db is
#  only ever opened read-only. Nothing is mirrored to the Google tracker. Nothing is sent to anyone.
#  Order: gates -> pins -> compile -> rebuild in memory = the kit's bytes -> walk (+ S497's walk) + the negative control ->
#  DRY stop -> backups -> place -> md5 read-back -> table and keys -> restart ring-hook + clinic-portal ONLY -> health ->
#  the page read as manoj with both switches off -> undo line. Red after placing -> both files put back byte for byte,
#  both services restarted, health confirmed, exit 1.  DRY=1 places nothing.  Needs the build lock free.
#  Every path and command can be given by the environment (the rehearsal on a made-up root uses this):
#   PD FINDB FINDIR WADIR PORURL RINGURL FINURL LOCK TMPBASE SPY_SVC SPY_VENV SYSTEMCTL CURL JOURNALCTL WAIT S497DIR FORCE_RED
# =============================================================================
set -u
KIT="S558_RING_LIST_LINK_CALL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PD="${PD:-/root/portal}"
FINDB="${FINDB:-/root/finance/finance.db}"
FINDIR="${FINDIR:-/root/finance}"
WADIR="${WADIR:-/root/wa}"
PORURL="${PORURL:-http://127.0.0.1:8099}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
TMPBASE="${TMPBASE:-/tmp}"
SPY_SVC="${SPY_SVC:-/usr/bin/python3}"
SPY_VENV="${SPY_VENV:-/root/wa/venv/bin/python3}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CURL="${CURL:-curl}"
JOURNALCTL="${JOURNALCTL:-journalctl}"
WAIT="${WAIT:-2}"
S497DIR="${S497DIR:-$KDIR/../S497_RING_LIST}"
RO_FROM=7cb60aad2df80f87fdc4a674ebe7ee45; RO_TO=25a169bfe280e16b4b39585d827cc36e
RC_FROM=4344b59277d94b2d11d8d7cc23328677; RC_TO=ce428b2c52582d4a30d460612a6da968
CA_PIN=930b42c49e8c03ecc46d5e53e1e8d386
PO_PIN=f8b059f61fa8b885f024f4f4ce73e4f2
B_RO="$PD/ring_outcome.py.bak_S558_$(echo "$RO_FROM" | cut -c1-8)"
B_RC="$PD/ring_common.py.bak_S558_$(echo "$RC_FROM" | cut -c1-8)"
SCR=""; PLACED=0; HAVE_LOCK=0; T0=""; RED=""; WPY=""; FACTS=""; LOOK=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { "$CURL" -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() {
  [ -n "$SCR" ] && rm -rf "$SCR"
  rm -f "$PD/.ring_outcome.py.s558" "$PD/.ring_common.py.s558"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  \cp -p "$B_RO" "$PD/ring_outcome.py"; \cp -p "$B_RC" "$PD/ring_common.py"
  for x in "ring_outcome.py:$RO_FROM" "ring_common.py:$RC_FROM"; do
    f="${x%%:*}"; h="${x##*:}"
    if [ "$(m5 "$PD/$f")" = "$h" ]; then say "   $f back at its old bytes ($h)"; else say "   !! $f is NOT its old bytes - put its .bak_S558_ copy back by hand"; fi
  done
  "$SYSTEMCTL" restart ring-hook clinic-portal 2>/dev/null || true
  for _w in 1 2 3 4 5 6 7 8 9 10; do sleep "$WAIT"; [ "$(health "$PORURL/portal/health")" = 200 ] && break; done
  HR="$(health "$PORURL/portal/health")"; HF="$(health "$FINURL/finance/healthz")"
  if [ "$HR" = 200 ] && [ "$HF" = 200 ] && "$SYSTEMCTL" is-active --quiet clinic-portal && "$SYSTEMCTL" is-active --quiet ring-hook; then
    say "   after the restore: portal health 200 . /finance/healthz 200 . clinic-portal active . ring-hook active -- the box is as it was before this run"
  else
    say "   !! after the restore: portal health $HR . finance healthz $HF . clinic-portal $("$SYSTEMCTL" is-active clinic-portal 2>/dev/null) . ring-hook $("$SYSTEMCTL" is-active ring-hook 2>/dev/null)"
    say "   !! THE OLD FILES ARE BACK BUT A SERVICE IS NOT UP - tell the assistant now"
  fi
  say "   NOT INSTALLED (restored). The ring store may have gained its new, empty table appt_link and the two OFF keys; the old program never reads them."
  clean; exit 1
}
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
on_signal() {
  trap '' INT TERM HUP
  say ""; say "!! interrupted"
  if [ "$PLACED" = 1 ]; then restore "the run was interrupted after placing"; fi
  clean; exit 130
}
trap on_exit EXIT
trap on_signal INT TERM HUP
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

# ---------------------------------------------------------------------------------------------- [1/9] the kit's own gates
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 ring_outcome.py)" = "$RO_TO" ] && [ "$(m5 ring_common.py)" = "$RC_TO" ] || { say "!! [1/9] the kit's two programs are not the ones this installer names - nothing installed"; exit 1; }
for p in "$SPY_VENV" "$SPY_SVC"; do [ -x "$p" ] || { say "!! [1/9] no python at $p - nothing installed"; exit 1; }; done
[ "$("$SPY_VENV" -B make_s558.py --pins 2>/dev/null | tr '\n' ' ')" = "ring_outcome.py $RO_FROM $RO_TO ring_common.py $RC_FROM $RC_TO " ] \
  || { say "!! [1/9] the builder does not name the pins this installer names - nothing installed"; exit 1; }
[ -f "$S497DIR/walk_s497.py" ] || { say "!! [1/9] S497's kit folder ($S497DIR) is not there - its walk is part of this one - nothing installed"; exit 1; }
WPYS=""
for p in "$SPY_VENV" "$SPY_SVC"; do "$p" -c "import flask, sqlite3" 2>/dev/null && WPYS="$WPYS $p"; done
[ -n "$WPYS" ] || { say "!! [1/9] neither python has Flask (the walk needs it) - nothing installed"; exit 1; }
say "[1/9] kit gates green (SUMS, KIT_ID, each program's own md5, the builder's pins, S497's walk at hand; Flask under:$WPYS)"

# ---------------------------------------------------------------------------------------------- [2/9] the live files' pins
H_RO="$(m5 "$PD/ring_outcome.py")"; H_RC="$(m5 "$PD/ring_common.py")"
if [ "$H_RO" = "$RO_TO" ] && [ "$H_RC" = "$RC_TO" ]; then
  say "-- ALREADY INSTALLED: both files are at the kit's pins; nothing changed. clinic-portal $("$SYSTEMCTL" is-active clinic-portal 2>/dev/null) . ring-hook $("$SYSTEMCTL" is-active ring-hook 2>/dev/null)"
  clean; exit 0
fi
BAD=0
[ "$H_RO" = "$RO_FROM" ] || { say "!! [2/9] $PD/ring_outcome.py is ${H_RO:-not there}, not $RO_FROM - it changed after this kit was built."; BAD=1; }
[ "$H_RC" = "$RC_FROM" ] || { say "!! [2/9] $PD/ring_common.py is ${H_RC:-not there}, not $RC_FROM - it changed after this kit was built."; BAD=1; }
[ "$(m5 "$WADIR/call_api.py")" = "$CA_PIN" ] || { say "!! [2/9] $WADIR/call_api.py is $(m5 "$WADIR/call_api.py"), not $CA_PIN - the call button was built on that file."; BAD=1; }
[ "$(m5 "$PD/portal.py")" = "$PO_PIN" ] || { say "!! [2/9] $PD/portal.py is $(m5 "$PD/portal.py"), not $PO_PIN - the list's routes are mounted through it."; BAD=1; }
[ "$BAD" = 0 ] || { say "   REFUSED: nothing placed, nothing restarted. Tell the assistant; the kit is rebuilt on the new file."; clean; exit 1; }
say "[2/9] ring_outcome.py and ring_common.py at the pins this kit was built on; call_api.py and portal.py (read only) at theirs"

mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [2/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "$TMPBASE/s558_scratch_XXXXXXXX")" || { say "!! [2/9] no scratch folder - nothing installed"; exit 1; }
chmod 700 "$SCR"

# ---------------------------------------------------------------------------------------------- [3/9] compile; rebuild
mkdir -p "$SCR/c" && \cp -p "$KDIR/ring_outcome.py" "$KDIR/ring_common.py" "$KDIR/make_s558.py" "$KDIR/walk_s558.py" "$SCR/c/" \
  || { say "!! [3/9] no scratch copy - nothing installed"; clean; exit 1; }
for p in "$SPY_SVC" "$SPY_VENV"; do
  ( cd "$SCR/c" && "$p" -W ignore -B -c "
for f in ('ring_outcome.py', 'ring_common.py', 'make_s558.py', 'walk_s558.py'):
    compile(open(f, encoding='utf-8').read(), f, 'exec')
" ) 2>"$SCR/compile.err" || { say "!! [3/9] compile failed under $p: $(tail -1 "$SCR/compile.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
done
( cd "$SCR" && "$SPY_VENV" -W ignore -B "$KDIR/make_s558.py" --check "$PD" "$KDIR" ) >"$SCR/make.out" 2>&1 \
  || { say "!! [3/9] the kit's programs are NOT what the builder makes from this box's live files: $(tail -2 "$SCR/make.out" | tr '\n' ' ' | cut -c1-300) - nothing installed"; clean; exit 1; }
say "[3/9] the programs compile under $SPY_SVC and $SPY_VENV; rebuilt here from this box's live bytes by counted anchored edits they are the kit's files, byte for byte"

# ---------------------------------------------------------------------------------------------- [4/9] the walk, and its control
unchanged() { [ "$(m5 "$PD/ring_outcome.py")" = "$RO_FROM" ] && [ "$(m5 "$PD/ring_common.py")" = "$RC_FROM" ]; }
DBARG=""; [ -f "$PD/ring_outcomes.db" ] && [ -f "$FINDB" ] && DBARG="--db $PD/ring_outcomes.db --finance-db $FINDB"
for WPY in $WPYS; do
  WOUT="$( cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 timeout 900 "$WPY" -W ignore -B "$KDIR/walk_s558.py" --kit "$KDIR" --portal "$PD" --s497 "$S497DIR" $DBARG 2>&1 )"
  echo "$WOUT" | grep -E '^  FAIL|^  note|^WALK_S558|^PART|real list|COPY only|S497.s own walk' | cut -c1-300 | sed 's/^/   /'
  echo "$WOUT" | tail -1 | grep -q "^WALK_S558 GREEN" || { say "!! [4/9] the walk is red under $WPY - nothing installed."; echo "$WOUT" | tail -15 | cut -c1-300; clean; exit 1; }
  COUT="$( cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 timeout 900 "$WPY" -W ignore -B "$KDIR/walk_s558.py" --kit "$KDIR" --portal "$PD" --control 2>&1 )"
  CL="$(echo "$COUT" | tail -1)"
  echo "$CL" | grep -q "^WALK_S558 RED" || { say "!! [4/9] the SAME walk on the live files did not go red under $WPY ($CL): it cannot tell old from new - nothing installed."; clean; exit 1; }
  CPARTS="$(echo "$COUT" | awk '/^PART/{p=$2} /^  FAIL/{n[p]++} END{for (k in n) printf "%s:%d ", k, n[k]}')"
  say "   under $WPY: $(echo "$WOUT" | tail -1) . the same walk on the live files: $CL (red per part: $CPARTS)"
done
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
unchanged || { say "!! [4/9] a live file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/9] walked on this box: off by default; (a) suggestions; (e) search; (b) link; (d) remembered; (c) undo; (f) IVR call; (g) off again; (h) S497's walk; copies of the real stores"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

# ---------------------------------------------------------------------------------------------- [5/9] backups
\cp -p "$PD/ring_outcome.py" "$B_RO" && [ "$(m5 "$B_RO")" = "$RO_FROM" ] && \cp -p "$PD/ring_common.py" "$B_RC" && [ "$(m5 "$B_RC")" = "$RC_FROM" ] \
  || { say "!! [5/9] a file backup failed - nothing placed"; clean; exit 1; }
STAMP="$(date +%Y%m%d_%H%M%S)"
dbbak() {  # $1 source db, $2 backup path -- the sqlite backup API, then an integrity check of the copy
  "$SPY_VENV" -B -c "
import sqlite3, sys
a = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=30); b = sqlite3.connect(sys.argv[2])
a.backup(b); b.close(); a.close()
c = sqlite3.connect('file:%s?mode=ro' % sys.argv[2], uri=True); assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'; c.close()
" "$1" "$2" 2>"$SCR/dbbak.err" && chmod 600 "$2"
}
RBAK="(no ring store yet)"
if [ -f "$PD/ring_outcomes.db" ]; then
  RBAK="$PD/ring_outcomes.db.bak_S558_$STAMP"
  dbbak "$PD/ring_outcomes.db" "$RBAK" || { say "!! [5/9] the ring store's backup failed: $(tail -1 "$SCR/dbbak.err" | cut -c1-200) - nothing placed"; rm -f "$RBAK"; clean; exit 1; }
fi
FBAK="$(dirname "$FINDB")/finance.db.bak_S558_$STAMP"
dbbak "$FINDB" "$FBAK" || { say "!! [5/9] the finance.db backup failed: $(tail -1 "$SCR/dbbak.err" | cut -c1-200) - nothing placed"; rm -f "$FBAK"; clean; exit 1; }
say "[5/9] backups made: $(basename "$B_RO") . $(basename "$B_RC") . $(basename "$RBAK") . $(basename "$FBAK") (finance.db is never written by this kit; backed up by rule)"

# ---------------------------------------------------------------------------------------------- [6/9] place, read back, table and keys, restart
\cp -p "$PD/ring_outcome.py" "$PD/.ring_outcome.py.s558" && cat "$KDIR/ring_outcome.py" > "$PD/.ring_outcome.py.s558" && [ "$(m5 "$PD/.ring_outcome.py.s558")" = "$RO_TO" ] \
  && \cp -p "$PD/ring_common.py" "$PD/.ring_common.py.s558" && cat "$KDIR/ring_common.py" > "$PD/.ring_common.py.s558" && [ "$(m5 "$PD/.ring_common.py.s558")" = "$RC_TO" ] \
  || { say "!! [6/9] could not stage the files - nothing placed"; clean; exit 1; }
PLACED=1
mv -f "$PD/.ring_common.py.s558" "$PD/ring_common.py" || restore "placing ring_common.py"
mv -f "$PD/.ring_outcome.py.s558" "$PD/ring_outcome.py" || restore "placing ring_outcome.py"
[ "$(m5 "$PD/ring_outcome.py")" = "$RO_TO" ] && [ "$(m5 "$PD/ring_common.py")" = "$RC_TO" ] || restore "md5 read-back"
DOUT="$( cd "$PD" && PYTHONDONTWRITEBYTECODE=1 FINANCE_DB="$FINDB" FINANCE_DIR="$FINDIR" "$SPY_VENV" -W ignore -B -c "
import sqlite3
import ring_outcome as ro
ro.init_db()
c = sqlite3.connect(ro.DB_FILE)
for k in ('link_on', 'call_on'):
    c.execute(\"INSERT OR IGNORE INTO kv(k, v, by_whom, at) VALUES(?, '0', 'install S558', ?)\", (k, ro._fmt(ro.now_ist())))
c.commit()
t = {r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}
kv = dict(c.execute(\"SELECT k, v FROM kv WHERE k IN ('link_on', 'call_on')\").fetchall())
n = c.execute('SELECT COUNT(*) FROM appt_link').fetchone()[0]
c.close()
assert 'appt_link' in t and kv.get('link_on') == '0' and kv.get('call_on') == '0', (sorted(t), kv)
print('table appt_link made (%d rows) . kv link_on=%s call_on=%s' % (n, kv['link_on'], kv['call_on']))
" 2>&1 )" || restore "the table and keys: $(echo "$DOUT" | tail -1 | cut -c1-200)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart ring-hook || restore "ring-hook restart"
"$SYSTEMCTL" restart clinic-portal || restore "clinic-portal restart"
for _w in 1 2 3 4 5 6 7 8 9 10; do sleep "$WAIT"; [ "$(health "$PORURL/portal/health")" = 200 ] && break; done
sleep "$WAIT"
say "[6/9] placed; md5 read back = the kit's pins; $DOUT; ring-hook and clinic-portal restarted (nothing else) at $T0"

# ---------------------------------------------------------------------------------------------- [7/9] is it well?
post_checks() {
  RED=""
  [ "${FORCE_RED:-0}" = 1 ] && { RED="forced red (rehearsal)"; return 1; }
  "$SYSTEMCTL" is-active --quiet clinic-portal || { RED="clinic-portal not active"; return 1; }
  "$SYSTEMCTL" is-active --quiet ring-hook || { RED="ring-hook not active"; return 1; }
  PH="$("$CURL" -s -m 8 "$PORURL/portal/health")"
  echo "$PH" | grep -q '"status": *"ok"' || { RED="portal health: $(echo "$PH" | tr -d '\n' | cut -c1-80)"; return 1; }
  RP="$(grep -m1 '^RING_HOOK_PORT=' "$PD/ring_hook.env" 2>/dev/null | cut -d= -f2)"; RP="${RP:-8110}"
  RH="$("$CURL" -s -m 8 "${RINGURL:-http://127.0.0.1:$RP}/ring-hook/health")"
  echo "$RH" | grep -q '"status": *"ok"' || { RED="ring-hook health: $(echo "$RH" | tr -d '\n' | cut -c1-80)"; return 1; }
  c=$(health "$FINURL/finance/healthz"); [ "$c" = 200 ] || { RED="/finance/healthz answered $c"; return 1; }
  # a page behind the login answers 302 to a caller with no login: that is EXPECTED, never a failure (rule 5)
  for u in /portal/ring/list "/portal/ring/list?d=30" /portal; do
    c=$(health "$PORURL$u"); case "$c" in 302|401) ;; *) RED="$u answered $c without a login (it must send a stranger to the login)"; return 1;; esac
  done
  for u in /portal/ring/list/act /portal/ring/list/switch; do
    c=$("$CURL" -s -o /dev/null -m 10 -w '%{http_code}' -X POST -H 'Content-Type: application/json' --data-binary '{"id":1,"act":"call"}' "$PORURL$u")
    case "$c" in 302|401) ;; *) RED="$u answered $c to a POST with no login (it must turn him away)"; return 1;; esac
  done
  JR="$("$JOURNALCTL" -u ring-hook -u clinic-portal --since "$T0" --no-pager 2>/dev/null | grep -c -i 'Traceback\|ModuleNotFoundError\|ImportError\|SyntaxError\|NameError')"
  [ "${JR:-0}" = 0 ] || { RED="journal: $JR error line(s) since the restart"; return 1; }
  [ "$(m5 "$WADIR/call_api.py")" = "$CA_PIN" ] && [ "$(m5 "$PD/portal.py")" = "$PO_PIN" ] || { RED="call_api.py or portal.py is not at its pin"; return 1; }
  return 0
}
post_checks || restore "$RED"
say "[7/9] clinic-portal and ring-hook active; portal health ok; ring-hook health ok; /finance/healthz 200; the list and its POST doors send a stranger to the login (302); journal clean; call_api.py and portal.py untouched"

# ---------------------------------------------------------------------------------------------- [8/9] the page, read as manoj
LOOK="$( cd "$PD" && PYTHONDONTWRITEBYTECODE=1 FINANCE_DB="$FINDB" FINANCE_DIR="$FINDIR" "$SPY_VENV" -W ignore -B -c "
import re, sqlite3
import ring_outcome as ro
d = ro.list_data('30')
h = ro.render_list(d, True, ro.list_on(), sorted(ro.list_holders()), '', viewer='manoj')
lines = ''.join(re.findall(r'(?s)<tbody>(.*?)</tbody>', h))
new = [m for m in ('Shayad yeh aaye?', 'Haan, yahi hai', 'IVR se call karein', 'Galat link', 'doosre number se', 'data-s558') if m in lines]
assert d['store_ok'] and not d['link_on'] and not d['call_on'], 'switches'
assert not new, new
assert 'Doosre number se link: <b>OFF</b>' in h and 'IVR call button: <b>OFF</b>' in h, 'toggles'
print('as manoj, /portal/ring/list?d=30 (rendered by the placed program from the live store, read-only): %d Nahi aaye . %d Aane baaki . %d Aa gaye' % (len(d['noshow']), len(d['due']), len(d['came'])))
print('as manoj: nothing new on any line (no fold, no IVR button, no link words); his box carries the two toggles, both OFF')
" 2>&1 )" || restore "the page read as manoj: $(echo "$LOOK" | tail -1 | cut -c1-200)"
[ "${FORCE_RED_LATE:-0}" = 1 ] && restore "forced red after the look (rehearsal)"
PLACED=0
echo "$LOOK" | sed 's/^/   /'
say "[8/9] the page read as manoj with both switches off: nothing new shows on the lines; only his two toggles (OFF)"
clean
say "[9/9] all green -- $KIT: DONE.  For the record:"
for x in "ring_outcome.py:$RO_FROM:$RO_TO" "ring_common.py:$RC_FROM:$RC_TO"; do
  f="${x%%:*}"; r="${x#*:}"; fr="${r%%:*}"; h="${r##*:}"; g="$(m5 "$PD/$f")"
  if [ "$g" = "$h" ]; then say "   $PD/$f  $fr -> $g (read back = the kit's TO pin)"; else say "   !! md5 read back $g $PD/$f is NOT the kit's TO pin $h"; fi
done
say "   read only, unchanged: $WADIR/call_api.py $(m5 "$WADIR/call_api.py") . $PD/portal.py $(m5 "$PD/portal.py")"
say "   restarted: ring-hook and clinic-portal -- nothing else"
say "   UNDO (one line): \\cp -p $B_RO $PD/ring_outcome.py && \\cp -p $B_RC $PD/ring_common.py && systemctl restart ring-hook clinic-portal && md5sum $PD/ring_outcome.py $PD/ring_common.py"
exit 0
