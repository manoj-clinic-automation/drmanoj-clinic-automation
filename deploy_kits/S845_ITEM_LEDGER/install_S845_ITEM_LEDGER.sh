#!/bin/bash
# =============================================================================
#  install_S845_ITEM_LEDGER.sh · kit S845 (16-Nov-2026, Sanjeevni session 470) · the owner's "ok" (09:46 IST) on the Item ledger mock-up v2
#  The Item ledger: one page for the doctor -- search any item; Marg stock and expected stock; scanned bills not yet in Marg (inline, their
#  read lines); the ledger by bill and voucher number, day by day against Marg's closing; red days = the Marg watch's own moves, with its
#  own "Ask Marg's Stock Register"; last 30 days / full ledger / a date range. READ ONLY: no table, no setting, no file is written by it.
#   1. NEW /root/finance/item_ledger.py
#   2. /root/finance/sanjeevni_approvals.py cd5174d6 -> TO   (one fail-soft block: the Hub mounts the ledger)
#   3. /root/finance/finance_ui/finance_approvals.html 9f629585 -> TO   (Go to: a search box and the link)
#  The two live files are rebuilt HERE from their live bytes (make_s845.py), checked against the TO pins. clinic-finance is restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s845kit && cp -rp /root/deploy/repo/deploy_kits/S845_ITEM_LEDGER /tmp/s845kit && bash /tmp/s845kit/install_S845_ITEM_LEDGER.sh
#  (DRY=1 before bash: every gate, the walks and the control; NOTHING written.)
# =============================================================================
set -u
KIT="S845_ITEM_LEDGER"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; SPDB="${SPDB:-$ROOT/finance/spine/spine.db}"
OLDK="${OLDK:-/root/deploy/repo/deploy_kits/S815_MARG_WATCH_DARPAN_REPORTS}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="finance/sanjeevni_approvals.py finance/finance_ui/finance_approvals.html"
NEW="finance/item_ledger.py"
from_of() { case "$1" in finance/sanjeevni_approvals.py) echo cd5174d6bfb9d62b55dd037e903e1d74;; finance/finance_ui/finance_approvals.html) echo 9f6295856e36f93a00028de7cc3fe769;; esac; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s845_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/$1.bak_S845_${f:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s845"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
flz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/sanjeevni/ledger/api/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/sanjeevni/ledger/api/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES $NEW; do rm -f "$(stg "$n")"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
PLACING=0
trap on_exit EXIT
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting the two files back and taking the new page away"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/$n"; done
  rm -f "$ROOT/$NEW"; "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $NEW present: $([ -e "$ROOT/$NEW" ] && echo yes || echo no) (expected no)"
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/finance_ui/*.html "$d/finance/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$d/finance/spine/" 2>/dev/null; \
  [ -f "$d/finance/sanjeevni_approvals.py" ] && [ -f "$d/finance/spine/spine_read.py" ]; }
w845() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="$SCR/spine.db" timeout 900 "$VPY" -u -W ignore -B "$KDIR/walk_s845.py" "$1" "$SCR/$2" --box 2>&1); }
w803() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -u -W ignore -B "$OLDK/walk_s803.py" "$1" "$ROOT/shared" "$2" "$SCR/finance_803.db" 2>&1); }
jnl() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; elif command -v journalctl >/dev/null 2>&1; then journalctl -u "$FSVC" --since "@$1" --no-pager 2>/dev/null; fi; }
full() { case "$1" in "WALK S845: "*" PASS, 0 FAIL") return 0;; *) return 1;; esac; }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES $NEW; do [ -n "$(to_of "$n")" ] || { say "!! [1/6] no TO pin for $n - nothing installed"; exit 1; }; done
for n in $NAMES; do [ -f "$ROOT/$n" ] || { say "!! [1/6] the live file $ROOT/$n is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$SPDB" ] || { say "!! [1/6] $DB or $SPDB missing - nothing installed"; exit 1; }
[ -f "$OLDK/walk_s803.py" ] || { say "!! [1/6] the Marg watch's walk is not in $OLDK - publish first. Nothing installed."; exit 1; }
ALL=1; for n in $NAMES $NEW; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
[ -e "$ROOT/$NEW" ] && { say "!! [1/6] $ROOT/$NEW already exists and is not this kit's - nothing installed. Tell Claude."; exit 1; }
mkdir -p "$SCR/built/finance/finance_ui" "$SCR/w803" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/6] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
"$APY" -B make_s845.py "$ROOT/finance" "$SCR/built/finance" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/6] the builder refused - nothing installed"; }
\cp -p "$KDIR/item_ledger.py" "$SCR/built/$NEW" || stop "!! [2/6] could not take the new page from the kit - nothing installed"
for n in $NAMES $NEW; do [ "$(m5 "$SCR/built/$n")" = "$(to_of "$n")" ] || stop "!! [2/6] rebuilt, $n is not at its TO pin - nothing installed"; done
for py in "$APY" "$VPY"; do for n in $NAMES $NEW; do case "$n" in *.py) PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$n" || stop "!! [2/6] $n does not compile on $py - nothing installed";; esac; done; done
say "[2/6] two live pins exact; rebuilt here at their TO pins with the new page; every .py compiles on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/finance.db" >/dev/null && "$VPY" -c "$CPDB" "$SPDB" "$SCR/spine.db" >/dev/null || stop "!! [3/6] could not copy the databases for the walk - nothing installed"
\cp -p "$SCR/finance.db" "$SCR/finance_ctl.db" && \cp -p "$SCR/finance.db" "$SCR/finance_803.db" || stop "!! [3/6] could not copy the database for the control - nothing installed"
lay new && for n in $NAMES $NEW; do \cp -p "$SCR/built/$n" "$SCR/root_new/$n" || stop "!! [3/6] could not copy $n into the walk's layout - nothing installed"; done || stop "!! [3/6] could not lay out the walk - nothing installed"
O=$(w845 "$SCR/root_new/finance" finance.db); R=$(printf '%s\n' "$O" | tail -1)
printf '%s\n' "$O" | grep -E "^FAIL|Error" | head -8 | sed 's/^/      /'
full "$R" || stop "!! [3/6] walk_s845: $R - nothing installed"
lay old || stop "!! [3/6] could not lay out the control - nothing installed"
R0=$(w845 "$SCR/root_old/finance" finance_ctl.db | tail -1); full "$R0" && stop "!! [3/6] the control on the live files did not go red ($R0) - nothing installed"
\cp -p "$SCR/built/finance/sanjeevni_approvals.py" "$SCR/built/finance/finance_ui/finance_approvals.html" "$ROOT/finance/marg_billwatch.py" "$ROOT/finance/owner_notice.py" "$SCR/w803/"
O4=$(w803 "$SCR/w803" "$SCR/root_new/finance"); R4=$(printf '%s\n' "$O4" | tail -1); [ "$R4" = "WALK S803 GREEN" ] || { printf '%s\n' "$O4" | grep -E "RED|Error" | head -6 | sed 's/^/      /'; stop "!! [3/6] the Marg watch's own walk (S803) on the rebuilt Hub: $R4 - nothing installed"; }
say "[3/6] walk_s845 on copies of the live databases: $R; the Marg watch's own walk on the rebuilt Hub: $R4; the control on the live files: red"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the control green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
for n in $NAMES $NEW; do st=$(stg "$n"); ref="$ROOT/$n"; [ -e "$ref" ] || ref="$ROOT/finance/sanjeevni_approvals.py"
  { cat "$SCR/built/$n" > "$st" && chmod --reference="$ref" "$st" 2>/dev/null; chown --reference="$ref" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(m5 "$SCR/built/$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
PLACING=1; T0=$(date +%s)
for n in $NEW finance/sanjeevni_approvals.py finance/finance_ui/finance_approvals.html; do mv -f "$(stg "$n")" "$ROOT/$n" || restore "the rename of $n"; done
for n in $NAMES $NEW; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
l1=$(flz); case "$l1" in 404|000|5*) restore "the ledger answered $l1 after the restart (not mounted)";; esac
jnl "$T0" | grep -q "item_ledger NOT mounted" && restore "the Hub's log says the ledger was NOT mounted"
PLACING=0
release_lock
say "[4/6] placed and read back: the new page and the two files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the ledger answers ($l1)"
say "[5/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s845.sh  (the two backups back, the page gone, $FSVC restarted)"
say "[6/6] nothing was written to any table; the Hub's Go to now opens the Item ledger."
say ""
say "$KIT: DONE. The Item ledger: https://followup.dr-manoj.in/finance/sanjeevni/ledger"
exit 0
