#!/bin/bash
# =============================================================================
#  install_S869_HUB_DAYS_CASH.sh · kit S869 (18-Nov-2026, Sanjeevni session 482) · D1005: the owner's OK (11:59 IST) on the Hub mock-up v3
#  The Hub's Days and Cash: the day panel names who a bill was typed to and what was sold (line values); a sale return carries its
#  patient / ID / mobile and the Returns card's own Approve / Reject; Dr Bhawna's handovers are stamped received by the owner (one or all);
#  his own day entries (money into another account; cash taken out on a doctor's word); the Cash card says WHY the drawer reads what it
#  reads; the one calculation writes off a short he accepted (F-1460); day_resync's pass 1 takes the bank's UPI on approved days too (F-1459);
#  and the ONE-TIME clean-up of his rulings (9-Oct's typo, 3-Nov's deleted bill, 4-Nov / 14-Nov entries): drawer Rs 21,508 -> 549.
#   1. NEW /root/finance/hub_cash.py
#   2. /root/finance/sanjeevni_cash.py 8e58691b -> TO (v1.2, whole)      3. /root/finance/sanjeevni_day.py 22a38006 -> TO (v1.3, whole)
#   4. /root/finance/day_resync.py 00b45a15 -> TO (5 anchors)             5. /root/finance/finance_ui/finance_approvals.html 17f13acc -> TO (9 anchors)
#  The four live files are rebuilt HERE from their live bytes (make_s869.py), checked against the TO pins. clinic-finance is restarted.
#  Then day_resync runs once (9-Oct, 14-Oct take the bank's UPI) and the one-off runs LIVE (it was DRY on a copy at [3/7]).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s869kit && cp -rp /root/deploy/repo/deploy_kits/S869_HUB_DAYS_CASH /tmp/s869kit && bash /tmp/s869kit/install_S869_HUB_DAYS_CASH.sh
#  (DRY=1 before bash: every gate, the proof on copies and the control; NOTHING written.)
# =============================================================================
set -u
KIT="S869_HUB_DAYS_CASH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
OLDK="${OLDK:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="finance/sanjeevni_cash.py finance/sanjeevni_day.py finance/day_resync.py finance/finance_ui/finance_approvals.html"
NEW="finance/hub_cash.py"
from_of() { case "$1" in finance/sanjeevni_cash.py) echo 8e58691bac16fceb00602e7f8eabdaf8;; finance/sanjeevni_day.py) echo 22a38006a4e3be59b47ea091ea1f971f;;
  finance/day_resync.py) echo 00b45a150df15123106fbcc641f913ab;; finance/finance_ui/finance_approvals.html) echo 17f13acc3b9f18ef2be71eefcc811c07;; esac; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s869_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { local f; f=$(from_of "$1"); echo "$ROOT/$1.bak_S869_${f:0:8}"; }
stg() { echo "$(dirname "$ROOT/$1")/.$(basename "$1").s869"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
hhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/sanjeevni/api/hub-cash/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/sanjeevni/api/hub-cash/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES $NEW; do rm -f "$(stg "$n")"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
PLACING=0
trap on_exit EXIT
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting the four files back and taking the new module away"
  for n in $NAMES; do \cp -p "$(bak "$n")" "$ROOT/$n"; done
  rm -f "$ROOT/$NEW"; "$SYSTEMCTL" restart "$FSVC" || true
  for n in $NAMES; do f=$(from_of "$n"); say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${f:0:8})"; done
  say "   $NEW present: $([ -e "$ROOT/$NEW" ] && echo yes || echo no) (expected no)"
  say "   $FSVC restarted, finance healthz $(wait200). Nothing was written to any table. Send a photo of this screen to Claude."
  release_lock; exit 1; }
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/finance_ui" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.html' -o -name '*.sql' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/finance_ui/*.html "$d/finance/finance_ui/" 2>/dev/null; [ -f "$d/finance/sanjeevni_day.py" ]; }
synth() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -u -W ignore -B "$KDIR/synth_s869.py" "$1" "$2" --box 2>&1); }
w365() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -u -W ignore -B "$OLDK/S365_DAY_PANEL/walk_s365.py" --app "$1" --db "$2" 2>&1 | tail -1); }
w399() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -u -W ignore -B "$OLDK/S399_DAY_TRUTH_5/walk_s399.py" --db "$1" --new "$2" --old "$OLDK/S367_DAY_TRUTH_4/day_resync.py" 2>&1 | tail -1); }
jnl() { if [ -n "${JOURNAL_CMD:-}" ]; then $JOURNAL_CMD; elif command -v journalctl >/dev/null 2>&1; then journalctl -u "$FSVC" --since "@$1" --no-pager 2>/dev/null; fi; }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES $NEW; do [ -n "$(to_of "$n")" ] || { say "!! [1/7] no TO pin for $n - nothing installed"; exit 1; }; done
for n in $NAMES; do [ -f "$ROOT/$n" ] || { say "!! [1/7] the live file $ROOT/$n is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/7] $DB missing - nothing installed"; exit 1; }
[ -f "$OLDK/S365_DAY_PANEL/walk_s365.py" ] && [ -f "$OLDK/S399_DAY_TRUTH_5/walk_s399.py" ] && [ -f "$OLDK/S367_DAY_TRUTH_4/day_resync.py" ] || { say "!! [1/7] the older walks (S365, S399, S367) are not in $OLDK - publish first. Nothing installed."; exit 1; }
ALL=1; for n in $NAMES $NEW; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- $KIT files are ALREADY INSTALLED."; if [ "${DRY:-0}" = 1 ]; then exit 0; fi
  say "   the one-off, once more (every step skips itself when done):"; "$VPY" -B "$KDIR/oneoff_s869.py" --db "$DB" --fin "$ROOT/finance" --apply 2>&1 | sed 's/^/   /'; exit 0; fi
[ -e "$ROOT/$NEW" ] && { say "!! [1/7] $ROOT/$NEW already exists and is not this kit's - nothing installed. Tell Claude."; exit 1; }
mkdir -p "$SCR/built/finance/finance_ui" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/7] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken by $KIT"
else say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do fr=$(from_of "$n"); [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/7] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
"$APY" -B make_s869.py "$ROOT/finance" "$SCR/built/finance" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused - nothing installed"; }
\cp -p "$KDIR/hub_cash.py" "$SCR/built/$NEW" || stop "!! [2/7] could not take the new module from the kit - nothing installed"
for n in $NAMES $NEW; do [ "$(m5 "$SCR/built/$n")" = "$(to_of "$n")" ] || stop "!! [2/7] rebuilt, $n is not at its TO pin - nothing installed"; done
for py in "$APY" "$VPY"; do for n in $NAMES $NEW; do case "$n" in *.py) PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$n" || stop "!! [2/7] $n does not compile on $py - nothing installed";; esac; done; done
say "[2/7] four live pins exact; rebuilt here at their TO pins with the new module; every .py compiles on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/finance.db" >/dev/null || stop "!! [3/7] could not copy the database for the proof - nothing installed"
\cp -p "$SCR/finance.db" "$SCR/finance_ctl.db" && \cp -p "$SCR/finance.db" "$SCR/f365.db" && \cp -p "$SCR/finance.db" "$SCR/f365o.db" && \cp -p "$SCR/finance.db" "$SCR/f399.db" || stop "!! [3/7] could not copy the database for the walks - nothing installed"
lay new && for n in $NAMES $NEW; do \cp -p "$SCR/built/$n" "$SCR/root_new/$n" || stop "!! [3/7] could not copy $n into the proof's layout - nothing installed"; done || stop "!! [3/7] could not lay out the proof - nothing installed"
O=$(synth "$SCR/root_new/finance" "$SCR/finance.db"); R=$(printf '%s\n' "$O" | tail -1)
printf '%s\n' "$O" | grep -E "^FAIL|Error|Traceback" | head -8 | sed 's/^/      /'
case "$R" in "SYNTH S869: "*" PASS, 0 FAIL") ;; *) stop "!! [3/7] synth_s869 on a copy of the live database: $R - nothing installed";; esac
lay old || stop "!! [3/7] could not lay out the control - nothing installed"
R0=$(synth "$SCR/root_old/finance" "$SCR/finance_ctl.db" | tail -1); case "$R0" in "SYNTH S869: "*" PASS, 0 FAIL") stop "!! [3/7] the control on the live files did not go red ($R0) - nothing installed";; esac
R3=$(w365 "$SCR/root_new/finance" "$SCR/f365.db"); R3o=$(w365 "$SCR/root_old/finance" "$SCR/f365o.db")
[ "${R3##* }" = "${R3o##* }" ] || stop "!! [3/7] S365's walk reads differently on the rebuilt files ($R3) than on the live ones ($R3o) - nothing installed"
R4=$(w399 "$SCR/f399.db" "$SCR/built/finance/day_resync.py"); case "$R4" in "WALK_S399 GREEN"*) ;; *) stop "!! [3/7] S399's own walk on the rebuilt day_resync: $R4 - nothing installed";; esac
say "[3/7] proof on a copy of the live database: $R (the one-off DRY and APPLY on the copy inside it); control on the live files: red; S365's walk same old/new (${R3##* }); S399's walk: $R4"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the proof and the control green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/7] finance healthz $f0 before the install - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/7] could not write the backup of $n - nothing placed"; done
for n in $NAMES $NEW; do st=$(stg "$n"); ref="$ROOT/$n"; [ -e "$ref" ] || ref="$ROOT/finance/sanjeevni_day.py"
  { cat "$SCR/built/$n" > "$st" && chmod --reference="$ref" "$st" 2>/dev/null; chown --reference="$ref" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(m5 "$SCR/built/$n")" ]; } || stop "!! [4/7] could not stage $n - nothing placed"; done
PLACING=1; T0=$(date +%s)
for n in $NEW $NAMES; do mv -f "$(stg "$n")" "$ROOT/$n" || restore "the rename of $n"; done
for n in $NAMES $NEW; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "read back of $n"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/7]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
l1=$(hhz); case "$l1" in 404|000|5*) restore "hub_cash healthz answered $l1 after the restart (not mounted)";; esac   # 302 = mounted behind the login gate (F-1439)
jnl "$T0" | grep -q "hub_cash not mounted" && restore "the Hub's log says hub_cash was NOT mounted"
PLACING=0
release_lock
say "[4/7] placed and read back: the new module and the four files at their TO pins; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, hub_cash answers ($l1)"
if [ -e "$ROOT/finance/_off/ALL_OFF" ] || [ -e "$ROOT/finance/_off/ALL_OFF.txt" ]; then say "!! [5/7] the Sanjeevni switch is OFF ($ROOT/finance/_off/ALL_OFF): day_resync will do nothing and the one-off will refuse 9-Oct. The files are installed and right. Turn the switch on (sanjeevni_switch.sh), then run the one-off line below."; say "   $VPY -B $ROOT/finance/day_resync.py && $VPY -B /root/deploy/repo/deploy_kits/$KIT/oneoff_s869.py --db $DB --fin $ROOT/finance --apply"; exit 4; fi
say "[5/7] day_resync once (pass 1 now takes the bank's UPI on approved days -- 9-Oct and 14-Oct):"
(cd "$ROOT/finance" && "$VPY" -B "$ROOT/finance/day_resync.py" --db "$DB" 2>&1 | grep -E "FIXED|OVER_NET|SHAPE|^summary|OFF" | sed 's/^/      /')
say "[6/7] the one-off clean-up LIVE (DRY on the copy was green at [3/7]):"
OO=$("$VPY" -B "$KDIR/oneoff_s869.py" --db "$DB" --fin "$ROOT/finance" --apply 2>&1); printf '%s\n' "$OO" | sed 's/^/      /'
case "$OO" in *"one-off APPLY: OK"*) ;; *) say "!! [6/7] the one-off REFUSED a step (see above). The files are installed and right; run the one-off again after Claude reads this:"; say "   $VPY -B /root/deploy/repo/deploy_kits/$KIT/oneoff_s869.py --db $DB --fin $ROOT/finance --apply"; exit 4;; esac
say "[7/7] undo of the FILES (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s869.sh  (the four backups back, the module gone, $FSVC restarted; the audited data changes stay -- they are the owner's rulings)"
say ""
say "$KIT: DONE. The Hub: https://followup.dr-manoj.in/finance/approvals  (Days: tap a day; the band for Dr Bhawna; the Cash card's 'Why the drawer reads')"
exit 0
