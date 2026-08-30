#!/usr/bin/env python3
"""
patch_finance_app_autofile.py -- S210 / D354 (owner-ruled 30-Aug-2026):
Marg + bank ARE the day. Apply may CREATE the day it is loading into.

THE OWNER'S RULING, his words: "making him checker, accepting his errors, and
they get to my page automatically is my purpose... everyone gets the correct
marg and bank data which is the sole truth, and i have the facility and
authority for any reconcile."

WHAT CHANGES -- one anchored block inside api_marg_push_apply
  A day in the staged report with no day_entry is no longer skipped. It is
  FILED from the two truths already ruled canonical:
      net sale  = the staged Marg bills, signed (credit notes subtract)
      UPI       = the bank record (upi_txn) for that date -- S208 final ruling
      cash      = net - UPI
  The day is created status='submitted', entered_by the applying owner, with
  a full audit row -- so it lands in the owner's approvals queue exactly like
  a hand-filed day. Approval, edits (day_revision keeps history), exceptions
  and review queues are untouched: the reconcile authority stays whole.

WHAT DOES NOT CHANGE -- the honesty guards
  - net <= 0, or bank UPI exceeding the net sale: that day CANNOT be built
    honestly by formula, so it stays manual (reported, skipped) -- filing it
    would overstate revenue or book negative cash.
  - a day already filed behaves exactly as before.
  - setting marg.autofile='0' turns the whole behaviour off.
  - expenses / hand-overs are NOT invented: they arrive by editing the day,
    as now. F-155 stands: the push is 'applied' only when every day loaded.

SAFETY: exact anchor, refuse if absent/ambiguous; backup; py_compile with
auto-restore.

USAGE
    /root/wa/venv/bin/python3 patch_finance_app_autofile.py /root/finance/finance_app.py
    python3 patch_finance_app_autofile.py --selftest <finance_app copies...>
"""
import datetime, os, py_compile, shutil, sys

MARK = "S210 (D354 autofile)"

A1 = """        e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                        (UNIT, iso_d)).fetchone()
        if not e:
            still_not_filed.append(iso_d)
            continue"""

N1 = """        e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                        (UNIT, iso_d)).fetchone()
        if not e:
            # %s -- owner ruling: Marg + bank ARE the day. Build it from the
            # two ruled truths; a day the formula cannot build honestly
            # (net<=0, or bank UPI over the net sale) stays manual.
            if setting(con, "marg.autofile", "1") != "1":
                still_not_filed.append(iso_d)
                continue
            _rows = list(csv.DictReader(io.StringIO(d["lines_csv"])))
            try:
                _net_p = int(round(sum(float(x.get("amount") or 0)
                                       for x in _rows) * 100))
            except (TypeError, ValueError):
                still_not_filed.append(iso_d)
                continue
            _upi_p = int(con.execute(
                "SELECT COALESCE(SUM(amount_p),0) FROM upi_txn "
                "WHERE unit=? AND txn_date=?", (UNIT, iso_d)).fetchone()[0] or 0)
            _cash_p = _net_p - _upi_p
            if _net_p <= 0 or _cash_p < 0:
                still_not_filed.append(iso_d)
                continue
            _cur = con.execute(
                "INSERT INTO day_entry (unit, business_date, status, source, "
                " entered_by, entered_at) VALUES (?,?,?,?,?,?)",
                (UNIT, iso_d, "submitted", "app", u["user"], now_iso()))
            _eid = _cur.lastrowid
            con.execute("INSERT INTO day_line (day_entry_id, service, mode, "
                        "amount_p) VALUES (?,'pharmacy_sale','cash',?)",
                        (_eid, _cash_p))
            if _upi_p:
                con.execute("INSERT INTO day_line (day_entry_id, service, mode, "
                            "amount_p) VALUES (?,'pharmacy_sale','upi',?)",
                            (_eid, _upi_p))
            audit(con, "day_entry", _eid, "autofile",
                  after={"date": iso_d, "net_p": _net_p, "upi_p": _upi_p,
                         "cash_p": _cash_p, "from_push": row["file_md5"][:8],
                         "rule": "D354 marg+bank"},
                  who=u["user"])
            e = {"id": _eid}""" % MARK


def patch_text(s):
    if MARK in s:
        return s, "already_patched"
    n = s.count(A1)
    if n != 1:
        return s, ("anchor_missing" if n == 0 else "anchor_ambiguous")
    return s.replace(A1, N1), "patched"


def selftest():
    ok = bad = 0
    def check(name, cond):
        nonlocal ok, bad
        if cond: ok += 1
        else: bad += 1; print("  FAIL:", name)
    for path in sys.argv[2:]:
        s = open(path, encoding="utf-8").read()
        out, st = patch_text(s)
        check("%s: patches" % path.split("/")[-2], st == "patched")
        check("  compiles", compile(out, path, "exec") is not None)
        check("  guard: net<=0 stays manual", "_net_p <= 0" in out)
        check("  guard: negative cash stays manual", "_cash_p < 0" in out)
        check("  off-switch present", "marg.autofile" in out)
        check("  audit row written", '"autofile"' in out)
        check("  F-155 applied-only-when-complete untouched",
              "F-155: a run is" in out and "still_not_filed" in out)
        _, st2 = patch_text(out)
        check("  second run no-op", st2 == "already_patched")
    _, st3 = patch_text("x=1\n")
    check("no anchor -> refused", st3 == "anchor_missing")
    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 2:
        print(__doc__); return 2
    p = argv[1]
    s = open(p, encoding="utf-8").read()
    new, st = patch_text(s)
    if st == "already_patched":
        print("already patched -- nothing to do."); return 0
    if st != "patched":
        print("!! REFUSING --", st, "\n   Nothing changed."); return 1
    bak = "%s.bak_S210_autofile_%s" % (p, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(p, bak)
    open(p, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(p, doraise=True)
    except Exception as e:
        shutil.copy2(bak, p)
        print("!! compile FAILED -- restored from", bak); print("  ", e); return 1
    print("patched OK"); print("backup:", bak)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
