"""synth_s857.py <finance dir under test> <finance.db COPY> [--real] -- kit S857_CHECK_OPEN_PATHS proof. Works on COPIES only.
 A made-up counted month (2025-02, purchase.register_from moved to it on the copy) with an older supplier-wise statement: the purchase check's
 strip names what is open and expands with each item's row, whose it is and its path; the open row is highlighted; 'your confirm' says which it
 is; the card counts what is open. --real: every open month's purchase check draws, its strip naming its items where it holds -- no frozen
 expectations. Last line: 'SYNTH S857: n PASS, m FAIL'."""
import os, re, shutil, sqlite3, sys, tempfile
FIN, DBC = sys.argv[1], sys.argv[2]
REAL = "--real" in sys.argv
tmp = tempfile.mkdtemp(prefix="s857synth_")
code = os.path.join(tmp, "finance")
shutil.copytree(FIN, code, ignore=shutil.ignore_patterns("*.db", "__pycache__", "_off"))
_me = os.path.dirname(os.path.abspath(__file__))           # F-1415: never the kit's own copy beside this script
sys.path[:] = [x for x in sys.path if os.path.abspath(x or os.getcwd()) != _me]
sys.path.insert(0, code)
P = F = 0
M = "2025-02"


def ok(c, what):
    global P, F
    if c:
        P += 1
        print("PASS", what)
    else:
        F += 1
        print("FAIL", what)


def fresh():
    db = os.path.join(tmp, "f%d.db" % (P + F))
    shutil.copy(DBC, db)
    con = sqlite3.connect(db, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def lay(con):
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                "('zzs857bw','BILLWISE','x','2025-02-01','2025-02-28','20250310-110000','2025-03-10T11:05:00',1,0)")
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                "('zzs857sw','SUPPLIERWISE','x','2025-02-01','2025-02-28','20250305-110000','2025-03-05T11:05:00',1,547000)")
    con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, sw_md5, bw_amount_p, sw_amount_p, source_md5, "
                "verdict, verdict_by, verdict_at, wrong_amount_p, reason) VALUES ('ZZKEDAR TEST','ZZKEDAR TEST','A9001','2025-02-15',?,536000,'zzs857bw','zzs857sw',"
                "536000,547000,'zzs857bw','WRONG','manoj','2025-03-01T10:00:00',536000,'made up')", (M,))
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('purchase.register_from', '2025-02-01')")
    con.commit()


try:
    import purchase_app as pa                                 # noqa: E402
    import month_asks as ma                                   # noqa: E402
    import scan_register as SR                                # noqa: E402
    from flask import Flask                                   # noqa: E402
    have = True
except Exception as e:                                        # noqa: BLE001
    print("import:", e)
    have = False
ok(have, "T0 the finance code under test holds month_asks.py and imports")


def page(con, m):
    app = Flask("s857_%d" % (P + F))
    pa.init(app, lambda: con, lambda *roles: (dict(user="manoj", roles=["checker"], role="checker"), None), assets_db="/nonexistent")
    r = app.test_client().get("/finance/purchase/page/check?month=%s" % m)
    return r.status_code, r.get_data(as_text=True)


if have and REAL:
    con = fresh()
    try:
        res = []
        for m in ma.months(con):
            code_, b = page(con, m)
            hold = 'class="strip hold' in b
            named = '<details class="strip hold s857" id="s726strip">' in b and "Open row" in b
            res.append((m, code_, hold, named))
        ok(res and all(c == 200 and (named or not hold) for _m, c, hold, named in res),
           "R1 the live copy: every open month's purchase check draws, its strip naming what holds it (%r)" % (res,))
    except Exception as e:                                    # noqa: BLE001
        ok(False, "R1 the live copy: %r" % (e,))
    con.close()
if have and not hasattr(ma, "open_items"):
    ok(False, "T1 month_asks under test has no open_items (the code before S857)")
elif have:
    con = fresh()
    lay(con)
    items = ma.open_items(con, M)
    exp = [it for it in items if it["row"] == 8]
    ok(exp and "supplier-wise statement for 01-02-2025 to 28-02-2025" in exp[0]["what"] and exp[0]["whose"].startswith("Amir")
       and any("SUPPLIER WISE PURCHASE STATEMENT, FROM 01-02-2025 TO 28-02-2025" in s for s in exp[0]["steps"]) and any("A9001" in s for s in exp[0]["steps"]),
       "T1 open_items: the export to do, whose it is (Amir), the exact report and dates, the bill it clears")
    code_, b = page(con, M)
    m = re.search(r'<details class="strip hold s857" id="s726strip"><summary>(NEFT on hold · \d+ open) — ([^<]*)', b)
    ok(code_ == 200 and m and "supplier-wise statement" in m.group(2) and b.count('<div class="s857i">') == len(items) and "Open row 8" in b,
       "T2 the strip names what is open and expands inline with every item and its path (%r)" % (m and m.group(0)[:160],))
    ok(re.search(r'<details id="s857r8" class="row s857open', b) is not None and re.search(r'<details id="s857r2" class="row"', b) is not None
       and "function s857row" in b, "T3 the open row (8) is highlighted, a clear one (2) is not; 'Open row N' opens it in place")
    h = ma.card_html(con, M, "/x")
    nA = ma.month_asks(con, M)
    ok(("Before February 2025 can lock — %d open" % nA["n"]) in h and "It clears by itself: Zzkedar Test A9001" in h and "<b>Zzkedar Test A9001</b>" not in h
       and h.count('<div class="it">') == len(nA["exports"]), "T4 the card counts what is open (%d) and lists the bill the export clears inside it, not as a second thing" % nA["n"])
    w0 = SR._s857_words("1 your confirm · Your confirm counts as the summary · your Confirm on row 3 counts as the summary", 0)
    w1 = SR._s857_words("1 your confirm · Your confirm counts as the summary", 1)
    ok("1 settled by your confirmation" in w0 and "Settled by your confirmation — it stands as the summary" in w0 and "settled by your confirmation on row 3" in w0
       and "1 waiting for your confirmation (row 3)" in w1 and "Waiting for your confirmation on row 3" in w1 and "your confirm " not in w0.lower().replace("your confirmation", ""),
       "T5 'your confirm' says which: settled by your confirmation / waiting for your confirmation (row 3)")
    off = os.path.join(code, "_off")
    os.makedirs(off, exist_ok=True)
    open(os.path.join(off, "S855_OFF"), "w").close()
    code_, b2 = page(con, M)
    ok(code_ == 200 and ma.open_items(con, M) == [] and '<details class="strip hold s857"' not in b2, "T6 OFF (month_asks): the check page as before S857")
    os.remove(os.path.join(off, "S855_OFF"))
    con.close()
    src = open(os.path.join(code, "scan_register.py"), encoding="utf-8").read()
    ok("_check_body_before_s857 = check_body" in src and "_ma857.open_items(con, month)" in src, "T7 the seam: the purchase check's strip, rows and words")
print("SYNTH S857: %d PASS, %d FAIL" % (P, F))
