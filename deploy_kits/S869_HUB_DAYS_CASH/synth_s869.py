"""synth_s869.py <finance dir under test> <finance.db COPY> [--box] -- kit S869_HUB_DAYS_CASH proof. Works on COPIES only; nothing of the
server is touched. On the 18-Nov copy (or the box's own copy of the live database): the one calculation's new rules (an accepted short is
written off; owner entries move the cash), the day panel's new fields (names as typed, line values, the returns' patient / ID / mobile / key,
the entries), hub_cash's doors through Flask (healthz, drawer-why, day-entry add + remove, received-all), day_resync pass 1 on approved days
(9-Oct, 14-Oct WOULD_FIX -> FIXED -> SAME), the one-off DRY then APPLY then again (drawer Rs 549 on the 18-Nov copy, with 17-Oct's 504 left),
and the Hub page's S869 markers. The CONTROL (the live files) goes red on the new rules. Last line: 'SYNTH S869: n PASS, m FAIL'."""
import json, os, shutil, sqlite3, subprocess, sys, tempfile
FIN, DBC = sys.argv[1], sys.argv[2]
BOX = "--box" in sys.argv
tmp = tempfile.mkdtemp(prefix="s869synth_")
code = os.path.join(tmp, "finance")
shutil.copytree(FIN, code, ignore=shutil.ignore_patterns("*.db", "__pycache__", "_off"))
_me = os.path.dirname(os.path.abspath(__file__))           # F-1415: never the kit's own copy beside this script
sys.path[:] = [x for x in sys.path if os.path.abspath(x or os.getcwd()) != _me]
sys.path.insert(0, code)
P = F = 0
PY = sys.executable


def ok(c, what):
    global P, F
    if c:
        P += 1
        print("PASS", what)
    else:
        F += 1
        print("FAIL", what)


def fresh(name=None):
    db = os.path.join(tmp, name or ("f%d.db" % (P + F)))
    shutil.copy(DBC, db)
    con = sqlite3.connect(db, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con, db


try:
    import sanjeevni_cash as sc
    import sanjeevni_day as sd
    import hub_cash as hc
    import day_resync as dr
    from flask import Flask
    # ---- 1. the one calculation: an accepted short is written off; entries move the cash
    con, db = fresh("base.db")
    CLEAN = con.execute("SELECT handed_p FROM darpan_kal_day WHERE business_date='2026-10-09'").fetchone()[0] == 1325800   # the one-off already applied
    r = sc.days(con, "2026-09-01", "9999-12-31")
    rows = {x["date"]: x for x in r["rows"]}
    ok(r["ok"] and len(rows) >= 60, "T1 the one calculation reads the copy (%d days%s)" % (len(rows), "; the one-off already applied on it" if CLEAN else ""))

    def frozen(name):
        if CLEAN:
            print("skip", name, "(the copy is already cleaned; the frozen expectation does not apply)")
        return not CLEAN
    s28 = rows.get("2026-09-28") or {}
    ok(s28.get("written_off_p") == 68000 and any(h["to"] == "written_off" and h["amount_p"] == 68000 for h in s28.get("handed", [])),
       "T2 28-Sep: the accepted Rs 680 short is written off (F-1460)")
    ok((rows.get("2026-10-14") or {}).get("written_off_p", 1) == 0, "T3 14-Oct: an accept on a -3 diff writes nothing off (only the short he accepted)")
    before = r["rows"][-1]["close"]["drawer"]
    hc.ensure_schema(con)
    if not CLEAN: con.execute("INSERT INTO owner_day_entry (unit, business_date, kind, amount_p, party, purpose, note, entered_by, entered_at) VALUES "
                "('medical','2026-11-14','other_account',158000,'NK','', 'x','t','2026-11-18T00:00:00')")
    if not CLEAN: con.execute("INSERT INTO owner_day_entry (unit, business_date, kind, amount_p, party, purpose, note, entered_by, entered_at) VALUES "
                "('medical','2026-11-14','taken_out',400000,'dr_bhawna','personal','x','t','2026-11-18T00:00:00')")
    con.commit()
    r2 = sc.days(con, "2026-09-01", "9999-12-31")
    d14 = [x for x in r2["rows"] if x["date"] == "2026-11-14"][0]
    if CLEAN: ok(d14["other_account_p"] == 158000 and any(h["src"] == "entry" and h["amount_p"] == 400000 for h in d14["handed"]),
                 "T4c on the cleaned copy 14-Nov carries the one-off's 1,580 and 4,000")
    if frozen("T4"): ok(d14["other_account_p"] == 158000 and d14["into_drawer_p"] == rows["2026-11-14"]["into_drawer_p"] - 158000,
       "T4 14-Nov: 'paid into another account' lowers the day's cash for the drawer by 1,580")
    if frozen("T5"): ok(any(h["src"] == "entry" and h["to"] == "dr_bhawna" and h["amount_p"] == 400000 for h in d14["handed"]),
       "T5 14-Nov: 'cash taken out' leaves the drawer to Dr Bhawna, counted once")
    after = r2["rows"][-1]["close"]
    if frozen("T6"): ok(after["drawer"] == before - 558000 and after["dr_bhawna"] == r["rows"][-1]["close"]["dr_bhawna"] + 400000,
       "T6 the drawer falls by 5,580; Dr Bhawna rises by 4,000; the 1,580 leaves the unit")
    bad7 = [x[0] for x in sc.prove(con)[1] if not x[3]]
    ok(bad7 == ["September: the two pool deposits (3,00,000 + 1,00,000) are recorded once"],
       "T7 sanjeevni_cash's own proof: conservation holds with the entries and the write-off (only its frozen 'two deposits' line red, as before S869): %s" % bad7)
    if not CLEAN: con.execute("UPDATE owner_day_entry SET removed_at='2026-11-18T00:00:01', removed_by='t'")
    con.commit()
    r3 = sc.days(con, "2026-09-01", "9999-12-31")
    if frozen("T8"): ok(r3["rows"][-1]["close"]["drawer"] == before, "T8 a removed entry counts for nothing")
    # ---- 2. the day panel
    v = sd.day_view(con, "2026-11-14")
    w = {x["bill"]: x for x in v["without_cash"]["list"]}
    ok(str(w.get("A004799", {}).get("typed") or "").upper().startswith("PROSIJER ") and len(w["A004799"]["typed"]) > 12,
       "T9 A004799 carries Darpan's text exactly as typed ('PROSIJER ...', the review queue's own)")
    it = (w.get("A004799") or {}).get("items") or []
    ok(len(it) == 1 and it[0]["value"] == "293" and it[0]["amount"] == "98", "T10 its line: 3 x 98 = 293 (the amount is the strip rate)")
    ok(sd.line_value_p("0:7", "1*10", 22000) == 15400 and sd.line_value_p("1:4", "1*10", 4680) == 6552 and sd.line_value_p("2.0", "200ML", 12300) == 24600
       and sd.line_value_p("x", "1*10", 100) is None, "T11 line values: strips:tabs x rate, a plain count, unreadable -> none")
    v12 = sd.day_view(con, "2026-11-12")
    rt = v12["returns"]["list"]
    ok(len(rt) == 3 and all(x.get("key") == "2026-11-12|" + x["bill"] for x in rt) and rt[0]["patient"] and len(str(rt[0]["clinic_id"])) >= 3,
       "T12 12-Nov's three returns carry the patient, the ID and the Returns card's key")
    ok(all("mobile" in x for x in rt) and any(x["mobile"] for x in rt), "T13 a return carries the mobile where the patient has one")
    v28 = sd.day_view(con, "2026-09-28")
    ok(v28["written_off"] == "680" and "written off" in (v28["went"] or ""), "T14 28-Sep's panel says 680 written off")
    if not CLEAN: con.execute("UPDATE owner_day_entry SET removed_at=NULL, removed_by=NULL")
    con.commit()
    v14 = sd.day_view(con, "2026-11-14")
    if frozen("T15"): ok(len(v14["entries"]) == 2 and v14["other_account"] == "1,580" and all(e.get("words") for e in v14["entries"]),
       "T15 14-Nov's panel lists the two entries with their words and the 1,580 line")
    if frozen("T16"): ok(v14["drawer"] == "19,216" and "4,000 to Dr Bhawna" in (v14["went"] or ""),
       "T16 14-Nov's cash for the drawer is 19,216 with the 1,580 out; where it went names the 4,000 taken out (15,216 handed + 4,000 = 19,216)")
    # ---- 3. hub_cash through Flask
    app = Flask("t")
    con2, db2 = fresh("flask.db")
    CUR = {"user": "manoj", "roles": ["checker"]}

    def req(*roles, **kw):
        if "checker" in roles and "checker" in CUR["roles"]:
            return dict(CUR), None
        from flask import jsonify
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    sd.init(app, lambda: con2, req)
    c = app.test_client()
    j = c.get("/finance/sanjeevni/api/hub-cash/healthz").get_json()
    ok(j and j.get("ok") and j.get("version") == hc.VERSION, "T17 hub_cash healthz answers through sanjeevni_day's mount")
    j = c.get("/finance/sanjeevni/api/drawer-why").get_json()
    days = {d["day"]: d for d in j.get("days", [])}
    if frozen("T18"): ok(j.get("ok") and set(days) == {"14-Oct", "17-Oct", "03-Nov", "04-Nov", "14-Nov"} and days["17-Oct"]["short"] == "504",
       "T18 drawer-why names the five short days of the copy (28-Sep written off, August closed): %s" % sorted(days))
    if frozen("T19"): ok("accept" in days["17-Oct"]["actions"] and "accept" not in days["14-Oct"]["actions"] and any("bank settled 11,985" in x for x in days["14-Oct"]["cause"]),
       "T19 17-Oct offers Accept; 14-Oct (already accepted) names the late bank UPI as its cause")
    n04 = len(hc.entries(con2).get("2026-11-04", []))
    j = c.post("/finance/sanjeevni/api/day-entry", json=dict(date="2026-11-04", kind="other_account", amount_p=95400, party="another account", note="UPI")).get_json()
    ok(j.get("ok") and len(j.get("entries", [])) == n04 + 1, "T20 an entry is added through the door")
    eid = j.get("id")
    j = c.get("/finance/sanjeevni/api/drawer-why").get_json()
    if frozen("T21"): ok("04-Nov" not in {d["day"] for d in j["days"]}, "T21 4-Nov leaves the short list once its 954 is entered")
    bad = c.post("/finance/sanjeevni/api/day-entry", json=dict(date="2026-11-04", kind="taken_out", amount_p=100, party="nobody", purpose="personal")).get_json()
    bad2 = c.post("/finance/sanjeevni/api/day-entry", json=dict(date="2099-01-01", kind="other_account", amount_p=100, party="x")).get_json()
    bad3 = c.post("/finance/sanjeevni/api/day-entry", json=dict(date="2026-11-04", kind="other_account", amount_p=-5, party="x")).get_json()
    ok(not bad.get("ok") and not bad2.get("ok") and not bad3.get("ok"), "T22 a bad party, a future date, a minus amount are refused")
    j = c.post("/finance/sanjeevni/api/day-entry/remove", json=dict(id=eid)).get_json()
    ok(j.get("ok") and len(j.get("entries", [None])) == n04 and con2.execute("SELECT removed_at FROM owner_day_entry WHERE id=?", (eid,)).fetchone()[0],
       "T23 the entry is removed (kept, removed_at set)")
    n0 = con2.execute("SELECT COUNT(*) FROM darpan_kal_day WHERE handed_to='dr_bhawna' AND handed_p IS NOT NULL AND received_at IS NULL").fetchone()[0]
    j = c.post("/finance/sanjeevni/api/received-all", json=dict(party="dr_bhawna")).get_json()
    n1 = con2.execute("SELECT COUNT(*) FROM darpan_kal_day WHERE handed_to='dr_bhawna' AND handed_p IS NOT NULL AND received_at IS NULL").fetchone()[0]
    na = con2.execute("SELECT COUNT(*) FROM darpan_kal_audit WHERE action='received' AND detail LIKE '%S869%'").fetchone()[0]
    ok(j.get("ok") and j.get("n") == n0 and (n0 > 0 or CLEAN) and n1 == 0 and na == n0, "T24 received-all stamps every unreceived handover to Dr Bhawna (%d), each audited" % n0)
    CUR["roles"] = ["maker"]
    r403 = c.get("/finance/sanjeevni/api/drawer-why").status_code
    r403b = c.post("/finance/sanjeevni/api/day-entry", json=dict(date="2026-11-04", kind="other_account", amount_p=100, party="x")).status_code
    ok(r403 == 403 and r403b == 403, "T25 a maker (Darpan / Bhati) is refused at every door")
    CUR["roles"] = ["checker"]
    j = c.get("/finance/sanjeevni/api/day/2026-11-14").get_json()
    ok(j.get("ok") and "entries" in j and "other_account" in j, "T26 the day door carries the new fields")
    # ---- 4. day_resync pass 1 on approved days (F-1459)
    con3, db3 = fresh("resync.db")
    pr = subprocess.run([PY, "-B", os.path.join(code, "day_resync.py"), "--db", db3, "--dry-run", "--no-reconcile"], capture_output=True, text=True)
    out = pr.stdout
    wf = [l.split()[1] for l in out.splitlines() if l.strip().startswith("WOULD_FIX")]
    if wf != ["2026-10-09", "2026-10-14"] and not CLEAN:
        print("   day_resync said:", (out + pr.stderr)[-600:])
    if frozen("T27"): ok(wf == ["2026-10-09", "2026-10-14"], "T27 pass 1 DRY names 9-Oct and 14-Oct only (approved days included)")
    else: ok(wf == [], "T27c pass 1 DRY on the cleaned copy: nothing to fix")
    out = subprocess.run([PY, "-B", os.path.join(code, "day_resync.py"), "--db", db3, "--no-reconcile"], capture_output=True, text=True).stdout
    ln = {m: a for m, a in con3.execute("SELECT l.mode, l.amount_p FROM day_line l JOIN day_entry e ON e.id=l.day_entry_id WHERE e.business_date='2026-10-09' AND l.service='pharmacy_sale'")}
    au = con3.execute("SELECT after_json FROM audit_log WHERE action='resync_upi' AND after_json LIKE '%2026-10-09%' ORDER BY id DESC LIMIT 1").fetchone()
    fx = [l.split()[1] for l in out.splitlines() if l.strip().startswith("FIXED")]
    if frozen("T28"): ok(fx == ["2026-10-09", "2026-10-14"] and ln == {"cash": 1325800, "upi": 1016300} and au and "F-1459" in au[0] and '"status": "approved"' in au[0],
       "T28 pass 1 APPLY: 9-Oct cash 13,258 / UPI 10,163, audited with the day's status")
    out = subprocess.run([PY, "-B", os.path.join(code, "day_resync.py"), "--db", db3, "--dry-run", "--no-reconcile"], capture_output=True, text=True).stdout
    ok(not [l for l in out.splitlines() if l.strip().startswith("WOULD_FIX")], "T29 pass 1 again: nothing left to fix (idempotent)")
    # ---- 5. the one-off: DRY, APPLY, again
    o = subprocess.run([PY, "-B", os.path.join(_me, "oneoff_s869.py"), "--db", db3, "--fin", code], capture_output=True, text=True).stdout
    n_before = con3.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    if CLEAN: ok("one-off DRY: OK" in o and "already" in o, "T30c the one-off DRY on the cleaned copy: every step already done")
    if frozen("T30"): ok("one-off DRY: OK" in o and "would correct 9-Oct" in o and "would remove A004591" in o, "T30 the one-off DRY says the five changes and writes nothing")
    if frozen("T31"): ok(con3.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == n_before and con3.execute("SELECT handed_p FROM darpan_kal_day WHERE business_date='2026-10-09'").fetchone()[0] == 2342100,
       "T31 after the DRY the copy is unchanged")
    o = subprocess.run([PY, "-B", os.path.join(_me, "oneoff_s869.py"), "--db", db3, "--fin", code, "--apply"], capture_output=True, text=True).stdout
    k9 = con3.execute("SELECT handed_p, diff_p FROM darpan_kal_day WHERE business_date='2026-10-09'").fetchone()
    mv = con3.execute("SELECT amount_p FROM cash_movement WHERE id=48").fetchone()[0]
    cv = con3.execute("SELECT amount_p FROM cash_handover_cover WHERE handover_src='movement' AND handover_id=48").fetchone()[0]
    ow = con3.execute("SELECT status FROM darpan_kal_owed WHERE business_date='2026-10-09'").fetchone()[0]
    if frozen("T32"): ok("one-off APPLY: OK" in o and tuple(k9) == (1325800, 0) and mv == 1325800 and cv == 1325800 and ow == "withdrawn",
       "T32 9-Oct: handover, movement, cover 13,258; diff 0; the owed row withdrawn")
    if frozen("T33"): ok(con3.execute("SELECT COUNT(*) FROM sale_bill WHERE bill_no='A004591'").fetchone()[0] == 0 and con3.execute("SELECT COUNT(*) FROM sale_line_item WHERE bill_no='A004591'").fetchone()[0] == 0
       and con3.execute("SELECT status FROM sale_item_review WHERE id=2321").fetchone()[0] == "resolved"
       and con3.execute("SELECT COUNT(*) FROM audit_log WHERE action='remove_gone_bill'").fetchone()[0] == 1,
       "T33 3-Nov: A004591 and its 6 lines gone, kept whole in one audit row; its review line resolved")
    ln3 = {m: a for m, a in con3.execute("SELECT l.mode, l.amount_p FROM day_line l JOIN day_entry e ON e.id=l.day_entry_id WHERE e.business_date='2026-11-03' AND l.service='pharmacy_sale'")}
    if frozen("T34"): ok(ln3 == {"cash": 476200, "upi": 841400}, "T34 3-Nov follows Marg's 13 bills: cash 4,762 = what Darpan handed")
    ne = con3.execute("SELECT COUNT(*) FROM owner_day_entry WHERE removed_at IS NULL").fetchone()[0]
    if frozen("T35"): ok(ne == 3, "T35 three owner entries written (14-Nov x2, 4-Nov)")
    con3.row_factory = None
    cl = sc.days(con3, "2026-09-01", "9999-12-31")["rows"][-1]["close"]
    if frozen("T36"): ok(cl["drawer"] == 54900, "T36 the drawer reads Rs 549 after the clean-up (17-Oct's 504 left for his tap; round-offs 45)")
    o2 = subprocess.run([PY, "-B", os.path.join(_me, "oneoff_s869.py"), "--db", db3, "--fin", code, "--apply"], capture_output=True, text=True).stdout
    if CLEAN: ok("one-off APPLY: OK" in o and con3.execute("SELECT COUNT(*) FROM owner_day_entry").fetchone()[0] == 3, "T37c the one-off APPLY on the cleaned copy writes nothing twice")
    if frozen("T37"): ok("one-off APPLY: OK" in o2 and "already" in o2 and con3.execute("SELECT COUNT(*) FROM owner_day_entry").fetchone()[0] == 3,
       "T37 the one-off again: every step already done, nothing written twice")
    con3.row_factory = sqlite3.Row
    j = hc.drawer_why(con3)
    if frozen("T38"): ok(j["ok"] and [d["day"] for d in j["days"]] == ["17-Oct"] and j["rest"] == "45", "T38 drawer-why after the clean-up: only 17-Oct (504) left, the rest 45")
    con3.execute("UPDATE darpan_kal_day SET owner_decision='accept', state='explained' WHERE business_date='2026-10-17'")
    con3.commit()
    con3.row_factory = None
    cl = sc.days(con3, "2026-09-01", "9999-12-31")["rows"][-1]["close"]
    if frozen("T39"): ok(cl["drawer"] == 4500, "T39 his tap on 17-Oct (Accept) brings the drawer to Rs 45")
    # ---- 5b. the review's asks (S482 cold review): the key join, the not-yet-handed morning, a multi-day cover, darpan_kal's doors, a locked day
    con4, db4 = fresh("review.db")
    try:
        import returns_kinds
        hub = returns_kinds.hub(con4, "medical")
        hkeys = {r["key"] for m in hub.get("months", []) for r in m.get("rows", [])}      # needs[] / cant[] are keys into these rows (rhFind)
        v12b = sd.day_view(con4, "2026-11-12")
        pk = {x["key"] for x in v12b["returns"]["list"]}
        hk12 = {k for k in hkeys if k.startswith("2026-11-12|")}
        ok(hk12 and hk12 <= pk, "T42 every 12-Nov return the Returns card (cn-hub) carries is found by its key on the panel -- one check, two places (%d of %d; the rest read 'not on the Returns card')" % (len(hk12), len(pk)))
    except Exception as ex:                                    # noqa: BLE001
        ok(False, "T42 the Returns card's reader could not be read: %r" % (ex,))
    last = con4.execute("SELECT MAX(business_date) FROM darpan_kal_day WHERE unit='medical' AND handed_p IS NOT NULL").fetchone()[0]
    mid = con4.execute("SELECT landed_movement_id FROM darpan_kal_day WHERE business_date=?", (last,)).fetchone()[0]
    con4.execute("DELETE FROM cash_handover_cover WHERE handover_src='movement' AND handover_id=?", (mid,))
    con4.execute("DELETE FROM cash_movement WHERE id=?", (mid,))
    con4.execute("DELETE FROM darpan_kal_day WHERE business_date=?", (last,))
    con4.commit()
    w4 = hc.drawer_why(con4)
    ok(last not in [d["date"] for d in w4["days"]] and last in [d["date"] for d in w4["not_yet"]] and w4["waiting_p"] > 0,
       "T43 a filed day not yet handed over (%s) is 'not yet handed', never 'short'" % last)
    # a multi-day cover: the day before last's handover now pays for both days
    prev = con4.execute("SELECT MAX(d.business_date) FROM darpan_kal_day d WHERE d.unit='medical' AND d.handed_p IS NOT NULL "
                        "AND d.business_date < ? AND ABS(COALESCE(d.diff_p,0)) <= 5000 AND d.landed_movement_id IS NOT NULL", (last,)).fetchone()[0]
    pmid = con4.execute("SELECT landed_movement_id FROM darpan_kal_day WHERE business_date=?", (prev,)).fetchone()[0]
    con4.row_factory = None
    cash_last = [x for x in sc.days(con4, "2026-09-01", "9999-12-31")["rows"] if x["date"] == last][0]["into_drawer_p"]
    con4.execute("UPDATE cash_movement SET amount_p=amount_p+? WHERE id=?", (cash_last, pmid))
    con4.execute("INSERT INTO cash_handover_cover (unit, handover_src, handover_id, covers_date, amount_p, note, entered_by, entered_at) VALUES "
                 "('medical','movement',?,?,?,'synth','t','2026-11-18T00:00:00')", (pmid, last, cash_last))
    con4.commit()
    con4.row_factory = sqlite3.Row
    w5 = hc.drawer_why(con4)
    ok(prev not in [d["date"] for d in w5["days"]] and last not in [d["date"] for d in w5["days"]] and last not in [d["date"] for d in w5["not_yet"]],
       "T44 a handover that paid for two days (%s covers %s): neither day is called short" % (prev, last))
    # darpan_kal's own doors as the page calls them
    try:
        import darpan_kal
        app2 = Flask("t2")
        con5, db5 = fresh("kal.db")
        CUR2 = {"user": "manoj", "roles": ["checker"]}

        def req2(*roles, **kw):
            if set(CUR2["roles"]) & set(roles):
                return dict(CUR2), None
            from flask import jsonify
            return None, (jsonify(ok=False, error="not_permitted"), 403)
        darpan_kal.init(app2, lambda: con5, req2)
        c2 = app2.test_client()
        con5.row_factory = None
        dr0 = sc.days(con5, "2026-09-01", "9999-12-31")["rows"][-1]["close"]["drawer"]
        con5.row_factory = sqlite3.Row
        d0 = con5.execute("SELECT business_date FROM darpan_kal_day WHERE handed_to='dr_bhawna' AND received_at IS NULL AND handed_p IS NOT NULL ORDER BY business_date LIMIT 1").fetchone()[0]
        j1 = c2.post("/finance/darpan/kal/api/received", json=dict(date=d0)).get_json()
        j2 = c2.post("/finance/darpan/kal/api/owner/decide", json=dict(date="2026-10-17", decision="accept", note="accepted on the Hub's Cash card")).get_json()
        CUR2["roles"] = ["maker"]
        j3 = c2.post("/finance/darpan/kal/api/owner/decide", json=dict(date="2026-10-17", decision="accept", note="x")).get_json()
        ok(j1.get("ok") and j2.get("ok") and j2.get("decision") == "accept" and not j3.get("ok"),
           "T45 darpan_kal's doors as the page calls them: received {date} ok; owner/decide accept ok; a maker refused")
        con5.row_factory = None
        cl5 = sc.days(con5, "2026-09-01", "9999-12-31")["rows"][-1]["close"]["drawer"]
        ok(cl5 == dr0 - 50400, "T46 after his Accept on 17-Oct the drawer is 504 less (%s -> %s)" % (dr0, cl5))
    except Exception as ex:                                    # noqa: BLE001
        ok(False, "T45 darpan_kal could not be mounted on the copy: %r" % (ex,))
    con6, db6 = fresh("locked.db")
    con6.execute("UPDATE day_entry SET status='locked' WHERE unit='medical' AND business_date='2026-10-14'")
    con6.commit()
    out6 = subprocess.run([PY, "-B", os.path.join(code, "day_resync.py"), "--db", db6, "--dry-run", "--no-reconcile"], capture_output=True, text=True).stdout
    wf6 = [l.split()[1] for l in out6.splitlines() if l.strip().startswith("WOULD_FIX")]
    ok("2026-10-14" not in wf6 and ("2026-10-09" in wf6 or CLEAN), "T47 pass 1 never touches a LOCKED day (14-Oct locked on the copy: left alone)")
    # ---- 6. the page
    h = open(os.path.join(code, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
    ok(h.count("KIT_S869_HUB_DAYS_CASH") == 1 and 'id="drawerWhy"' in h and "s869ReceivedAll" in h and "s869AfterDecide" in h and "retList(" in h and "itemTable(" in h,
       "T40 the Hub page carries the S869 script, the drawer-why box, the band, the decide hook, the returns and items renderers")
    ok("Received ✓ for Dr Bhawna" in h and "+ Add an entry" in h and "Accept (write off)" in h, "T41 the page's words: Received for Dr Bhawna, Add an entry, Accept (write off)")
except Exception as ex:                                        # noqa: BLE001
    import traceback
    traceback.print_exc()
    F += 1
    print("FAIL the proof raised: %r" % (ex,))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("SYNTH S869: %d PASS, %d FAIL" % (P, F))
sys.exit(0 if F == 0 else 1)
