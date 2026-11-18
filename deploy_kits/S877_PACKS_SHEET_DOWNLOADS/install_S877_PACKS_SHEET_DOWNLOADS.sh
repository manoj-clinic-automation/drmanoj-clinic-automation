#!/bin/bash
# =============================================================================
#  install_S877_PACKS_SHEET_DOWNLOADS.sh · kit S877 (the parent, S484, 18-Nov-2026) · his word of 14:49 (D1011): the sheets
#   1. /root/finance/packs.html FROM d931f746 -> TO   every xlsx link of the pack table (4.4 the card sheet, 1, 2 + the bank
#      check, 7) downloads in place with one click -- no new window that opens and closes (F-1474, F-1476) -- and a note
#      beside the link says it is downloading and where it lands. PDFs and pages still open a tab.
#   2. /root/finance/packs.py   FROM b1174cb0 -> TO   sheet 7 (and NK Pathology's sheet) laid out to be read: widths, wrapped
#      text, the header shaded, frozen and filtered, Rs money, real dates, the TOTAL row bold, prints one page wide.
#      No figure changes; the other sheets are written as before.
#   clinic-finance restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s877kit && cp -rp /root/deploy/repo/deploy_kits/S877_PACKS_SHEET_DOWNLOADS /tmp/s877kit && bash /tmp/s877kit/install_S877_PACKS_SHEET_DOWNLOADS.sh
#  DRY=1 before bash: every gate, the walks and the shape check on a copy of the live database; nothing live changes.
#  --undo: the two files back.
# =============================================================================
set -u
KIT="S877_PACKS_SHEET_DOWNLOADS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="packs.py packs.html"
from_of() { case "$1" in packs.py) echo b1174cb08c4de39c6dd28ca32aa74d34;; packs.html) echo d931f746c0deda6404834106d97a298e;; esac; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s877_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
isfrom() { [ "$(m5 "$FIN/$1")" = "$(from_of "$1")" ]; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S877_$(from_of "$1" | cut -c1-8)"; }
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES; do rm -f "$FIN/.$n.s877"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do [ -f "$(bak "$n")" ] && \cp -p "$(bak "$n")" "$FIN/$n"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do say "   $n $(m5 "$FIN/$n" | cut -c1-8) (expected $(from_of "$n" | cut -c1-8))"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release_lock; exit 1; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }   # as the app runs (F-1444: no -s)

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do isfrom "$n" || U=0; done
  [ "$U" = 1 ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  for n in $NAMES; do isfrom "$n" || [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || { say "!! $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), not this kit's - nothing undone. Tell Claude."; exit 1; }; done
  for n in $NAMES; do isfrom "$n" && continue; b=$(bak "$n"); [ -f "$b" ] && [ "$(m5 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  for n in $NAMES; do isfrom "$n" || \cp -p "$(bak "$n")" "$FIN/$n"; done; "$SYSTEMCTL" restart "$FSVC"
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (packs.py + packs.html back; $FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do isfrom "$n" || stop "!! [2/5] $FIN/$n is $(m5 "$FIN/$n" | cut -c1-8), expected $(from_of "$n" | cut -c1-8) - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/packs.py" || stop "!! [2/5] packs.py does not compile on $p - nothing installed"; done
say "[2/5] the live pins exact; packs.py compiles on both pythons"
{ mkdir -p "$SCR/fin_new" "$SCR/fin_old" && cp -p "$FIN"/*.py "$FIN"/*.html "$SCR/fin_new/" && cp -p "$FIN"/*.py "$FIN"/*.html "$SCR/fin_old/" && for n in $NAMES; do \cp -p "$KDIR/$n" "$SCR/fin_new/$n"; done; } || stop "!! [3/5] could not lay out the walks - nothing installed"
R1=$(pya "$KDIR/walk_s877.py" "$SCR/fin_new" "$SCR/w_new" | tail -1)
case "$R1" in "WALK 25/25") ;; *) pya "$KDIR/walk_s877.py" "$SCR/fin_new" "$SCR/w_new2" | grep FAIL | head -6; stop "!! [3/5] walk_s877 (made-up) on the new files: $R1 - nothing installed";; esac
R1c=$(pya "$KDIR/walk_s877.py" "$SCR/fin_old" "$SCR/w_old" | tail -1)
case "$R1c" in "WALK 25/25") stop "!! [3/5] walk_s877's control (the live files) did not go red - nothing installed";; esac
R2=$(pya "$KDIR/walk_s875.py" "$SCR/fin_new" "$SCR/w875" | tail -1)
case "$R2" in "WALK 34/34") ;; *) stop "!! [3/5] S875's walk on the new files: $R2 - nothing installed";; esac
R3=$(pya "$KDIR/walk_s866.py" "$SCR/fin_new" "$SCR/w866" | tail -1)
case "$R3" in "WALK 18/18") ;; *) stop "!! [3/5] S866's walk on the new files: $R3 - nothing installed";; esac
R4=$(pya "$KDIR/walk_s873.py" "$SCR/fin_new" "$SCR/w873" | tail -1)
case "$R4" in "WALK 11/11") ;; *) stop "!! [3/5] S873's walk on the new files: $R4 - nothing installed";; esac
# the shape: last month's pack on a COPY of the live database, old against new -- every row and every attachment name the
# same (this kit changes no figure, only sheet 7's layout and the page's links); and sheet 7 from the copy reads laid out
pya -c "import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close()" "$FIN/finance.db" "$SCR/shape.db" >/dev/null || stop "!! [3/5] could not copy the database for the shape check - nothing installed"
cp -p "$SCR/shape.db" "$SCR/shape_old.db"
SHAPE='import sys,sqlite3,json,datetime as dt,io
sys.path.insert(0,sys.argv[1]);import packs as p
con=sqlite3.connect(sys.argv[2]);con.row_factory=sqlite3.Row
t=dt.date.today().replace(day=1)-dt.timedelta(days=1);m=t.strftime("%Y-%m")
r,att=p.pack_rows(con,m)
for x in r: print(json.dumps(["R",x["key"],x["status"],x["why"]],ensure_ascii=False))
for a in att:
  if a[1]: print(json.dumps(["A",a[0]],ensure_ascii=False))
b,why=p.build_digest(con,m)
fz=""
if b:
  from openpyxl import load_workbook
  fz=str(load_workbook(io.BytesIO(b)).worksheets[0].freeze_panes)
print(json.dumps(["D",bool(b),fz]))'
pya -c "$SHAPE" "$SCR/fin_old" "$SCR/shape_old.db" > "$SCR/shape_old.txt" || stop "!! [3/5] the shape check could not run on the live files: $(tail -2 "$SCR/shape_old.txt" | tr -d '\n' | cut -c1-200) - nothing installed"
pya -c "$SHAPE" "$SCR/fin_new" "$SCR/shape.db" > "$SCR/shape_new.txt" || stop "!! [3/5] the shape check could not run on the new files: $(tail -2 "$SCR/shape_new.txt" | tr -d '\n' | cut -c1-200) - nothing installed. Tell Claude."
SH=$("$APY" - "$SCR/shape_old.txt" "$SCR/shape_new.txt" <<'PY'
import json, sys
def rd(p):
    out = []
    for l in open(p):
        try:
            out.append(json.loads(l))
        except ValueError:
            pass
    return out
a, b = rd(sys.argv[1]), rd(sys.argv[2])
ra = [x for x in a if x[0] == "R"]; rb = [x for x in b if x[0] == "R"]
aa = [x[1] for x in a if x[0] == "A"]; ab = [x[1] for x in b if x[0] == "A"]
db = [x for x in b if x[0] == "D"]
bad = sum(1 for x, y in zip(ra, rb) if x != y)
laid = bool(db) and ((not db[0][1]) or db[0][2] == "A3")
ok = len(ra) >= 10 and len(ra) == len(rb) and bad == 0 and aa == ab and laid
print("%s rows=%d differing=%d attachments %d->%d sheet7_built=%s frozen_at=%s" % ("OK" if ok else "BAD", len(rb), bad, len(aa), len(ab), db[0][1] if db else "?", db[0][2] if db else "?"))
PY
)
case "$SH" in OK*) ;; *) stop "!! [3/5] the shape check: $SH - nothing installed. Tell Claude.";; esac
say "[3/5] walk_s877 $R1 (made-up; control red: $R1c); S875's walk $R2; S866's $R3; S873's $R4; last month's pack on a copy of the live database: $SH"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the shape green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$FIN/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for n in $NAMES; do st="$FIN/.$n.s877"; { cat "$KDIR/$n" > "$st" && chmod --reference="$FIN/$n" "$st" 2>/dev/null; chown --reference="$FIN/$n" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in packs.html packs.py; do mv -f "$FIN/.$n.s877" "$FIN/$n" || restore "the rename of $n"; done
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
pg=$(fget /finance/packs); case "$pg" in 200|302|303|401|403) ;; *) restore "the packs page answered $pg";; esac
release_lock
say "[4/5] placed and read back: packs.py + packs.html at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the page answers $pg"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""; say "$KIT: DONE. Your page: https://followup.dr-manoj.in/finance/packs"; exit 0
