#!/bin/bash
# =============================================================================
#  install_S866_PACKS_LATE_AND_CARD_BILL.sh · kit S866 (the parent, S480, 18-Nov-2026) · his word 09:05 on /finance/packs
#  "1050 not there · card statements not decrypted · only one electricity bill -- rectify, and never again":
#   1. cron: the statement shelf also reads Drive at 09:15, 13:15 and 19:15 IST (a statement saved after 07:30 waited a day)
#      15 9,13,19 * * * ... stmt_shelf.py run   # S866_SHELF_LATER        -- and ONE read now, at the end of this install
#   2. /root/finance/packs.py   FROM 7dc8c39a -> TO   a card says its TRUE reason: here but locked (no card password stored) /
#      the bank never mailed the month's statement (a later one came) / not come yet; the electricity line names the card
#      statement its second bill waits on. A newer locked statement never makes the month 'late'.
#   3. /root/finance/packs.html FROM f5991911 -> TO   the shelf's card cell shows that reason (not "no decrypted twin")
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s866kit && cp -rp /root/deploy/repo/deploy_kits/S866_PACKS_LATE_AND_CARD_BILL /tmp/s866kit && bash /tmp/s866kit/install_S866_PACKS_LATE_AND_CARD_BILL.sh
#  DRY=1 before bash: every gate, the walk and the shape check; nothing live changes.   --undo: the two files back, the cron line out.
# =============================================================================
set -u
KIT="S866_PACKS_LATE_AND_CARD_BILL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CRONTAB="${CRONTAB:-crontab}"; MARK="# S866_SHELF_LATER"; MIN_CRON="${MIN_CRON:-20}"
CRONLINE="15 9,13,19 * * * cd $FIN && FINANCE_DB=$FIN/finance.db $VPY -B $FIN/stmt_shelf.py run >> $FIN/stmt_shelf.log 2>&1 $MARK"
NAMES="packs.py packs.html"
from_of() { case "$1" in packs.py) echo 7dc8c39a83965b5839cac46138bb1d63;; packs.html) echo f5991911369c65583673ff26d22dcaba;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s866_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
isfrom() { [ "$(m5 "$FIN/$1")" = "$(from_of "$1")" ]; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S866_$(from_of "$1" | cut -c1-8)"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$FIN/.$n.s866"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
cron_has() { "$CRONTAB" -l 2>/dev/null | grep -qF "$MARK"; }
cron_read() { "$CRONTAB" -l > "$SCR/cron.cur" 2>/dev/null && [ "$(grep -c . "$SCR/cron.cur")" -ge "$MIN_CRON" ]; }
cron_drop() { cron_read || { say "!! the crontab could not be read whole - left as it is"; return 1; }
  grep -vF "$MARK" "$SCR/cron.cur" > "$SCR/cron.new"; [ "$(grep -c . "$SCR/cron.new")" -ge "$MIN_CRON" ] && "$CRONTAB" "$SCR/cron.new"; }
restore() { say "!! RED after placing ($1) - putting everything back"
  mkdir -p "$SCR"
  for _t in 1 2 3; do if cron_read; then grep -qF "$MARK" "$SCR/cron.cur" && cron_drop; break; fi; sleep "${NAP:-2}"; done
  if cron_read; then grep -qF "$MARK" "$SCR/cron.cur" && CR="the cron line is STILL THERE" || CR="no S866 cron line"; else CR="the crontab could not be read, so the S866 line may still be there (it only reads Drive, as the 05:40 one)"; fi
  for n in $NAMES; do [ -f "$(bak "$n")" ] && \cp -p "$(bak "$n")" "$FIN/$n"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do say "   $n $(m5 "$FIN/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   $CR; $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }   # as the app runs (F-1444: no -s)

if [ "${1:-}" = "--undo" ]; then
  mkdir -p "$SCR"
  U=1; for n in $NAMES; do isfrom "$n" || U=0; done
  [ "$U" = 1 ] && ! cron_has && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  for n in $NAMES; do isfrom "$n" || [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || { say "!! $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), not this kit's - nothing undone. Tell Claude."; exit 1; }; done
  for n in $NAMES; do isfrom "$n" && continue; b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  cron_has && { cron_drop || { say "!! the cron line could not be removed (the crontab did not read whole) - nothing undone. Run it again in a minute."; release_lock; exit 1; }; }
  for n in $NAMES; do isfrom "$n" || \cp -p "$(bak "$n")" "$FIN/$n"; done; "$SYSTEMCTL" restart "$FSVC"
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (the two files back, no S866 cron line; $FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && cron_has && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do isfrom "$n" || stop "!! [2/5] $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), expected $(from_of "$n" | cut -c1-8) - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
cron_has && stop "!! [2/5] the crontab already holds a $MARK line - STOP, nothing installed. Tell Claude."
cron_read || stop "!! [2/5] the crontab could not be read whole - nothing installed"
[ "$(grep -c 'stmt_shelf.py run' "$SCR/cron.cur")" -ge 1 ] || stop "!! [2/5] no stmt_shelf.py line in the crontab (expected 05:40 and 07:30) - STOP, nothing installed. Tell Claude."
[ -f "$FIN/stmt_shelf.py" ] || stop "!! [2/5] $FIN/stmt_shelf.py is not there - nothing installed"
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/packs.py" || stop "!! [2/5] packs.py does not compile on $p - nothing installed"; done
say "[2/5] the live pins exact; no S866 cron line yet; the shelf's own lines there; packs.py compiles on both pythons"
{ mkdir -p "$SCR/fin_new" "$SCR/fin_old" && cp -p "$FIN"/*.py "$FIN"/packs*.html "$SCR/fin_new/" && cp -p "$FIN"/*.py "$FIN"/packs*.html "$SCR/fin_old/" && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n"; done; } || stop "!! [3/5] could not lay out the walk - nothing installed"
R1=$(pya "$KDIR/walk_s866.py" "$SCR/fin_new" "$SCR/w_new" | tail -1)
case "$R1" in "WALK 18/18") ;; *) stop "!! [3/5] walk_s866 (made-up shelf) on the new files: $R1 - nothing installed";; esac
R1c=$(pya "$KDIR/walk_s866.py" "$SCR/fin_old" "$SCR/w_old" | tail -1)
case "$R1c" in "WALK 18/18") stop "!! [3/5] walk_s866's control (the live files) did not go red - nothing installed";; esac
# the shape: last month's pack on a COPY of the live database, old against new -- only the card rows and the electricity row may differ
pya -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close()" "$FIN/finance.db" "$SCR/shape.db" >/dev/null || stop "!! [3/5] could not copy the database for the shape check - nothing installed"
cp -p "$SCR/shape.db" "$SCR/shape_old.db"
SHAPE='import sys,sqlite3,json,datetime as dt
sys.path.insert(0,sys.argv[1]);import packs as p
con=sqlite3.connect(sys.argv[2]);con.row_factory=sqlite3.Row
t=dt.date.today().replace(day=1)-dt.timedelta(days=1);m=t.strftime("%Y-%m")
r=p.pack_rows(con,m,light=True);r=r[0] if isinstance(r,tuple) else r
for x in r: print(json.dumps([x["key"],x["status"],x["why"]],ensure_ascii=False))'
pya -c "$SHAPE" "$SCR/fin_old" "$SCR/shape_old.db" > "$SCR/shape_old.txt"; pya -c "$SHAPE" "$SCR/fin_new" "$SCR/shape.db" > "$SCR/shape_new.txt"
NO=$(grep -c '^\[' "$SCR/shape_old.txt"); NN=$(grep -c '^\[' "$SCR/shape_new.txt")
[ "$NO" -ge 10 ] && [ "$NO" = "$NN" ] || stop "!! [3/5] the shape check: last month's pack read $NO rows on the live files, $NN on the new - nothing installed"
BAD=$("$APY" - "$SCR/shape_old.txt" "$SCR/shape_new.txt" <<'PY'
import json, sys
a = [json.loads(l) for l in open(sys.argv[1]) if l.startswith("[")]
b = [json.loads(l) for l in open(sys.argv[2]) if l.startswith("[")]
print(sum(1 for x, y in zip(a, b) if x != y and not (x[0] == y[0] and (x[0].startswith("card:") or x[0] == "electricity"))))
PY
)
[ "$BAD" = 0 ] || stop "!! [3/5] the shape check: $BAD row(s) other than the cards and electricity changed - nothing installed. Tell Claude."
TW=$(grep -c 'decrypted twin' "$SCR/shape_new.txt")
say "[3/5] walk_s866 $R1 (made-up shelf; control red: $R1c); shape: last month's pack on a copy of the live database, $NN rows, only the card and electricity rows changed ('decrypted twin' left: $TW)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the shape green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$FIN/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$FIN/.$n.s866"; { cat "$KDIR/$n" > "$st" && chmod --reference="$FIN/$n" "$st" 2>/dev/null; chown --reference="$FIN/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in packs.html packs.py; do mv -f "$FIN/.$n.s866" "$FIN/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
cron_read || restore "the crontab could not be read whole (nothing written to it)"
{ cat "$SCR/cron.cur"; echo "$CRONLINE"; } > "$SCR/cron.new" && "$CRONTAB" "$SCR/cron.new" || restore "the cron line"
[ "$("$CRONTAB" -l 2>/dev/null | grep -c .)" -ge "$(( $(grep -c . "$SCR/cron.cur") + 1 ))" ] || restore "the crontab read back shorter than before"
[ "$("$CRONTAB" -l 2>/dev/null | grep -cF "$MARK")" = 1 ] || restore "the cron line read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
pg=$(fget /finance/packs); case "$pg" in 200|302|303|401|403) ;; *) restore "the packs page answered $pg";; esac
release_lock
say "[4/5] placed and read back: packs.py + packs.html at their TO pins; one cron line (09:15, 13:15, 19:15); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the page answers $pg"
say "      undo (one line): bash $KDIR/install_$KIT.sh --undo"
say "[5/5] the shelf reads Drive now (up to 10 minutes) ..."
(cd "$FIN" && FINANCE_DB="$FIN/finance.db" timeout 600 "$VPY" -B "$FIN/stmt_shelf.py" run >> "$FIN/stmt_shelf.log" 2>&1); rc=$?
ST=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" "$APY" -W ignore -B - "$FIN" <<'PY' 2>&1 | tail -3
import sys, sqlite3, datetime as dt
sys.path.insert(0, sys.argv[1]); import packs as p
con = sqlite3.connect(sys.argv[1] + "/finance.db", timeout=60); con.row_factory = sqlite3.Row
t = dt.date.today().replace(day=1) - dt.timedelta(days=1); m = t.strftime("%Y-%m")
cl = p.cells(con, m)
emp = [c["label"] for c in cl if c["kind"] != "card" and c["state"] in ("empty", "partial")]
print("%s: %d statements on the shelf, %d still empty%s" % (p._month_name(m), sum(1 for c in cl if c["kind"] != "card" and c["state"] not in ("empty",)), len(emp), (" (" + "; ".join(emp) + ")") if emp else ""))
PY
)
say "      shelf read: exit $rc · $ST"
say ""; say "$KIT: DONE. Your page: https://followup.dr-manoj.in/finance/packs"; exit 0
