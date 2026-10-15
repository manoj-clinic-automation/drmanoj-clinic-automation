#!/usr/bin/env python3
"""walk_s560_pack.py -- the S560 walk of THE PARENT'S packs.py (build_bundle and the item-8 list). packs.py (built or live)
imported from a copy of the finance folder's program files; its scan-app reader pointed at a MADE-UP database (made-up rows
dated September / October 2031, made-up names; no live row is read); the pack's own book a made-up in-memory one. The index
page's lines are taken as they are handed to the PDF writer (no PDF tool is run).

    python3 -B walk_s560_pack.py <packs.py to walk> <the finance folder> [--before <the live packs.py>] [--expect-red]

--before: also print the September / October bundles of the live file beside the walked one (the before / after table).
GREEN/RED per check; exit 1 on any RED (--expect-red: exit 0 only if every check in MUST_RED is RED -- the control)."""
import importlib.util, os, re, shutil, sqlite3, sys, tempfile

A = sys.argv[1:]
PK, FIN = os.path.abspath(A[0]), os.path.abspath(A[1])
BEFORE = os.path.abspath(A[A.index("--before") + 1]) if "--before" in A else None
EXPECT_RED = "--expect-red" in A
MUST_RED = ("P2", "P3", "P5", "P6", "P7", "P8", "C2")
if "--must-red" in A:                                                    # FIX1: the control on the S560 kit as it was before fix round 1
    MUST_RED = tuple(x for x in A[A.index("--must-red") + 1].split(",") if x)
R, NAMES = [], []
LANES = ("lab_purchase", "owner_expense", "owner_expense_bhawna", "construction_accountant")


def check(name, ok, detail=""):
    R.append(bool(ok)); NAMES.append(name.split(" ")[0])
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(detail)[:300]) if (detail and not ok) else ""))


ROWS = [  # stamp, vendor, lane, status, bill_date, doc_kind, challan_state, subgroup, to_accountant, pe_who
    ("Z-S560-LB", "Made-Up Lab Reagents 2031", "lab_purchase", "captured", "2031-09-04", "bill", None, None, 0, None),
    ("Z-S560-LR", "Made-Up Lab Reagents 2031", "lab_purchase", "captured", "2031-09-08", "receipt", None, None, 0, None),
    ("Z-S560-LC", "Made-Up Lab Glass 2031", "lab_purchase", "captured", "2031-09-09", "challan", "awaiting", None, 0, None),
    ("Z-S560-LF", "Made-Up Lab Gas 2031", "lab_purchase", "captured", "2031-09-10", "challan", "final", None, 0, None),
    ("Z-S560-LX", "Made-Up Lab Rejected 2031", "lab_purchase", "rejected", "2031-09-11", "bill", None, None, 0, None),
    ("Z-S560-E1", "Made-Up Computers 2031", "owner_expense", "captured", "2031-09-05", None, None, None, 0, None),
    ("Z-S560-E2", "Made-Up Computers 2031", "owner_expense", "captured", "2031-09-25", "statement", None, None, 0, None),
    ("Z-S560-E3", "Made-Up Optics 2031", "owner_expense", "captured", "2031-09-06", "bill", None, None, 0, "bhawna"),
    ("Z-S560-C1", "Made-Up Cement 2031", "clinic", "approved", "2031-09-12", "bill", None, "construction", 1, None),
    ("Z-S560-C2", "Made-Up Paints 2031", "owner_expense", "captured", "2031-09-13", "bill", None, "construction", 1, None),
    ("Z-S560-C3", "Made-Up Tiles 2031", "clinic", "approved", "2031-09-14", "bill", None, "construction", 0, None),
    ("Z-S560-C4", "Made-Up Mason 2031", "clinic", "approved", "2031-09-15", "estimate", None, "construction", 1, None),
    ("Z-S560-C5", "Made-Up Sand 2031", "clinic", "rejected", "2031-09-16", "bill", None, "construction", 1, None),
    ("Z-S560-C6", "Made-Up Wiring 2031", "other_doc", "captured", "2031-09-17", None, None, "construction", 1, None),
    ("Z-S560-C7", "Made-Up Plumbing 2031", "clinic", "approved", "2031-10-03", "bill", None, "construction", 1, None),
    ("Z-S560-L2", "Made-Up Lab Reagents 2031", "lab_purchase", "captured", "2031-10-04", "bill", None, None, 0, None),
]


def made_up_db(path):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE bills(id INTEGER PRIMARY KEY, stamp_no TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, "
               "source_stored TEXT, late_for TEXT, created_at TEXT, bill_month TEXT, lane TEXT, status TEXT, doc_kind TEXT, challan_state TEXT, "
               "subgroup TEXT, to_accountant INTEGER NOT NULL DEFAULT 0, pe_who TEXT)")
    for i, (st, v, lane, status, bd, dk, cs, sg, ta, who) in enumerate(ROWS, 1):
        db.execute("INSERT INTO bills VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (i, st, v, "N%d" % i, bd, 100.0 * i, None, None, bd + " 10:00", bd[:7], lane, status, dk, cs, sg, ta, who))
    db.commit(); db.close()


def load(path, name, fin):
    shutil.copy(path, os.path.join(fin, name + ".py"))
    spec = importlib.util.spec_from_file_location(name, os.path.join(fin, name + ".py"))
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return m


def bundles(pk, dbp):
    """{(month, lane): sorted stamps} -- build_bundle's own rows, read off its index lines."""
    out = {}
    cap = []

    def con():
        c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row; return c
    pk._assets_con = con
    pk._text_pdf = lambda title, lines: (cap.append(list(lines)), b"%PDF-1.4 made-up index")[1]
    book = sqlite3.connect(":memory:")
    book.execute("CREATE TABLE pack_send(id INTEGER PRIMARY KEY, month TEXT, sent_at TEXT, sent_by TEXT)")
    for month in ("2031-09", "2031-10"):
        for lane in LANES:
            del cap[:]
            b, why = pk.build_bundle(book, month, lane)
            out[(month, lane)] = sorted(re.findall(r"Z-S560-\w\w", " ".join(cap[0]))) if (b and cap) else []
    return out


def main():
    wd = tempfile.mkdtemp(prefix="s560_pack_", dir=os.path.expanduser("~"))
    try:
        fin = os.path.join(wd, "finance"); os.makedirs(fin)
        for f in os.listdir(FIN):                                     # the program files only -- never a database, a statement or a scan
            fp = os.path.join(FIN, f)
            if os.path.isfile(fp) and f.endswith((".py", ".html")) and ".bak" not in f and f != "packs.py":
                shutil.copy(fp, fin)
        sys.path.insert(0, fin)
        dbp = os.path.join(wd, "assets.db"); made_up_db(dbp)
        try:
            pk = load(PK, "packs", fin)
        except Exception as e:                                         # noqa: BLE001
            check("P1 packs.py imports", False, repr(e)); return
        check("P1 packs.py imports from the copy of the finance folder; the scan app's reader is the made-up database", pk.__file__.startswith(fin))
        new = bundles(pk, dbp)
        old = None
        if BEFORE:
            old = bundles(load(BEFORE, "packs_before", fin), dbp)
            print("BEFORE / AFTER (made-up rows; stamps in each bundle):")
            for k in sorted(new):
                print("  %s %-24s before %-46s after %s" % (k[0], k[1], ",".join(s[7:] for s in old[k]) or "-", ",".join(s[7:] for s in new[k]) or "-"))
        S = lambda *t: sorted("Z-S560-" + x for x in t)                # noqa: E731
        check("P2 8.1 (the lab's bills), September: the receipt and the awaiting challan are out; the bill and the challan-turned-final stay",
              new[("2031-09", "lab_purchase")] == S("LB", "LF"), new[("2031-09", "lab_purchase")])
        check("P3 8.2 (Dr Manoj's expense file), September: the statement is out; the bill stays; the construction bill ticked for the "
              "accountant (C2) is out too -- it goes in 8.4 only (FIX1 C1)",
              new[("2031-09", "owner_expense")] == S("E1"), new[("2031-09", "owner_expense")])
        check("P4 8.3 (Dr Bhawna's expense file): unchanged -- her bill only", new[("2031-09", "owner_expense_bhawna")] == S("E3"), new[("2031-09", "owner_expense_bhawna")])
        check("P5 the NEW item, September: 'Construction bills marked for the accountant' carries exactly the ticked construction BILLS, "
              "whatever their lane (clinic, Personal expense, Other document) -- never the unticked bill, the ticked estimate or the rejected bill",
              new[("2031-09", "construction_accountant")] == S("C1", "C2", "C6"), new[("2031-09", "construction_accountant")])
        check("P6 October: the new item carries October's ticked bill only (the pack's own month rule); 8.1 October unchanged",
              new[("2031-10", "construction_accountant")] == S("C7") and new[("2031-10", "lab_purchase")] == S("L2"),
              (new[("2031-10", "construction_accountant")], new[("2031-10", "lab_purchase")]))
        src = open(os.path.join(fin, "packs.py"), encoding="utf-8").read()
        m8 = re.search(r"for n8, \(lane, label\) in enumerate\(\((.*?)\), 1\):", src, re.S)
        lanes8 = re.findall(r'\("(\w+)", "', m8.group(1)) if m8 else []
        check("P7 the item-8 list numbers it after the last: 8.1 lab, 8.2 Dr Manoj, 8.3 Dr Bhawna, 8.4 Construction bills marked for the accountant",
              lanes8 == ["lab_purchase", "owner_expense", "owner_expense_bhawna", "construction_accountant"]
              and '("construction_accountant", "Construction bills marked for the accountant")' in src, lanes8)
        if old is not None:
            gone = sorted(set(sum((old[k] for k in old), [])) - set(sum((new[k] for k in new), [])))
            changed = sorted("%s %s" % k for k in new if new[k] != old[k])
            check("P8 before / after: only the intended rows change -- out: the receipt, the awaiting challan, the statement; new: item 8.4 "
                  "(September, October); every other bundle as before",
                  gone == S("LC", "LR", "E2") and changed == ["2031-09 construction_accountant", "2031-09 lab_purchase", "2031-09 owner_expense",
                                                                "2031-10 construction_accountant"]
                  and old[("2031-09", "construction_accountant")] == [], (gone, changed))
        else:
            check("P8 before / after (needs --before)", False, "no --before file given")
        # FIX1 C1: made-up bill C2 (construction, ticked) on the owner-expense lane, then moved to the lab lane -- in the pack once, 8.4 only
        seen2 = {}
        for ln in ("owner_expense", "lab_purchase"):
            c = sqlite3.connect(dbp); c.execute("UPDATE bills SET lane=? WHERE stamp_no='Z-S560-C2'", (ln,)); c.commit(); c.close()
            nb = bundles(pk, dbp)
            seen2[ln] = sorted(k[1] for k in nb if "Z-S560-C2" in nb[k])
        c = sqlite3.connect(dbp); c.execute("UPDATE bills SET lane='owner_expense' WHERE stamp_no='Z-S560-C2'"); c.commit(); c.close()
        print("C2-LANES (the bundles holding made-up C2): %s" % seen2)
        check("C2 a construction bill ticked 'Send to accountant' goes into the pack ONCE: made-up C2 on the owner-expense lane, then on the "
              "lab lane -- each time only in 8.4, never also in 8.1 / 8.2 / 8.3",
              seen2 == {"owner_expense": ["construction_accountant"], "lab_purchase": ["construction_accountant"]}, seen2)
    finally:
        shutil.rmtree(wd, ignore_errors=True)


try:
    main()
except Exception as _e:                                                          # noqa: BLE001
    import traceback; traceback.print_exc()
    check("the walk ran to its end", False, repr(_e))
red = R.count(False)
print("%d pack checks: %d GREEN, %d RED" % (len(R), len(R) - red, red))
if EXPECT_RED:
    seen = dict(zip(NAMES, R))
    nr = [k for k in MUST_RED if seen.get(k) is not False]
    print("CONTROL must-be-red: %s -- %s" % (", ".join(MUST_RED), "all RED" if not nr else "NOT red: " + ", ".join(nr)))
    sys.exit(0 if (red and not nr) else 1)
sys.exit(1 if red else 0)
