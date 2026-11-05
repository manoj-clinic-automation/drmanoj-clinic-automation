#!/usr/bin/env python3
"""hold_waive_s709.py -- kit S709_HOLD_WAIVE_OCT (05-Nov-2026, session S385, the parent).

The owner, 20:15 IST 05-Nov-2026: "REMOVE PREVIOUS HOLD DEDUCTION FRM OCTOBER SALARY SHEET".

September's suspended late charges sit in the register's hold ledger (hold_ledger.jsonl) as HELD.
October's salary collects every HELD one whose late minutes did not improve by the bar
(salary_policy.compute: prior_collect -> "Pichhle mahine ka late"). This tool closes each HELD
September hold with the ledger's own closing action, WAIVE (salary_policy.hold_state: "Actions
RELEASE/LAPSE/WAIVE close a hold"), written through salary_policy.append_hold -- the ledger's only
writer. Nothing else is touched: no setting, no code, no other month, no other file.

  python3 hold_waive_s709.py            plan only (the default): lists the holds, writes nothing
  python3 hold_waive_s709.py --apply    backup -> append the WAIVE lines -> verify -> restore on any red

Verify after writing: the ledger's old bytes are untouched (append only), exactly one new line per
hold, every planned hold now closed as WAIVE, none of the hold month still HELD; October's own
computation collects nothing from September, and each person's October net rises by exactly what
was being collected (everyone else unchanged). Any red -> the backup is put back byte-identically.
Refuses if the pay month is LOCKED (a locked month's figures do not change; unlock it first).
"""
import argparse
import datetime
import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import sys

KIT = "S709_HOLD_WAIVE_OCT"
REASON = ("owner 05-Nov-2026 20:15 IST: remove the previous hold deduction from the October "
          "salary sheet (kit S709)")


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def md5_prefix(p, n):
    with open(p, "rb") as f:
        return hashlib.md5(f.read(n)).hexdigest()


def stop(msg):
    print("!! STOPPED: " + msg)
    print("   Nothing was changed. Send a photo of this screen to Claude.")
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/root/staff_register")
    ap.add_argument("--hold-month", default="2026-09")
    ap.add_argument("--pay-month", default="2026-10")
    ap.add_argument("--by", default="manoj")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-compute", action="store_true", help="test only: skip October's computation")
    a = ap.parse_args()

    d = os.path.abspath(a.dir)
    if not os.path.isfile(os.path.join(d, "salary_policy.py")):
        stop("salary_policy.py not found in " + d)
    sys.path.insert(0, d)
    os.chdir(d)
    import salary_policy as P
    HL = P.HOLD_LEDGER
    if os.path.dirname(os.path.abspath(HL)) != d:
        stop("the hold ledger is not in " + d + " (" + HL + ")")
    if not os.path.isfile(HL):
        stop("no hold ledger at " + HL)
    if P.prev_ym(a.pay_month) != a.hold_month:
        stop("%s is not the month before %s" % (a.hold_month, a.pay_month))

    # the pay month must not be locked -- the register's own DB path rule (staff_register._cfg:
    # environment, then staff_register_config.py, then the default); any read failure STOPS.
    def db_path():
        v = os.environ.get("SR_DB_PATH")
        if v:
            return v
        try:
            import staff_register_config as C
            v = getattr(C, "SR_DB_PATH", None)
            if v:
                return v
        except Exception:
            pass
        return os.path.join(d, "staff_register.db")

    def check_lock():
        db = db_path()
        if not os.path.isfile(db):
            stop("the register's database is not at %s -- cannot tell whether %s is locked" % (db, a.pay_month))
        try:
            con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
            if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='locked_run'").fetchone():
                con.close()
                stop("the register's database has no locked_run table -- cannot tell whether %s is locked" % a.pay_month)
            r = con.execute("SELECT status FROM locked_run WHERE ym=?", (a.pay_month,)).fetchone()
            con.close()
        except sqlite3.Error as e:
            stop("could not read the lock (%s)" % e)
        if r and str(r[0]).lower() == "locked":
            stop("%s is LOCKED -- its figures no longer change. Unlock it at the Lock desk first." % a.pay_month)
        return "not locked" if not r else "status %s" % r[0]

    lk = check_lock()

    def held():
        return {k: v for k, v in P.hold_state().items()
                if k[1] == a.hold_month and v.get("status") == "HELD" and float(v.get("held") or 0) > 0}

    plan = held()
    print("== %s ==" % KIT)
    print("[1/4] hold ledger %s (%d bytes, md5 %s); %s %s" % (HL, os.path.getsize(HL), md5(HL)[:8], a.pay_month, lk))
    if not plan:
        print("-- NOTHING TO WAIVE: no %s hold is still HELD (ALREADY DONE, or none were written)." % a.hold_month)
        return 0

    def run_month():
        res = P.compute(a.pay_month)
        out = {}
        for st in res["staff"]:
            if "net_exact" not in st:
                raise KeyError("compute() no longer returns net_exact")
            out[st["name"]] = (float(st.get("prior_collect", 0) or 0), float(st["net_exact"] or 0),
                               float(st.get("release", 0) or 0), float(st.get("net", 0) or 0))
        return out

    before = None
    if not a.no_compute:
        try:
            before = run_month()
        except Exception as e:
            stop("October's computation could not run (%s: %s)" % (type(e).__name__, e))
    total = 0.0
    keep = {}
    if before is not None:
        for (staff, ym), v in list(plan.items()):
            if staff in before and before[staff][2] > 0 and before[staff][0] <= 0.005:
                keep[(staff, ym)] = plan.pop((staff, ym))
    if not plan:
        print("-- NOTHING TO WAIVE: October collects none of the %s holds (the rest are cancelled for improvement)." % a.hold_month)
        return 0
    print("[2/4] %s holds October would deduct (%d):" % (a.hold_month, len(plan)))
    for (staff, ym), v in sorted(plan.items()):
        note = ""
        if before is not None and staff in before:
            pc = before[staff][0]
            note = ("  -> October deducts %.2f now" % pc) if pc else "  -> October deducts nothing"
        print("      %-12s %9.2f%s" % (staff, float(v["held"]), note))
        total += float(v["held"])
    for (staff, ym), v in sorted(keep.items()):
        print("      %-12s %9.2f  -> already CANCELLED by October (improved) -- left as it is" % (staff, float(v["held"])))
    if before is not None:
        coll = sum(before[s][0] for (s, _y) in plan if s in before)
        print("      October is collecting %.2f in all from these holds" % coll)
    if not a.apply:
        print("PLAN ONLY: nothing written. Run again with --apply to waive them.")
        return 0

    size0, m0 = os.path.getsize(HL), md5(HL)
    bak = HL + ".bak_S709_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(HL, bak)
    if md5(bak) != m0:
        stop("the backup does not match the ledger")
    print("[3/4] backup %s" % bak)

    def restore(why):
        if os.path.getsize(HL) >= size0 and md5_prefix(HL, size0) == m0:
            with open(HL, "r+b") as f:
                f.truncate(size0)
        else:
            shutil.copy2(bak, HL)
        ok = md5(HL) == m0
        print("!! RED (%s) -- the hold ledger put back: %s" % (why, "byte-identical (%s)" % m0[:8] if ok else "NOT identical -- copy %s back by hand" % bak))
        print("   Send a photo of this screen to Claude.")
        sys.exit(1)

    check_lock()
    if md5(HL) != m0:
        stop("the hold ledger changed while this ran -- run the line again")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        for (staff, ym), v in sorted(plan.items()):
            P.append_hold({"id": secrets.token_hex(6), "action": "WAIVE", "staff": staff, "ym": ym,
                           "amount": float(v["held"]), "reason": REASON, "by": a.by, "ts": now})
    except Exception as e:
        restore("writing: %s" % e)

    # verify the ledger
    if md5_prefix(HL, size0) != m0:
        restore("the ledger's old lines changed")
    with open(HL, "rb") as f:
        f.seek(size0)
        tail = [ln for ln in f.read().decode("utf-8").splitlines() if ln.strip()]
    if len(tail) != len(plan):
        restore("%d new lines, expected %d" % (len(tail), len(plan)))
    st = P.hold_state()
    for k in plan:
        if st.get(k, {}).get("status") != "WAIVE":
            restore("%s is not closed as WAIVE" % (k,))
    still = held()
    if any(k in still for k in plan):
        restore("a waived %s hold still reads HELD" % a.hold_month)
    if set(still) != set(keep):
        restore("the %s holds left HELD are not exactly the ones October cancels" % a.hold_month)
    # verify October
    if before is not None:
        try:
            after = run_month()
        except Exception as e:
            restore("October's computation failed: %s" % e)
        for name, (pc, net, rel, _n) in before.items():
            pa, na, ra, _na = after.get(name, (None, None, None, None))
            if pa is None:
                restore("%s missing from October after the waive" % name)
            if (name, a.hold_month) in plan:
                if pa > 0.005:
                    restore("%s: October still collects %.2f" % (name, pa))
                if abs((na - net) - pc) > 0.02:
                    restore("%s: net moved %.2f, expected %.2f" % (name, na - net, pc))
            elif abs(na - net) > 0.02 or abs(pa - pc) > 0.005:
                restore("%s changed though no hold of theirs was waived" % name)
        print("[4/4] waived %d holds (%.2f); October now collects 0 from %s:" % (len(plan), total, a.hold_month))
        for (staff, ym) in sorted(plan):
            pc, net, rel, npay = before.get(staff, (0, 0, 0, 0))
            pa, na, ra, napay = after.get(staff, (0, 0, 0, 0))
            print("      %-12s deducted %.2f -> 0.00   pay %.0f -> %.0f" % (staff, pc, npay, napay))
    else:
        print("[4/4] waived %d holds (%.2f) (October not computed: test run)" % (len(plan), total))
    print("%s: DONE. Reload October's Sheet 2: September's holds read 'already closed (waive)' and nothing is deducted for them." % KIT)
    print("Undo:  \\cp -p %s %s" % (bak, HL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
