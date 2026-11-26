#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s962.py -- S962_MORNING_MATCH's walk, on a made-up database (no real name, number or clinic ID).
    python3 walk_s962.py <code_dir>      code_dir holds the finance modules (the live set with the kit's TO files laid over them)
The last line is ALL PASS or N FAIL. CONTROL: the same walk on the FROM files must go red at T1 (a refund Docterz kept still
makes a false parchi card there -- F-1678)."""
import json
import os
import shutil
import sqlite3
import sys
import tempfile

CODE = os.path.abspath(sys.argv[1])
TMP = tempfile.mkdtemp(prefix="w962_")
DB = os.path.join(TMP, "finance.db")
D = "2026-11-25"                                              # yesterday (a Wednesday)
os.environ.update(SLIP_NOW="2026-11-26T10:00:00", EVCHK_LIVE_DB=os.path.join(TMP, "not_this.db"),
                  RING_PORTAL_DIR=os.path.join(TMP, "no_portal"), FINANCE_DB=DB, NID_CONSOLE_DB=os.path.join(TMP, "none.db"))
sys.path.insert(0, CODE)
sys.dont_write_bytecode = True

RES = []


def ok(key, cond, note=""):
    RES.append((key, bool(cond)))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", key, ("  -- " + str(note)[:300]) if (note and not cond) else ""))


from flask import Flask                                        # noqa: E402
import slip_log as SL                                          # noqa: E402
import slip_adjust as SA                                       # noqa: E402
import docterz_ingest as DI                                    # noqa: E402
import clinic_register as CR                                   # noqa: E402
import day_check as DC                                         # noqa: E402
import not_in_docterz as NID                                   # noqa: E402

NEW = hasattr(DC, "_s962_html")
CON = None
USER = {"user": "shavez", "roles": ["maker"]}
PUSHES = []


def db():
    return CON


def require(*roles, unit=None):
    return dict(USER), None


app = Flask("w962")
app.secret_key = "walk"
SL.init(app, db, require)
CR.init(app, db, require)
cli = app.test_client()


def fresh(alter=True):
    global CON
    if CON is not None:
        CON.close()
    for p in (DB,):
        if os.path.exists(p):
            os.remove(p)
    SL._schema_done = False
    SA._done = False
    DC._done = False
    NID._done = False
    CR._schema_done = False
    CON = sqlite3.connect(DB, timeout=10)
    CON.row_factory = sqlite3.Row
    SL.ensure(CON)
    CON.executescript(SA.SCHEMA)                               # the live table's shape BEFORE S962 (no refund_t)
    if alter:
        SA.ensure(CON)
    CON.executescript(DI.SCHEMA)
    CR._ensure(CON)
    DC.ensure(CON)
    for i in range(1, 6):                                      # the usual fee: Rs 600
        CON.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)",
                    ("2026-11-1%d" % i, "consult", 1, "x", "1", 60000, "Cash"))
    CON.commit()
    return CON


SN = {"opd": 100, "xp": 200, "line": 0}


def slip(series, cid, state="ok", name="", items=(), paid=""):
    SN[series] += 1
    cur = CON.execute("INSERT INTO slip (series, slip_no, day, clinic_id, name_seen, state, paid_mode, logged_by, logged_at) "
                      "VALUES (?,?,?,?,?,?,?,?,?)", (series, SN[series], D, cid, name, state, paid, "shavez", D + " 10:00:00"))
    sid = cur.lastrowid
    for j, (kind, nm, price) in enumerate(items):
        CON.execute("INSERT INTO slip_item (slip_id, kind, name, price_p, sort) VALUES (?,?,?,?,?)", (sid, kind, nm, price, j))
    CON.commit()
    return sid


def dline(section, cid, amount, mode="Cash", name="Test Person"):
    SN["line"] += 1
    CON.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)",
                (D, section, SN["line"], name, cid, amount, mode))
    CON.commit()


def exported():
    CON.execute("INSERT OR REPLACE INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, "
                "cons_amount_p, xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, free_revisits, "
                "free_concession, f93_phantom_rows, tender_json) VALUES (?,?,?,?,?,0,0,0,0,0,0,0,0,0,0,0,'{}')",
                (D, "x.csv", "walk", D + " 21:00:00", D + " 21:05:00"))
    CON.commit()


def register(**kw):
    cols = ", ".join(kw)
    CON.execute("INSERT OR REPLACE INTO clinic_register_day (business_date, %s) VALUES (?, %s)" % (cols, ",".join("?" * len(kw))),
                [D] + list(kw.values()))
    CON.commit()


def cancel(sid, cid, how, tender="", approve=False):
    if NEW:
        SA.add_cancel(CON, "shavez", sid, cid, how, note="walk", tender=tender)
    else:
        SA.add_cancel(CON, "shavez", sid, cid, how, note="walk")
    if approve:
        aid = CON.execute("SELECT id FROM slip_adjust WHERE slip_id=? AND kind='cancel'", (sid,)).fetchone()[0]
        SA.decide(CON, "manoj", aid, True)


def cards_of(chk, cid):
    return [c for c in chk["cards"] if str(c.get("cid") or "") == cid]


# ---------------------------------------------------------------- the day: every case on one made-up day
fresh()
exported()
slip("opd", "101", name="Test Person A")                                   # S1 clean
dline("consult", "101", 60000)
sb = slip("opd", "102", name="Test Person B")                              # S2 refund in cash, Docterz kept the bill (pending)
dline("consult", "102", 60000)
cancel(sb, "102", "returned", "cash")
sc = slip("xp", "103", name="Test Person C", items=(("xray", "Knee AP", 40000),), paid="upi")   # S3 refund UPI, Docterz cancelled too
cancel(sc, "103", "returned", "upi", approve=True)
se = slip("opd", "104", name="Test Person E")                              # S4 money never taken, Docterz kept the bill (approved)
dline("consult", "104", 60000)
cancel(se, "104", "never_taken", approve=True)
sf = slip("opd", "105", name="Test Person F")                              # S5 not in Docterz, the register holds it
sg = slip("xp", "106", name="Test Person G", items=(("proc", "Dressing", 30000),))   # S6 not in Docterz, not in the register
slip("xp", "107", name="Test Person H", items=(("xray", "Wrist AP", 50000),), paid="cash")   # S7 part-billed
dline("xray", "107", 30000)
# register (the book, written net of a refund, as the 23-Oct database shows): consult cash = 101 + 105 = 1200; X-ray cash 500 (H)
register(cons_cash_p=120000, xray_cash_p=50000)

chk = DC.check_day(CON, D)
ok("T0  the day is checked", chk.get("state") == "checked", chk.get("state"))
ok("T1  a refund Docterz kept makes no card (F-1678)", not cards_of(chk, "102"), [c["en"] for c in cards_of(chk, "102")])
ok("T2  a refund Docterz cancelled too makes no card", not cards_of(chk, "103") and not any(c["kind"] == "notfound" for c in chk["cards"]),
   [c["en"] for c in chk["cards"]])
ok("T3  money never taken, Docterz kept the bill: no card", not cards_of(chk, "104") and not any(c["key"].startswith("over:") for c in chk["cards"]),
   [c["en"] for c in chk["cards"]])
ok("T4  a slip not in Docterz makes no staff 'missing' card (F-1679)", not cards_of(chk, "105") and not cards_of(chk, "106"),
   [c["en"] for c in chk["cards"]])
bd = {b["cid"]: b for b in chk.get("backdate") or []}
ok("T5  both go to his back-date list (placed / not in the register)", bd.get("105", {}).get("placed") is True
   and bd.get("106", {}).get("placed") is False, bd)
ok("T6  the part-billed line stays a staff card", any(c["kind"] == "missing" and c.get("cid") == "107" for c in chk["cards"]),
   [c["en"] for c in chk["cards"]])
rf = {r["cid"]: r["word"] for r in chk.get("refunds") or []}
ok("T7  the three radds matched both ways", rf == {"102": "billed_ret", "103": "cancelled_ret", "104": "billed_nt"}, rf)
tp = chk.get("top") or {}
ok("T8  the day in one line adds up, nothing unexplained", tp.get("left") == 0 and tp.get("nid") == 60000 and tp.get("missing") == 20000
   and tp.get("back") == 120000 and tp.get("reg") == 170000 and tp.get("doc") == 210000, tp)
ok("T9  matched patients counted (101 only)", chk.get("matched_n") == 1, chk.get("matched_n"))
line = DC.summary_en(chk)
ok("T10 his console line", line.endswith(": 2 to back-date · staff fixing 1"), line)
ok("T11 not clean while the list holds rows", not DC.is_clean(chk))

def part_page():
    global USER
    # the page, as Shavez: the list, the two taps, no 'Added' on a back-date row
    r = cli.get("/finance/clinic/check/%s" % D)
    html = r.get_data(as_text=True)
    ok("T12 the page renders for Shavez", r.status_code == 200 and "Dr sahab ki back-date list" in html and "Dr sahab ko yaad dilayein" in html,
       r.status_code)
    ok("T13 Shavez sees 'Paise liye hi nahi' once (the row the register lacks) and one 'Added' (the part-billed line only)",
       html.count(">Paise liye hi nahi<") == 1 and html.count(">Add kar diya<") == 1, (html.count(">Paise liye hi nahi<"), html.count(">Add kar diya<")))
    DC.PUSHER = lambda who, title, body, url, tag: (PUSHES.append(dict(who=who, title=title, body=body, url=url, tag=tag)) or (1, ""))
    r = cli.post("/finance/clinic/check/%s/act" % D, data={"key": "remind", "act": "remind"})
    ok("T14 remind pushes once to his login, counts only", len(PUSHES) == 1 and PUSHES[0]["who"] == ["manoj"]
       and "2 slips not in Docterz" in PUSHES[0]["body"] and "Test Person" not in PUSHES[0]["body"] and PUSHES[0]["url"] == DC.NID_PAGE, PUSHES)
    r = cli.post("/finance/clinic/check/%s/act" % D, data={"key": "remind", "act": "remind"})
    ok("T15 a second remind within three hours is refused, nothing sent", len(PUSHES) == 1 and "err=" in r.headers.get("Location", ""),
       r.headers.get("Location"))
    r = cli.post("/finance/clinic/check/%s/act" % D, data={"key": bd["106"]["key"], "act": "nidfree", "slip": str(sg), "kind": "proc"})
    chk2 = DC.check_day(CON, D)
    ok("T16 'Paise liye hi nahi' takes the row off, named as Shavez's", "106" not in {b["cid"] for b in chk2["backdate"]}
       and any("money never taken (Shavez)" in en for en, _hi in chk2["notes"]), (r.headers.get("Location"), chk2["notes"]))
    m = CON.execute("SELECT who, act FROM nid_mark WHERE slip_id=?", (sg,)).fetchone()
    ok("T17 the mark is his list's own ('free', by shavez)", m is not None and m["who"] == "shavez" and m["act"] == "free", dict(m) if m else None)
    r = cli.post("/finance/clinic/check/%s/act" % D, data={"key": "x", "act": "nidfree", "slip": str(sb), "kind": "opd"})
    ok("T18 'Paise liye hi nahi' on a slip not on the list is refused", "err=" in r.headers.get("Location", ""), r.headers.get("Location"))
    USER = {"user": "manoj", "roles": ["checker"]}
    r = cli.get("/finance/clinic/check/%s" % D)
    html = r.get_data(as_text=True)
    ok("T19 his page: English, his list link, no staff taps", r.status_code == 200 and "Your back-date list" in html and DC.NID_PAGE in html
       and "Dr sahab ko yaad dilayein" not in html, r.status_code)
    r = cli.post("/finance/clinic/check/%s/act" % D, data={"key": "remind", "act": "remind"})
    ok("T20 his own login cannot 'remind' himself", "err=" in r.headers.get("Location", ""), r.headers.get("Location"))
    USER = {"user": "shivani", "roles": ["maker"]}
    NID.mark(CON, "manoj", sf, "opd", "entered")
    chk3 = DC.check_day(CON, D)
    ok("T21 his 'Entered' answer keeps his name, the row leaves", "105" not in {b["cid"] for b in chk3["backdate"]}
       and any("by Dr Manoj" in en for en, _hi in chk3["notes"]), chk3["notes"])
    ok("T22 his line after both answers", DC.summary_en(chk3).endswith(": staff fixing 1"), DC.summary_en(chk3))



def part_desk():
    global USER
    # the desk: 'Fee lautai' with Cash / UPI, the tag at once; an old-shape table gains the column on the first radd
    fresh(alter=False)
    SN.update(opd=300, xp=400)
    s1 = slip("opd", "201", name="Test Person J")
    USER = {"user": "shavez", "roles": ["maker"]}
    r = cli.post("/finance/slips/radd", data={"slip_id": str(s1), "clinic_id": "201", "how": "returned_upi", "back": "list"})
    a = CON.execute("SELECT * FROM slip_adjust WHERE slip_id=?", (s1,)).fetchone()
    ok("T23 'UPI se lautaye' writes a returned radd with refund_t upi (column added on first use)",
       a is not None and a["cancel_how"] == "returned" and a["refund_t"] == "upi" and a["state"] == "pending", dict(a) if a else r.status_code)
    tag = SL._radd_form(CON, dict(CON.execute("SELECT * FROM slip WHERE id=?", (s1,)).fetchone()), "list")
    ok("T24 the slip shows the Refunded tag at once", "Refunded · UPI" in tag and "manzoori baaki" in tag, tag)
    s2 = slip("opd", "202")
    form = SL._radd_form(CON, dict(CON.execute("SELECT * FROM slip WHERE id=?", (s2,)).fetchone()), "list")
    ok("T25 the radd form asks Cash / UPI / never taken", all(x in form for x in ("returned_cash", "returned_upi", "never_taken")), form)
    r = cli.post("/finance/slips/radd", data={"slip_id": str(s2), "clinic_id": "202", "how": "never_taken", "back": "list"})
    a2 = CON.execute("SELECT * FROM slip_adjust WHERE slip_id=?", (s2,)).fetchone()
    ok("T26 'Paise liye hi nahi' as before (no tender)", a2 is not None and a2["cancel_how"] == "never_taken" and (a2["refund_t"] or "") == "",
       dict(a2) if a2 else None)
    try:
        SA.add_cancel(CON, "shavez", slip("opd", "203"), "203", "returned", tender="card")
        bad = False
    except SA.AdjustError:
        bad = True
    ok("T27 a refund tender other than cash / UPI is refused", bad)
    s4 = slip("opd", "204")
    r = cli.post("/finance/slips/radd", data={"slip_id": str(s4), "clinic_id": "204", "how": "returned", "back": "list"})
    a4 = CON.execute("SELECT * FROM slip_adjust WHERE slip_id=?", (s4,)).fetchone()
    ok("T28 an old form's plain 'returned' still works (tender unknown)", a4 is not None and a4["cancel_how"] == "returned", dict(a4) if a4 else None)



def part_clean():
    # a clean day reads 'all matched'; the push is refused away from the live database
    fresh()
    SN.update(opd=500, xp=600, line=0)
    exported()
    slip("opd", "301")
    dline("consult", "301", 60000)
    register(cons_cash_p=60000)
    chk = DC.check_day(CON, D)
    ok("T29 a clean day: 'all matched' and clean", DC.summary_en(chk).endswith(": all matched") and DC.is_clean(chk), DC.summary_en(chk))
    DC.PUSHER = None
    sent, why = DC._s962_push(CON, ["manoj"], "t", "b", "/x", "t")
    ok("T30 no push from a database that is not the live one (A-D147)", sent == 0 and why == "not the live database", (sent, why))



def part_cases():
    # cold review case A: a bill paid two ways (Cash 600 + Online 400) whose X-ray part was refunded; the consultation lives on
    fresh()
    SN.update(opd=700, xp=800, line=0)
    exported()
    slip("opd", "401")
    sx = slip("xp", "401", items=(("xray", "Knee AP", 40000),))
    cancel(sx, "401", "returned", "upi", approve=True)
    dline("consult", "401", 60000, mode="Split Payment")
    dline("xray", "401", 40000, mode="Split Payment")
    for t, a in (("Cash", 60000), ("Online Payment", 40000)):
        CON.execute("INSERT INTO clinic_day_tender (business_date, clinic_id, invoice_no, tender, amount_p) VALUES (?,?,?,?,?)", (D, "401", "i1", t, a))
    CON.commit()
    register(cons_cash_p=60000)
    chk = DC.check_day(CON, D)
    ok("T31 a refund on a bill paid two ways: no card, nothing unexplained", not chk["cards"] and (chk.get("top") or {}).get("left") == 0,
       ([c["en"] for c in chk["cards"]], chk.get("top")))
    # cold review case B: two X-ray parchis of one ID at the same amount, one refunded and cancelled in Docterz too
    fresh()
    SN.update(opd=900, xp=950, line=0)
    exported()
    slip("xp", "402", items=(("xray", "Knee AP", 40000),))
    sy = slip("xp", "402", items=(("xray", "Knee AP", 40000),))
    cancel(sy, "402", "returned", "cash", approve=True)
    dline("xray", "402", 40000)
    register(xray_cash_p=40000)
    chk = DC.check_day(CON, D)
    rf = [r["word"] for r in chk.get("refunds") or []]
    ok("T32 two parchis of one ID, one refunded and cancelled too: no back-date row, 'cancelled . refunded'",
       not chk.get("backdate") and rf == ["cancelled_ret"] and not chk["cards"] and chk["top"]["left"] == 0,
       (chk.get("backdate"), rf, [c["en"] for c in chk["cards"]]))
    # a failed push never blocks the next reminder for three hours
    fresh()
    SN.update(opd=980, xp=990, line=0)
    exported()
    slip("opd", "403")
    slip("opd", "404")
    dline("consult", "404", 60000)
    register(cons_cash_p=120000)
    global USER
    USER = {"user": "shavez", "roles": ["maker"]}
    DC.PUSHER = lambda *a: (0, "no device")
    cli.post("/finance/clinic/check/%s/act" % D, data={"key": "remind", "act": "remind"})
    DC.PUSHER = lambda who, title, body, url, tag: (PUSHES.append(dict(who=who, body=body)) or (1, ""))
    n0 = len(PUSHES)
    cli.post("/finance/clinic/check/%s/act" % D, data={"key": "remind", "act": "remind"})
    ok("T33 a reminder that did not send does not block the next", len(PUSHES) == n0 + 1 and len(DC.check_day(CON, D)["backdate"]) == 1,
       (n0, len(PUSHES)))
    USER = {"user": "bhawna", "roles": ["checker"]}
    r = cli.post("/finance/clinic/check/%s/act" % D, data={"key": "remind", "act": "remind"})
    ok("T34 a checker login that is not named staff cannot tap", "err=" in r.headers.get("Location", ""), r.headers.get("Location"))
    # second look case A: Docterz's clinical report knows the visit (no bill) -- not on his list, so the staff card stays
    fresh()
    SN.update(opd=1100, xp=1200, line=0)
    exported()
    CON.execute("CREATE TABLE IF NOT EXISTS dx_visit (visit_date TEXT, clinic_id TEXT)")
    CON.execute("INSERT INTO dx_visit VALUES (?,?)", (D + " 11:00:00", "501"))
    slip("opd", "501")
    slip("opd", "502")
    dline("consult", "502", 60000)
    register(cons_cash_p=60000)
    chk = DC.check_day(CON, D)
    ok("T35 a visit Docterz's clinical report knows is never a back-date row nobody can clear",
       not chk["backdate"] and any(c["kind"] == "notbilled" and c.get("cid") == "501" for c in chk["cards"]),
       (chk["backdate"], [c["kind"] for c in chk["cards"]]))
    # second look case B: a bill paid cash 500 + UPI 500, its X-ray part (400) refunded by UPI; the register cash 500 / UPI 100
    fresh()
    SN.update(opd=1300, xp=1400, line=0)
    exported()
    slip("opd", "601")
    sx = slip("xp", "601", items=(("xray", "Knee AP", 40000),))
    cancel(sx, "601", "returned", "upi", approve=True)
    dline("consult", "601", 60000, mode="Split Payment")
    dline("xray", "601", 40000, mode="Split Payment")
    for t, a in (("Cash", 50000), ("Online Payment", 50000)):
        CON.execute("INSERT INTO clinic_day_tender (business_date, clinic_id, invoice_no, tender, amount_p) VALUES (?,?,?,?,?)", (D, "601", "i2", t, a))
    CON.commit()
    register(cons_cash_p=50000, cons_upi_p=10000)
    chk = DC.check_day(CON, D)
    ok("T36 a UPI refund on a bill paid two ways comes off the UPI leg: no card", not chk["cards"] and chk["top"]["left"] == 0,
       ([c["en"] for c in chk["cards"]], chk["top"]))
    # re-look: two lines of one X-ray slip not in Docterz, the register holding room for one -- one row, no 'never taken' tap
    fresh()
    SN.update(opd=1500, xp=1600, line=0)
    exported()
    slip("opd", "701")
    dline("consult", "701", 60000)
    s2 = slip("xp", "702", items=(("xray", "Knee AP", 40000), ("xray", "Knee Lat", 30000)))
    register(cons_cash_p=60000, xray_cash_p=40000)
    chk = DC.check_day(CON, D)
    b = chk["backdate"]
    ok("T37 two lines of one slip's kind make one back-date row, in the register", len(b) == 1 and b[0]["amount"] == 70000 and b[0]["placed"],
       [(x["amount"], x["placed"]) for x in b])
    USER = {"user": "shavez", "roles": ["maker"]}
    r = cli.post("/finance/clinic/check/%s/act" % D, data={"key": "x", "act": "nidfree", "slip": str(s2), "kind": "xray"})
    ok("T38 'never taken' on a row the register holds is refused at the door", "err=" in r.headers.get("Location", "")
       and (CON.execute("SELECT 1 FROM sqlite_master WHERE name='nid_mark'").fetchone() is None
            or CON.execute("SELECT COUNT(*) FROM nid_mark").fetchone()[0] == 0), r.headers.get("Location"))


for _fn in (part_page, part_desk, part_clean, part_cases):
    try:
        _fn()
    except Exception as _ex:                                   # noqa: BLE001 -- the control may lack the new names
        ok("TERR %s" % _fn.__name__, False, repr(_ex))

shutil.rmtree(TMP, ignore_errors=True)
n_fail = sum(1 for _k, v in RES if not v)
print("ALL PASS" if not n_fail else "%d FAIL" % n_fail)
sys.exit(0 if not n_fail else 1)
