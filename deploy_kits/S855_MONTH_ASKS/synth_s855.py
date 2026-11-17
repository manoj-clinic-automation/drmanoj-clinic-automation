"""synth_s855.py <finance dir under test> <finance.db COPY> [--real] -- kit S855_MONTH_ASKS proof. Works on COPIES only.
 A made-up ended month (2025-02) laid into a copy of finance.db: a supplier-wise statement older than a correction in Marg (asked again),
 item lines not received (asked), a Wrong mark settled as a purchase return (resolved by itself), a Wrong mark the newer report already carries
 (inside the export ask), a Wrong mark nothing will clear (his Correct tap), the OFF switch, the seams, and the real pages and door in a Flask app.
 --real: every open month of the copy is read, its payment sheet and purchase check drawn (200), the Needs-you and Amir's lines read -- no
 frozen expectations. Last line: 'SYNTH S855: n PASS, m FAIL'."""
import json, os, shutil, sqlite3, sys, tempfile
FIN, DBC = sys.argv[1], sys.argv[2]
REAL = "--real" in sys.argv
tmp = tempfile.mkdtemp(prefix="s855synth_")
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
    """Three made-up bills of 2025-02 under two live exports: bill-wise (newer) and supplier-wise (older). Returns {name: id}."""
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                "('zzs855bw','BILLWISE','x','2025-02-01','2025-02-28','20250310-110000','2025-03-10T11:05:00',3,0)")
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                "('zzs855sw','SUPPLIERWISE','x','2025-02-01','2025-02-28','20250305-110000','2025-03-05T11:05:00',3,1100000)")
    ids = {}
    for name, sup, no, d, bw, sw, verdict, wrong in (("x", "ZZKEDAR TEST", "A9001", "2025-02-15", 536000, 547000, "WRONG", 536000),
                                                     ("r", "ZZJANTA TEST", "9002", "2025-02-02", 320500, 320500, "WRONG", 445000),
                                                     ("y", "ZZOTHER TEST", "9003", "2025-02-20", 100000, 100000, "WRONG", 120000)):
        cur = con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, sw_md5, bw_amount_p, sw_amount_p, "
                          "source_md5, verdict, verdict_by, verdict_at, wrong_amount_p, reason) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (sup, sup, no, d, M, bw, "zzs855bw", "zzs855sw", bw, sw, "zzs855bw", verdict, "darpan", "2025-03-01T10:00:00", wrong, "made up"))
        ids[name] = cur.lastrowid
    con.execute("INSERT INTO s740_answer (sup, bill_no, bill_date, answer, paper_p, marg_p, ret_p, by, at) VALUES (?,?,?,?,?,?,?,?,?)",
                ("ZZJANTA TEST", "9002", "2025-02-02", "yes", 445000, 320500, 124500, "manoj", "2025-03-02T09:00:00"))
    con.execute("INSERT INTO s740_track (rkey, kind, month, first_seen, last_seen, resolved_at, road, ref) VALUES (?,?,?,?,?,?,?,?)",
                ("bill:ZZJANTA TEST|9002|2025-02-02", "on_bill", M, "2025-03-02T09:00:00", "2025-03-09T09:00:00", "2025-03-09T09:00:00", "revised", "B-9999"))
    con.commit()
    return ids


try:
    import purchase_app as pa                                 # noqa: E402
    import month_asks as ma                                   # noqa: E402
    have = True
except Exception as e:                                        # noqa: BLE001
    print("import:", e)
    have = False
ok(have, "T0 the finance code under test holds month_asks.py and imports")
if have:
    pa._assets_db = "/nonexistent"
if have and REAL:
    con = fresh()
    try:
        ms = ma.months(con)
        got = {m: ma.month_asks(con, m) for m in ms}
        ok(bool(ms), "R1 the live copy: %d open month(s) read: %s" % (len(ms), "; ".join("%s %d export ask(s), %d Wrong" % (m, len(a["exports"]), len(a["wrong"])) for m, a in got.items())))
    except Exception as e:                                    # noqa: BLE001
        ok(False, "R1 the live copy's months: %r" % (e,))
    try:
        from flask import Flask
        app = Flask("s855real")
        pa.init(app, lambda: con, lambda *roles: (dict(user="manoj", roles=["checker"], role="checker"), None), assets_db="/nonexistent")
        cl = app.test_client()
        codes = []
        for m in ma.months(con):
            rp, rc = cl.get("/finance/purchase/page/pay/%s" % m), cl.get("/finance/purchase/page/check?month=%s" % m)
            Am = ma.month_asks(con, m)
            want = bool(Am["exports"] or Am["disagree"] or [w for w in Am["wrong"]]) and pa._s454_sr().month_class(con, m) == "counted"
            bp, bc = rp.get_data(as_text=True), rc.get_data(as_text=True)
            codes.append((m, rp.status_code, rc.status_code, want, ('id="s855_pay"' in bp) == want and ('id="s855_check"' in bc) == want))
        ok(codes and all(a == 200 and b == 200 and drawn for _m, a, b, _w, drawn in codes),
           "R2 every open month's payment sheet and purchase check draw on the live copy, the card exactly where asks stand (%r)" % (codes,))
    except Exception as e:                                    # noqa: BLE001
        ok(False, "R2 the pages on the live copy: %r" % (e,))
    try:
        nl, al = ma.needs_lines(con), ma.amir_lines(con)
        ok(isinstance(nl, list) and isinstance(al, list), "R3 the Needs-you (%d) and Amir's lines (%d) read on the live copy" % (len(nl), len(al)))
    except Exception as e:                                    # noqa: BLE001
        ok(False, "R3 the Needs-you and Amir's lines: %r" % (e,))
    con.close()
if have:
    con = fresh()
    ids = lay(con)
    A = ma.month_asks(con, M)
    keys = [a["key"] for a in A["exports"]]
    sw = next((a for a in A["exports"] if a["key"] == "SUPPLIERWISE"), None)
    ok("SUPPLIERWISE" in keys and "ITEMS" in keys and sw and [b["bill_no"] for b in sw["bills"]] == ["A9001"] and "corrected" in sw["why"],
       "T1 the older supplier-wise is asked again (A9001), and the item lines not received are asked (%r)" % keys)
    hw = {w["bill"]["bill_no"]: w["how"] for w in A["wrong"]}
    ok(hw.get("A9001") == "export" and hw.get("9003") == "yours", "T2 Wrong marks: A9001 clears with the export, 9003 is his (%r)" % hw)
    st = ma.settle(con, M)
    v = con.execute("SELECT verdict, reason FROM purchase_bill WHERE id=?", (ids["r"],)).fetchone()
    ok(len(st) == 1 and v[0] == "CORRECT" and "B-9999" in v[1] and con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='verdict_resolved' AND ref=?",
                                                                                 (str(ids["r"]),)).fetchone()[0] == 1,
       "T3 the Wrong mark settled as a purchase return is resolved by itself, recorded (revised bill B-9999)")
    h = ma.card_html(con, M, "/finance/purchase", True)
    h2 = ma.card_html(con, M, "/finance/purchase", False)
    ok("SUPPLIER WISE PURCHASE STATEMENT, FROM 01-02-2025 TO 28-02-2025" in h and h.count('onclick="s855c(this)"') == 1 and 'data-b="%d"' % ids["y"] in h
       and "onclick=\"s855c(this)\"" not in h2 and "Zzjanta" not in h, "T4 the card: the export ask, one Correct button (9003) for the doctor only, the settled bill gone")
    n, lines = ma.row8_lines(con, M)
    ok(n == 3 and len(lines) == 3, "T5 row 8: 3 open (two exports + one Wrong mark of his) (%d)" % n)
    hi = ma.export_hi(sw)
    ok(hi == "SUPPLIER WISE PURCHASE STATEMENT, FROM 01-02-2025 TO 28-02-2025", "T6 Amir's words name the report and its dates exactly")
    r1 = ma.correct(con, "manoj", ids["y"])
    r2 = ma.correct(con, "manoj", ids["y"])
    ok(r1[0] and not r2[0] and con.execute("SELECT verdict FROM purchase_bill WHERE id=?", (ids["y"],)).fetchone()[0] == "CORRECT",
       "T7 his Correct tap: saved once, a second tap refused")
    con.execute("UPDATE purchase_export SET superseded_by='zzs855bw' WHERE md5='zzs855sw'")
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                "('zzs855sw2','SUPPLIERWISE','x','2025-02-01','2025-02-28','20250312-110000','2025-03-12T11:05:00',3,1089000)")
    con.execute("UPDATE purchase_bill SET sw_md5='zzs855sw2', sw_amount_p=bw_amount_p WHERE month=?", (M,))
    con.commit()
    A2 = ma.month_asks(con, M)
    ok([a["key"] for a in A2["exports"]] == ["ITEMS"], "T8 the fresh supplier-wise arrives: its ask leaves by itself (only the item lines remain)")
    con.execute("UPDATE purchase_export SET export_stamp='20250312-090000' WHERE md5='zzs855bw'")
    con.execute("UPDATE purchase_bill SET bw_amount_p=bw_amount_p+5000 WHERE id=?", (ids["x"],))
    con.commit()
    A3 = ma.month_asks(con, M)
    ok([a["key"] for a in A3["exports"]] == ["ITEMS"] and [b["bill_no"] for b in A3["disagree"]] == ["A9001"] and "Marg's two reports disagree" in ma.card_html(con, M, "/x"),
       "T12 the supplier-wise the newer of the two and still differing: no export asked (it would never end) -- his line 'Marg's two reports disagree'")
    off = os.path.join(code, "_off")
    os.makedirs(off, exist_ok=True)
    open(os.path.join(off, "S855_OFF"), "w").close()
    ok(ma.card_html(con, M, "/x") == "" and ma.month_asks(con, M)["n"] == 0 and ma.needs_lines(con) == [] and ma.amir_lines(con) == [] and ma.settle(con) == [],
       "T9 OFF: no card, no asks, nothing resolved")
    os.remove(os.path.join(off, "S855_OFF"))
    con.close()
    src = {n: open(os.path.join(code, n), encoding="utf-8").read() for n in ("purchase_app.py", "scan_register.py", "sanjeevni_approvals.py", "amir_day.py")}
    ok("_ma855.card_html(con, month, request.script_root + _url_prefix, doctor" in src["purchase_app.py"] and '@bp.route("/api/s855/correct"' in src["purchase_app.py"]
       and "_ma855.row8_lines(con, month)" in src["scan_register.py"] and "_check_body_before_s855 = check_body" in src["scan_register.py"]
       and "_needs_you_before_s855 = _needs_you_before_s761" in src["sanjeevni_approvals.py"] and "month_asks.amir_lines(cx)" in src["amir_day.py"]
       and "_card_rows_before_s855 = _card_rows" in src["amir_day.py"], "T10 the seams: the payment sheet, its door, row 8, the check's card, the Needs-you, Amir's card")
    try:                                                      # T11: the real pages and the real door, in a Flask app on the copy
        from flask import Flask
        con = fresh()
        ids = lay(con)
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('purchase.register_from', '2025-02-01')")   # the made-up month counted
        con.commit()
        who = {"u": dict(user="manoj", roles=["checker"], role="checker")}
        app = Flask("s855synth")
        pa.init(app, lambda: con, lambda *roles: (who["u"], None), assets_db="/nonexistent")
        cl = app.test_client()
        b1 = cl.get("/finance/purchase/page/pay/" + M).get_data(as_text=True)
        b2 = cl.get("/finance/purchase/page/check?month=" + M)
        who["u"] = dict(user="amir", roles=["maker"], role="maker")
        r403 = cl.post("/finance/purchase/api/s855/correct", json=dict(bill=ids["y"]))
        who["u"] = dict(user="manoj", roles=["checker"], role="checker")
        r200 = cl.post("/finance/purchase/api/s855/correct", json=dict(bill=ids["y"]))
        b2t = b2.get_data(as_text=True)
        ok('id="s855_pay"' in b1 and "SUPPLIER WISE PURCHASE STATEMENT" in b1 and b2.status_code == 200 and 'id="s855_check"' in b2t and "Marg report to export" in b2t
           and r403.status_code == 403 and r200.status_code == 200,
           "T11 the payment sheet and the purchase check (card + row 8) carry the asks (%d); a non-doctor's tap refused (%d); the doctor's saved (%d)"
           % (b2.status_code, r403.status_code, r200.status_code))
        con.close()
    except Exception as e:                                    # noqa: BLE001
        ok(False, "T11 the pages and the door in a Flask app: %r" % (e,))
print("SYNTH S855: %d PASS, %d FAIL" % (P, F))
