#!/usr/bin/env python3
"""
selftest_marg_autoapply.py -- S219 M1.

Proves the SHIPPED bytes, not a re-typed copy of them: the helper block is
sliced out of the PATCHED finance_app.py and exec'd against a database built
to the shapes those helpers actually touch.  If the patch changes, this test
tests the change.

It is deliberately honest about its scope: this is a unit proof of the new
helpers' logic and SQL.  It is NOT a proof of the live join -- that is the
live-shape walk, run against the real database before install (S208/S209: a
green selftest proves the kit, not the join).

USAGE:  python3 -B selftest_marg_autoapply.py [path/to/patched/finance_app.py]
"""
import json
import os
import re
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "finance_app.patched.py")
CHECKS = []


def ck(name, cond):
    CHECKS.append((name, bool(cond)))


def load_helpers(path):
    """Slice the S219 helper block + marg_net_sql + rupees out of the real
    file and exec them.  Nothing is re-keyed."""
    src = open(path, encoding="utf-8").read()
    start = src.index("# ============================================================================\n#  S219 M1 -- MARG AUTO-APPLY")
    end = src.index('def _replay_pending_marg_for_day(con, iso, by="auto"):')
    block = src[start:end]
    mns = src[src.index("def marg_net_sql(alias=\"sale_item\"):"):]
    mns = mns[:mns.index("\n\n\n")]
    rup = src[src.index("def rupees(p):"):]
    rup = rup[:rup.index("\n\n\n")]
    # the sliced functions rely on finance_app's module-level imports
    ns = {"UNIT": "medical", "re": re, "json": json,
          # finance_app reads tunables through setting(); the default
          # path is what ships, so that is what is tested.
          "setting": lambda con, k, d=None: d}
    exec(compile(mns, "marg_net_sql", "exec"), ns)
    exec(compile(rup, "rupees", "exec"), ns)
    exec(compile(block, "s219_helpers", "exec"), ns)
    return ns


def make_db():
    fd, p = tempfile.mkstemp(suffix=".db", prefix="s219_selftest_")
    os.close(fd)
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    con.executescript("""
        CREATE TABLE day_entry (id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit TEXT, business_date TEXT, status TEXT);
        CREATE TABLE sale_item (id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_entry_id INTEGER, unit TEXT, service TEXT, description TEXT,
            amount_p INTEGER NOT NULL CHECK (amount_p >= 0),
            mode TEXT, source_ref TEXT);
        CREATE TABLE data_flag (id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit TEXT, business_date TEXT, code TEXT, severity TEXT, detail TEXT);
    """)
    return con, p


def day(con, iso):
    return con.execute("INSERT INTO day_entry (unit, business_date, status) "
                       "VALUES ('medical',?, 'submitted')", (iso,)).lastrowid


def bill(con, eid, ref, amount_p, mode="cash", ret=False):
    con.execute("INSERT INTO sale_item (day_entry_id, unit, service, amount_p, "
                "mode, source_ref) VALUES (?,'medical',?,?,?,?)",
                (eid, "pharmacy_sale_return" if ret else "pharmacy_sale",
                 amount_p, mode, ref))


def main():
    if not os.path.exists(TARGET):
        print("!! patched finance_app.py not found at %s" % TARGET)
        print("   build it first:  FA_PATH=<copy> python3 -B patch_marg_autoapply_s219.py")
        return 2
    ns = load_helpers(TARGET)
    key = ns["_marg_bill_key"]
    summary = ns["_marg_apply_summary"]
    cont = ns["_marg_continuity_check"]

    # ---- 1 · bill-number parsing -----------------------------------------
    ck("A001988 -> ('A', 1988)", key("A001988") == ("A", 1988))
    ck("CN00184 -> ('CN', 184)", key("CN00184") == ("CN", 184))
    ck("lowercase is normalised", key("a001988") == ("A", 1988))
    ck("surrounding space ignored", key("  A001988 ") == ("A", 1988))
    ck("pure digits keep an empty series", key("001988") == ("", 1988))
    ck("no trailing number -> None", key("WALKIN") is None)
    ck("empty -> None", key("") is None)
    ck("None -> None", key(None) is None)
    ck("leading zeros do not change the number", key("A000007") == ("A", 7))

    con, path = make_db()
    try:
        # ---- 2 · the summary, on a day with a credit note ----------------
        e1 = day(con, "2026-08-20")
        bill(con, e1, "A001000", 10000)
        bill(con, e1, "A001001", 25000, mode="upi")
        bill(con, e1, "A001002", 5000, mode="upi")
        bill(con, e1, "CN00010", 2000, ret=True)
        con.commit()
        s = summary(con, "2026-08-20")
        ck("summary found the day", s is not None)
        ck("bill count is every loaded row", s["bills"] == 4)
        ck("credit notes counted by service, not by sign", s["cn"] == 1)
        ck("net SUBTRACTS the credit note (marg_net_sql)",
           s["net_p"] == 10000 + 25000 + 5000 - 2000)
        ck("UPI per Marg is Marg's own mode column", s["upi_marg_p"] == 30000)
        ck("both series appear in the range", s["bill_range"] == "A1000-A1002, CN10-CN10")
        ck("the one-line summary names all four facts",
           all(t in s["line"] for t in ("bills", "total Rs", "UPI per Marg", "credit note")))
        ck("summary of an unfiled day is None", summary(con, "2026-08-19") is None)

        # A LAKH-SIZED DAY.  Found by the live-shape walk, not by this file:
        # rupees() only reaches its comma-grouping branch above Rs 1,000, and
        # every amount above is smaller than that, so the branch the real days
        # all take was never once executed here.
        e9 = day(con, "2026-08-25")
        bill(con, e9, "A009000", 12345678)
        con.commit()
        s9 = summary(con, "2026-08-25")
        ck("a lakh-sized day formats in Indian grouping",
           s9 and "1,23,456.78" in s9["line"])

        # ---- 3 · continuity: contiguous days do NOT flag ------------------
        e2 = day(con, "2026-08-21")
        bill(con, e2, "A001003", 4000)
        bill(con, e2, "A001004", 4000)
        con.commit()
        g = cont(con, "2026-08-21")
        con.commit()
        ck("a contiguous next export raises nothing", g == [])
        ck("and writes no flag",
           con.execute("SELECT COUNT(*) c FROM data_flag").fetchone()["c"] == 0)

        # ---- 4 · continuity: a real gap DOES flag ------------------------
        e3 = day(con, "2026-08-22")
        bill(con, e3, "A001020", 7000)
        con.commit()
        g = cont(con, "2026-08-22")
        con.commit()
        ck("a gap is raised", len(g) == 1)
        ck("the missing count is exact (1005..1019)", g and g[0]["missing"] == 15)
        ck("it names the previous export's day", g and g[0]["prev_date"] == "2026-08-21")
        ck("a flag row is written", con.execute(
            "SELECT COUNT(*) c FROM data_flag WHERE code='MARG_BILL_RANGE_GAP'"
        ).fetchone()["c"] == 1)
        ck("the flag reads as a sentence, not a code",
           "never reached the books" in con.execute(
               "SELECT detail d FROM data_flag").fetchone()["d"])

        # ---- 5 · re-running an apply must not double the flag ------------
        cont(con, "2026-08-22")
        con.commit()
        ck("re-apply does not duplicate the flag", con.execute(
            "SELECT COUNT(*) c FROM data_flag WHERE code='MARG_BILL_RANGE_GAP'"
        ).fetchone()["c"] == 1)

        # ---- 6 · series are independent ----------------------------------
        e4 = day(con, "2026-08-23")
        bill(con, e4, "A001021", 3000)
        bill(con, e4, "CN00011", 500, ret=True)
        con.commit()
        g = cont(con, "2026-08-23")
        con.commit()
        ck("a sale series continuing cleanly raises nothing",
           not [x for x in g if x["series"] == "A"])
        ck("a credit-note series is judged on its own numbering",
           not [x for x in g if x["series"] == "CN"])

        # ---- 7 · a silence longer than 14 days is not a gap --------------
        e5 = day(con, "2026-09-20")
        bill(con, e5, "A003000", 9000)
        con.commit()
        g = cont(con, "2026-09-20")
        con.commit()
        ck("beyond 14 days it stays silent (that is a missing DAY, not a gap)",
           g == [])

        # ---- 7b · the MEASURED noise floor -------------------------------
        # Five months of real history produced 47 gaps and the largest was
        # SIX.  A small gap is a cancelled bill, not a lost export, and a flag
        # that fires on it is an amber nobody reads.
        e6 = day(con, "2026-08-26")
        bill(con, e6, "A001022", 1000)
        con.commit()
        e7 = day(con, "2026-08-27")
        bill(con, e7, "A001029", 1000)          # a gap of SIX -- the observed max
        con.commit()
        g = cont(con, "2026-08-27")
        con.commit()
        ck("a six-bill gap stays quiet (below the measured floor)", g == [])
        e8 = day(con, "2026-08-28")
        bill(con, e8, "A001045", 1000)          # a gap of FIFTEEN -- a real loss
        con.commit()
        g = cont(con, "2026-08-28")
        con.commit()
        ck("a fifteen-bill gap does shout", len(g) == 1)
        ck("the flag says what it could mean",
           g and "never exported" in g[0]["detail"])

        # ---- 7c · foreign source_refs are not a bill series ---------------
        ck("an S186 backfill marker is not a bill", key("S186-F104-1332") is None)
        ck("a four-letter prefix is not a Marg series", key("ABCD0001") is None)
        ck("a mixed prefix is not a Marg series", key("A1B002") is None)
        ck("but a real two-letter series still parses", key("CN00196") == ("CN", 196))

        # ---- 8 · a day with no Marg bills is inert -----------------------
        day(con, "2026-08-24")
        con.commit()
        ck("a day with no bills raises nothing", cont(con, "2026-08-24") == [])
        s0 = summary(con, "2026-08-24")
        ck("and summarises as an empty day", s0 and s0["bills"] == 0
           and s0["bill_range"] is None)
    finally:
        con.close()
        os.unlink(path)

    bad = [n for n, ok in CHECKS if not ok]
    for n, ok in CHECKS:
        print("  %s  %s" % ("ok  " if ok else "FAIL", n))
    print("\n%d/%d checks passed" % (len(CHECKS) - len(bad), len(CHECKS)))
    if bad:
        print("SELFTEST RED")
        return 1
    print("SELFTEST GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
