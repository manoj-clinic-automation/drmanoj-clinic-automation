#!/bin/bash
# =============================================================================
#  install_S963_STOCK_VOUCHERS.sh · kit S963 (26-Nov-2026, Sanjeevni session 530) · the owner's "proceed" of 16:16 IST on mock-up v4 (D1083,
#  D1084). Marg's STOCK ISSUE and STOCK RECEIVE reports (one per period, taken by him) read at the server's door, NAME-FREE, into
#  mi_voucher_file / mi_voucher / mi_voucher_line (+ the views mi_voucher_now / mi_voucher_line_now: a later report of the same days replaces
#  them, never doubles). The medical PC's reader (marg_txt.py S963) goes by Drive's ToMedical\_kit AFTER this, by the chat.
#   1. /root/marg_ingest/signatures.json 50ca61f4 -> TO (two signatures, STOCK_VOUCHERS ISSUE / RECEIVE)
#   2. /root/marg_ingest/marg_take.py    bc621caf -> TO (one hook)      3. /root/marg_ingest/marg_ingest.py b11099ff -> TO (one hook)
#   4. NEW /root/marg_ingest/marg_vouchers.py
#  Rebuilt HERE from the live bytes (make_s963.py), checked against TO_PINS.md5. Placed under the collector's own lock; clinic-finance
#  restarted (the upload door lives in it).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s963kit && cp -rp /root/deploy/repo/deploy_kits/S963_STOCK_VOUCHERS /tmp/s963kit && bash /tmp/s963kit/install_S963_STOCK_VOUCHERS.sh
#  (DRY=1 before bash: every gate, the walk and the control; NOTHING written.)
# =============================================================================
set -u
KIT="S963_STOCK_VOUCHERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; MLOCK="${MLOCK:-/tmp/marg_ingest.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="marg_ingest/signatures.json marg_ingest/marg_take.py marg_ingest/marg_ingest.py"
NEW="marg_ingest/marg_vouchers.py"
from_of() { case "$1" in marg_ingest/signatures.json) echo 50ca61f470da66dcc7b22f32f9740190;; marg_ingest/marg_take.py) echo bc621caf202de958517cd5e8d9c25290;;
  marg_ingest/marg_ingest.py) echo b11099ffdf66f6fd78409cecd36a1ec5;; esac; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s963_inst_$STAMP"; TOOK_LOCK=0; HELD_M=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/$1.bak_S963_${f:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s963"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
take_m() { exec 9>>"$MLOCK" && flock -w "${MWAIT:-120}" 9 && HELD_M=1; }
free_m() { [ "$HELD_M" = 1 ] || return 0; flock -u 9; exec 9>&-; HELD_M=0; }
release_lock() { free_m; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES $NEW; do rm -f "$(stg "$n")"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the three files back and taking the new reader away (tables it made stay; nothing reads them)"
  [ "$HELD_M" = 1 ] || take_m || say "   (the collector's lock was not free in ${MWAIT:-120} s - putting the files back anyway)"
  for n in $NAMES; do st="$(stg "$n")"; { cat "$(bak "$n")" > "$st" && mv -f "$st" "$ROOT/$n"; } || \cp -p "$(bak "$n")" "$ROOT/$n"; done
  rm -f "$ROOT/$NEW"; "$SYSTEMCTL" restart "$FSVC" || true
  free_m
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $NEW present: $([ -e "$ROOT/$NEW" ] && echo yes || echo no) (expected no)"
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/marg_ingest/lib" \
  && find "$ROOT/marg_ingest" -maxdepth 1 -type f \( -name '*.py' -o -name '*.json' \) -exec cp -p {} "$d/marg_ingest/" \; \
  && { \cp -p "$ROOT"/marg_ingest/lib/*.py "$d/marg_ingest/lib/" 2>/dev/null; true; } && rm -f "$d/marg_ingest/marg_vouchers.py" \
  && [ -f "$d/marg_ingest/marg_take.py" ]; }
walk() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s963.py" "$1" "$KDIR" 2>&1); }
full() { case "$1" in "WALK "*) local a=${1#WALK }; [ "${a%/*}" = "${a#*/}" ];; *) return 1;; esac; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES $NEW; do [ -n "$(to_of "$n")" ] || { say "!! [1/6] no TO pin for $n - nothing installed"; exit 1; }; done
for n in $NAMES; do [ -f "$ROOT/$n" ] || { say "!! [1/6] the live file $ROOT/$n is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/6] $DB missing - nothing installed"; exit 1; }
ALL=1; for n in $NAMES $NEW; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
[ -e "$ROOT/$NEW" ] && { say "!! [1/6] $ROOT/$NEW already exists and is not this kit's - nothing installed. Tell Claude."; exit 1; }
mkdir -p "$SCR/built/marg_ingest" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi

for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/6] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
"$APY" -B make_s963.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/6] the builder refused - nothing installed"; }
\cp -p "$KDIR/marg_vouchers.py" "$SCR/built/$NEW" || stop "!! [2/6] could not copy the new reader - nothing installed"
for n in $NAMES $NEW; do [ "$(m5 "$SCR/built/$n")" = "$(to_of "$n")" ] || stop "!! [2/6] rebuilt, $n is not at its TO pin - nothing installed"; done
for py in "$APY" "$VPY"; do for n in $NAMES $NEW; do case "$n" in *.py) PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$n" || stop "!! [2/6] $n does not compile on $py - nothing installed";; esac; done
  "$py" -c "import json,sys;json.load(open(sys.argv[1]))" "$SCR/built/marg_ingest/signatures.json" || stop "!! [2/6] signatures.json does not parse on $py - nothing installed"; done
say "[2/6] three live pins exact; rebuilt here at their TO pins with the new reader; every .py compiles and the signatures parse on both pythons"

lay new && for n in $NAMES $NEW; do \cp -p "$SCR/built/$n" "$SCR/root_new/$n" || stop "!! [3/6] could not copy $n into the walk's layout - nothing installed"; done || stop "!! [3/6] could not lay out the walk - nothing installed"
O=$(walk "$SCR/root_new"); R=$(printf '%s\n' "$O" | tail -1)
printf '%s\n' "$O" | grep -E "^FAIL|Error" | head -8 | sed 's/^/      /'
full "$R" || stop "!! [3/6] walk_s963 on the rebuilt files: $R - nothing installed"
lay old || stop "!! [3/6] could not lay out the control - nothing installed"
R0=$(walk "$SCR/root_old" | tail -1); full "$R0" && stop "!! [3/6] the control on the live files did not go red ($R0) - nothing installed"
RS=$(cd "$SCR/root_new/marg_ingest" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B marg_router.py --selftest 2>&1 | tail -1)
RS0=$(cd "$SCR/root_old/marg_ingest" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B marg_router.py --selftest 2>&1 | tail -1)
[ "$RS" = "$RS0" ] || stop "!! [3/6] the router's own selftest differs with the new signatures ('$RS', live '$RS0') - nothing installed"
say "[3/6] walk_s963 (made-up reports, a scratch database): $R; the control on the live files: red ($R0); the router's selftest unchanged ($RS)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the control green; NOTHING written"; exit 0; fi

f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
for n in $NAMES $NEW; do st=$(stg "$n"); ref="$ROOT/$n"; [ -e "$ref" ] || ref="$ROOT/marg_ingest/marg_take.py"
  { cat "$SCR/built/$n" > "$st" && chmod --reference="$ref" "$st" 2>/dev/null; chown --reference="$ref" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(m5 "$SCR/built/$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
take_m || stop "!! [4/6] the collector's lock $MLOCK was not free within ${MWAIT:-120} s - nothing placed. Run it again."
for n in $NEW marg_ingest/marg_ingest.py marg_ingest/marg_take.py marg_ingest/signatures.json; do
  mv -f "$(stg "$n")" "$ROOT/$n" || restore "the rename of $n"; done
for n in $NAMES $NEW; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
free_m
say "[4/6] placed under the collector's lock and read back: three files and the new reader at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
TB=$(cd "$ROOT/marg_ingest" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B -c "import sqlite3,sys;sys.path.insert(0,'.');import marg_vouchers as M;c=sqlite3.connect(sys.argv[1],timeout=60);M.ensure(c);c.commit();n=[r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE name LIKE 'mi_voucher%' ORDER BY name\")];print(' '.join(n))" "$DB" 2>&1 | tail -1)
say "      $TB"
[ "$TB" = "mi_voucher mi_voucher_file mi_voucher_line mi_voucher_line_now mi_voucher_now" ] || restore "the tables: $TB"
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
release_lock
say "[5/6] the voucher tables and the two views made in finance.db"
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s963.sh  (the three backups back, the new reader gone, $FSVC restarted)"
say ""
say "$KIT: DONE. The server now reads Marg's Stock Issue / Stock Receive reports. Claude puts the medical PC's reader in place next."
exit 0
