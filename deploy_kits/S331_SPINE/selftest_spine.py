"""selftest_spine.py -- S272 / kit S331. Every reader and the gate are MADE TO FAIL on purpose (the F-536 rule).

    python selftest_spine.py            -> 'SELFTEST OK  n checks' or 'SELFTEST FAILED' with the first failure

Fixtures are synthetic rows (no real export ships in a kit: F-185, PHI). Each reader is shown a correct
report and then a corrupted one, and must pass the first and refuse the second. The builder is given a
tiny evidence store and must swap a good build in, refuse a bad one, and leave the last good spine alone.
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import marg_read as M          # noqa: E402
import spine_build as B        # noqa: E402
import spine_evidence as E     # noqa: E402
from spine_read import Spine   # noqa: E402

N = 0


def check(name, ok):
    global N
    N += 1
    if not ok:
        print("SELFTEST FAILED at check %d: %s" % (N, name))
        sys.exit(1)


MOB = "9" + "0" * 8 + "1"          # a synthetic 10-digit string, built here so no number sits in the file (F-185)
HEAD = [["SANJEEVNI MEDICOS"], ["35G/15B , RAMPUR BAGH BAREILLY"], ["Phone : 0000000000"]]


def closing(items, total, day="31-03-2026"):
    rows = HEAD + [["WHOLE STORES CLOSING STOCK AS ON " + day], ["S.No.", "Description", "Total Stock", "Unit"]]
    for n, (name, pack, qty, unit) in enumerate(items, 1):
        rows.append(["%d.0" % n, "%-30s%s" % (name, pack), qty, unit])
    rows.append(["TOTAL", "", str(total), ""])
    rows.append(["MARG ERP NANO Rs.5550 | Manage Stock | Call 0000000000"])
    return rows


def salt_list(groups):
    rows = HEAD + [["SALT WISE ITEM LIST"], ["S.No.  DESCRIPTION", "PACKING", "P.RATE", "S.RATE", "M.R.P."]]
    for g, items in groups:
        rows.append([g, "", "0.0", "0.0", "0.0"])
        for n, (name, pack, p, s, m) in enumerate(items, 1):
            rows.append(["%d   %s" % (n, name), pack, p, s, m])
    return rows


def sale(bills, day="01-04-2026"):
    rows = HEAD + [["BILL WISE SALES STATEMENT"], ["BILL NO.", "DESCRIPTION", "D.R.", "GROSS AMT.", "DISCOUNT", "TAX", "DR/CR", "NET AMT.", "CASH"], [day]]
    tot = 0.0
    for no, gross, lines in bills:
        rows.append([no, "SOME PERSON", MOB, str(gross), "0", "0", "0", str(gross), str(gross)])   # the patient columns
        tot += gross
        for i, (name, qty, rate) in enumerate(lines, 1):
            rows.append(["", "%d   0 %-20s1*10" % (i, name), qty, "%.2f  1/28" % rate, "B1"])
    rows.append(["", "", "DAY TOTAL :", "%.2f" % tot, "0", "0", "0", "%.2f" % tot, "%.2f" % tot])
    rows.append(["Total No. of", "Bills: %d" % len(bills), "GRAND TOTAL :", "%.2f" % tot, "0", "0", "0", "%.2f" % tot, "%.2f" % tot])
    return rows


def pbill(bills, d1="01-04-2026", d2="30-04-2026"):
    rows = HEAD + [["BILL WISE PURCHASE STATEMENT FROM %s TO %s" % (d1, d2)], ["BILL NO.", "PARTY NAME", "CASH", "CREDIT"]]
    tot = 0.0
    day = None
    for d, no, party, amt in bills:
        if d != day:
            rows.append([d]); day = d
        rows.append([no, party, "-", str(amt)]); tot += amt
    rows.append(["TOTAL", str(tot), "-", str(tot)])
    return rows


def plines(sups, d1="01-04-2026", d2="30-04-2026"):
    rows = HEAD + [["SUPPLIER/ITEM WISE PURCHASE STATEMENT FROM %s TO %s" % (d1, d2)],
                   ["BILL", "ITEM DESCRIPTION", "PACKING BATCH", "EXP.", "TAX", "QTY.", "FREE", "RATE", "DIS.", "AMOUNT NET RATE", "LOOS PURC. ?", "AMOUNT"]]
    gt = [0.0, 0.0]
    for sup, lines in sups:
        rows.append([sup]); st = [0.0, 0.0]
        for bill, name, pack, qty, rate in lines:
            amt = qty * rate
            rows.append([bill, name, pack, "1/28", "5.0", str(qty), "", str(rate), "0.0", "%.2f  %.2f" % (amt, rate / 10), "%d  %.2f" % (qty * 10, rate), str(amt)])
            st[0] += amt; st[1] += amt
        rows.append(["", "", "", "", "", "", "", "TOTAL", "", "%.2f" % st[0], "", "%.2f" % st[1]])
        gt[0] += st[0]; gt[1] += st[1]
    rows.append(["GRAND", "TOTAL", "", "", "", "", "", "", "", "%.2f" % gt[0], "", "%.2f" % gt[1]])
    return rows


# ======================================================================= readers
def test_readers():
    items = [("ALPHA TAB", "1*10", "3:5", "STRI"), ("BETA BELT L", "1*1", "2.0", "ITEM"), ("GAMMA SYP", "1*1", "-", "BTL")]
    r = M.read_closing(closing(items, 37))
    check("closing: a correct report passes", r.ok and r.data["as_on"] == "2026-03-31" and len(r.data["items"]) == 3)
    check("closing: 3:5 of a 1*10 is 35 units, a plain figure is itself", r.data["items"][0]["units"] == 35 and r.data["items"][1]["units"] == 2)
    check("closing: a wrong printed TOTAL is refused", not M.read_closing(closing(items, 36)).ok)
    rows = closing(items, 37); rows[6][0] = "3.0"
    check("closing: a broken serial is refused", not M.read_closing(rows).ok)
    rows = closing(items, 37); rows.insert(7, ["some stray text"])
    check("closing: an unclassified row is refused", not M.read_closing(rows).ok)
    check("closing: a category-filtered print is NOT this reader's report", M.identify(HEAD + [["ORTHOTICS CLOSING STOCK AS ON 01-01-2026"], ["S.No.", "Description", "Total Stock", "Unit"]]) is None)

    groups = [("PARACETAMOL", [("ALPHA TAB", "1*10", "8.0", "9.0", "10.0")]), ("BELTS", [("BETA BELT L", "1*1", "100.0", "110.0", "120.0")])]
    r = M.read_grouped_list(salt_list(groups), "SALT_WISE_ITEM_LIST", r'SALT\s+WISE\s+ITEM\s+LIST')
    check("salt list: a correct report passes and carries the MRP", r.ok and r.data["items"][0]["mrp"] == 10.0 and r.data["items"][1]["group"] == "BELTS")
    rows = salt_list(groups); rows.insert(6, ["SANJEEVNI MEDICOS"]); rows.insert(7, ["Page No..2"])
    r = M.read_grouped_list(rows, "SALT_WISE_ITEM_LIST", r'SALT\s+WISE\s+ITEM\s+LIST')
    check("salt list: a page header inside a group is furniture, not a salt (F-536)", r.ok and all(d["group"] != "SANJEEVNI MEDICOS" for d in r.data["items"]))
    rows = salt_list(groups); rows[6][0] = "2   ALPHA TAB"
    check("salt list: a serial that does not restart at 1 under a heading is refused", not M.read_grouped_list(rows, "SALT_WISE_ITEM_LIST", r'SALT\s+WISE').ok)

    bills = [("A000001", 100.0, [("ALPHA TAB", "1:0", 100.0)]), ("CN000001", -50.0, [("ALPHA TAB", "0:5", 100.0)])]
    r = M.read_sale_detail(sale(bills))
    check("sale: a correct report passes; a CN bill is a credit note", r.ok and len(r.data["bills"]) == 2 and r.data["bills"][1]["credit_note"])
    js = json.dumps(r.data)
    check("sale: the reading carries NO patient cell (name or mobile)", "SOME PERSON" not in js and MOB not in js)
    check("sale: bill money is in paise", r.data["bills"][0]["gross_p"] == 10000)
    rows = sale(bills); rows[-1][1] = "Bills: 3"
    check("sale: a footer bill count that disagrees is refused", not M.read_sale_detail(rows).ok)
    rows = sale(bills); rows[-1][3] = "60.00"
    check("sale: a GRAND TOTAL that does not equal the bills is refused", not M.read_sale_detail(rows).ok)
    rows = sale(bills); rows[7][1] = "2   0 ALPHA TAB           1*10"
    check("sale: line numbers that do not run 1..n are refused", not M.read_sale_detail(rows).ok)

    pb = [("02-04-2026", "0160.0", "DRUG DEAL BAREILLY", 500.0), ("02-04-2026", "7.0", "OTHER PHARMA", -120.0)]
    r = M.read_purchase_billwise(pbill(pb))
    check("purchase bill-wise: passes; a minus bill is a RETURN; bill number is text with its zeros", r.ok and r.data["bills"][1]["direction"] == "RETURN"
          and r.data["bills"][0]["bill"] == "0160" and r.data["bills"][0]["date"] == "2026-04-02")
    rows = pbill(pb); rows[-1][1] = "381.0"; rows[-1][3] = "381.0"
    check("purchase bill-wise: a TOTAL that does not equal the bills is refused", not M.read_purchase_billwise(rows).ok)

    pl = [("DRUG DEAL BAREILLY", [("160.0", "ALPHA TAB", "1*10", 10, 50.0)]), ("OTHER PHARMA", [("7.0", "BETA BELT L", "1*1", 1, 120.0)])]
    r = M.read_purchase_lines(plines(pl))
    check("purchase lines: passes, grouping and period read from the title, bill number text", r.ok and r.data["grouping"] == "SUPPLIER" and r.data["lines"][0]["bill"] == "160" and r.data["lines"][0]["supplier"] == "DRUG DEAL BAREILLY")
    rows = plines(pl); rows[-1][11] = "999.00"
    check("purchase lines: a GRAND TOTAL off by a rupee is refused", not M.read_purchase_lines(rows).ok)
    rows = plines(pl); rows[7][11] = "501.0"
    check("purchase lines: a supplier TOTAL that does not re-add its lines is refused", not M.read_purchase_lines(rows).ok)

    check("identify: a report is known by its title, not its file name", M.identify(sale(bills)) == "SALE_BILLWISE" and M.identify(pbill(pb)) == "PURCHASE_BILLWISE")
    check("identify: a summary sale layout is refused", M.identify(HEAD + [["BILL WISE SALES STATEMENT"], ["BILL NO.", "PARTY", "AMOUNT"]]) is None)
    check("furniture: Marg's footer is furniture in any capitals", M.furniture(["Marg ERP nano | Call 0000000000"]) == "ADVERT")


# ======================================================================= evidence store
def test_evidence():
    check("evidence: an md5 is not a mobile number", E.phi_free(dict(md5="9" * 32, name="x")))
    check("evidence: a 10-digit mobile anywhere is refused", not E.phi_free(dict(data=dict(note="call " + "9" * 10))))
    check("evidence: a key naming a person is refused", not E.phi_free(dict(data={"patient": "x"})))
    tmp = tempfile.mkdtemp()
    try:
        arch = os.path.join(tmp, "MargArchive", "STOCK_CLOSING", "2026-03")
        os.makedirs(arch)
        import xlwt_free  # noqa: F401  (never present; the .xls writer is not a dependency) -- pragma: no cover
    except ImportError:
        pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ======================================================================= the builder and its gate
def rec(name, family, data, ok=True, checks=None, stamp="20260401-000000"):
    import hashlib
    return dict(md5=hashlib.md5(name.encode()).hexdigest(), name=name, stamp=stamp, reader="test", family=family, ok=ok,
                checks=checks or [("test", ok, "")], failed=[] if ok else ["test"], data=data)


def store(tmp, opening_units=35, recon=True, break_closing=False, bad_file=False):
    d = os.path.join(tmp, "store"); os.makedirs(d, exist_ok=True)
    it = lambda q, name="ALPHA TAB", plain=False: dict(serial=1, name=name, packing="1*10", qty_raw=q, units=M.qty_units(q, "1*10"), unit="STRI", plain=plain)
    recs = [
        rec("open.XLS", "STOCK_CLOSING", dict(as_on="2026-03-31", items=[it("3:5" if opening_units == 35 else "3:6")] + [dict(serial=2, name="X%d" % i, packing="1*1", qty_raw="-", units=0.0, unit="ITEM", plain=False) for i in range(300)], printed_total=35, lines_total=35)),
        rec("close.XLS", "STOCK_CLOSING", dict(as_on="2026-04-05", items=[it("2:0" if not break_closing else "2:1")] + [dict(serial=2, name="X%d" % i, packing="1*1", qty_raw="-", units=0.0, unit="ITEM", plain=False) for i in range(300)], printed_total=20, lines_total=20), stamp="20260405-230000"),
        rec("salt.XLS", "SALT_WISE_ITEM_LIST", dict(as_on="2026-04-01", items=[dict(group="PARACETAMOL", name="ALPHA TAB", packing="1*10", p_rate=8.0, s_rate=9.0, mrp=10.0)])),
        rec("pb.XLS", "PURCHASE_BILLWISE", dict(date_from="2026-04-01", date_to="2026-04-05", bills=[dict(date="2026-04-02", bill="160", supplier="DRUG DEAL", cash_p=0, credit_p=5000, amount_p=5000, direction="PURCHASE")])),
        rec("pl.XLS", "PURCHASE_ITEMWISE", dict(grouping="SUPPLIER", date_from="2026-04-01", date_to="2026-04-05", lines=[dict(seq=1, bill="160", supplier="DRUG DEAL", date="", name="ALPHA TAB", packing="1*10", batch="", qty=1, free=0, loose=10, rate=50.0, purc=50.0, net_amount_p=5000, amount_p=5000, glued=False)])),
    ]
    # sales: 5 days, every day 01..05 Apr, each selling 1 strip; 35 + 10 - 25 = 20 with the reconciliation of -0 ... make it need a recon of -... :
    # opening 35, purchase 10, sales 5x5 = 25 -> 20 = closing 2:0. With recon=False and opening 36 -> 21 != 20.
    for i in range(1, 6):
        d0 = "2026-04-%02d" % i
        recs.append(rec("sale%d.XLS" % i, "SALE_BILLWISE", dict(date_from=d0, date_to=d0, days=[d0], bills=[dict(
            date=d0, bill="A%06d" % i, gross_p=5000, disc_p=0, tax_p=0, drcr_p=0, net_p=5000, cash_p=5000, credit_note=False,
            lines=[dict(seq=1, name="ALPHA TAB", pack="1*10", qty="0:5", rate_p=10000, expiry="", batch="")])]), stamp="202604%02d-230000" % i))
    if bad_file:
        recs.append(rec("bad.XLS", "STOCK_CLOSING", dict(as_on="2026-04-05", items=[it("9:9")] + [dict(serial=2, name="X%d" % i, packing="1*1", qty_raw="-", units=0.0, unit="ITEM", plain=False) for i in range(300)], printed_total=1, lines_total=99), ok=False, checks=[("TOTAL units = sum of every line", False, "printed 1, lines 99")], stamp="20260405-235900"))
    for r in recs:
        json.dump(r, open(os.path.join(d, r["md5"] + ".json"), "w"))
    rules = dict(version="test", opening=dict(as_on="2026-03-31", file_md5_prefix=recs[0]["md5"][:8]), exceptions=[], aliases={}, families={},
                 reconciliation=[dict(k20="ALPHA TAB", units=-1, reason="test", source="test")] if recon else [], min_full_closing_items=250)
    rp = os.path.join(tmp, "rules.json"); json.dump(rules, open(rp, "w"))
    return d, rp


def fake_finance(tmp, n=373):
    p = os.path.join(tmp, "f%d.db" % n)
    if os.path.exists(p):
        return p
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE stock_count_item (id INTEGER)"); c.executemany("INSERT INTO stock_count_item VALUES (?)", [(i,) for i in range(n)]); c.commit(); c.close()
    return p


def test_builder():
    tmp = tempfile.mkdtemp()
    import io, contextlib
    real_main = B.main

    def quiet(argv):
        with contextlib.redirect_stdout(io.StringIO()):
            return real_main(argv)
    B.main = quiet
    try:
        d, rp = store(tmp, opening_units=36, recon=True)             # 36 + 10 - 25 - 1 = 20 = Marg
        out = os.path.join(tmp, "spine.db")
        rc = B.main(["--readings", d, "--rules", rp, "--out", out, "--finance-db", fake_finance(tmp), "--acceptance"])
        check("builder: a consistent store builds and swaps", rc == 0 and os.path.exists(out))
        sp = Spine(out)
        check("read door: stock equals Marg at the closing", sp.stock("ALPHA TAB", "2026-04-05")["spine_units"] == 20 and sp.stock("ALPHA TAB", "2026-04-05")["marg_units"] == 20)
        check("read door: MRP comes from the salt list", sp.fact("ALPHA TAB", "mrp")[0]["value"] == "10.0")
        check("read door: a return-less purchase is a PURCHASE", sp.purchases("2026-04")[0]["direction"] == "PURCHASE")
        good_md5 = open(out, "rb").read()
        d2, rp2 = store(os.path.join(tmp, "b"), opening_units=36, recon=False)     # 36 + 10 - 25 = 21 != 20
        rc = B.main(["--readings", d2, "--rules", rp2, "--out", out, "--finance-db", fake_finance(os.path.join(tmp, "b")), "--acceptance"])
        check("gate: a stock difference at the latest closing FAILS acceptance and swaps nothing", rc == 3 and open(out, "rb").read() == good_md5 and os.path.exists(out + ".failed"))
        c = sqlite3.connect(out + ".failed")
        check("gate: the failed build records the difference as an open finding", c.execute("SELECT COUNT(*) FROM sp_finding WHERE note LIKE 'OPEN%'").fetchone()[0] == 1)
        rc = B.main(["--readings", d2, "--rules", rp2, "--out", os.path.join(tmp, "b", "s.db"), "--finance-db", fake_finance(os.path.join(tmp, "b"))])
        check("gate: without --acceptance the same difference is a dated finding and the build swaps", rc == 0 and Spine(os.path.join(tmp, "b", "s.db")).findings()[0]["k20"] == "ALPHA TAB")
        d3, rp3 = store(os.path.join(tmp, "c"), opening_units=36, recon=True, bad_file=True)
        rc = B.main(["--readings", d3, "--rules", rp3, "--out", os.path.join(tmp, "c", "s.db"), "--finance-db", fake_finance(os.path.join(tmp, "c")), "--acceptance"])
        check("gate: a closing that failed its witness is refused, and the build with it", rc == 3)
        d4, rp4 = store(os.path.join(tmp, "d"), opening_units=36, recon=True)
        rc = B.main(["--readings", d4, "--rules", rp4, "--out", os.path.join(tmp, "d", "s.db"), "--finance-db", fake_finance(os.path.join(tmp, "d"), n=372), "--acceptance"])
        check("gate: a count baseline that is not 373 rows blocks the build", rc == 3)
        rules = json.load(open(rp4)); rules["opening"]["file_md5_prefix"] = "00000000"; json.dump(rules, open(rp4, "w"))
        rc = B.main(["--readings", d4, "--rules", rp4, "--out", os.path.join(tmp, "d", "s.db"), "--finance-db", fake_finance(os.path.join(tmp, "d")), "--acceptance"])
        check("gate: an opening that is not in the store blocks the build", rc == 3)
        c = sqlite3.connect(out)
        check("spine: every movement carries its source reference", c.execute("SELECT COUNT(*) FROM sp_move WHERE ref='' OR ref IS NULL").fetchone()[0] == 0)
        check("spine: the reconciliation entry is booked, dated and sourced", c.execute("SELECT date, source FROM sp_recon").fetchone() == ("2026-04-05", "test"))
        d5, rp5 = store(os.path.join(tmp, "e"), opening_units=36, recon=True)
        for fn in os.listdir(d5):
            if "sale3" in json.load(open(os.path.join(d5, fn))).get("name", ""):
                os.remove(os.path.join(d5, fn))
        rc = B.main(["--readings", d5, "--rules", rp5, "--out", os.path.join(tmp, "e", "s.db"), "--finance-db", fake_finance(os.path.join(tmp, "e"))])
        check("gate: a missing sale day before the closing means NO closing is checkable, and that blocks even without --acceptance", rc == 3)
    finally:
        B.main = real_main
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    test_readers()
    test_evidence()
    test_builder()
    print("SELFTEST OK  %d checks" % N)
