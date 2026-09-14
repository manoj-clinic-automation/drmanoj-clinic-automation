# -*- coding: utf-8 -*-
"""S261 live-shape walk -- the page is RENDERED, not reasoned about.

It builds a database with the real August shape from the server's own schema,
mounts the patched blueprint in a real Flask app, and asks for the page over
HTTP the way a browser does. Every check reads the bytes that came back.

    python3 walk_vendor_pay_s261.py [--file purchase_app.py]
"""
import argparse, importlib.util, json, os, re, sqlite3, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OK = BAD = 0


def ck(name, cond, detail=""):
    global OK, BAD
    if cond:
        OK += 1
        print("  ok    %s" % name)
    else:
        BAD += 1
        print("  FAIL  %s   %s" % (name, str(detail)[:300]))


AUG = [
 ("A.A. PHARMACEUTICALS",[("310","2026-08-03",94300),("317","2026-08-05",94800),
   ("330","2026-08-10",189000),("334","2026-08-13",204500),("351","2026-08-21",219500),
   ("355","2026-08-24",219500),("370","2026-08-29",109700)]),
 ("KEDAR PHARMACEUTICAL",[("126","2026-08-03",1300000),("148","2026-08-20",460200),
   ("155","2026-08-28",1112000)]),
 ("RAMA MEDICOSE",[("279","2026-08-22",146900)]),
 ("VERMA BROS. AND CO.",[("45754","2026-08-19",1820000),("48066","2026-08-25",69300)]),
]
SW = "swmd5aug2026"
IW = "iwmd5aug2026"


def build_db(path, schema):
    con = sqlite3.connect(path)
    con.executescript(open(schema, encoding="utf-8").read())
    con.commit()
    return con


def seed(con):
    con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,export_stamp,"
                "received_at,n_rows,grand_amount_p) VALUES (?,?,?,?,?,?,?,?,?)",
                (SW, "SUPPLIERWISE", "SUP.XLS", "2026-08-01", "2026-08-31",
                 "20260901-090000", "2026-09-01T09:05:00", 13, 0))
    con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,export_stamp,"
                "received_at,n_rows,grand_amount_p) VALUES (?,?,?,?,?,?,?,?,?)",
                (IW, "ITEMWISE", "ITEM.XLS", "2026-08-01", "2026-08-31",
                 "20260901-091000", "2026-09-01T09:15:00", 6, 0))
    for sup, bills in AUG:
        norm = re.sub(r"\s+", " ", sup.upper()).strip()
        for no, d, amt in bills:
            con.execute("INSERT INTO purchase_bill (supplier_norm,supplier,bill_no,bill_date,month,"
                        "amount_p,sw_amount_p,sw_md5,date_src) VALUES (?,?,?,?,?,?,?,?,?)",
                        (norm, sup, no, d, "2026-08", amt, amt, SW, "SUPPLIERWISE"))
    # item lines: one bill that agrees, and the Rs 6 purchase return on KEDAR 148
    k = "KEDAR PHARMACEUTICAL"
    con.execute("INSERT INTO purchase_line (supplier_norm,bill_no,bill_date,month,item,packing,"
                "batch,expiry,qty,rate_p,net_amount_p,amount_p,source_md5,line_type) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (k, "126", "2026-08-03", "2026-08", "LOFTYPRED 80 INJ", "2ML", "B12", "05/28",
                 10, 130000, 1300000, 1300000, IW, "ITEMWISE"))
    con.execute("INSERT INTO purchase_line (supplier_norm,bill_no,bill_date,month,item,packing,"
                "batch,expiry,qty,rate_p,net_amount_p,amount_p,source_md5,line_type) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (k, "148", "2026-08-20", "2026-08", "DENGEN PLUS", "1*10", "D77", "11/27",
                 4, 57600, 230400, 230400, IW, "ITEMWISE"))
    con.execute("INSERT INTO purchase_line (supplier_norm,bill_no,bill_date,month,item,packing,"
                "batch,expiry,qty,rate_p,net_amount_p,amount_p,source_md5,line_type) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (k, "148", "2026-08-20", "2026-08", "TYNOR WRIST SPLINT", "1*1", "T09", "—",
                 2, 115200, 230400, 230400, IW, "ITEMWISE"))
    con.commit()
    return con


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=os.path.join(HERE, "purchase_app.py"))
    ap.add_argument("--schema", default=os.path.join(HERE, "purchase_schema.sql"))
    a = ap.parse_args(argv)

    spec = importlib.util.spec_from_file_location("purchase_app_s261", a.file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "finance.db")
    build_db(dbp, a.schema).close()

    import flask
    app = flask.Flask(__name__)
    holder = {}

    def db():
        if "con" not in holder:
            c = sqlite3.connect(dbp)
            c.row_factory = sqlite3.Row
            holder["con"] = c
        return holder["con"]

    USER = {"user": "manoj", "role": "checker", "roles": ["checker"]}

    def require(*roles):
        return USER, None

    mod.init(app, db, require, unit="medical", url_prefix="/finance/purchase")
    with app.test_request_context("/"):
        mod._ensure(db())          # the server's own migrations, then the fixture
        seed(db())
    c = app.test_client()

    # --------------------------------------------------- the page renders
    r = c.get("/finance/purchase/page/pay/2026-08")
    ck("the page answers 200", r.status_code == 200, r.status_code)
    h = r.get_data(as_text=True)
    ck("it is the vendor payments page", "Vendor payments" in h and "August 2026" in h)

    # ------------------------ the owner's order: PREPARE first, VERIFY second
    ck("the sheet comes first and the verification second",
       h.index("1 &middot; The sheet") < h.index("2 &middot; Verify against the supplier-wise"),
       "the two steps are the wrong way round")
    ck("the sheet is a sheet: both fortnights, carried in, payable",
       "1st–15th" in h and "16th–end" in h and "Carried in" in h and "Payable" in h)
    ck("it says plainly that carried-in is the one thing typed here",
       "the only thing typed here" in h)

    # ------------------------------------------------ one line per vendor
    for sup, bills in AUG:
        ck("%s has one line" % sup, h.count('>' + sup.replace("&", "&amp;")) >= 1, sup)
    ck("A.A.'s seven bills add up on its line", "₹11,313" in h, "11,313 missing")
    ck("KEDAR's three bills add up on its line", "₹28,722" in h, "28,722 missing")

    # ------------------------- rule 2: an unconfirmed vendor is not on NEFT
    ck("RAMA MEDICOSE is routed to a cheque", "CHEQUE" in h)
    ck("and the page says why, in words", "no account on this server" in h)
    ck("and it is named in the cheque section with the way to fix it",
       "not in the NEFT file" in h and "add / confirm the account" in h)
    ck("every vendor is on the cheque lane while no account is confirmed",
       h.count("CHEQUE") >= len(AUG), "expected a chip per vendor")

    # ---- and a vendor WITH a confirmed account is on NEFT, with no chip at all
    con = sqlite3.connect(dbp)
    con.execute("UPDATE purchase_vendor_contact SET acct_no='X', bank_status='VERIFIED' "
                "WHERE vendor_norm=?", ("KEDAR PHARMACEUTICAL",))
    if con.total_changes == 0:
        con.execute("INSERT INTO purchase_vendor_contact (vendor_norm,vendor,acct_no,bank_status,"
                    "updated_at,source) VALUES (?,?,?,?,?,?)",
                    ("KEDAR PHARMACEUTICAL", "KEDAR PHARMA", "X", "VERIFIED",
                     "2026-09-14T10:00:00", "server"))
    con.commit(); con.close()
    holder.pop("con", None)
    h3 = c.get("/finance/purchase/page/pay/2026-08").get_data(as_text=True)
    kedar = h3[h3.index("KEDAR PHARMACEUTICAL"):]
    kedar = kedar[:kedar.index("</button>")]
    ck("a vendor whose account IS confirmed carries no cheque chip",
       "CHEQUE" not in kedar, kedar[:200])
    ck("and the NEFT total now holds that vendor", "\u20b928,722" in h3 or "28,722" in h3)
    ck("the cheque section shrank to the vendors that really need one",
       "not in the NEFT file (%d)" % (len(AUG) - 1) in h3,
       h3[h3.index("Paid by cheque"):h3.index("Paid by cheque") + 80])
    holder.pop("con", None)

    # ------------------------------------ rule 3: a small difference is flagged
    ck("the ₹6 purchase return is flagged, not swallowed",
       "purchase return against it" in h and "₹6 more than the bill" in h)
    ck("and it says it may be an entry that needs correcting",
       "may be an entry that needs correcting" in h)

    # ------------------------------- the verification runs, and keeps its run
    ck("the verification has not been claimed before it is run", "Not checked yet" in h)
    rv = c.post("/finance/purchase/api/pay-verify", json={"month": "2026-08"})
    ck("the check runs", rv.status_code == 200, rv.status_code)
    jv = json.loads(rv.get_data(as_text=True))
    ck("and it agrees with the statement on this month", jv.get("verified") is True, jv)
    h = c.get("/finance/purchase/page/pay/2026-08").get_data(as_text=True)
    ck("the page now says it was checked and agrees",
       "Checked against the statement and it agrees" in h)
    ck("and it names the statement it checked against", "SUP.XLS" in h)

    # --------------------------------- carried-in is typed, kept and added in
    rp = c.post("/finance/purchase/api/pay-line",
                json={"month": "2026-08", "vendor_norm": "KEDAR PHARMACEUTICAL",
                      "carry_fwd": "310", "note": "left from July"})
    ck("a carry-forward can be typed on the sheet", rp.status_code == 200, rp.get_data(as_text=True))
    h = c.get("/finance/purchase/page/pay/2026-08").get_data(as_text=True)
    ck("and the payable moves by exactly that much",
       "\u20b929,032" in h, "28,722 + 310 = 29,032 not found")

    # --------------------------------------- the third level really loads
    bid = None
    con = sqlite3.connect(dbp)
    bid = con.execute("SELECT id FROM purchase_bill WHERE bill_no='148'").fetchone()[0]
    con.close()
    r2 = c.get("/finance/purchase/api/bill-lines?bill=%d" % bid)
    ck("the bill's own lines load", r2.status_code == 200, r2.status_code)
    j = json.loads(r2.get_data(as_text=True))
    ck("two item lines come back for bill 148", j.get("ok") and len(j.get("lines", [])) == 2, j)
    ck("they carry item, batch, expiry, qty, rate and amount",
       all(k in (j["lines"][0] or {}) for k in ("item", "batch", "expiry", "qty", "rate", "amount")), j)
    ck("a bill that does not exist is refused, not guessed",
       c.get("/finance/purchase/api/bill-lines?bill=999999").status_code == 404)

    # ---------------------------------------------- the stable tile address
    r3 = c.get("/finance/purchase/page/pay")
    ck("the tile address redirects to the newest month",
       r3.status_code in (301, 302) and "2026-08" in (r3.headers.get("Location") or ""),
       "%s %s" % (r3.status_code, r3.headers.get("Location")))

    # ------------------------------------------- nothing else was disturbed
    r4 = c.get("/finance/purchase/page/month/2026-08")
    ck("the month page still renders exactly as before", r4.status_code == 200, r4.status_code)
    ck("the hub still renders", c.get("/finance/purchase/page/hub").status_code == 200)
    ck("the new way in appears in the nav of the old pages",
       "/page/pay" in r4.get_data(as_text=True))

    # -------------------- the verification when there is no statement to check
    con = sqlite3.connect(dbp)
    con.execute("UPDATE purchase_export SET type='BILLWISE' WHERE md5=?", (SW,))
    con.commit(); con.close()
    holder.pop("con", None)
    rv2 = c.post("/finance/purchase/api/pay-verify", json={"month": "2026-08"})
    jv2 = json.loads(rv2.get_data(as_text=True))
    ck("with NO supplier-wise statement the check FAILS rather than passing quietly",
       jv2.get("verified") is False, jv2)
    ck("and it says exactly what to go and take",
       any("supplier, bill number, bill date, amount" in p for p in jv2.get("problems", [])), jv2)
    h2 = c.get("/finance/purchase/page/pay/2026-08").get_data(as_text=True)
    ck("the page carries that failure instead of the earlier pass",
       "these do not line up" in h2)

    # ------------------------------ a statement that disagrees is named, not hidden
    con = sqlite3.connect(dbp)
    con.execute("UPDATE purchase_export SET type='SUPPLIERWISE', grand_amount_p=9999999 "
                "WHERE md5=?", (SW,))
    con.commit(); con.close()
    holder.pop("con", None)
    jv3 = json.loads(c.post("/finance/purchase/api/pay-verify",
                            json={"month": "2026-08"}).get_data(as_text=True))
    ck("a statement whose printed grand total differs is caught",
       jv3.get("verified") is False and
       any("printed grand total" in p or "prints its own grand total" in p
           for p in jv3.get("problems", [])), jv3)

    print("\n%d ok, %d failed" % (OK, BAD))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
