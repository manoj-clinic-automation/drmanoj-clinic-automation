#!/bin/bash
# =============================================================================
#  install_S868_DOCTOR_OFF_DAY.sh · kit S868 (the parent, S480, 18-Nov-2026) · his "proceed" 12:11
#  A day Dr Manoj does not sit:
#   1. NEW /root/finance/off_days.py              his page /finance/console/off-days ("Not sitting today", a day ahead, take back)
#   2. /root/finance/docterz_pickup.py  FROM a26c1467 -> TO   an EMPTY consultation report is that day's report when the day has
#      no OPD slip (or he marked it) -- the day marked not sitting; on a day with OPD slips it is set aside and said
#   3. /root/finance/owner_console.py   FROM bbe47872 -> TO   mounts the page; "No consultations -- you were not sitting"; a link
#   4. /root/finance/pc_kits.py         FROM 9353d510 -> TO   the reception PC heard lately = Working; the lab PC's item named
#   then marks 16, 17 and 18-Nov-2026 not sitting (his word, 18-Nov 12:08).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s868kit && cp -rp /root/deploy/repo/deploy_kits/S868_DOCTOR_OFF_DAY /tmp/s868kit && bash /tmp/s868kit/install_S868_DOCTOR_OFF_DAY.sh
#  DRY=1 before bash: every gate, the walk and the console shape; nothing live changes.   --undo: the three files back, the page out
#  (the marks stay in finance.db -- they only ever say 'no consultations' for those days).
# =============================================================================
set -u
KIT="S868_DOCTOR_OFF_DAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="docterz_pickup.py owner_console.py pc_kits.py"
NEWF="off_days.py"
MARK_DAYS="${MARK_DAYS:-2026-11-16 2026-11-17 2026-11-18}"
from_of() { case "$1" in docterz_pickup.py) echo a26c1467314a754f8966bfbf72c00b2b;; owner_console.py) echo bbe4787209c6f8b04bcdb46660785a6f;; pc_kits.py) echo 9353d510682c8278e911f65ebdc1e820;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s868_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
isfrom() { [ "$(m5 "$FIN/$1")" = "$(from_of "$1")" ]; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S868_$(from_of "$1" | cut -c1-8)"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES $NEWF; do rm -f "$FIN/.$n.s868"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do [ -f "$(bak "$n")" ] && \cp -p "$(bak "$n")" "$FIN/$n"; done
  [ -f "$FIN/$NEWF" ] && mv -f "$FIN/$NEWF" "$FIN/$NEWF.undone_S868"
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do say "   $n $(m5 "$FIN/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   off_days.py set aside; $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }   # as the app runs (F-1444)

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do isfrom "$n" || U=0; done
  [ "$U" = 1 ] && [ ! -f "$FIN/$NEWF" ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  for n in $NAMES; do isfrom "$n" || [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || { say "!! $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), not this kit's - nothing undone. Tell Claude."; exit 1; }; done
  for n in $NAMES; do isfrom "$n" && continue; b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  for n in $NAMES; do isfrom "$n" || \cp -p "$(bak "$n")" "$FIN/$n"; done
  [ -f "$FIN/$NEWF" ] && mv -f "$FIN/$NEWF" "$FIN/$NEWF.undone_S868"
  "$SYSTEMCTL" restart "$FSVC"; h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (three files back, the page out; $FSVC restarted, finance healthz 200; the marks stay in finance.db)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES $NEWF; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
ALL=1; for n in $NAMES $NEWF; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do isfrom "$n" || stop "!! [2/5] $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), expected $(from_of "$n" | cut -c1-8) - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
[ -e "$FIN/$NEWF" ] && stop "!! [2/5] $FIN/$NEWF already exists and is not this kit's - STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do for n in $NAMES $NEWF; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $p - nothing installed"; done; done
say "[2/5] the live pins exact; no off_days.py yet; all four files compile on both pythons"
{ mkdir -p "$SCR/fin_new" "$SCR/fin_old" && cp -p "$FIN"/*.py "$SCR/fin_new/" && cp -p "$FIN"/*.py "$SCR/fin_old/" && for n in $NAMES $NEWF; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n"; done && \cp -p "$KDIR/$NEWF" "$SCR/fin_old/$NEWF"; } || stop "!! [3/5] could not lay out the walk - nothing installed"
R1=$(pya "$KDIR/walk_s868.py" "$SCR/fin_new" "$SCR/w_new" | tail -1)
case "$R1" in "WALK 34/34") ;; *) stop "!! [3/5] walk_s868 (made-up root) on the new files: $R1 - nothing installed";; esac
R1c=$(pya "$KDIR/walk_s868.py" "$SCR/fin_old" "$SCR/w_old" | tail -1)
case "$R1c" in "WALK 34/34") stop "!! [3/5] walk_s868's control (the live files + the new page) did not go red - nothing installed";; esac
# the console's shape on a COPY of the live database: every section read, old against new; only the 'work' section may change
cp -p "$FIN"/*.json "$SCR/fin_new/" 2>/dev/null; cp -p "$FIN"/*.json "$SCR/fin_old/" 2>/dev/null; rm -f "$SCR/fin_old/$NEWF"
pya -c "import sqlite3,sys;s=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close()" "$FIN/finance.db" "$SCR/shape.db" >/dev/null || stop "!! [3/5] could not copy the database for the shape check - nothing installed"
for w in old new; do (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 280 "$APY" -W ignore -B "$SCR/fin_$w/owner_console.py" --build --db "$SCR/shape.db" --out "$SCR/c_$w.json" > "$SCR/c_$w.log" 2>&1); done
SH=$("$APY" - "$SCR/c_old.json" "$SCR/c_new.json" <<'PY' 2>&1
import json, sys
try:
    a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
except Exception as e:
    print("BAD the console did not build: %s" % e); sys.exit()
if b.get("failed"):
    print("BAD sections not read on the new files: %s" % b.get("failed")); sys.exit()
import re
bad = []
n = lambda s: re.sub(r"\d+", "#", str(s or ""))          # a clock or a count read seconds apart is not a change
for k in a["sections"]:
    la = [n(l.get("text")) for l in a["sections"][k].get("lines", [])]
    lb = [n(l.get("text")) for l in b["sections"].get(k, {}).get("lines", [])]
    if la != lb and k not in ("work", "system"):
        bad.append(k)
print(("BAD sections changed: %s" % ", ".join(bad)) if bad else "OK %d sections, only 'work' (and the timing line) changed" % len(b["sections"]))
PY
)
case "$SH" in OK*) ;; *) stop "!! [3/5] the console's shape: $SH - nothing installed";; esac
say "[3/5] walk_s868 $R1 (made-up root, every role; control red: $R1c); console on a copy of the live database: $SH"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the console's shape green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$FIN/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES $NEWF; do st="$FIN/.$n.s868"; ref="$FIN/$n"; [ -f "$ref" ] || ref="$FIN/owner_console.py"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$ref" "$st" 2>/dev/null; chown --reference="$ref" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in $NEWF pc_kits.py docterz_pickup.py owner_console.py; do mv -f "$FIN/.$n.s868" "$FIN/$n" || restore "the rename of $n"; done
for n in $NAMES $NEWF; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/console /finance/console/off-days /finance/pcs; do pg=$(fget "$u"); case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg";; esac; done
release_lock
say "[4/5] placed and read back: off_days.py + three files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the three pages answer"
say "      undo (one line): bash $KDIR/install_$KIT.sh --undo"
MK=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata "$APY" -W ignore -B - "$FIN" $MARK_DAYS <<'PY' 2>&1 | tail -1
import sys, sqlite3
sys.path.insert(0, sys.argv[1]); import off_days as o
con = sqlite3.connect(sys.argv[1] + "/finance.db", timeout=60)
out = []
for d in sys.argv[2:]:
    ok, why = o.mark(con, d, "manoj", "owner", "his word in chat, 18-Nov-2026 12:08: not sitting the last 2 days and today")
    out.append("%s %s" % (d[8:10], "marked" if ok else "not marked (%s)" % why))
print("; ".join(out))
PY
)
say "[5/5] his days not sitting: $MK"
say ""; say "$KIT: DONE. Your page: https://followup.dr-manoj.in/finance/console/off-days"; exit 0
