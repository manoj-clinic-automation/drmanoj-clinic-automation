#!/bin/bash
# =============================================================================
#  install_S644_BUYING_MODEL.sh · kit S644 (25-Oct-2026, Sanjeevni session 350) · D678 built -- KIT II, THE BUYING MODEL
#  Brief: claude_code_briefs/S486_BUYING_MODEL.md Part B as re-read by S308 and planned in claude/S350_KIT_II_PLAN.md (the owner's
#  go-ahead 07:01 IST 25-Oct). One setting order.model = fixed | levels. fixed = today's engine line for line (proved by the walk, old bytes
#  against new on three days). levels = each supplier's own rhythm, the shop's lots, the rate ending on the last sale day, the largest-day
#  floor, between-review orders only when the stock will not last; the untouched list made again when an input moves. NOTHING REACHES A
#  STAFF SCREEN: order.source is read, never written; the proposals exist already (shadow) and the nightly rehearsal scores them per model.
#
#   /root/finance/order_rules.py                  8d078dbe -> TO   (the model: 7 anchored edits + the S644 block)
#   /root/finance/porders_s454.py                 673883e8 -> TO   (the settings route: the 11 new keys, the word / clock / clamp checks; the score line per model; the model line on the old page)
#   /root/finance/spine/spine_read.py             10697b38 -> TO   (one read: last_sale_day)
#   /root/finance/spine/order_rehearsal.py        104d366d -> TO   (B.8: model / held / added / qty_engine kept; by_model and darpan in the weekly file)
#   /root/finance/spine/selftest_spine.py         7d0edb4a -> TO   (test_s644: the pure functions made to fail on purpose)
#   /root/finance/finance_ui/finance_approvals.html a7016a4e -> TO (THE PARENT'S TEMPLATE, served by finance_app.py which is NOT touched:
#                                                                    the 'How the list is made' block in the Buying rules fold; two fields on the supplier form)
#  finance.db: backed up first (backup API); then four columns on order_supplier_rule (rhythm_mode seeded once: fixed for Kedar / owner-set
#  days, learnt for the rest), the eleven settings at their defaults (INSERT OR IGNORE), bill_days90 / rhythm_at refreshed, and
#  order.model = levels ONLY IF order.source = marg_sheet at that moment (else it stays fixed and this script says so). No crontab change.
#  One restart of clinic-finance.
#  ORDER: gates (window 08:02-23:49 IST, SUMS, KIT_ID, the spine's health file) -> the build lock -> ALREADY INSTALLED? -> the FROM pins
#  -> build from the live bytes (make_s644.py) -> compile (both pythons) -> the walk on scratch (old vs new, both models, negative control)
#  -> the replay (the kit's arithmetic within 10 % of the reference) -> DRY stops -> backups -> DOCTOR_AUTO_OFF -> staged + renamed ->
#  md5 read back -> ONE restart -> healthz 200, the pages 302 without a login, journal clean -> the data step -> the owner's lines
#  -> DOCTOR_AUTO_OFF removed -> lock released -> DONE.  Red after placing: every file back from its backup, one restart, healthz.
#  Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S644_BUYING_MODEL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="${FIN:-$ROOT/finance}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
declare -A LIVE FROM TO
EREL="finance/order_rules.py finance/porders_s454.py finance/spine/spine_read.py finance/spine/order_rehearsal.py finance/spine/selftest_spine.py finance/finance_ui/finance_approvals.html"
PYREL="finance/order_rules.py finance/porders_s454.py finance/spine/spine_read.py finance/spine/order_rehearsal.py finance/spine/selftest_spine.py"
for r in $EREL; do LIVE[$r]="$ROOT/$r"; done
FROM[finance/order_rules.py]=8d078dbe1b63a4706dc6f35e3c31ac9a
FROM[finance/porders_s454.py]=673883e86c340b272e58d4bab127657d
FROM[finance/spine/spine_read.py]=10697b3869218151a75268e2259248d7
FROM[finance/spine/order_rehearsal.py]=104d366d2e284ccfedef46ca0a744230
FROM[finance/spine/selftest_spine.py]=7d0edb4aafb17c83cf07be1052623f76
FROM[finance/finance_ui/finance_approvals.html]=a7016a4e65a1410a574572813a54626d
while read -r h f; do TO[$f]=$h; done < "$KDIR/TO_PINS.md5"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s644_inst_$STAMP"
DBBAK="$DB.bak_S644_$STAMP"
PLACED=0; TOOK_LOCK=0; OFF_MINE=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
bak() { echo "${LIVE[$1]}.bak_S644_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting every file back"
  for r in $EREL; do \cp -p "$(bak "$r")" "${LIVE[$r]}" || say "   !! could not put back ${LIVE[$r]}"; done
  rm -f "$FIN"/.*.s644 "$FIN"/finance_ui/.*.s644 "$FIN"/spine/.*.s644
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for r in $EREL; do say "   ${LIVE[$r]} $(m5 "${LIVE[$r]}") (expected ${FROM[$r]})"; done
  say "   finance healthz $h; the data step had not run: the database is as it was; its backup $DBBAK is kept"
  [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep sleep find sed timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } \
  || { say "!! [1/9] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }   # SKIP_WINDOW only with DRY=1 (a rehearsal off the box)
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for r in $EREL; do [ -f "${LIVE[$r]}" ] || { say "!! [1/9] ${LIVE[$r]} is not there - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$FIN/spine/spine.db" ] || { say "!! [1/9] finance.db or the spine is missing - nothing installed"; exit 1; }
# the spine's health (charter 1b, S308 vii): refuse while the job is red or stale
SPINE_OK="$("$APY" - "$FIN/spine/spine_state.json" <<'PYEOF' 2>/dev/null
import json, sys, datetime as dt
j = json.load(open(sys.argv[1]))
at = dt.datetime.fromisoformat(str(j.get("at"))[:19])
age_h = (dt.datetime.now() - at).total_seconds() / 3600.0
print("ok" if (j.get("passed") is True and age_h <= 36) else "red passed=%s age_h=%.1f" % (j.get("passed"), age_h))
PYEOF
)"
[ "$SPINE_OK" = "ok" ] || { say "!! [1/9] the spine is not green or not fresh ($SPINE_OK) - the model would read a red spine: nothing installed"; exit 1; }
ALL=1; for r in $EREL; do [ "$(m5 "${LIVE[$r]}")" = "${TO[$r]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the six files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/9] DRY RUN: kit gates green (SUMS, KIT_ID, the window, the spine $SPINE_OK); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] kit gates green (the spine $SPINE_OK); the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/9] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

for r in $EREL; do C="$(m5 "${LIVE[$r]}")"; [ "$C" = "${FROM[$r]}" ] || stop_unlocked "!! [2/9] ${LIVE[$r]} is $C, expected ${FROM[$r]} - it changed after this kit was built: STOP, nothing installed"; done
say "[2/9] live pins exact: six files at their FROM"
say "       read only (not pinned): stock_figure.py $(m5 "$FIN/stock_figure.py" | cut -c1-8) . purchase_app.py $(m5 "$FIN/purchase_app.py" | cut -c1-8) . shelf_figure.py $(m5 "$FIN/shelf_figure.py" | cut -c1-8) . stock_watch.py $(m5 "$FIN/stock_watch.py" | cut -c1-8) . darpan_kal.py $(m5 "$FIN/darpan_kal.py" | cut -c1-8) (not touched)"

mkdir -p "$SCR/built" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s644.py --src "$ROOT" --out "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/9] the builder refused a live file - nothing installed"; }
for r in $EREL; do [ "$(m5 "$SCR/built/$r")" = "${TO[$r]}" ] || stop_unlocked "!! [3/9] rebuilt, $r is $(m5 "$SCR/built/$r"), not ${TO[$r]} - nothing installed"; done
for py in "$APY" "$VPY"; do for r in $PYREL; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$r" || stop_unlocked "!! [3/9] the built $r does not compile on $py - nothing installed"; done; done
say "[3/9] rebuilt here from this box's live bytes: each at its TO pin; the Python compiles under both pythons"

copydb "$DB" "$SCR/base.db" && copydb "$FIN/spine/spine.db" "$SCR/spine_live.db" || stop_unlocked "!! [4/9] no copy of the databases - nothing installed"
say "[4/9] scratch: finance.db and the spine by the backup API"
( cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 2400 "$APY" -B "$KDIR/walk_s644.py" --live "$ROOT" --to "$SCR/built" --db "$SCR/base.db" --spine "$SCR/spine_live.db" --scratch "$SCR/walk" --python "$APY" 2>&1 ) | mask > "$SCR/walk.txt"
say "       $(grep '^WALK' "$SCR/walk.txt")"
grep -q "^WALK GREEN" "$SCR/walk.txt" || { cat "$SCR/walk.txt"; stop_unlocked "!! [5/9] the walk is red - nothing installed"; }
( cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$APY" -B "$KDIR/replay_s644.py" --db "$SCR/base.db" --app "$SCR/walk/new/finance" 2>&1 ) | mask > "$SCR/replay.txt"
say "       $(grep '^REPLAY' "$SCR/replay.txt")"
grep -q "^REPLAY OK" "$SCR/replay.txt" || { cat "$SCR/replay.txt"; stop_unlocked "!! [5/9] the replay is off the reference - nothing installed"; }
say "[5/9] the walk: old = new on fixed, the model on levels, the negative control red; the replay within 10 % (the whole output is in the report)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the replay green; NOTHING written, nothing placed, nothing restarted"; cat "$SCR/walk.txt" "$SCR/replay.txt"; exit 0; fi

HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
{ [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; } || stop_unlocked "!! [6/9] the walk ran past 23:49 IST - nothing placed; run it again tomorrow"
copydb "$DB" "$DBBAK" || stop_unlocked "!! [6/9] could not back up the database - nothing placed"
for r in $EREL; do \cp -p "${LIVE[$r]}" "$(bak "$r")" && [ "$(m5 "$(bak "$r")")" = "${FROM[$r]}" ] || stop_unlocked "!! [6/9] could not write the backup of ${LIVE[$r]} - nothing placed"; done
if [ -e "$OFFSW" ]; then
  say "       $OFFSW was already on ($(head -c 120 "$OFFSW" 2>/dev/null)) -- left exactly as found"
else
  mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" && OFF_MINE=1 || stop_unlocked "!! [6/9] could not write $OFFSW - nothing placed"
fi
for r in $EREL; do
  L="${LIVE[$r]}"; STG="$(dirname "$L")/.$(basename "$L").s644"
  { cat "$SCR/built/$r" > "$STG" && [ "$(m5 "$STG")" = "${TO[$r]}" ]; } || { rm -f "$FIN"/.*.s644 "$FIN"/finance_ui/.*.s644 "$FIN"/spine/.*.s644; [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; stop_unlocked "!! [6/9] could not stage $L - nothing placed"; }
  chmod --reference="$L" "$STG" 2>/dev/null; chown --reference="$L" "$STG" 2>/dev/null
done
PLACED=1
for r in $EREL; do L="${LIVE[$r]}"; mv -f "$(dirname "$L")/.$(basename "$L").s644" "$L" || restore "the rename of $L"; [ "$(m5 "$L")" = "${TO[$r]}" ] || restore "the md5 read back of $L"; done
say "[6/9] placed and read back: six files at their TO pins (backups *.bak_S644_<from8>; the database $DBBAK)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000; for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/porders/api/rules/state); c3=$(health /finance/approvals)
case "$c2" in 302|401|303) ;; *) restore "api/rules/state answered $c2 without a login (302 = the login gate, expected)";; esac
case "$c3" in 302|401|303) ;; *) restore "the approvals page answered $c3 without a login (302 = the login gate, expected)";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q -i "not mounted" && restore "a finance module not mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[7/9] $SVC restarted at $T0 (the box's clock) and active - healthz $c1 - rules api $c2, approvals page $c3 without a login; journal clean"

say "       the data step (the columns, the settings, the display columns, the model):"
( cd "$FIN" && FINANCE_DB="$DB" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -B - "$DB" <<'PYEOF' 2>&1 ) | mask | sed 's/^/       /'
import sqlite3, sys, os
sys.path.insert(0, os.getcwd())
import order_rules as OR
con = sqlite3.connect(sys.argv[1], timeout=60)
con.row_factory = sqlite3.Row
OR.ensure(con)                                                        # the four columns (rhythm_mode seeded once) + the eleven settings (INSERT OR IGNORE)
n = OR._s644_refresh_columns(con)
cols = [r[1] for r in con.execute("PRAGMA table_info(order_supplier_rule)")]
modes = dict(con.execute("SELECT rhythm_mode, COUNT(*) FROM order_supplier_rule GROUP BY 1").fetchall())
src = OR._setting(con, "order.source", "marg_sheet")
before = OR._setting(con, "order.model", "fixed")
if src == "marg_sheet" and before != "levels":
    OR._set_setting(con, "order.model", "levels", "S644_install", note="S644 -- " + OR.SETTINGS["order.model"][1])
    con.commit()
after = OR._setting(con, "order.model", "fixed")
print("columns:", ", ".join(c for c in cols if c in ("rhythm_mode", "review_days", "bill_days90", "rhythm_at")), "| rhythm_mode:", dict(modes), "| display columns refreshed for", n, "suppliers")
print("settings:", con.execute("SELECT COUNT(*) FROM setting WHERE key IN (%s)" % ",".join("?" * len(OR.S644_KEYS)), list(OR.S644_KEYS)).fetchone()[0], "of", len(OR.S644_KEYS), "S644 keys present")
print("order.source =", src, "(read, never written) | order.model:", before, "->", after, ("(levels: Darpan's sheet decides the order; the system's list is made and scored in the background)" if after == "levels" else "(stays fixed: the source is not marg_sheet -- flip it from the Buying rules fold when you are ready)"))
t = OR._today().isoformat()
rows = con.execute("SELECT kind, status, COUNT(*) FROM order_proposal WHERE day=? GROUP BY 1,2", (t,)).fetchall()
print("today's proposals (%s):" % t, [tuple(r) for r in rows] or "none yet (the 09:00 prepare makes them; before 13:00 an untouched list is made again when an input moves)")
print("staff screens: nothing new at this minute -- on order.source = marg_sheet no staff page draws the proposals (the old page ?old=1 shows them to the owner)")
PYEOF
if [ "$OFF_MINE" = 1 ]; then rm -f "$OFFSW"; say "[8/9] $OFFSW removed (this kit's)"; else say "[8/9] $OFFSW not this kit's -- left as found"; fi
release_lock
say "[9/9] the build lock released"
UNDO=""; for r in $EREL; do UNDO="$UNDO\\cp -p $(bak "$r") ${LIVE[$r]} && "; done
say "undo (one line): ${UNDO}$SYSTEMCTL restart $SVC   (the new columns and settings are harmless to the old bytes; order.model is read by nobody there)"
say "$KIT: DONE"
exit 0
