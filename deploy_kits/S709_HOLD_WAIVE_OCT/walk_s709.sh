#!/bin/bash
# walk_s709.sh -- S709 on made-up ledgers (made-up names; no real staff figure). PASS/FAIL lines, WALK OK/RED.
set -u
K="$(cd "$(dirname "$0")" && pwd)"; SP="${1:-$K/../salary_policy_bundle.py}"; TOOL="$K/hold_waive_s709.py"
pass=0; fail=0; ok(){ if eval "$1"; then pass=$((pass+1)); echo "PASS $2"; else fail=$((fail+1)); echo "FAIL $2"; fi; }
mk(){ D=$(mktemp -d); cp "$SP" "$D/salary_policy.py"
cat > "$D/hold_ledger.jsonl" <<J
{"id":"a1","ym":"2026-08","staff":"Delta","computed":40,"collected":10,"held":30,"ts":"2026-09-05 10:00:00","by":"manoj"}
{"id":"a2","ym":"2026-09","staff":"Alpha","computed":400,"collected":100,"held":273.13,"ts":"2026-10-05 10:00:00","by":"manoj"}
{"id":"a6","ym":"2026-09","staff":"Eps","computed":40,"collected":10,"held":62.5,"ts":"2026-10-05 10:00:00","by":"manoj"}
{"id":"a3","ym":"2026-09","staff":"Beta","computed":80,"collected":20,"held":60,"ts":"2026-10-05 10:00:00","by":"manoj"}
{"id":"a4","ym":"2026-09","staff":"Gamma","computed":40,"collected":10,"held":30,"ts":"2026-10-05 10:00:00","by":"manoj"}
{"id":"a5","action":"RELEASE","staff":"Gamma","ym":"2026-09","amount":30,"reason":"improved","by":"manoj","ts":"2026-11-01 10:00:00"}
J
"${VPY:-python3}" -c "import sqlite3;c=sqlite3.connect('$D/staff_register.db');c.execute('CREATE TABLE locked_run(ym TEXT PRIMARY KEY,status TEXT)');c.commit()"
echo "$D"; }
stub(){ # $1 dir, $2 = honest|ignore : a stand-in compute() over the real hold_state()
cat >> "$1/salary_policy.py" <<'P'

def _s709_compute(ym, with_prev=True):
    out = []
    for name in ("Alpha", "Beta", "Gamma", "Delta", "Eps"):
        if _S709_MODE == "ignore":
            pc = sum(float(r.get("held") or 0) for r in hold_rows() if r.get("staff") == name and r.get("ym") == prev_ym(ym) and not r.get("action"))
        else:
            h = hold_state().get((name, prev_ym(ym)))
            pc = float(h["held"]) if h and h["status"] == "HELD" else 0.0
        rel = 0.0
        if name == "Eps":
            h = hold_state().get((name, prev_ym(ym)))
            rel, pc = (float(h["held"]) if h and h["status"] == "HELD" else 0.0), 0.0
        ne = round(8657.41 - pc, 2)
        out.append({"name": name, "prior_collect": pc, "net_exact": ne, "net": float(int(ne / 10) * 10), "release": rel})
    return {"staff": out}
compute = _s709_compute
P
echo "_S709_MODE = '$2'" >> "$1/salary_policy.py"; }
# 1 plan only writes nothing
D=$(mk); m0=$(md5sum $D/hold_ledger.jsonl|cut -c1-32)
O=$("${VPY:-python3}" -B "$TOOL" --dir $D --no-compute); ok '[ "$(md5sum $D/hold_ledger.jsonl|cut -c1-32)" = "$m0" ]' "plan only: ledger untouched"
ok 'echo "$O" | grep -q "Alpha" && echo "$O" | grep -q "Beta" && ! echo "$O" | grep -q " Gamma " && ! echo "$O" | grep -q "Delta"' "plan lists Alpha and Beta (Gamma already released, Delta another month)"
# 2 apply (no compute): two WAIVE lines, old bytes intact, Delta still HELD
O=$("${VPY:-python3}" -B "$TOOL" --dir $D --no-compute --apply); rc=$?
ok '[ $rc = 0 ] && echo "$O" | grep -q "DONE"' "apply: DONE"
ok '[ "$(head -c $(stat -c%s $D/hold_ledger.jsonl.bak_S709_*) $D/hold_ledger.jsonl | md5sum|cut -c1-32)" = "$m0" ]' "apply: the old lines are byte-identical (append only)"
ok '[ $(grep -c WAIVE $D/hold_ledger.jsonl) = 3 ]' "apply (no computation): exactly three WAIVE lines (Alpha, Beta, Eps)"
ok '"${VPY:-python3}" -B -c "import sys,os;sys.path.insert(0,\"$D\");os.chdir(\"$D\");import salary_policy as P;s=P.hold_state();assert s[(\"Alpha\",\"2026-09\")][\"status\"]==\"WAIVE\" and s[(\"Beta\",\"2026-09\")][\"status\"]==\"WAIVE\" and s[(\"Delta\",\"2026-08\")][\"status\"]==\"HELD\" and s[(\"Gamma\",\"2026-09\")][\"status\"]==\"RELEASE\""' "apply: Alpha, Beta WAIVE; Gamma RELEASE and Delta HELD untouched"
# 3 again: nothing to waive
O=$("${VPY:-python3}" -B "$TOOL" --dir $D --no-compute --apply); ok 'echo "$O" | grep -q "NOTHING TO WAIVE" && [ $(grep -c WAIVE $D/hold_ledger.jsonl) = 3 ]' "again: NOTHING TO WAIVE, no line added"
rm -rf $D
# 4 with October's computation (honest stand-in): green, nets up by exactly the collection
D=$(mk); stub $D honest
O=$("${VPY:-python3}" -B "$TOOL" --dir $D --apply); rc=$?
ok '[ $rc = 0 ] && echo "$O" | grep -q "Alpha.*deducted 273.13 -> 0.00   pay 8380 -> 8650"' "compute (real rounding to the last 10): Alpha 273.13 -> 0, pay 8380 -> 8650"
ok 'echo "$O" | grep -q "Eps.*already CANCELLED" && "${VPY:-python3}" -B -c "import sys,os;sys.path.insert(0,\"$D\");os.chdir(\"$D\");import salary_policy as P;assert P.hold_state()[(\"Eps\",\"2026-09\")][\"status\"]==\"HELD\""' "compute: a hold October cancels is left HELD (its RELEASE stays October's)"
ok 'echo "$O" | grep -q "Beta.*deducted 60.00 -> 0.00"' "compute: Beta 60 -> 0"
rm -rf $D
# 5 CONTROL: a computation that ignores the waive must go red and put the ledger back
D=$(mk); stub $D ignore; m0=$(md5sum $D/hold_ledger.jsonl|cut -c1-32)
O=$("${VPY:-python3}" -B "$TOOL" --dir $D --apply); rc=$?
ok '[ $rc = 1 ] && echo "$O" | grep -q "still collects"' "CONTROL: October still collecting -> RED"
ok '[ "$(md5sum $D/hold_ledger.jsonl|cut -c1-32)" = "$m0" ]' "CONTROL: the ledger put back byte-identically"
rm -rf $D
# 6 locked month refuses
D=$(mk); "${VPY:-python3}" -c "import sqlite3;c=sqlite3.connect('$D/staff_register.db');c.execute(\"INSERT INTO locked_run VALUES('2026-10','locked')\");c.commit()"; m0=$(md5sum $D/hold_ledger.jsonl|cut -c1-32)
O=$("${VPY:-python3}" -B "$TOOL" --dir $D --no-compute --apply); rc=$?
ok '[ $rc = 1 ] && echo "$O" | grep -q "LOCKED" && [ "$(md5sum $D/hold_ledger.jsonl|cut -c1-32)" = "$m0" ]' "locked October: STOP, nothing written"
"${VPY:-python3}" -c "import sqlite3;c=sqlite3.connect('$D/staff_register.db');c.execute(\"UPDATE locked_run SET status='unlocked'\");c.commit()"
O=$("${VPY:-python3}" -B "$TOOL" --dir $D --no-compute); ok 'echo "$O" | grep -q "PLAN ONLY"' "unlocked October: plan offered"
rm -rf $D
# 6b the lock cannot be read -> STOP
D=$(mk); rm $D/staff_register.db; m0=$(md5sum $D/hold_ledger.jsonl|cut -c1-32); O=$("${VPY:-python3}" -B "$TOOL" --dir $D --no-compute --apply); rc=$?
ok '[ $rc = 1 ] && echo "$O" | grep -q "database is not at" && [ "$(md5sum $D/hold_ledger.jsonl|cut -c1-32)" = "$m0" ]' "no register database: STOP, nothing written"
"${VPY:-python3}" -c "import sqlite3;c=sqlite3.connect('$D/staff_register.db');c.execute('CREATE TABLE other(x)');c.commit()"
O=$("${VPY:-python3}" -B "$TOOL" --dir $D --no-compute --apply); rc=$?
ok '[ $rc = 1 ] && echo "$O" | grep -q "no locked_run table"' "no locked_run table: STOP"
O=$(SR_DB_PATH=/nonexistent/x.db "${VPY:-python3}" -B "$TOOL" --dir $D --no-compute --apply); ok 'echo "$O" | grep -q "/nonexistent/x.db"' "the register's SR_DB_PATH is honoured"
rm -rf $D
# 7 a wrong month pair refuses
D=$(mk); O=$("${VPY:-python3}" -B "$TOOL" --dir $D --no-compute --hold-month 2026-08 --pay-month 2026-10); ok 'echo "$O" | grep -q "not the month before"' "hold month must be the month before"; rm -rf $D
find "$K" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
[ $fail = 0 ] && echo "WALK OK $pass/$pass" || echo "WALK RED $fail of $((pass+fail))"; [ $fail = 0 ]
