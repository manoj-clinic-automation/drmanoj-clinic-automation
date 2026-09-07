"""LIVE-SHAPE WALK -- S226 READINESS.

Not a unit test. It builds the real schemas, fills them with the shape of
05/06-Sep-2026 as the server actually holds it, mounts the blueprint the way
finance_app mounts it, and then LOOKS AT THE PAGES a person would open.

The rule this exists for: S208 had two defects behind 65 green checks and
S209 a page that killed a console behind four green gates. A check that
cannot fail on a broken build is not a check.
"""
import io, json, os, sqlite3, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from flask import Flask                                  # noqa: E402
import stock_app                                         # noqa: E402

OK = []
BAD = []


def chk(name, cond, detail=""):
    (OK if cond else BAD).append(name + (("  -- " + str(detail)) if detail and not cond else ""))
    print(("  ok   " if cond else "  FAIL ") + name + (("   " + str(detail)) if detail else ""))



def _sql(name):
    """Find a schema file whether this walk runs from inside the kit folder or
    from a copy with the files beside it. Relative always -- never a hard-coded
    mount (the S212 lesson)."""
    here = os.path.join(HERE, name)
    if os.path.exists(here):
        return here
    up = os.path.dirname(HERE)
    for rel in ("S208_STOCK_LEDGER/stock_schema.sql",
                "S224_MARG_PURCHASES/purchase_schema.sql",
                "S204_VPS_LIVE/root__finance__finance_returns.sql"):
        if os.path.basename(rel) == name or rel.endswith("/" + name):
            cand = os.path.join(up, *rel.split("/"))
            if os.path.exists(cand):
                return cand
    if name == "finance_returns.sql":
        cand = os.path.join(up, "S204_VPS_LIVE", "root__finance__finance_returns.sql")
        if os.path.exists(cand):
            return cand
    raise SystemExit("walk cannot find %s -- run it from inside the kit folder" % name)


DB = os.path.join(HERE, "_walk226.db")


def build():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB, check_same_thread=False)
    for f in ("stock_schema.sql", "purchase_schema.sql"):
        con.executescript(io.open(_sql(f), encoding="utf-8").read())
    # the tables finance_returns.sql leans on, in their live shape
    con.executescript("""
      CREATE TABLE IF NOT EXISTS business_unit(code TEXT PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS ingest_batch(id INTEGER PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS day_entry(id INTEGER PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS setting(key TEXT PRIMARY KEY, value TEXT, note TEXT);
      INSERT OR IGNORE INTO business_unit(code) VALUES ('medical');
      INSERT OR IGNORE INTO day_entry(id) VALUES (1);
    """)
    con.executescript(io.open(_sql("finance_returns.sql"), encoding="utf-8").read())
    stock_app._feed_ensure(con)
    stock_app._f_ensure(con)
    con.commit()
    return con


def fill(con):
    # ---- sales: 04 and 05-Sep, bills A003390..A003412, the 05-Sep last is A003412
    seq = 0
    for day, first, last in (("2026-09-04", 3390, 3395), ("2026-09-05", 3397, 3412)):
        for n in range(first, last + 1):
            seq += 1
            con.execute(
                "INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no,"
                " is_return, seq, item_name, item_key, qty_raw) VALUES (1,'medical',?,?,0,?,?,?,?)",
                (day, "A%06d" % n, seq, "BIO D3 MAX", "biod3max", "0:7"))
    # ---- a credit note, 04-Sep
    con.execute(
        "INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no,"
        " is_return, seq, item_name, item_key) VALUES (1,'medical','2026-09-04','CN00161',1,1,'X','x')")
    # ---- purchases: last dated day 03-Sep, four bills, as Bill-wise shows them
    for sup, bno, amt in (("ANMOL AGENCIES", "AN/1188", 1240500),
                          ("BHARAT MEDICAL", "BM-7741", 386300),
                          ("PRIME ORTHO", "PO/2210", 5411900),
                          ("SHREE DISTRIBUTORS", "SD/990", 92750)):
        con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no,"
                    " bill_date, month, amount_p) VALUES (?,?,?,?,?,?)",
                    (sup.lower(), sup, bno, "2026-09-03", "2026-09", amt))
    con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date,"
                " month, amount_p) VALUES ('old co','OLD CO','OC/1','2026-08-31','2026-08',100)")
    con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,"
                "export_stamp,received_at,n_rows,grand_amount_p) VALUES "
                "('05dc3bbb','SUPPLIERWISE','x.XLS','2026-08-01','2026-08-31',"
                "'20260904-093037','2026-09-04T11:31:00',147,35487900)")
    # ---- the two stock feeds for 05-Sep
    for src, qty, at in (("push_snapshot.py as on 05-09-2026", 58, "2026-09-06T03:10:22"),
                         ("push_expected.py pur_to=03-09-2026", 65, "2026-09-06T02:50:47")):
        con.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at)"
                    " VALUES (?,?,?,?,?)", ("2026-09-05", src, "BIO D3 MAX", qty, at))
        con.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at)"
                    " VALUES (?,?,?,?,?)", ("2026-09-05", src, "PRIME CAST 5\"", -45, at))
    # ---- a snapshot so /page/count has an item universe (Marg writes dd-mm-yyyy)
    for item, q, pk, ps in (("BIO D3 MAX", 58, "1*15", 15), ("PRIME CAST 5\"", -45, "1*1", 1)):
        con.execute("INSERT INTO stock_snapshot (as_on,item,qty,packing,pack_size,"
                    "source,loaded_at) VALUES (?,?,?,?,?,?,?)",
                    ("05-09-2026", item, q, pk, ps, "push_snapshot.py", "2026-09-06T03:10:22"))
    con.commit()


def app_for(con):
    app = Flask(__name__)
    stock_app.init(app, lambda: con,
                   lambda *roles: ({"user": "walk", "roles": ["medical.checker"],
                                    "role": "checker"}, None),
                   unit="medical")
    return app


def main():
    print("== S226 READINESS -- live-shape walk ==")
    con = build()
    fill(con)
    app = app_for(con)
    c = app.test_client()

    # ---------------------------------------------------------------- 1 the API
    r = c.get("/finance/stock/api/readiness")
    j = r.get_json()
    chk("api/readiness answers 200", r.status_code == 200, r.status_code)
    chk("api/readiness ok", j.get("ok") is True)
    chk("headline is the owner's words", j.get("headline") == "Read first -- know the data.",
        j.get("headline"))

    s = j["sale"]
    chk("sale horizon is 05-09", s["business_date"] == "2026-09-05", s["business_date"])
    chk("LAST BILL NUMBER is A003412, not A003395",
        s["bill_no"] == "A003412", s["bill_no"])
    chk("bill count for that day is 16", s["bills"] == 16, s["bills"])
    chk("sale line reads plainly", "last bill A003412" in s["line"], s["line"])
    chk("sale line prints dd-mm-yyyy", "05-09-2026" in s["line"], s["line"])

    p = j["purchase"]
    chk("purchases dated to 03-09 (NOT the 31-Aug bill)",
        p["bill_date"] == "2026-09-03", p["bill_date"])
    chk("that last day's bills are listed", p["bills_n"] == 4, p["bills_n"])
    chk("the bills carry supplier + bill no + amount",
        all(b.get("supplier") and b.get("bill_no") and b.get("amount_p") for b in p["bills"]))
    chk("the day's total is right", p["amount_p"] == 1240500 + 386300 + 5411900 + 92750,
        p["amount_p"])
    chk("the day's money is printed", "Rs 71,314.50" in p["line"], p["line"])
    chk("Indian grouping, lakhs not thousands",
        stock_app._r_rupees(3548790000) == "Rs 3,54,87,900.00", stock_app._r_rupees(3548790000))
    chk("Indian grouping, crores", stock_app._r_rupees(123456789012) == "Rs 1,23,45,67,890.12",
        stock_app._r_rupees(123456789012))
    chk("small and negative amounts", (stock_app._r_rupees(0), stock_app._r_rupees(-5099))
        == ("Rs 0.00", "-Rs 50.99"), (stock_app._r_rupees(0), stock_app._r_rupees(-5099)))
    chk("the purchase feed stamp is read too", p["known_to_feed"] == "2026-09-03",
        p["known_to_feed"])
    chk("the live purchase export is listed", p["exports"] and p["exports"][0]["type"] == "SUPPLIERWISE")

    st = j["stock"]
    chk("Marg's export: as-on date", st["marg"]["as_on"] == "2026-09-05", st["marg"])
    chk("Marg's export: WHEN IT WAS PROCESSED",
        "06-09-2026 03:10" in st["line"], st["line"])
    chk("our computed figure is named separately",
        "Our computed figure: as on 05-09-2026" in st["line"], st["line"])

    rt = j["returns"]
    chk("the credit-note sentence is the owner's, verbatim in shape",
        rt["sentence"] == "All sale returns up to credit-note CN00161 dated 04-09-2026 "
                          "have been processed.", rt["sentence"])

    chk("four readiness lines, in order", len(j["lines"]) == 4, len(j["lines"]))
    w = " ".join(j["warnings"])
    chk("the horizon gap is WARNED, not left to be noticed",
        "purchases are known only to 03-09-2026" in w.lower(), j["warnings"])

    # ---------------------------------------------------------------- 2 the drift page
    r = c.get("/finance/stock/api/drift")
    jd = r.get_json()
    chk("drift carries readiness in the SAME round trip",
        jd.get("readiness", {}).get("ok") is True)
    chk("drift still does its own job", jd.get("comparable") == 2, jd.get("comparable"))

    r = c.get("/finance/stock/page/drift")
    h = r.get_data(as_text=True)
    chk("drift page serves 200", r.status_code == 200, r.status_code)
    chk("the readiness card is ON the drift page", 'id="rdy-card"' in h)
    chk("it OPENS with it -- before any result",
        h.index('id="rdy-card"') < h.index("Stock drift &mdash;")
        if "Stock drift &mdash;" in h else h.index('id="rdy-card"') < h.index("<h1>Stock drift"))
    chk("the header is wired to render", "rdyRender(document.getElementById" in h)
    chk("the page's own script is untouched", "function purchase(p){" in h)

    # ---------------------------------------------------------------- 3 the count page
    r = c.get("/finance/stock/page/count")
    h = r.get_data(as_text=True)
    chk("count page serves 200", r.status_code == 200, r.status_code)
    chk("the readiness card is ON the count page too", 'id="rdy-card"' in h)
    chk("it opens with it, above the gate",
        h.index('id="rdy-card"') < h.index("<h1>Stock check</h1>"))
    chk("the count page fetches its own readiness", '"/api/readiness"' in h)
    chk("the count page's data injection still happened", "__STOCK_DATA__" not in h)

    # ---------------------------------------------------------------- 4 the logged result
    body = {"marg_as_on": "05-09-2026", "bill_no": "A003412", "bill_date": "05-09-2026",
            "items_total": 2,
            "items": [{"item": "BIO D3 MAX", "marg_qty": 58, "counted_qty": 55,
                       "pack_size": 15, "counted_by": "Amir", "entered_by": "Amir"},
                      {"item": "PRIME CAST 5\"", "marg_qty": -45, "counted_qty": -45,
                       "pack_size": 1, "counted_by": "Amir", "entered_by": "Amir"}]}
    r = c.post("/finance/stock/api/count", json=body)
    jc = r.get_json()
    chk("a count can still be submitted", jc.get("ok") is True, jc)
    cid = jc.get("count_id")
    chk("it was sealed", bool(jc.get("finding_no")), jc.get("finding_no"))
    chk("one difference raised", jc.get("differences") == 1, jc.get("differences"))

    row = con.execute("SELECT captured_at, payload FROM stock_check_readiness "
                      "WHERE count_id=?", (cid,)).fetchone()
    chk("THE RESULT IS LOGGED WITH ITS DATA HORIZON", row is not None)
    pay = json.loads(row[1]) if row else {}
    chk("the log carries the last sale bill and its date",
        pay.get("sale", {}).get("bill_no") == "A003412"
        and pay.get("sale", {}).get("business_date") == "2026-09-05")
    chk("the log carries purchases-to-date with that day's bills",
        pay.get("purchase", {}).get("bill_date") == "2026-09-03"
        and len(pay.get("purchase", {}).get("bills") or []) == 4)
    chk("the log carries the credit-note sentence",
        "CN00161" in pay.get("returns", {}).get("sentence", ""))

    r = c.get("/finance/stock/api/finding/%d" % cid)
    jf = r.get_json()
    chk("the finding document shows the frozen header",
        jf.get("readiness", {}).get("frozen") is True)
    chk("the counted and the expected stock are on the finding",
        any(l["marg_qty"] == 58 and l["counted_qty"] == 55
            for l in (jf.get("lines", []) + jf.get("unvalued", []))))

    # ------------------------------------------- 5 the header must never kill a page
    con.execute("DROP TABLE purchase_bill")
    con.commit()
    r = c.get("/finance/stock/page/drift")
    chk("a missing purchase table does NOT kill the drift page", r.status_code == 200,
        r.status_code)
    j2 = c.get("/finance/stock/api/readiness").get_json()
    chk("...and the header says so instead of guessing",
        "unknown" in j2["purchase"]["line"].lower(), j2["purchase"]["line"])
    chk("...while the other three lines still stand",
        j2["sale"]["ok"] and j2["stock"]["ok"] and j2["returns"]["ok"])

    con2 = build()
    app2 = app_for(con2)
    j3 = app2.test_client().get("/finance/stock/api/readiness").get_json()
    chk("an EMPTY server says 'nothing has reached the server yet', not zero",
        "nothing has reached the server yet" in j3["sale"]["line"]
        and "never received" in j3["stock"]["line"], j3["lines"])
    chk("an empty server raises no warning it cannot support", j3["warnings"] == [],
        j3["warnings"])

    print("\n%d ok, %d FAILED" % (len(OK), len(BAD)))
    for b in BAD:
        print("   FAILED: " + b)
    sys.exit(1 if BAD else 0)


if __name__ == "__main__":
    main()
