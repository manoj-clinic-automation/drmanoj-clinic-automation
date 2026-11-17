"""synth_s850.py <finance dir under test> <finance.db COPY> [--real <assets.db COPY>] -- kit S850_MARG_IS_RIGHT proof. Works on COPIES only.
 Made-up bills of a made-up month (2099-01) and a made-up dealer, laid into a copy of finance.db, with a made-up assets.db: the line verdicts
 (totals agree -> Marg accepted by itself; totals differ -> 'Marg is right'), the corrections kept, the tap and its undo, a moved link, the
 Item ledger's verdict, the OFF switch, F-1440 (a bill named by its number and its total). --real: the live copies -- October's lines judged
 and its corrections kept from the scans' own readings; B-0122, while still asked, names Marg bill 3499. Last line: 'SYNTH S850: n PASS, m FAIL'."""
import json, os, shutil, sqlite3, sys, tempfile
FIN, DBC = sys.argv[1], sys.argv[2]
REAL = sys.argv[sys.argv.index("--real") + 1] if "--real" in sys.argv else None
tmp = tempfile.mkdtemp(prefix="s850synth_")
code = os.path.join(tmp, "finance")
shutil.copytree(FIN, code, ignore=shutil.ignore_patterns("*.db", "__pycache__", "_off"))
_me = os.path.dirname(os.path.abspath(__file__))           # F-1415: never the kit's own copy beside this script
sys.path[:] = [x for x in sys.path if os.path.abspath(x or os.getcwd()) != _me]
sys.path.insert(0, code)
P = F = 0
M = "2099-01"


def ok(c, what):
    global P, F
    if c:
        P += 1
        print("PASS", what)
    else:
        F += 1
        print("FAIL", what)


def made_up_assets(path):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE bills(id INTEGER PRIMARY KEY, kind TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, stamp_no TEXT, "
              "status TEXT, lane TEXT, bill_month TEXT, created_at TEXT)")
    c.execute("CREATE TABLE bill_items(id INTEGER PRIMARY KEY, bill_id INTEGER, item_name TEXT, pack_size TEXT, quantity REAL, rate REAL, amount REAL, "
              "make TEXT, model TEXT, serial_no TEXT, batch TEXT, expiry TEXT, hsn TEXT, asset_id INTEGER)")
    for i, no, tot in ((990001, "7001", 1597.0), (990002, "7002", 3570.0)):
        c.execute("INSERT INTO bills(id,kind,vendor,bill_no,bill_date,total_amount,stamp_no,status,lane,bill_month,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (i, "Pharmacy", "ZZTEST DEALER", no, "2099-01-10", tot, "B-%04d" % (i % 10000), "captured", "pharmacy", M, "2099-01-10 18:00:00"))
    for b, n, q, r, bt, e in ((990001, "XYCAL-K2 TAB", 10, 159.7, "XK2-114", "5/28"), (990001, "KT-ROS DT", 5, 10.0, "KR1", "6/28"),
                              (990002, "TAB ORICOX-P", 5010, 213.36, "OP1", "1/28"), (990002, "Q2-7 CAP", 10, 30.0, "QQ9", "2/28")):
        c.execute("INSERT INTO bill_items(bill_id,item_name,quantity,rate,batch,expiry) VALUES (?,?,?,?,?,?)", (b, n, q, r, bt, e))
    c.commit()
    c.close()


def lay(con):
    """Two made-up Marg bills (one per scan) with their lines and their check rows; returns the bill ids."""
    md5 = con.execute("SELECT md5 FROM purchase_export WHERE superseded_by IS NULL LIMIT 1").fetchone()[0]
    ids = []
    for no, amt in (("7001", 159700), ("7002", 361200)):
        cur = con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, source_md5) VALUES (?,?,?,?,?,?,?,?)",
                          ("ZZTEST DEALER", "ZZTEST DEALER", no, "2099-01-10", M, amt, md5, md5))
        ids.append(cur.lastrowid)
    for no, it, q, f, rp, bt, e in (("7001", "XYCAL K2", 10, 0, 15970, "XK2-118", "05/28"), ("7001", "KT ROS DT", 5, 0, 1000, "KR1", "06/28"),
                                    ("7002", "ORICOX P", 50, 10, 21336, "OP1", "01/28"), ("7002", "Q2-7 CAP", 10, 0, 3000, "QQ7", "02/28")):
        con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, qty, free, rate_p, batch, expiry, direction, source_md5) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("ZZTEST DEALER", no, "2099-01-10", M, it, q, f, rp, bt, e, "PURCHASE", md5))
    det = {990001: [dict(scan_item="XYCAL-K2 TAB", marg_item="XYCAL K2", score=1.0, bad=["batch"]),
                    dict(scan_item="KT-ROS DT", marg_item="KT ROS DT", score=1.0, bad=[])],
           990002: [dict(scan_item="TAB ORICOX-P", marg_item="ORICOX P", score=1.0, bad=["qty"]),
                    dict(scan_item="Q2-7 CAP", marg_item="Q2-7 CAP", score=1.0, bad=["batch"])]}
    for sid, bid, tok, st, mt in ((990001, ids[0], 1, 159700, 159700), (990002, ids[1], 0, 357000, 361200)):
        con.execute("INSERT OR REPLACE INTO purchase_sarvam_check (asset_bill_id, bill_id, month, checked_at, supplier_ok, billno_ok, date_ok, total_ok, items_read, "
                    "items_wrong, all_ok, detail) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (sid, bid, M, "2099-01-11T10:00:00", 1, 1, 1, tok, 2, 1, 0,
                     json.dumps(dict(scan=dict(vendor="ZZTEST DEALER", bill_no=str(7000 + sid % 10), date="2099-01-10", total_p=st),
                                     marg=dict(supplier="ZZTEST DEALER", bill_no=str(7000 + sid % 10), date="2099-01-10", total_p=mt), items=det[sid]))))
        con.execute("INSERT OR REPLACE INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                    (bid, sid, "CONFIRMED", "synth", "2099-01-11T10:00:00"))
    con.commit()
    return ids, md5


def fresh():
    db = os.path.join(tmp, "f%d.db" % (P + F))
    shutil.copy(DBC, db)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return con


try:
    import purchase_app as pa                                 # noqa: E402
    import marg_right as mr                                   # noqa: E402
    import scan_ask as sa                                     # noqa: E402
    have = True
except Exception as e:                                        # noqa: BLE001
    print("import:", e)
    have = False
ok(have, "T0 the finance code under test holds marg_right.py and imports")
if have and REAL:
    pa._assets_db = REAL
    con = fresh()
    h = mr.cards_html(con, "2026-10", "/finance/purchase")
    T = mr.month_table(con, "2026-10")
    nk = sum(n for k, n, a, t in T["kinds"])
    filled = con.execute("SELECT COUNT(*), SUM(CASE WHEN read_value<>'' THEN 1 ELSE 0 END) FROM s850_correction WHERE month='2026-10'").fetchone()
    ok(T["bills"] >= 60 and T["differing"] >= 40 and T["agreeing"] >= 1 and nk >= 50 and (filled[1] or 0) * 2 >= filled[0] and "s850kept" in h,
       "R1 the live copies: October %d bills, %d differing, %d accepted by totals; %d corrections kept, %d with the scan's own reading"
       % (T["bills"], T["differing"], T["agreeing"], nk, filled[1] or 0))
    a1 = mr.sync(con, "2026-10", None, pa._assets_con())
    ok(a1 == (0, 0), "R2 a second open writes nothing (%r)" % (a1,))
    v = sa.view(con)
    c = next((x for x in v["asked"] + v["parked"] if x["stamp"] == "B-0122"), None)
    best = c and next((y for y in c["cands"] if y["best"]), None)
    ok(c is None or (best is not None and best["bill"]["bill_no"] == "3499"),
       "R3 B-0122 (Shivaaz): %s" % ("already answered" if c is None else "best match %r" % (best and best["bill"]["bill_no"])))
    con.close()
if have:
    A = os.path.join(tmp, "assets.db")
    made_up_assets(A)
    pa._assets_db = A
    con = fresh()
    ids, md5 = lay(con)
    BL = mr.bills(con, M)
    st = {(B["asset_bill_id"], ln["scan_item"]): ln["state"] for B in BL for ln in B["lines"]}
    ok(len(BL) == 2 and st[(990001, "XYCAL-K2 TAB")] == "auto" and st[(990001, "KT-ROS DT")] == "agrees", "T1 totals agree: the batch line Marg-accepted by itself, the other agrees")
    ok(st[(990002, "TAB ORICOX-P")] == "ask" and st[(990002, "Q2-7 CAP")] == "ask", "T2 totals differ: both differing lines wait for a tap")
    h = mr.cards_html(con, M, "/finance/purchase")
    ok("Marg accepted — totals agree" in h and h.count('data-do="right"') == 2 and "totals differ by" in h and "XK2-114" in h and "XK2-118" in h
       and "Accepted by themselves — totals agree: 1 bill" in h, "T3 the cards: the auto verdict, two 'Marg is right' buttons, the totals' difference, read vs Marg values")
    r = con.execute("SELECT how, read_value, marg_value FROM s850_correction WHERE asset_bill_id=990001").fetchall()
    ok([tuple(x) for x in r] == [("totals", "XK2-114", "XK2-118")], "T4 the auto line kept as a correction: batch, read XK2-114, Marg XK2-118, by totals")
    k = next(ln["key"] for B in BL for ln in B["lines"] if ln["scan_item"] == "TAB ORICOX-P")
    res = mr.tap(con, "manoj", 990002, k)
    r = con.execute("SELECT kind, how, read_value, marg_value, by_user FROM s850_correction WHERE asset_bill_id=990002").fetchall()
    ok(res[0] and [tuple(x) for x in r] == [("qty", "tap", "5010", "50 + 10 free", "manoj")], "T5 'Marg is right' on ORICOX: kept -- qty read 5010, Marg 50 + 10 free, by manoj")
    ok(mr.tap(con, "manoj", 990002, k)[0] is False, "T6 a second tap on the same line is refused")
    ka = next(ln["key"] for B in BL for ln in B["lines"] if ln["scan_item"] == "XYCAL-K2 TAB")
    kg = next(ln["key"] for B in BL for ln in B["lines"] if ln["scan_item"] == "KT-ROS DT")
    ok(mr.tap(con, "manoj", 990001, ka)[0] is False and mr.tap(con, "manoj", 990001, kg)[0] is False and mr.tap(con, "manoj", 990001, "NOPE#1")[0] is False,
       "T7 no tap on a line accepted by totals, on one that agrees, or on a line not there")
    T = mr.month_table(con, M)
    ok(T["kinds"] == [("qty", 1, 0, 1), ("batch", 1, 1, 0)] and (T["bills"], T["differing"], T["agreeing"], T["for_tap"], T["tapped"]) == (2, 2, 1, 1, 1),
       "T8 the month's corrections: qty 1 by a tap, batch 1 by totals; 2 bills, 2 differing, 1 by totals, 1 for a tap, 1 answered (%r)" % (T,))
    h = mr.cards_html(con, M, "/finance/purchase")
    ok("Marg is right · manoj" in h and h.count('data-do="undo"') == 1 and h.count('data-do="right"') == 1 and mr.sync(con, M, None, pa._assets_con()) == (0, 0),
       "T9 the tapped line shows its answer with Undo; the page again writes nothing")
    ok(mr.tap(con, "manoj", 990002, k, "undo")[0] and con.execute("SELECT COUNT(*) FROM s850_correction WHERE how='tap'").fetchone()[0] == 0
       and next(ln["state"] for B in mr.bills(con, M) for ln in B["lines"] if ln["key"] == k) == "ask", "T10 Undo: the line asks again, its correction gone")
    con.execute("DELETE FROM purchase_sarvam_check WHERE asset_bill_id=990001")
    con.commit()
    ok(mr.sync(con, M, None, pa._assets_con()) == (0, 1) and con.execute("SELECT COUNT(*) FROM s850_correction WHERE asset_bill_id=990001").fetchone()[0] == 0,
       "T11 a check row gone (its link moved): its kept correction leaves")
    con.execute("INSERT OR REPLACE INTO purchase_sarvam_check (asset_bill_id, bill_id, month, checked_at, supplier_ok, billno_ok, date_ok, total_ok, items_read, "
                "items_wrong, all_ok, detail) VALUES (990001,?,?,?,1,1,1,1,2,1,0,?)",
                (ids[0], M, "2099-01-11T10:00:00", json.dumps(dict(scan=dict(vendor="ZZTEST DEALER", bill_no="7001", date="2099-01-10", total_p=159700),
                                                                  marg=dict(supplier="ZZTEST DEALER", bill_no="7001", date="2099-01-10", total_p=159700),
                                                                  items=[dict(scan_item="XYCAL-K2 TAB", marg_item="XYCAL K2", score=1.0, bad=["batch"]),
                                                                         dict(scan_item="KT-ROS DT", marg_item="KT ROS DT", score=1.0, bad=[])]))))
    con.commit()
    sup = "ZZTESTDE"
    v = mr.ledger_verdict(con, ["XYCAL K2"], sup, "7001", "2099-01-10", pa._assets_con())
    v2 = mr.ledger_verdict(con, ["ORICOX P"], sup, "7002", "2099-01-10", pa._assets_con())
    v3 = mr.ledger_verdict(con, ["KT ROS DT"], sup, "7001", "2099-01-10")
    ok(v and v[0] == "auto" and v[1] == "Marg accepted — totals agree" and "scan read batch XK2-114" in v[2] and v2 and v2[0] == "ask" and v3 and v3[0] == "agrees"
       and mr.ledger_verdict(con, ["NOT AN ITEM"], sup, "7001", "2099-01-10") is None, "T12 the Item ledger: accepted (scan read batch XK2-114), for a tap, agrees, none")
    L = dict(days=[dict(day="2099-01-10", entries=[dict(kind="PURCHASE", ref="7001", supkey=sup, u=10.0), dict(kind="SALE", ref="1", u=-1.0)])])
    n = mr.annotate_ledger(con, dict(names=["XYCAL K2"], name="XYCAL K2"), L)
    ok(n == 1 and "Marg accepted — totals agree" in L["days"][0]["entries"][0]["s850_html"] and "s850_html" not in L["days"][0]["entries"][1],
       "T13 annotate_ledger: the purchase row gets its tag, the sale row nothing")
    off = os.path.join(code, "_off")
    os.makedirs(off, exist_ok=True)
    open(os.path.join(off, "S850_OFF"), "w").close()
    ok(mr.cards_html(con, M, "/x") == "" and mr.ledger_verdict(con, ["XYCAL K2"], sup, "7001", "2099-01-10") is None and mr.tap(con, "manoj", 990002, k)[0] is False,
       "T14 OFF: no cards, no ledger tag, no tap")
    os.remove(os.path.join(off, "S850_OFF"))
    ok(con.execute("SELECT COUNT(*) FROM purchase_sarvam_check WHERE asset_bill_id IN (990001,990002) AND all_ok=0").fetchone()[0] == 2,
       "T15 purchase_sarvam_check stays strict: nothing here writes it")
    # the cold review's three points
    c2 = fresh()
    ids2, _m = lay(c2)
    ko = next(ln["key"] for B in mr.bills(c2, M) for ln in B["lines"] if ln["scan_item"] == "TAB ORICOX-P")
    mr.tap(c2, "manoj", 990002, ko)
    c2.execute("UPDATE purchase_sarvam_check SET bill_id=? WHERE asset_bill_id=990002", (ids2[0],))
    c2.commit()
    ok(next(ln["state"] for B in mr.bills(c2, M) for ln in B["lines"] if ln["key"] == ko) == "ask" and mr.sync(c2, M, None, pa._assets_con())[1] >= 1
       and mr.tap(c2, "manoj", 990002, ko)[0] and c2.execute("SELECT bill_id FROM s850_tap WHERE asset_bill_id=990002").fetchone()[0] == ids2[0],
       "T19 a tap judged one Marg bill: the scan relinked, the line asks again, its old correction leaves, a new tap replaces the stale one")
    mr.tap(c2, "manoj", 990002, ko, "undo")
    c2.execute("UPDATE purchase_sarvam_check SET bill_id=? WHERE asset_bill_id=990002", (ids2[1],))
    a2 = sqlite3.connect(A)
    a2.execute("INSERT INTO bill_items(bill_id,item_name,quantity,rate,batch,expiry) VALUES (990001,'XYCAL-K2 TAB',4,159.7,'XK2-200','5/28')")
    a2.commit()
    det = json.loads(c2.execute("SELECT detail FROM purchase_sarvam_check WHERE asset_bill_id=990001").fetchone()[0])
    det["items"].append(dict(scan_item="XYCAL-K2 TAB", marg_item="XYCAL K2", score=1.0, bad=["batch"]))
    c2.execute("UPDATE purchase_sarvam_check SET detail=? WHERE asset_bill_id=990001", (json.dumps(det),))
    c2.commit()
    B1 = next(B for B in mr.bills(c2, M) if B["asset_bill_id"] == 990001)
    V = mr.values(c2, pa._assets_con(), B1)
    ok(V["XYCALK2TAB#2"][0]["batch"] == "XK2-200" and V["XYCALK2TAB#2"][1] is not None and V["XYCALK2TAB#2"][1]["batch"] == "XK2-118",
       "T20 one item in two batches on the paper: the second line is paired with Marg's line as the check paired it (XK2-200 / XK2-118)")
    mr.sync(c2, M, None, pa._assets_con())
    a2.execute("UPDATE bill_items SET batch='XK2-999' WHERE bill_id=990001 AND item_name='XYCAL-K2 TAB'")
    a2.commit()
    a2.close()
    mr.sync(c2, M, None, pa._assets_con())
    ok(c2.execute("SELECT read_value FROM s850_correction WHERE asset_bill_id=990001 AND line_key='XYCALK2TAB#1'").fetchone()[0] == "XK2-114",
       "T21 a kept misread is never overwritten when the scan is read again (XK2-114 stays)")
    a3 = sqlite3.connect(A)
    a3.execute("UPDATE bill_items SET batch='XK2-118' WHERE bill_id=990001 AND item_name='XYCAL-K2 TAB'")
    a3.commit()
    a3.close()
    mr.sync(c2, M, None, pa._assets_con())
    r = c2.execute("SELECT read_value FROM s850_correction WHERE asset_bill_id=990001 AND line_key='XYCALK2TAB#1'").fetchone()
    ok(r is not None and r[0] == "XK2-114", "T21b the scan read again now equal to Marg's: the kept misread stays")
    c2.row_factory = None
    ok(mr.ledger_verdict(c2, ["XYCAL K2"], "ZZTESTDE", "7001", "2099-01-10") is not None and mr.bills(c2, M), "T22 the reads work whatever the connection's row factory")
    c2.close()
    # F-1440: the number read and the total name the bill, whatever the read lines say
    for no, amt, it, rp, bt in (("3600", 400000, "ZZ ITEM A", 10000, "BT1"), ("3499", 474700, "QQQ OTHER THING", 20000, "XX9")):
        con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, source_md5) VALUES (?,?,?,?,?,?,?,?)",
                    ("ZZFOUR DEALER", "ZZFOUR DEALER", no, "2099-01-03", M, amt, md5, md5))
        con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, qty, free, rate_p, batch, expiry, direction, source_md5) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("ZZFOUR DEALER", no, "2099-01-03", M, it, 10, 0, rp, bt, "01/28", "PURCHASE", md5))
    con.commit()
    import datetime as dt
    cands = sa._candidates(con, pa.supplier_key("ZZFOUR DEALER"), dt.date(2099, 1, 3), 474700,
                           [dict(name="ZZ ITEM A", qty=10, rate=100.0, batch="BT1", expiry="1/28")], "3499", {})
    best = next((c for c in cands if c["best"]), None)
    ok(best is not None and best["bill"]["bill_no"] == "3499" and best.get("why") == "numtot",
       "T16 F-1440: the paper reads 3499 and its total is Marg's: Marg bill 3499 is the best, though bill 3600's line agrees (%r)"
       % ([(c["bill"]["bill_no"], c["agree"], c["tail"], c["total"], c["best"]) for c in cands],))
    con.close()
    src = {n: open(os.path.join(code, n), encoding="utf-8").read() for n in ("purchase_app.py", "item_ledger.py")}
    ok("_s850.cards_html(con, month, request.script_root + _url_prefix)" in src["purchase_app.py"] and '@bp.route("/api/s850/line"' in src["purchase_app.py"]
       and "_s850.annotate_ledger(con, it, L)" in src["item_ledger.py"] and 'btn + (e.get("s850_html") or "")' in src["item_ledger.py"],
       "T17 the seams: the page's cards, the tap's route, the ledger's verdict")
    try:                                                      # T18: the real page and the real route, in a Flask app on the copy
        from flask import Flask
        con = fresh()
        con.row_factory = sqlite3.Row
        lay(con)
        who = {"u": dict(user="manoj", roles=["checker"], role="checker")}
        app = Flask("s850synth")
        pa.init(app, lambda: con, lambda *roles: (who["u"], None), assets_db=A)
        cl = app.test_client()
        r = cl.get("/finance/purchase/page/sarvam?month=" + M)
        body = r.get_data(as_text=True)
        k2 = next(ln["key"] for B in mr.bills(con, M) for ln in B["lines"] if ln["scan_item"] == "Q2-7 CAP")
        who["u"] = dict(user="amir", roles=["maker"], role="maker")
        r403 = cl.post("/finance/purchase/api/s850/line", json=dict(a=990002, k=k2, do="right"))
        who["u"] = dict(user="manoj", roles=["checker"], role="checker")
        r2 = cl.post("/finance/purchase/api/s850/line", json=dict(a=990002, k=k2, do="right"))
        ok(r.status_code == 200 and 'id="s850lines"' in body and 'id="s850kept"' in body and "async function s850(b)" in body and "Scan reading against Marg" in body
           and r403.status_code == 403 and r2.status_code == 200 and (r2.get_json() or {}).get("ok") is True,
           "T18 the page draws its two cards and the script (%d); a non-doctor's tap refused (%d); the doctor's tap saved (%d)" % (r.status_code, r403.status_code, r2.status_code))
        con.close()
    except Exception as e:                                    # noqa: BLE001
        ok(False, "T18 the page and the route in a Flask app: %r" % (e,))
print("SYNTH S850: %d PASS, %d FAIL" % (P, F))
