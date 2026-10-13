#!/usr/bin/env python3
"""walk_s548.py -- the S548_PACK_BHAWNA_FILE walk: packs.py (built or live) imported from a copy of the finance folder, its
scan-app reader pointed at a MADE-UP database (made-up rows dated 2031, made-up names; no live row is read), the pack's own
book a made-up in-memory one.

    python3 walk_s548.py <packs.py to walk> <the finance folder it lives in> [--expect-red]

GREEN/RED per check; exit 1 on any RED (--expect-red: exit 0 only if some check is RED -- the control on the live file)."""
import importlib.util, os, shutil, sqlite3, sys, tempfile

PK, FIN = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
EXPECT_RED = "--expect-red" in sys.argv
R = []


def check(name, ok, detail=""):
    R.append(bool(ok)); print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(detail)[:200]) if (detail and not ok) else ""))


def made_up_db(path, with_pe):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE bills(id INTEGER PRIMARY KEY, stamp_no TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, "
               "source_stored TEXT, late_for TEXT, created_at TEXT, bill_month TEXT, lane TEXT, status TEXT" + (", pe_who TEXT" if with_pe else "") + ")")
    rows = [("Z-MK-1", "Made-Up Battery House 2031", "owner_expense", None), ("Z-MK-2", "Made-Up Electricals 2031", "owner_expense", None),
            ("Z-BH-1", "Made-Up Optics 2031", "owner_expense", "bhawna"), ("Z-LAB-1", "Made-Up Lab Supplies 2031", "lab_purchase", None),
            ("Z-RJ-1", "Made-Up Rejected 2031", "owner_expense", "bhawna")]
    for i, (st, v, lane, who) in enumerate(rows, 1):
        status = "rejected" if st.startswith("Z-RJ") else "captured"
        if with_pe:
            db.execute("INSERT INTO bills VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (i, st, v, "N%d" % i, "2031-01-1%d" % i, 100.0 * i, None, None,
                                                                              "2031-01-1%d 10:00" % i, "2031-01", lane, status, who))
        else:
            db.execute("INSERT INTO bills VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (i, st, v, "N%d" % i, "2031-01-1%d" % i, 100.0 * i, None, None,
                                                                           "2031-01-1%d 10:00" % i, "2031-01", lane, status))
    db.commit(); db.close()


def main():
    wd = tempfile.mkdtemp(prefix="s548_walk_", dir=os.path.expanduser("~"))
    try:
        fin = os.path.join(wd, "finance"); os.makedirs(fin)
        for f in os.listdir(FIN):                                     # the program files only -- never a database, a statement or a scan
            fp = os.path.join(FIN, f)
            if os.path.isfile(fp) and f.endswith((".py", ".html")) and ".bak" not in f:
                shutil.copy(fp, fin)
        shutil.copy(PK, os.path.join(fin, "packs.py"))
        sys.path.insert(0, fin)
        spec = importlib.util.spec_from_file_location("packs", os.path.join(fin, "packs.py"))
        try:
            pk = importlib.util.module_from_spec(spec); sys.modules["packs"] = pk; spec.loader.exec_module(pk)
        except Exception as e:                                                    # noqa: BLE001
            check("K1 packs.py imports", False, repr(e)); return
        check("K1 packs.py imports", True)
        book = sqlite3.connect(":memory:")
        book.execute("CREATE TABLE pack_send(id INTEGER PRIMARY KEY, month TEXT, sent_at TEXT, sent_by TEXT)")
        for with_pe in (True, False):
            p = os.path.join(wd, "assets_%s.db" % ("pe" if with_pe else "old"))
            made_up_db(p, with_pe)
            def con(p=p):
                c = sqlite3.connect(p); c.row_factory = sqlite3.Row; return c
            pk._assets_con = con
            mk, _w1 = pk.build_bundle(book, "2031-01", "owner_expense", count_only=True)
            bh, w2 = pk.build_bundle(book, "2031-01", "owner_expense_bhawna", count_only=True)
            lab, _w3 = pk.build_bundle(book, "2031-01", "lab_purchase", count_only=True)
            if with_pe:
                check("K2 8.2 Dr Manoj's expense file carries only Dr MK's papers (2 of the 3 live expenses)", mk == 2, (mk, _w1))
                check("K3 8.3 Dr Bhawna's expense file carries only hers (1; the rejected one left out)", bh == 1, (bh, w2))
                check("K4 8.1 the lab file is untouched (1)", lab == 1, (lab, _w3))
                b, why = pk.build_bundle(book, "2031-01", "owner_expense_bhawna")
                check("K5 Dr Bhawna's file builds as a PDF (its index page)", bool(b) and b[:4] == b"%PDF", why)
            else:
                check("K6 before S544 (no pe_who column): 8.2 carries every expense as today (3)", mk == 3, (mk, _w1))
                check("K7 before S544: 8.3 is simply not ready, with words", bh is None and "Dr Bhawna" in (w2 or ""), (bh, w2))
        src = open(os.path.join(fin, "packs.py"), encoding="utf-8").read()
        check("K8 the pack's item 8 lists the third file, Dr Bhawna's expense-file bills", "(\"owner_expense_bhawna\", \"Dr Bhawna's expense-file bills\")" in src)
    finally:
        shutil.rmtree(wd, ignore_errors=True)


try:
    main()
except Exception as _e:                                                          # noqa: BLE001
    check("the walk ran to its end", False, repr(_e))
red = R.count(False)
print("%d checks, %d green, %d red" % (len(R), len(R) - red, red))
if EXPECT_RED:
    sys.exit(0 if red else 1)
sys.exit(1 if red else 0)
