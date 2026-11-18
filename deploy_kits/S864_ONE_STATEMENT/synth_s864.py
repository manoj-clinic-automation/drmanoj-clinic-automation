"""synth_s864.py <finance dir under test> <finance.db COPY> [--real] -- kit S864_ONE_STATEMENT proof. Works on COPIES only.
 A made-up ended month (2025-02) laid into a copy of finance.db: an older supplier-wise and a newer bill-wise of the same month (one family: the
 newer is the figure, the older retired by the one-off and by the push), a Wrong mark the newest statement already shows (resolved by itself), a
 Wrong mark settled as a purchase return (resolved), a Wrong mark nothing will clear (his tap), the finished month's pair asked ONLY for a named
 reason (not received; Amir's correction list; his own 'self' answer after the statement) and gone when the pair arrives, the push door across the
 family, two reports in the month-end card, the cross-check on the newest statement, Amir's steps 3 and 4, the OFF switch, the seams.
 --real: every open month of the copy is read, its payment sheet and purchase check drawn (200), the Needs-you, Amir's lines and pairs read; the
 one-off run DRY on the copy. Last line: 'SYNTH S864: n PASS, m FAIL'."""
import json, os, re, shutil, sqlite3, sys, tempfile
FIN, DBC = sys.argv[1], sys.argv[2]
REAL = "--real" in sys.argv
tmp = tempfile.mkdtemp(prefix="s864synth_")
code = os.path.join(tmp, "finance")
shutil.copytree(FIN, code, ignore=shutil.ignore_patterns("*.db", "__pycache__", "_off"))
_me = os.path.dirname(os.path.abspath(__file__))           # F-1415: never the kit's own copy beside this script
sys.path[:] = [x for x in sys.path if os.path.abspath(x or os.getcwd()) != _me]
sys.path.insert(0, code)
P = F = 0
M = "2025-02"
TOK = "zz-s864-test-token"


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


def lay(con, items=True):
    """Three made-up bills of 2025-02 under two live statements: supplier-wise (older, 05-Mar) and bill-wise (newer, 10-Mar), the same period.
    Item lines covering the month when items=True. Returns {name: id}."""
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                "('zzs864bw','BILLWISE','x','2025-02-01','2025-02-28','20250310-110000','2025-03-10T11:05:00',3,956500)")
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                "('zzs864sw','SUPPLIERWISE','x','2025-02-01','2025-02-28','20250305-110000','2025-03-05T11:05:00',3,967500)")
    if items:
        con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                    "('zzs864iw','ITEMWISE','x','2025-02-01','2025-02-28','20250310-110500','2025-03-10T11:06:00',3,0)")
    ids = {}
    for name, sup, no, d, bw, sw, verdict, wrong in (("x", "ZZKEDAR TEST", "A9001", "2025-02-15", 536000, 547000, "WRONG", 536000),
                                                     ("r", "ZZJANTA TEST", "9002", "2025-02-02", 320500, 320500, "WRONG", 445000),
                                                     ("y", "ZZOTHER TEST", "9003", "2025-02-20", 100000, 100000, "WRONG", 120000)):
        cur = con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, sw_md5, bw_amount_p, sw_amount_p, "
                          "source_md5, verdict, verdict_by, verdict_at, wrong_amount_p, reason) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (sup, sup, no, d, M, bw, "zzs864bw", "zzs864sw", bw, sw, "zzs864bw", verdict, "darpan", "2025-03-01T10:00:00", wrong, "made up"))
        ids[name] = cur.lastrowid
        if items:
            con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, qty, amount_p, net_amount_p, direction, source_md5, line_type) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (sup, no, d, M, "ZZ ITEM " + no, 1, bw, bw, "PURCHASE", "zzs864iw", "ITEMWISE"))
    con.execute("INSERT INTO s740_answer (sup, bill_no, bill_date, answer, paper_p, marg_p, ret_p, by, at) VALUES (?,?,?,?,?,?,?,?,?)",
                ("ZZJANTA TEST", "9002", "2025-02-02", "yes", 445000, 320500, 124500, "manoj", "2025-03-02T09:00:00"))
    con.execute("INSERT INTO s740_track (rkey, kind, month, first_seen, last_seen, resolved_at, road, ref) VALUES (?,?,?,?,?,?,?,?)",
                ("bill:ZZJANTA TEST|9002|2025-02-02", "on_bill", M, "2025-03-02T09:00:00", "2025-03-09T09:00:00", "2025-03-09T09:00:00", "revised", "B-9999"))
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('purchase.register_from', '2025-02-01')")
    con.commit()
    return ids


def push(cl, typ, md5, pf, pt, stamp, rows):
    return cl.post("/finance/purchase/api/push", json=dict(type=typ, md5=md5, period_from=pf, period_to=pt, export_stamp=stamp, rows=rows, file="x"),
                   headers={"X-Finance-Marg": TOK})


try:
    import purchase_app as pa                                 # noqa: E402
    import month_asks as ma                                   # noqa: E402
    import export_watch as ew                                 # noqa: E402
    have = True
except Exception as e:                                        # noqa: BLE001
    print("import:", e)
    have = False
ok(have, "T0 the finance code under test imports (purchase_app, month_asks, export_watch)")
if have:
    pa._assets_db = "/nonexistent"
    ok(hasattr(pa, "s864_one_off") and hasattr(pa, "_s864_statement") and hasattr(ma, "amir_pairs") and getattr(ma, "VERSION", "").startswith("S864"),
       "T0b the S864 pieces are present (one-off, the statement reader, amir_pairs, month_asks %s)" % getattr(ma, "VERSION", "?"))
if have and REAL:
    con = fresh()
    try:
        ms = ma.months(con)
        got = {m: ma.month_asks(con, m) for m in ms}
        ok(bool(ms), "R1 the live copy: %d open month(s) read: %s" % (len(ms), "; ".join("%s %d export ask(s), %d Wrong, pair %s" % (m, len(a["exports"]), len(a["wrong"]), "yes" if a.get("pair") else "no") for m, a in got.items())))
    except Exception as e:                                    # noqa: BLE001
        ok(False, "R1 the live copy's months: %r" % (e,))
    try:
        r = pa.s864_one_off(con, dry=True)
        ok(isinstance(r, dict), "R1b the one-off DRY on the live copy: %d statement(s) to retire (%s)" % (len(r["superseded"]), ", ".join("%s<-%s %s %d->%d only %d" % (x[0][:8], x[1][:8], x[2], x[3], x[4], x[5]) for x in r["superseded"])))
    except Exception as e:                                    # noqa: BLE001
        ok(False, "R1b the one-off DRY: %r" % (e,))
    try:
        from flask import Flask
        app = Flask("s864real")
        pa.init(app, lambda: con, lambda *roles: (dict(user="manoj", roles=["checker"], role="checker"), None), assets_db="/nonexistent")
        cl = app.test_client()
        codes = []
        for m in ma.months(con):
            rp, rc = cl.get("/finance/purchase/page/pay/%s" % m), cl.get("/finance/purchase/page/check?month=%s" % m)
            bp, bc = rp.get_data(as_text=True), rc.get_data(as_text=True)
            codes.append((m, rp.status_code, rc.status_code, "supplier-wise statement" not in bp.replace("Verified against", "")))
        ok(codes and all(a == 200 and b == 200 for _m, a, b, _n in codes),
           "R2 every open month's payment sheet and purchase check draw on the live copy (%r)" % (codes,))
    except Exception as e:                                    # noqa: BLE001
        ok(False, "R2 the pages on the live copy: %r" % (e,))
    try:
        nl, al, ap = ma.needs_lines(con), ma.amir_lines(con), ma.amir_pairs(con)
        ok(isinstance(nl, list) and isinstance(al, list) and isinstance(ap, list), "R3 the Needs-you (%d), Amir's lines (%d) and pairs (%d) read on the live copy" % (len(nl), len(al), len(ap)))
    except Exception as e:                                    # noqa: BLE001
        ok(False, "R3 the Needs-you, Amir's lines and pairs: %r" % (e,))
    con.close()
def _body():
    global con, ids
    # ---- the family rule: the one-off on stored statements, the figure, the self-resolution
    con = fresh()
    ids = lay(con)
    s0 = pa._month_summary(con, M)
    ok(s0["marg_p"] == 956500 and s0["basis"] == "bill-wise" and s0["month_disagree_p"] == 0 and all(b["disagree_p"] == 0 for b in s0["bills"]),
       "T1 two live statements, the bill-wise newer: the month's figure is the bill-wise (%s), no disagreement bucket" % pa._r(s0["marg_p"]))
    r = pa.s864_one_off(con)
    sup = con.execute("SELECT superseded_by FROM purchase_export WHERE md5='zzs864sw'").fetchone()[0]
    vx = con.execute("SELECT verdict, reason FROM purchase_bill WHERE id=?", (ids["x"],)).fetchone()
    ok(sup == "zzs864bw" and [x[2] for x in r["superseded"] if x[0] == "zzs864sw"] == [M] and [x[3:] for x in r["superseded"] if x[0] == "zzs864sw"] == [(3, 3, 0)] and vx[0] == "CORRECT" and "newest" in vx[1].lower() or ("re-export" in vx[1]) and vx[0] == "CORRECT",
       "T2 the one-off: the older supplier-wise retired by the newer bill-wise (3->3 rows, 0 bills only in the old); A9001's Wrong mark (paper = the newest statement) resolved by itself (%s)" % vx[1][:60])
    r2 = pa.s864_one_off(con)
    ok(r2["superseded"] == [] and r2["resolved"] == [], "T3 the one-off run again does nothing (idempotent)")
    fin = con.execute("SELECT COUNT(*) FROM purchase_month WHERE status='final'").fetchone()[0]
    finals = [r0[0] for r0 in con.execute("SELECT month FROM purchase_month WHERE status='final'")]
    ok(all(x[2] not in finals and x[2] >= "2025-02" for x in r["superseded"]) and any(x[2] == M for x in r["superseded"]),
       "T3b the one-off retired nothing in a FINAL month (%s); only counted, open months touched (%s)" % (",".join(finals) or "none on the copy", ",".join(sorted({x[2] for x in r["superseded"]}))))
    # the month-end card and the cross-check on the newest statement
    s1 = pa._month_summary(con, M)
    reps = pa._month_reports(con, M, s1)
    v = pa._verify_statement(con, M, s1)
    ok([e["key"] for e in reps] == ["STATEMENT", "ITEMS"] and all(e["state"] == "received" for e in reps) and v["ok"] and v["export"]["md5"] == "zzs864bw"
       and v["printed_p"] == 956500, "T4 two reports, both received; the cross-check reads the bill-wise and its printed total agrees (%r)" % (v["problems"],))
    st = ma.settle(con, M)
    vr = con.execute("SELECT verdict, reason FROM purchase_bill WHERE id=?", (ids["r"],)).fetchone()
    ok(vr[0] == "CORRECT" and "B-9999" in vr[1], "T5 the Wrong mark settled as a purchase return is resolved by itself (revised bill B-9999)")
    A = ma.month_asks(con, M)
    ok(A["exports"] == [] and A.get("pair") is None and [w["bill"]["bill_no"] for w in A["wrong"]] == ["9003"] and A["wrong"][0]["how"] == "yours" and A["n"] == 1,
       "T6 nothing is asked of Amir: the month is in and agrees; only 9003's Wrong mark is his (n=%d)" % A["n"])
    con.close()
    # ---- the pair asked for a named reason, and gone when it arrives
    con = fresh()
    ids = lay(con, items=False)
    pa.s864_one_off(con)
    A = ma.month_asks(con, M)
    ok(A.get("pair") is not None and [k for k, _l in A["pair"]["kinds"]] == ["ITEMWISE"] and [a["key"] for a in A["exports"]] == ["ITEMS"]
       and "no item lines" in A["pair"]["why"][0], "T7 the lines not received: the item-wise alone is asked, with its reason (%r)" % (A["pair"]["why"],))
    con.execute("UPDATE purchase_export SET export_stamp='20250110-110000' WHERE md5='zzs864bw'")   # a statement from BEFORE the month ended -> none covers... it still covers the period
    con.commit()
    con.execute("DELETE FROM purchase_export WHERE md5='zzs864bw'")
    con.execute("UPDATE purchase_bill SET bw_md5=NULL WHERE month=?", (M,))
    con.execute("UPDATE purchase_export SET superseded_by=NULL WHERE md5='zzs864sw'")
    con.commit()
    A = ma.month_asks(con, M)
    ok(A.get("pair") is not None and [a["key"] for a in A["exports"]] == ["ITEMS"] and [k for k, _l in A["pair"]["kinds"]] == ["ITEMWISE"],
       "T8 only an old supplier-wise live: it IS the statement (received) -- only the lines are asked (%r)" % ([a["key"] for a in A["exports"]],))
    # Amir's correction list on a bill of the month -> the pair asked with the reason, in English and Hindi
    con.close()
    con = fresh()
    ids = lay(con)
    pa.s864_one_off(con)
    con.execute("INSERT INTO s738_fix (bill_id, kind, month, first_seen, last_seen, marg_p) VALUES (?,?,?,?,?,?)", (ids["y"], "more", M, "2025-03-11T09:00:00", "2025-03-11T09:00:00", 100000))
    con.commit()
    A = ma.month_asks(con, M)
    p = A.get("pair")
    ok(p is not None and [k for k, _l in p["kinds"]] == ["ITEMWISE", "BILLWISE"] and "correction list" in p["why"][0] and "9003" in p["why"][0] and "dobara" in p["why_hi"][0]
       and [a["key"] for a in A["exports"]] == ["STATEMENT", "ITEMS"] and {w["bill"]["bill_no"]: w["how"] for w in A["wrong"]}.get("9003") == "amir",
       "T9 a bill of the month on Amir's correction list: the pair is asked, the reason named (en: %s | hi: %s)" % (p["why"][0][:70] if p else "", p["why_hi"][0][:60] if p else ""))
    h = ma.card_html(con, M, "/finance/purchase", True)
    ok("last month's pair once more" in h and "BILL WISE PURCHASE STATEMENT, FROM 01-02-2025 TO 28-02-2025" in h and "SUPPLIER/ITEM WISE PURCHASE STATEMENT, FROM 01-02-2025 TO 28-02-2025" in h
       and "correction list" in h and 'onclick="s855c(this)"' not in h and "SUPPLIER WISE PURCHASE STATEMENT," not in h,
       "T10 his card names the pair, its dates and the reason; no Correct button (the bill is with Amir); the supplier-wise never named")
    n8, l8 = ma.row8_lines(con, M)
    items8 = ma.open_items(con, M)
    r8 = [x for x in items8 if x["row"] == 8]
    ok(n8 == 2 and len(l8) == 2 and len(r8) == 1 and "Last month's pair" in r8[0]["what"] and any("Why:" in s for s in r8[0]["steps"]),
       "T11 row 8 counts the two reports; the check's open item is ONE line for the pair with its why (%d)" % n8)
    ap = ma.amir_pairs(con, day="2025-03-12")
    ok(len(ap) == 1 and ap[0]["month"] == M and ap[0]["first"] == "2025-02-01" and ap[0]["last"] == "2025-02-28" and set(ap[0]["got"]) == {"ITEMWISE", "BILLWISE"}
       and all(g["state"] == "none" for g in ap[0]["got"].values()), "T12 amir_pairs: the finished month's pair, both reports 'none' for the day")
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                "('zzs864bw2','BILLWISE','x','2025-02-01','2025-02-28','20250312-100000','2025-03-12T10:05:00',3,956500)")
    con.execute("UPDATE purchase_bill SET bw_md5='zzs864bw2' WHERE month=?", (M,))                  # as the push does: the bills move to the newest
    con.execute("UPDATE purchase_export SET superseded_by='zzs864bw2' WHERE md5='zzs864bw'")        # and the older contained statement retires
    con.commit()
    ap = ma.amir_pairs(con, day="2025-03-12")
    ok(ap and ap[0]["got"]["BILLWISE"]["state"] == "ok" and ap[0]["got"]["BILLWISE"]["at"] == "10:00" and ap[0]["got"]["ITEMWISE"]["state"] == "none",
       "T13 the bill-wise of the pair exported today reads ok 10:00 on step 4; the item-wise still none")
    al = ma.amir_lines(con)
    ok(len(al) == 1 and "Pichhle mahine" in al[0] and "FROM 01-02-2025 TO 28-02-2025" in al[0] and "dobara" in al[0], "T14 his card's line: last month's pair, the dates, the reason in Hindi")
    con.execute("UPDATE s738_fix SET settled_at='2025-03-12T10:10:00', settled_export='zzs864bw2' WHERE bill_id=?", (ids["y"],))
    con.commit()
    A = ma.month_asks(con, M)
    ok(A.get("pair") is None and A["exports"] == [], "T15 the correction settled by the fresh export: the ask leaves by itself")
    # his own 'self' answer after the statement
    con.execute("INSERT INTO amir_bill_answer (bill_id, supplier_norm, bill_no, bill_date, day, reason, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                (ids["y"], "ZZOTHER TEST", "9003", "2025-02-20", "2025-03-13", "self", "amir", "2025-03-13T09:30:00"))
    con.commit()
    A = ma.month_asks(con, M)
    ok(A.get("pair") is not None and "own entry" in A["pair"]["why"][0], "T16 Amir's 'meri entry galat thi' after the statement: the pair asked, the reason named")
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                "('zzs864bw3','BILLWISE','x','2025-02-01','2025-02-28','20250313-100000','2025-03-13T10:05:00',3,956500)")
    con.execute("UPDATE purchase_export SET superseded_by='zzs864bw3' WHERE md5='zzs864bw2'")
    con.execute("UPDATE purchase_bill SET bw_md5='zzs864bw3' WHERE month=?", (M,))
    con.commit()
    A = ma.month_asks(con, M)
    ok(A.get("pair") is None, "T17 a statement newer than his correction arrives: the ask leaves")
    # ---- a bill carried only by the retired statement leaves the month (Marg deleted / re-keyed it); the part guard in the one-off
    con.close()
    con = fresh()
    ids = lay(con)
    con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, sw_md5, sw_amount_p, source_md5) VALUES "
                "('ZZGONE TEST','ZZGONE TEST','9004','2025-02-21',?,70000,'zzs864sw',70000,'zzs864sw')", (M,))
    con.commit()
    n_before = len(pa._bills_for_month(con, M))
    r = pa.s864_one_off(con)
    mine = [x for x in r["superseded"] if x[0] == "zzs864sw"]
    n_after = len(pa._bills_for_month(con, M))
    ok(n_before == 4 and n_after == 3 and mine and mine[0][5] == 1 and con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s864_superseded' AND ref='zzs864sw'").fetchone()[0] == 1,
       "T25 a bill only the retired supplier-wise carried leaves the month (4 -> 3), the one-off said so (1 bill only in the old), audited")
    con.execute("UPDATE purchase_export SET n_rows=6 WHERE md5='zzs864bw'")            # a real-sized statement; the part is 1 row
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                "('zzs864part','SUPPLIERWISE','x','2025-02-01','2025-02-28','20250320-100000','2025-03-20T10:05:00',1,100000)")
    con.commit()
    r = pa.s864_one_off(con)
    ok([x[:2] for x in r["superseded"]] == [("zzs864part", "zzs864bw")] and con.execute("SELECT superseded_by FROM purchase_export WHERE md5='zzs864bw'").fetchone()[0] is None
       and con.execute("SELECT superseded_by FROM purchase_export WHERE md5='zzs864part'").fetchone()[0] == "zzs864bw"
       and con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s864_part_retired' AND ref='zzs864part'").fetchone()[0] == 1,
       "T26 a newer one-row supplier-wise (a part list) retires nothing in the one-off (the S795 guard): it is itself kept as a part of the bill-wise, audited")
    con.execute("UPDATE purchase_export SET superseded_by=NULL WHERE md5='zzs864part'")     # a live part by hand (the push and the one-off never leave one)
    con.commit()
    s4 = pa._month_summary(con, M)
    v4 = pa._verify_statement(con, M, s4)
    ok(not v4["ok"] and v4["export"]["md5"] == "zzs864part" and any("not carried by that statement" in x for x in v4["problems"]),
       "T27 the cross-check reads the newest statement and names the bills it does not carry (%s)" % (v4["problems"][0][:70] if v4["problems"] else ""))
    A27 = ma.month_asks(con, M)
    ok(A27.get("pair") is not None and any("does not carry" in w for w in A27["pair"]["why"]) and [a["key"] for a in A27["exports"]] == ["STATEMENT", "ITEMS"],
       "T27b a whole-month statement that does not carry the sheet's bills is a named reason: the pair is asked, never a dead end (%s)" % (A27["pair"]["why"][0][:80] if A27.get("pair") else ""))
    con.execute("UPDATE purchase_export SET superseded_by='zzs864bw' WHERE md5='zzs864part'")
    con.commit()
    # OFF
    off = os.path.join(code, "_off")
    os.makedirs(off, exist_ok=True)
    open(os.path.join(off, "S855_OFF"), "w").close()
    ok(ma.card_html(con, M, "/x") == "" and ma.month_asks(con, M)["n"] == 0 and ma.needs_lines(con) == [] and ma.amir_lines(con) == [] and ma.amir_pairs(con) == [] and ma.settle(con) == [],
       "T18 OFF: no card, no asks, no pairs, nothing resolved")
    os.remove(os.path.join(off, "S855_OFF"))
    con.close()
    # ---- the push door across the family, in a Flask app on the copy
    try:
        from flask import Flask
        con = fresh()
        ids = lay(con)
        pa.s864_one_off(con)
        who = {"u": dict(user="manoj", roles=["checker"], role="checker")}
        app = Flask("s864synth")
        pa.init(app, lambda: con, lambda *roles: (who["u"], None), marg_token=TOK, assets_db="/nonexistent")
        cl = app.test_client()
        rows = [dict(supplier="ZZKEDAR TEST", bill_no="A9001", bill_date="2025-02-15", cash_p=0, credit_p=536000),
                dict(supplier="ZZJANTA TEST", bill_no="9002", bill_date="2025-02-02", cash_p=0, credit_p=320500),
                dict(supplier="ZZOTHER TEST", bill_no="9003", bill_date="2025-02-20", cash_p=0, credit_p=100000)]
        r1 = push(cl, "SUPPLIERWISE", "a" * 32, "2025-02-01", "2025-02-28", "20250314-100000", rows)
        j1 = r1.get_json()
        sup_bw = con.execute("SELECT superseded_by FROM purchase_export WHERE md5='zzs864bw'").fetchone()[0]
        r2 = push(cl, "BILLWISE", "b" * 32, "2025-02-01", "2025-02-27", "20250301-100000", rows[:2])
        j2 = r2.get_json()
        r3 = push(cl, "BILLWISE", "c" * 32, "2025-02-01", "2025-02-28", "20250315-100000", rows)
        j3 = r3.get_json()
        sup_sw = con.execute("SELECT superseded_by FROM purchase_export WHERE md5=?", ("a" * 32,)).fetchone()[0]
        s2 = pa._month_summary(con, M)
        ok(r1.status_code == 200 and j1.get("stored") and sup_bw == "a" * 32 and j2.get("reason") == "superseded_older" and j3.get("stored") and sup_sw == "c" * 32
           and s2["marg_p"] == 956500 and s2["basis"] == "bill-wise",
           "T19 the push: a newer supplier-wise retires the bill-wise (family); an older contained bill-wise is 'superseded_older'; a newer bill-wise retires the supplier-wise; the figure follows the newest")
        rows6 = rows + [dict(supplier="ZZMORE TEST", bill_no="M%d" % i, bill_date="2025-02-1%d" % i, cash_p=0, credit_p=1000) for i in range(3)]
        r4a = push(cl, "BILLWISE", "f" * 32, "2025-02-01", "2025-02-28", "20250315-120000", rows6)
        r4 = push(cl, "SUPPLIERWISE", "d" * 32, "2025-02-01", "2025-02-28", "20250316-100000", rows[:1])
        j4 = r4.get_json()
        ok(r4a.get_json().get("stored") and j4.get("reason") == "part_export" and con.execute("SELECT superseded_by FROM purchase_export WHERE md5=?", ("f" * 32,)).fetchone()[0] is None,
           "T19b a one-row supplier-wise after a 6-row bill-wise is kept as a part (the family's S795 guard) -- the bill-wise stays live")
        con.execute("UPDATE purchase_bill SET verdict='WRONG', wrong_amount_p=99000, verdict_by='manoj', verdict_at='2025-03-16T11:00:00' WHERE id=?", (ids["y"],))
        con.commit()
        rows2 = [dict(r0) for r0 in rows6]
        rows2[2]["credit_p"] = 99000
        r5 = push(cl, "BILLWISE", "e" * 32, "2025-02-01", "2025-02-28", "20250317-100000", rows2)
        vy = con.execute("SELECT verdict, bw_amount_p FROM purchase_bill WHERE id=?", (ids["y"],)).fetchone()
        ok(r5.get_json().get("stored") and vy[0] == "CORRECT" and vy[1] == 99000, "T19c a Wrong mark resolves at the push when the newest statement carries the paper's figure (9003 -> Rs 990)")
        r6 = push(cl, "BILLWISE", "e" * 32, "2025-02-01", "2025-02-28", "20250318-100000", rows2)
        st6 = con.execute("SELECT export_stamp, superseded_by FROM purchase_export WHERE md5=?", ("e" * 32,)).fetchone()
        ok(r6.get_json().get("reason") == "duplicate_restamped" and st6[0] == "20250318-100000" and st6[1] is None
           and con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='push_again' AND ref=?", ("e" * 32,)).fetchone()[0] == 1,
           "T19d the same bytes exported again: the live statement takes the newer stamp (an ask waiting for a newer statement can clear), audited")
        r7 = push(cl, "BILLWISE", "f" * 32, "2025-02-01", "2025-02-28", "20250319-100000", rows6)
        ok(r7.get_json().get("reason") == "duplicate" and con.execute("SELECT export_stamp FROM purchase_export WHERE md5=?", ("f" * 32,)).fetchone()[0] == "20250315-120000",
           "T19e the same bytes of a SUPERSEDED statement: left as it is")
        hub = cl.get("/finance/purchase/page/hub")
        mon = cl.get("/finance/purchase/page/month/" + M)
        ht, mt = hub.get_data(as_text=True), mon.get_data(as_text=True)
        if os.environ.get("S864_DUMP"):
            open(os.environ["S864_DUMP"], "w", encoding="utf-8").write(mt)
        ok(hub.status_code == 200 and mon.status_code == 200 and "Marg total (statement)" in ht and "supplier-wise figure" not in mt and "newest purchase statement" in mt,
           "T19f the hub and the month page draw with the new words (%d, %d; %r)" % (hub.status_code, mon.status_code, ("Marg total (statement)" in ht, "supplier-wise figure" not in mt, "newest purchase statement" in mt)))
        ma.settle(con, M)
        ma.correct(con, "manoj", ids["y"])
        s3 = pa._month_summary(con, M)
        gate = pa._lock_gate(con, M, s3)
        b1 = cl.get("/finance/purchase/page/pay/" + M).get_data(as_text=True)
        b2 = cl.get("/finance/purchase/page/check?month=" + M)
        ok(b2.status_code == 200 and "All three reports" not in b1 and "Verified against Marg" in b1 and not any("statement" in x or "supplier-wise" in x for x in gate[1])
           and (("Both reports are in and agree" in b1) == gate[0]) and "Waiting for Marg\'s supplier-wise" not in b1,
           "T20 the payment sheet: verified against Marg's statement, no report holds the gate (%s); the purchase check draws (%d)" % ("open" if gate[0] else "held by: " + "; ".join(gate[1])[:120], b2.status_code))
        who["u"] = dict(user="amir", roles=["viewer"], role="viewer")
        con.close()
    except Exception as e:                                    # noqa: BLE001
        ok(False, "T19/T20 the push door and the pages in a Flask app: %r" % (e,))
    # ---- Amir's steps 3 and 4 (amir_day under test) -- fail-soft seams and the render anchors
    try:
        import amir_day as ad                                 # noqa: E402
        src = open(os.path.join(code, "amir_day.py"), encoding="utf-8").read()
        ok("_step3_before_s864 = _step3" in src and "_step4_before_s864 = _step4" in src and "month_asks.amir_pairs(cx, day=day)" in src
           and src.count("<div class=card><h2>Do report nikaaliye</h2>") == 2 and src.count("<div class=card><h2>Do report</h2>") == 2,
           "T21 amir_day: the S864 tail wraps state, step 3 and step 4; each render anchor stands once in the live text and once as the tail's constant")
        class S:                                              # a stand-in state with one pair
            pass
        st = S()
        st.s864 = [dict(month=M, first="2025-02-01", last="2025-02-28", kinds=[("ITEMWISE", "Item-detail purchase report"), ("BILLWISE", "Bill-wise purchase report")],
                        why_hi=["9003 Marg mein theek karein, phir dono report dobara"], why=["x"], got={"ITEMWISE": dict(state="none"), "BILLWISE": dict(state="ok", at="10:00")})]
        c3, c4 = ad._s864_step3_card(st), ad._s864_step4_card(st)
        ok("Pehle pichhle mahine (February 2025) ki report" in c3 and "01-02-2025" in c3 and "28-02-2025" in c3 and "dobara" in c3 and "Item-detail purchase report" in c3
           and "&#10003;" in c4 and "10:00 baje" in c4 and "Abhi nikaali nahi gayi" in c4 and "Pichhle mahine (February 2025) ki do report" in c4,
           "T22 step 3's card: the finished month, its two dates, both reports, the reason; step 4's card: bill-wise ✓ 10:00, item-wise not yet")
        st.s864 = []
        ok(ad._s864_step3_card(st) == "" and ad._s864_step4_card(st) == "", "T23 no pair asked: the steps draw as before")
    except Exception as e:                                    # noqa: BLE001
        ok(False, "T21-T23 amir_day: %r" % (e,))
    # ---- export_watch: a whole-month bill-wise after month end satisfies the month-end expectation
    try:
        con = sqlite3.connect(":memory:")
        con.executescript(ew.SCHEMA if hasattr(ew, "SCHEMA") else "")
    except Exception:                                         # noqa: BLE001
        con = None
    try:
        import datetime as _dt
        con = fresh()
        con.execute("DELETE FROM purchase_export")
        con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
                    "('zzew','BILLWISE','f','2026-09-01','2026-09-30','20261002-100000','2026-10-02T10:05:00',1,0)")
        con.commit()
        ev = ew.evidence(con, _dt.date(2026, 10, 3))
        ok(ev.get("SUPPLIERWISE", {}).get("covers") is True and "BILL WISE for the whole of last month" in ew.LABEL["SUPPLIERWISE"],
           "T24 export_watch: a whole-month BILL-WISE after month end satisfies the month-end expectation; its label names the bill-wise")
        con.close()
    except Exception as e:                                    # noqa: BLE001
        ok(False, "T24 export_watch: %r" % (e,))
if have:
    try:
        _body()
    except Exception as e:                                    # noqa: BLE001 -- the control (live files) crashes here: red, and the last line still prints
        ok(False, "the proof stopped: %r" % (e,))
shutil.rmtree(tmp, ignore_errors=True)                      # the copies and the code under test leave with the run
print("SYNTH S864: %d PASS, %d FAIL" % (P, F))
