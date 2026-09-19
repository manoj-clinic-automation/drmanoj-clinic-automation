#!/usr/bin/env python3
"""walk_s324.py -- the live-shape walk of the slip tile: THE REAL finance_app.py (patched) over a
SCRATCH COPY of the real finance.db, every role at the front gate and through each screen, the way a
browser does it (relative-free forms, the exact action URLs the page prints, the 303s it follows).
Nothing live is touched: the caller passes a copy. Header identity is used ONLY here.
Usage: FINANCE_DB=<copy> FINANCE_ALLOW_HEADER_AUTH=1 SLIP_NOW=<iso> python3 walk_s324.py <app dir>
"""
import os
import re
import sqlite3
import sys

N = [0]


def check(name, cond, extra=""):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s %s" % (N[0], name, extra))
        sys.exit(1)


def main():
    sys.path.insert(0, sys.argv[1])
    os.chdir(sys.argv[1])
    assert os.environ.get("FINANCE_ALLOW_HEADER_AUTH") == "1"
    dbp = os.environ["FINANCE_DB"]
    assert "walk" in dbp or "scratch" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
    day = os.environ["SLIP_NOW"][:10]
    os.environ["FINANCE_CRON_TOKEN"] = "walk-token-s330"          # a walk-only token; the box's own is never read
    import finance_app as fa
    check("slip_log mounted", "slip_log" in fa.app.blueprints)
    check("petty_book still mounted", "petty_book" in fa.app.blueprints)
    check("owner_sheets still mounted", "owner_sheets" in fa.app.blueprints)
    c = fa.app.test_client()
    H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}          # noqa: E731

    def get(u, p):
        return c.get(p, headers=H(u))

    def post(u, p, d):
        return c.post(p, data=d, headers=H(u))

    def page(u, p="/finance/slips?s=all"):
        r = get(u, p)
        return r.status_code, r.get_data(as_text=True)

    def form_actions(t):
        return set(re.findall(r'action="([^"]+)"', t))

    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    # ---- gate
    check("stranger refused", get("stranger", "/finance/slips").status_code in (302, 403))
    check("darpan (no slips row) refused", get("darpan", "/finance/slips").status_code in (302, 403))
    check("amir refused", get("amir", "/finance/slips").status_code in (302, 403))
    check("bhati still refused clinic pages", get("bhati", "/finance/clinic/day").status_code in (302, 403))
    check("awdhesh refused clinic pages", get("awdhesh", "/finance/clinic/day").status_code in (302, 403))
    for u in ("shavez", "alisha", "shivani", "bhati", "awdhesh"):
        s, t = page(u)
        check("%s opens the tile" % u, s == 200, str(s))
    check("manoj lands on the report", get("manoj", "/finance/slips").status_code == 302)
    s, t = page("manoj", "/finance/slips?tile=1")
    check("manoj can open the tile", s == 200)
    check("manoj cannot save (checker, not maker)", post("manoj", "/finance/slips/save", {"series": "opd"}).status_code == 403)
    # ---- the page shape: back button first, one open section, the top one
    s, t = page("shavez")
    check("Back to portal at the top", t.find('href="/portal"') < t.find("<details"), "")
    check("exactly one open section", len(re.findall(r'<details class="sec"[^>]* open', t)) == 1)
    check("the open one is OPD for the chamber", re.search(r'<details class="sec" open name="sec" id="opd"', t) is not None)
    s, ta = page("awdhesh")
    check("the room is on top and open for awdhesh", re.search(r'<details class="sec" open name="sec" id="room"', ta) is not None)
    check("first use asks for today's first number", "Pehli baar" in t)
    # every action the page prints is a route the app answers (F-544: walk the page's own buttons)
    for a in form_actions(t):
        check("the page's form action %s is absolute" % a, a.startswith("/finance/slips/"))
    # ---- books
    r = post("shavez", "/finance/slips/book", {"series": "opd", "first_no": "19201", "last_no": "19600", "start_no": "19373", "sec": "opd"})
    check("opd book set", r.status_code == 303)
    r = post("shavez", "/finance/slips/book", {"series": "xp", "first_no": "1001", "last_no": "1400", "start_no": "1137", "sec": "xp"})
    check("xp book set", r.status_code == 303)
    r = post("shavez", "/finance/slips/book", {"series": "xp", "first_no": "1001", "last_no": "1400", "start_no": "999"})
    check("a start outside the book refused", "err=" in r.headers.get("Location", ""))
    s, t = page("shavez")
    check("OPD prompts 19373", 'value="19373"' in t)
    check("X-ray/Proc prompts 1137", 'value="1137"' in t)
    for a in form_actions(t):
        check("action %s absolute" % a, a.startswith("/finance/slips/"))
    # ---- the patient master
    known = con.execute("SELECT clinic_id, name FROM patient_ref WHERE clinic_id GLOB '[0-9]*' AND name<>'' "
                        "AND (merged_into IS NULL OR merged_into='') ORDER BY id DESC LIMIT 1").fetchone()
    hi = con.execute("SELECT MAX(CAST(clinic_id AS INTEGER)) FROM patient_ref WHERE clinic_id GLOB '[0-9]*'").fetchone()[0]
    j = get("shavez", "/finance/slips/api/patient?id=%s" % known["clinic_id"]).get_json()
    check("a known ID autofills", j["ok"] and j["known"] and j["name"] == known["name"])
    gap_id = con.execute("WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<?) SELECT x FROM n "
                         "WHERE CAST(x AS TEXT) NOT IN (SELECT clinic_id FROM patient_ref) AND CAST(x AS TEXT) NOT IN "
                         "(SELECT clinic_id FROM clinic_day_line) LIMIT 1", (hi,)).fetchone()[0]
    j = get("shavez", "/finance/slips/api/patient?id=%d" % gap_id).get_json()
    check("S325: an old ID missing from the master is OLD, not new", j["ok"] and not j["known"] and j["old"])
    ceil = 0
    for q in ("SELECT MAX(CAST(clinic_id AS INTEGER)) FROM clinic_day_line WHERE clinic_id GLOB '[0-9]*' AND business_date<?",
              "SELECT MAX(CAST(clinic_id AS INTEGER)) FROM patient_visit WHERE clinic_id GLOB '[0-9]*' AND visit_date<?"):
        v = con.execute(q, (day,)).fetchone()[0]
        ceil = max(ceil, int(v or 0))
    con.execute("INSERT OR IGNORE INTO patient_ref (clinic_id, name) VALUES (?, 'Stray Ahead')", (str(ceil + 40),))
    con.commit()
    fresh = next(x for x in range(ceil + 1, ceil + 40)
                 if not con.execute("SELECT 1 FROM patient_ref WHERE clinic_id=?", (str(x),)).fetchone())
    j = get("shavez", "/finance/slips/api/patient?id=%d" % fresh).get_json()
    check("S326: the next ID after yesterday's highest is NAYA despite a stray master row ahead", j["ok"] and not j["known"] and not j["old"], str(j))
    j = get("shavez", "/finance/slips/api/patient?id=%d" % (ceil + 40)).get_json()
    check("S326: a master row with a name but ahead of the series is known AND new", j["known"] and j["new"], str(j))
    j = get("shavez", "/finance/slips/api/patient?id=%d" % (hi + 1)).get_json()
    check("the next ID is new, not far", j["ok"] and not j["known"] and not j["far"])
    j = get("shavez", "/finance/slips/api/patient?id=%d" % (hi + 500)).get_json()
    check("an ID far ahead is flagged", j["far"])
    check("a phone number never comes back", "mobile" not in j)
    # ---- OPD
    def save(u, d):
        r = post(u, "/finance/slips/save", d)
        loc = r.headers.get("Location", "")
        return r.status_code, loc
    st, loc = save("shavez", {"series": "opd", "slip_no": "19373", "clinic_id": known["clinic_id"]})
    check("OPD 19373 saved", st == 303 and "ok=" in loc, loc)
    row = con.execute("SELECT * FROM slip WHERE series='opd' AND slip_no=19373").fetchone()
    check("its name came from the master", row["name_seen"] == known["name"] and row["is_new"] == 0 and row["day"] == day)
    st, loc = save("alisha", {"series": "opd", "slip_no": "19373", "clinic_id": known["clinic_id"]})
    check("the same number twice is refused", "err=" in loc)
    st, loc = save("shavez", {"series": "opd", "slip_no": "19376", "clinic_id": str(hi + 1)})
    check("a jump saves and names the gap", "ok=" in loc and "19374" in loc)
    miss = [r["slip_no"] for r in con.execute("SELECT slip_no FROM slip WHERE series='opd' AND state='missing' ORDER BY slip_no")]
    check("19374 and 19375 held as missing", miss == [19374, 19375], str(miss))
    row = con.execute("SELECT * FROM slip WHERE series='opd' AND slip_no=19376").fetchone()
    check("a new ID is saved as new today", row["is_new"] == 1 and row["name_seen"] == "")
    st, loc = save("shavez", {"series": "xp", "slip_no": "1399", "clinic_id": str(fresh), "xray0": str(con.execute("SELECT id FROM owner_service WHERE kind='xray' AND active=1 LIMIT 1").fetchone()[0]), "gap_ok": "1"})
    check("S326: a fresh ID saves as NEW", con.execute("SELECT is_new FROM slip WHERE series='xp' AND slip_no=1399").fetchone()[0] == 1)
    x99 = con.execute("SELECT id FROM slip WHERE series='xp' AND slip_no=1399").fetchone()[0]
    post("shavez", "/finance/slips/state/%d" % x99, {"act": "void"})
    st, loc = save("shavez", {"series": "opd", "slip_no": "19374", "clinic_id": str(gap_id)})
    check("S325: that old ID saves without the NEW mark", con.execute("SELECT is_new FROM slip WHERE series='opd' AND slip_no=19374").fetchone()[0] == 0)
    check("a missing number is filled later", "ok=" in loc)
    check("19374 is now a slip", con.execute("SELECT state FROM slip WHERE series='opd' AND slip_no=19374").fetchone()[0] == "ok")
    sid = con.execute("SELECT id FROM slip WHERE series='opd' AND slip_no=19375").fetchone()[0]
    r = post("shivani", "/finance/slips/state/%d" % sid, {"act": "cancelled"})
    check("a skipped number marked cancelled", con.execute("SELECT state FROM slip WHERE id=?", (sid,)).fetchone()[0] == "cancelled")
    st, loc = save("shavez", {"series": "opd", "slip_no": "19377", "clinic_id": str(hi + 500)})
    check("an ID far ahead is refused first", "err=" in loc)
    st, loc = save("shavez", {"series": "opd", "slip_no": "19377", "clinic_id": str(hi + 500), "id_ok": "1"})
    check("...and accepted once confirmed", "ok=" in loc)
    st, loc = save("shavez", {"series": "opd", "slip_no": "19378", "noid": "1", "no_id_name": "Attendant"})
    check("a slip with no clinic ID, by name", "ok=" in loc)
    st, loc = save("shavez", {"series": "opd", "slip_no": "19420", "clinic_id": known["clinic_id"]})
    check("a jump of 41 asks first", "err=" in loc)
    st, loc = save("shavez", {"series": "opd", "slip_no": "25000", "clinic_id": known["clinic_id"]})
    check("a number outside the book refused", "err=" in loc)
    st, loc = save("shavez", {"series": "opd", "slip_no": "19379"})
    check("no ID and no name refused", "err=" in loc)
    # ---- X-ray / Proc
    svc = [dict(r) for r in con.execute("SELECT id, kind, name FROM owner_service WHERE active=1 ORDER BY kind, id")]
    xr = [s for s in svc if s["kind"] == "xray"]
    pr = [s for s in svc if s["kind"] == "proc"]
    check("the rate page has X-ray and procedure lines", xr and pr)
    svc_before = [tuple(r) for r in con.execute("SELECT * FROM owner_service WHERE id<>? ORDER BY id", (xr[0]["id"],))]
    con.execute("UPDATE owner_service SET price_p=50000 WHERE id=?", (xr[0]["id"],))
    con.commit()
    s, t = page("shavez")
    check("today's OPD patients offered in the X-ray form", 'class="pick"' in t and known["clinic_id"] in t)
    check("X-ray and procedure are separate lists", 'name="xray0"' in t and 'name="proc0"' in t and 'name="proc2"' in t and 'name="xray5"' in t)
    check("both lists end in Other", t.count('<option value="other">Other</option>') >= 9)
    st, loc = save("shavez", {"series": "xp", "slip_no": "1137", "pick": known["clinic_id"],
                              "xray0": str(xr[0]["id"]), "xray0_side": "R", "xray1": str(xr[0]["id"]), "xray1_side": "L",
                              "proc0": "other", "proc0_other": "Plaster removal"})
    check("X-ray/Proc 1137 saved with 3 items", "ok=" in loc, loc)
    its = con.execute("SELECT i.* FROM slip_item i JOIN slip s ON s.id=i.slip_id WHERE s.series='xp' AND s.slip_no=1137 ORDER BY sort").fetchall()
    check("items stored with sides and the price", len(its) == 3 and its[0]["side"] == "R" and its[0]["price_p"] == 50000
          and its[2]["name"] == "Other: Plaster removal")
    st, loc = save("shavez", {"series": "xp", "slip_no": "1138", "pick": known["clinic_id"]})
    check("an X-ray/Proc slip with nothing chosen refused", "err=" in loc)
    st, loc = save("bhati", {"series": "xp", "slip_no": "1138", "noid": "1", "no_id_name": "Relative", "xray0": str(xr[1]["id"])})
    check("bhati logs a no-ID X-ray (the attendant case)", "ok=" in loc)
    st, loc = save("shavez", {"series": "xp", "slip_no": "1139", "clinic_id": known["clinic_id"],
                              "proc0": str(pr[0]["id"]), "proc1": str(pr[1]["id"]), "proc2": str(pr[2]["id"])})
    check("three procedures on one slip", "ok=" in loc)
    st, loc = save("shavez", {"series": "xp", "slip_no": "1140", "clinic_id": known["clinic_id"], "xray0": str(pr[0]["id"])})
    check("a procedure id in the X-ray list refused", "err=" in loc)
    # ---- the room
    x1 = con.execute("SELECT id FROM slip WHERE series='xp' AND slip_no=1137").fetchone()[0]
    s, t = page("awdhesh")
    check("the room lists 1137 with its buttons", "/finance/slips/room/%d" % x1 in t)
    check("S327: the room shows the slip's amount, read-only", '<span class="amt">\u20b91,000 + 1 rate nahi</span>' in t)
    check("S327: the book section is 'Start new book'", "Start new book" in t and "naya book shuru karein" in t)
    check("S327: a confirmed big jump still leaves every skipped number to be given a reason",
          con.execute("SELECT COUNT(*) FROM slip WHERE series='xp' AND state='missing'").fetchone()[0] > 200)
    post("awdhesh", "/finance/slips/room/%d" % x1, {"act": "upi"})
    post("awdhesh", "/finance/slips/room/%d" % x1, {"act": "done"})
    r = con.execute("SELECT paid_mode, paid_by, done_by FROM slip WHERE id=?", (x1,)).fetchone()
    check("paid UPI and done, by awdhesh", tuple(r) == ("upi", "awdhesh", "awdhesh"))
    post("awdhesh", "/finance/slips/room/%d" % x1, {"act": "unpaid"})
    check("a paid tick can be undone", con.execute("SELECT paid_mode FROM slip WHERE id=?", (x1,)).fetchone()[0] == "")
    post("awdhesh", "/finance/slips/room/%d" % x1, {"act": "cash"})
    s, t = page("awdhesh")
    check("the room badge counts what is open", re.search(r'id="room"><summary><span>X-ray room work</span><span class="badge">2 baaki', t) is not None)
    # ---- S328: the EMR upload list
    s, t = page("alisha", "/finance/slips/emr")
    check("S328: reception opens the upload list", s == 200 and "Upload ho gaya" in t)
    check("S328: back to portal on top", t.find('href="/portal"') < t.find("<details"))
    check("S328: slip 1137's X-rays are waiting", "parchi 1137" in t)
    check("S328: Docterz X-rays with no slip are listed too (the backlog)", "(Docterz)" in t)
    check("S328: exactly one day open", len(re.findall(r'<details class="sec" open', t)) == 1)
    check("S328: a stranger is refused", get("stranger", "/finance/slips/emr").status_code in (302, 403))
    xis = [r[0] for r in con.execute("SELECT id FROM slip_item WHERE slip_id=? AND kind='xray' ORDER BY sort", (x1,))]
    check("S329: slip 1137 carries two X-rays, so two upload lines", len(xis) == 2 and t.count("parchi 1137") == 2)
    k1 = "xi:%d" % xis[0]
    r = post("alisha", "/finance/slips/emr/mark", {"key": k1, "act": "done"})
    check("S328: marked uploaded", con.execute("SELECT uploaded_by FROM emr_upload WHERE key=?", (k1,)).fetchone()[0] == "alisha")
    s, t = page("alisha", "/finance/slips/emr")
    check("S329: one X-ray done, the other still pending", t.count("parchi 1137") == 1 and "Galti se" in t)
    check("S329: the upload screen goes back to the menu", 'href="/finance/slips">\u2190 Menu' in t)
    post("shivani", "/finance/slips/emr/mark", {"key": k1, "act": "undo"})
    check("S328: undo puts it back", con.execute("SELECT COUNT(*) FROM emr_upload WHERE key=?", (k1,)).fetchone()[0] == 0)
    r = post("alisha", "/finance/slips/emr/mark", {"key": "dz:2026-09-18:not-real", "act": "done"})
    check("S328: an unknown key writes nothing", con.execute("SELECT COUNT(*) FROM emr_upload WHERE key LIKE 'dz:2026-09-18:not%'").fetchone()[0] == 0)
    keys = re.findall(r'name="key" value="(dz:2026-09-18:[^"]+)"', page("alisha", "/finance/slips/emr")[1])
    check("S329: Docterz X-rays are one line per X-ray too", all(k.count(":") == 3 for k in keys))
    post("alisha", "/finance/slips/emr/mark", {"key": sorted(set(keys)), "act": "done"})
    check("S328: 'all of this day' marks the whole day", len(set(keys)) > 0 and con.execute(
        "SELECT COUNT(*) FROM emr_upload WHERE key LIKE 'dz:2026-09-18:%'").fetchone()[0] == len(set(keys)))
    check("S328: manoj cannot tick (checker)", post("manoj", "/finance/slips/emr/mark", {"key": k1, "act": "done"}).status_code == 403)
    # ---- S329: the menu
    s, t = page("shivani", "/finance/slips")
    check("S329: the tile opens a menu, no forms", s == 200 and 'class="menu"' in t and "<form" not in t)
    check("S329: reception sees the upload first", t.find("X-ray upload (Docterz)") < t.find("OPD parchi"))
    check("S329: the menu's back goes to the portal", 'href="/portal"' in t)
    check("S329: shavez gets the report in his menu", "/finance/slips/report" in page("shavez", "/finance/slips")[1])
    check("S329: shivani does not", "/finance/slips/report" not in t)
    s, t = page("awdhesh", "/finance/slips")
    check("S329: awdhesh sees the room first", t.find("X-ray room work") < t.find("OPD parchi"))
    s, t = page("shavez", "/finance/slips?s=opd")
    check("S329: one screen, open, back to the menu", t.count("<details") == 1 and 'href="/finance/slips">\u2190 Menu' in t)
    # ---- S330: blood tests
    import datetime as _d
    yday = (_d.date.fromisoformat(day) - _d.timedelta(days=1)).isoformat()
    s, t = page("shavez", "/finance/slips")
    check("S330: the menu has Blood test", "/finance/slips/blood" in t)
    s, t = page("shavez", "/finance/slips/blood")
    check("S330: the blood screen offers today's OPD", s == 200 and known["clinic_id"] in t and 'href="/finance/slips">\u2190 Menu' in t)
    r = post("shavez", "/finance/slips/blood", {"pick": known["clinic_id"]})
    check("S330: two taps log an order", con.execute("SELECT COUNT(*) FROM blood_order WHERE day=? AND clinic_id=? AND state='ok'",
                                                    (day, known["clinic_id"])).fetchone()[0] == 1)
    r = post("shavez", "/finance/slips/blood", {"pick": known["clinic_id"]})
    check("S330: the same patient twice a day is refused", "pehle se likha" in r.get_data(as_text=True))
    check("S330: manoj cannot order (checker)", post("manoj", "/finance/slips/blood", {"pick": "1"}).status_code == 403)
    s, t = page("alisha", "/finance/slips/emr")
    check("S330: today's order asks nothing today (never during OPD)", "Blood report nahi aaya" not in t)
    ids = [r[0] for r in con.execute("SELECT clinic_id FROM patient_ref WHERE clinic_id GLOB '[0-9]*' AND name<>'' "
                                     "AND (merged_into IS NULL OR merged_into='') ORDER BY id DESC LIMIT 3 OFFSET 5")]
    for cid in ids:
        con.execute("INSERT INTO blood_order(day, clinic_id, logged_by, logged_at) VALUES (?,?, 'walk', ?)", (yday, cid, yday + " 10:00:00"))
    con.commit()
    s, t = page("alisha", "/finance/slips/emr")
    check("S330: yesterday's orders with no report ask, at upload time", "Blood report nahi aaya" in t and t.count("Test nahi karaya") == 3)
    check("S330: still only one section open", len(re.findall(r'<details class="sec" open', t)) == 1)
    oid = lambda cid: con.execute("SELECT id FROM blood_order WHERE clinic_id=? AND day=?", (cid, yday)).fetchone()[0]
    post("alisha", "/finance/slips/blood/outcome", {"id": oid(ids[0]), "act": "not_tested"})
    post("alisha", "/finance/slips/blood/outcome", {"id": oid(ids[1]), "act": "lab_missed"})
    s, t = page("alisha", "/finance/slips/emr")
    check("S330: 'not tested' leaves the reception list", t.count("Test nahi karaya") == 1 and "lab ko email bhejne" in t)
    s, t = page("manoj", "/finance/slips/report/%s" % day)
    check("S330: the report names who never got tested", "never got tested" in t and "has not e-mailed" in t)
    r = c.post("/finance/slips/api/lab-report", json={"msg_id": "m1", "clinic_id": ids[1], "received_at": day + " 12:05:00"},
               headers={"X-Finance-Cron": "wrong"})
    check("S330: a wrong key is refused", r.status_code in (401, 302))
    for mid in ("m1", "m2"):                              # the lab re-sends: still one upload
        r = c.post("/finance/slips/api/lab-report", json={"msg_id": mid, "clinic_id": ids[1], "received_at": day + " 12:0%s:00" % mid[-1]},
                   headers={"X-Finance-Cron": "walk-token-s330"})
        check("S330: the mailbox push is taken (%s)" % mid, r.status_code == 200 and r.get_json()["ok"])
    s, t = page("alisha", "/finance/slips/emr")
    check("S330: the report closes the lab-missed order by itself", "lab ko email bhejne" not in t)
    lr = sorted(set(re.findall(r'name="key" value="(lr:[^"]+)"', t)))
    check("S330: one upload line for a re-sent report", len(lr) == 1 and "Blood report" in t)
    post("alisha", "/finance/slips/emr/mark", {"key": lr[0], "act": "done"})
    check("S330: the blood report marked uploaded, kind path",
          con.execute("SELECT kind FROM emr_upload WHERE key=?", (lr[0],)).fetchone()[0] == "path")
    # ---- corrections
    x3 = con.execute("SELECT id FROM slip WHERE series='xp' AND slip_no=1139").fetchone()[0]
    r = post("alisha", "/finance/slips/state/%d" % x3, {"act": "void"})
    check("someone else needs a reason to take a slip off", "err=" in r.headers.get("Location", ""))
    r = post("shavez", "/finance/slips/state/%d" % x3, {"act": "void"})
    check("the same person, same day, takes it off", con.execute("SELECT state FROM slip WHERE id=?", (x3,)).fetchone()[0] == "void")
    st, loc = save("shavez", {"series": "xp", "slip_no": "1139", "clinic_id": known["clinic_id"], "proc0": str(pr[0]["id"])})
    check("...and logs it again right", "ok=" in loc)
    # ---- the report, the 18-Sep shape (consultation 1600 carrying 2 X-rays of 500, no X-ray line)
    cid = known["clinic_id"]
    con.execute("DELETE FROM clinic_day_line WHERE business_date=?", (day,))
    con.execute("DELETE FROM clinic_day_revenue WHERE business_date=?", (day,))
    cols = [r[1] for r in con.execute("PRAGMA table_info(clinic_day_revenue)")]
    src = con.execute("SELECT * FROM clinic_day_revenue ORDER BY business_date DESC LIMIT 1").fetchone()
    vals = [day if k == "business_date" else (day + " 22:00:07" if k == "taken_at" else src[k]) for k in cols]
    con.execute("INSERT INTO clinic_day_revenue (%s) VALUES (%s)" % (",".join(cols), ",".join("?" * len(cols))), vals)
    con.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift, gateway_ref) "
                "VALUES (?, 'consult', 1, ?, ?, 150000, 'Cash', 'Morning', '')", (day, known["name"], cid))
    con.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift, gateway_ref) "
                "VALUES (?, 'consult', 2, 'Walk Newpatient', ?, 60000, 'Cash', 'Morning', '')", (day, str(hi + 1)))
    con.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift, gateway_ref) "
                "VALUES (?, 'consult', 3, 'Walk Noslip', '99999', 60000, 'Cash', 'Morning', '')", (day,))
    con.commit()
    s, t = page("manoj", "/finance/slips/report/%s" % day)
    check("report 200", s == 200)
    check("report: back to portal at the top", t.find('href="/portal"') < t.find("<details"))
    check("report: the X-ray money inside the consultation is named", "booked as consultation" in t, "")
    check("report: X-ray not in Docterz", "X-ray not in Docterz" in t)
    check("report: the new patient's name came from Docterz", "Walk Newpatient" in t)
    check("report: a Docterz line with no slip", "Docterz entries with no slip" in t and "Walk Noslip" in t)
    check("report: the no-ID slips go to a hand match", "no clinic ID" in t)
    check("report: the cancelled number shows as cancelled", ">cancelled<" in t)
    check("report: OPD and X-ray sections apart", "OPD — slip order" in t and "X-ray &amp; Procedures — slip order" in t)
    check("report: slip order", t.find(">19373<") < t.find(">19374<") < t.find(">19376<"))
    s, t = page("manoj", "/finance/slips/report/2026-09-18")
    check("report of a real Docterz day with no slips renders", s == 200 and "no slip logged" in t)
    s, t = page("manoj", "/finance/slips/report/2099-01-01")
    check("a day Docterz has not sent reads as waiting", "has not arrived yet" in t)
    check("a bad date is sent home", get("manoj", "/finance/slips/report/2026-13-45").status_code == 302)
    # ---- nothing outside its own tables was written
    check("the rate page untouched by the tile (every other line byte-equal)",
          [tuple(r) for r in con.execute("SELECT * FROM owner_service WHERE id<>? ORDER BY id", (xr[0]["id"],))] == svc_before)
    print("WALK OK %d checks" % N[0])


if __name__ == "__main__":
    main()
