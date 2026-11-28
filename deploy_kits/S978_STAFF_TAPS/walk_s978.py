#!/usr/bin/env python3
"""walk_s978.py -- kit S978 (K2b, the staff taps). Made-up data only (letters for IDs, no number of any patient), through the
real Flask routes. Usage: walk_s978.py FINANCE_DIR REAL_SCHEMA_DB [PORTAL_DIR]"""
import sys, os, sqlite3, shutil, tempfile, types, datetime as dt
FIN, SCHEMA_DB = sys.argv[1], sys.argv[2]
sys.path.insert(0, FIN)
os.environ.update({"EVCHK_LIVE_DB": "/nonexistent/live.db", "REGPUSH_SPAWN": "0", "DAYCHK_REVENUE": "1", "DAYCHK_TAPS": "1",
                   "RING_PORTAL_DIR": "/nonexistent/portal"})
NIDCALLS = []
stub = types.ModuleType("not_in_docterz")                 # his list, stubbed: the walk's IDs are letters (no patient number)
stub.rows = lambda con, a=None, b=None, cid=None: []
stub.MarkError = Exception
def _mark(con, who, sid, kind, act):
    NIDCALLS.append(("mark", who, sid, kind, act))
    if STUB_REFUSE[0]:
        raise Exception("Docterz already carries this one")
    return 1
stub.mark = _mark
stub.undo = lambda con, who, mid: NIDCALLS.append(("undo", who, mid))
stub.init = lambda *a, **k: None
STUB_REFUSE = [False]
sys.modules["not_in_docterz"] = stub
from flask import Flask
import day_check as dc, register_push as rp, clinic_register as CR, slip_log as SL, slip_adjust as SA
D = (dt.date.today() - dt.timedelta(days=1)).isoformat()
TMP = tempfile.mkdtemp(prefix="w978_")
PASS = FAIL = 0
def ok(name, cond, info=""):
    global PASS, FAIL
    if cond: PASS += 1; print("PASS", name)
    else: FAIL += 1; print("FAIL", name, str(info)[:300])
sch = sqlite3.connect(SCHEMA_DB)
DDL = [r[0] for r in sch.execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index') AND sql IS NOT NULL AND name NOT LIKE 'sqlite_%'")]
CON = [None]; USER = [{"user": "shavez", "roles": ["maker"]}]
app = Flask("w978"); app.config["TESTING"] = True
CR.init(app, lambda: CON[0], lambda *r, **k: (USER[0], None), None)
cl = app.test_client()
n_db = 0
def fresh(day=None):
    global n_db
    n_db += 1
    p = os.path.join(TMP, "w%d.db" % n_db)
    c = sqlite3.connect(p); c.row_factory = sqlite3.Row
    for s in DDL:
        try: c.execute(s)
        except sqlite3.Error: pass
    for dd in sorted({day or D, D}):
        c.execute("INSERT INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, "
                  "xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, free_revisits, free_concession, "
                  "f93_phantom_rows, tender_json) VALUES (?, 'f', 'i', 'm', ?, 0,0,0,0,0,0,0,0,0,0,0,'{}')", (dd, dd + " 20:00:00"))
    c.execute("DELETE FROM slip_book")
    c.execute("INSERT INTO slip_book (series, first_no, last_no, start_no) VALUES ('opd', 100, 199, 100), ('xp', 200, 299, 200)")
    c.execute("DELETE FROM owner_service")
    for k, nm, pr in (("xray", "Walk XA", 500), ("xray", "Walk XB", 500), ("xray", "Walk XC", 300), ("proc", "Walk PD", 100)):
        c.execute("INSERT INTO owner_service (kind, name, price_p, active, status) VALUES (?,?,?,1,'approved')", (k, nm, pr * 100))
    c.commit()
    for m in (dc, CR, SL, SA):
        for a in ("_done", "_schema_done"):
            if hasattr(m, a): setattr(m, a, False)
    CON[0] = c
    return c, p
SN = [0]
def line(c, sec, cid, amt, mode="Cash", day=None):
    SN[0] += 1
    c.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)",
              (day or D, sec, SN[0], "Walk Person " + cid, cid, amt * 100, mode))
def reg(c, day=None, **kw):
    cols = {k + "_p": v * 100 for k, v in kw.items()}
    c.execute("INSERT INTO clinic_register_day (business_date, %s) VALUES (?, %s)" % (", ".join(cols), ",".join("?" * len(cols))), (day or D, *cols.values()))
NO = {"opd": 100, "xp": 200}
def slip(c, series, cid, items=(), day=None):
    NO[series] += 1
    c.execute("INSERT INTO slip (series, slip_no, day, clinic_id, state, name_seen) VALUES (?,?,?,?,'ok',?)", (series, NO[series], day or D, cid, "Walk " + cid))
    sid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    for i, (kind, name, price) in enumerate(items):
        c.execute("INSERT INTO slip_item (slip_id, kind, name, side, price_p, sort, discount_p) VALUES (?,?,?,?,?,?,0)", (sid, kind, name, "", price * 100, i))
    return sid
def chk(c, day=None):
    c.commit(); return dc.check_day(c, day or D)
def card(ch, kind):
    return next((x for x in ch["cards"] if x["kind"] == kind), None)
def page(day=None):
    return cl.get("/finance/clinic/check/%s" % (day or D)).get_data(as_text=True)
def post(day=None, **form):
    r = cl.post("/finance/clinic/check/%s/act" % (day or D), data=form)
    return r.status_code, r.headers.get("Location", "")
def as_user(u, roles=("maker",)):
    USER[0] = {"user": u, "roles": list(roles)}
from urllib.parse import unquote

def base_nf(day=None):
    c, p = fresh(day)
    line(c, "consult", "WKA", 600, day=day); line(c, "consult", "WKB", 0, day=day)
    reg(c, day=day, cons_cash=1200); slip(c, "opd", "WKA", day=day)
    return c, p

# W1 -- the late OPD parchi from the nf: card (a patient Docterz holds at Rs 0)
as_user("shavez"); c, p = base_nf(); ch = chk(c); k = card(ch, "notfound")
ok("W1 nf card", k is not None and k["key"] == "nf:consult:60000" and [x[0] for x in k["cands"]] == ["WKB"], k and (k["key"], k.get("cands")))
ok("W1 the card carries its one cell", k is not None and k.get("cell") == ("consult", "cash"), k and k.get("cell"))
h = page()
ok("W1 the page offers the late parchi", "value='lateslip'" in h and "Kiska tha?" in h and "agla: 102" in h and "Consultation Rs 600" in h, h[:200])
ok("W1 ... the register one-tap and Pata nahi", "value='regfix'" in h and "Register galat likha — theek karein" in h and "value='dunno'" in h)
ok("W1 ... no K2a 'Found it' beside them", "value='found'" not in h)
for bad, why in (({"pick": "WKA"}, "not a candidate"), ({"svc": "zz"}, "a service not at the price"), ({"no": ""}, "no number"),
                 ({"no": "101"}, "a number already written"), ({"no": "150"}, "a number far past the next one (review M3)")):
    f = dict(key=k["key"], act="lateslip", pick="WKB", svc="opd", no="102"); f.update(bad)
    st, loc = post(**f)
    ok("W1 refused: %s" % why, "err=" in loc and c.execute("SELECT COUNT(*) FROM slip WHERE clinic_id='WKB'").fetchone()[0] == 0, unquote(loc))
NIDCALLS.clear()
st, loc = post(key=k["key"], act="lateslip", pick="WKB", svc="opd", no="102")
s = c.execute("SELECT * FROM slip WHERE clinic_id='WKB' AND state='ok'").fetchone()
ok("W1 the parchi is made by slip_log, dated that day", st == 303 and "ok=" in loc and s is not None and s["day"] == D and s["series"] == "opd"
   and s["slip_no"] == 102 and s["logged_by"] == "shavez", (st, unquote(loc), s and dict(s)))
t = c.execute("SELECT * FROM day_check_tick WHERE act='lateslip' AND state='live'").fetchone()
ok("W1 the late tick (pick = the slip)", t is not None and t["pick"] == str(s["id"]) and t["who"] == "shavez", t and dict(t))
ok("W1 kept outside Docterz on his list by the staff login", ("mark", "shavez", s["id"], "opd", "outside") in NIDCALLS, NIDCALLS)
ch2 = chk(c)
ok("W1 the day matches by itself", card(ch2, "notfound") is None and ch2["top"]["left"] == 0, (ch2["top"], [x["key"] for x in ch2["cards"]]))
c.execute("UPDATE day_check_tick SET state='undone' WHERE id=?", (t["id"],)); ch3 = chk(c)
ok("W1 CONTROL: without the late tick the Rs 0 patient's parchi explains nothing", card(ch3, "notfound") is not None, ch3["top"])
c.execute("UPDATE day_check_tick SET state='live' WHERE id=?", (t["id"],)); c.commit()
h = page()
ok("W1 'done from this check' with its Undo", "Parchi 102" in h and "value='undolate'" in h, h[-600:])
as_user("shivani"); st, loc = post(key="", act="undolate", tid=str(t["id"]))
ok("W1 another login cannot undo it", "err=" in loc and c.execute("SELECT state FROM slip WHERE id=?", (s["id"],)).fetchone()[0] == "ok", unquote(loc))
as_user("shavez"); st, loc = post(key="", act="undolate", tid=str(t["id"]))
ok("W1 Undo voids that parchi", "ok=" in loc and c.execute("SELECT state FROM slip WHERE id=?", (s["id"],)).fetchone()[0] == "void", unquote(loc))
ok("W1 ... and the line is back", card(chk(c), "notfound") is not None)
k2 = dict(k); k2["cands"] = [("WKA", "x"), ("WKB", "y")]
r = dc._s978_late(c, D, k2, {"pick": "WKA", "svc": "opd", "no": "103"}, "shavez", True)
ok("W1 refused: a patient already billed of that head", r[0] == "" and "already billed" in r[1], r)
OLD = (dt.date.today() - dt.timedelta(days=9)).isoformat()
c, p = base_nf(OLD); ko = card(chk(c, OLD), "notfound"); h = page(OLD)
ok("W1 an old day (9 days): no late parchi offered", ko is not None and "value='lateslip'" not in h)
st, loc = post(OLD, key=ko["key"], act="lateslip", pick="WKB", svc="opd", no="102")
ok("W1 ... and refused if posted", "err=" in loc and c.execute("SELECT COUNT(*) FROM slip WHERE clinic_id='WKB'").fetchone()[0] == 0, unquote(loc))

# W2 -- an X-ray: the price-filtered list (two at Rs 500, none chosen for them); his list refuses (Docterz holds the patient)
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "xray", "WKC", 0); reg(c, cons_cash=600, xray_cash=500); slip(c, "opd", "WKA")
k = card(chk(c), "notfound"); h = page()
xa = c.execute("SELECT id FROM owner_service WHERE name='Walk XA'").fetchone()[0]; xc = c.execute("SELECT id FROM owner_service WHERE name='Walk XC'").fetchone()[0]
ok("W2 nf X-ray card", k is not None and k["key"] == "nf:xray:50000" and [x[0] for x in k["cands"]] == ["WKC"], k and k["key"])
ok("W2 the list holds only the Rs 500 services, none pre-chosen", "Walk XA Rs 500" in h and "Walk XB Rs 500" in h and "Walk XC" not in h and " selected" not in h)
st, loc = post(key=k["key"], act="lateslip", pick="WKC", svc=str(xc), no="201")
ok("W2 refused: a Rs 300 service for a Rs 500 gap", "err=" in loc)
STUB_REFUSE[0] = True; NIDCALLS.clear()
st, loc = post(key=k["key"], act="lateslip", pick="WKC", svc=str(xa), no="201"); STUB_REFUSE[0] = False
it = c.execute("SELECT i.* FROM slip_item i JOIN slip s ON s.id=i.slip_id WHERE s.clinic_id='WKC' AND s.state='ok'").fetchone()
ok("W2 the X-ray parchi with its one line", "ok=" in loc and it is not None and it["kind"] == "xray" and it["price_p"] == 50000 and it["service_id"] == xa,
   (unquote(loc), it and dict(it)))
ok("W2 his list refused the mark: the parchi still stands", len(NIDCALLS) == 1)
ch = chk(c); ok("W2 the day matches", card(ch, "notfound") is None and ch["top"]["left"] == 0, ch["top"])
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "proc", "WKD", 0); reg(c, cons_cash=600, proc_cash=100); slip(c, "opd", "WKA")
h = page(); ok("W2 a list of one is chosen for them", "Walk PD Rs 100" in h and " selected" in h)

# W3 -- the register one-tap (nf:), the drawer guard, Undo
c, p = base_nf(); k = card(chk(c), "notfound")
st, loc = post(key=k["key"], act="regfix", field="cons_cash_p", was="1", now="60000")
ok("W3 refused: the page's figures are not the register's", "err=" in loc and CR.register_row(c, D)["cons_cash_p"] == 120000, unquote(loc))
st, loc = post(key=k["key"], act="regfix", field="cons_cash_p", was="120000", now="60000")
ok("W3 the register cell set", "ok=" in loc and CR.register_row(c, D)["cons_cash_p"] == 60000 and CR.register_row(c, D)["updated_by"] == "shavez", unquote(loc))
ch = chk(c); ok("W3 the day matches", card(ch, "notfound") is None and ch["top"]["left"] == 0, ch["top"])
t = c.execute("SELECT * FROM day_check_tick WHERE act='regfix' AND state='live'").fetchone()
ok("W3 the fix is kept with its before-value", t is not None and t["reason"] == "cons_cash_p" and t["pick"] == "120000>60000", t and dict(t))
h = page(); ok("W3 'done from this check' shows it", "Register consultation cash: Rs 1,200 → Rs 600" in h and "value='undoreg'" in h, h[-500:])
st, loc = post(key="", act="undoreg", tid=str(t["id"]))
ok("W3 Undo puts the audited before-value back", "ok=" in loc and CR.register_row(c, D)["cons_cash_p"] == 120000, unquote(loc))
ok("W3 ... the line is back", card(chk(c), "notfound") is not None)
c.execute("INSERT INTO clinic_drawer_day (business_date, counted_p, status) VALUES (?, 120000, 'counted')", (D,)); c.commit()
ok("W3 drawer guard: the count equals the register's cash -- no cash fix", "value='regfix'" not in page())
c.execute("UPDATE clinic_drawer_day SET counted_p=100000"); c.commit()
ok("W3 drawer guard: a count the fix would not meet -- no cash fix (review M1)", "value='regfix'" not in page())
c.execute("UPDATE clinic_drawer_day SET counted_p=60000"); c.commit()
ok("W3 drawer guard: the fix makes the register meet the count -- offered", "value='regfix'" in page())
c.execute("DELETE FROM clinic_drawer_day"); c.commit()
ok("W3 drawer guard: no count -- the fix is offered", "value='regfix'" in page())
k = card(chk(c), "notfound"); post(key=k["key"], act="regfix", field="cons_cash_p", was="120000", now="60000")
c.execute("UPDATE clinic_register_day SET cons_cash_p=120000"); c.commit()   # the register page saved again with the old figure
kb = card(chk(c), "notfound")
ok("W3 a gap that comes back after a fix is a fresh, unticked line (review M2)", kb is not None and not kb.get("tick"), kb and kb.get("tick"))
ok("W3 ... and the fix is named to him", any(x.startswith("rf:cons_cash_p:") for x in rp.owner_lines(chk(c))), rp.owner_lines(chk(c)))
c, p = base_nf(); k = card(chk(c), "notfound")
post(key=k["key"], act="regfix", field="cons_cash_p", was="120000", now="60000")
c.execute("INSERT INTO clinic_drawer_day (business_date, counted_p, status) VALUES (?, 60000, 'counted')", (D,)); c.commit()
t3 = c.execute("SELECT id FROM day_check_tick WHERE act='regfix' AND state='live'").fetchone()[0]
st, loc = post(key="", act="undoreg", tid=str(t3))
ok("W3 an Undo that would make a counted drawer disagree is refused (second look S1)", "err=" in loc and CR.register_row(c, D)["cons_cash_p"] == 60000, unquote(loc))
c.execute("DELETE FROM clinic_drawer_day"); c.commit()
st, loc = post(key="", act="undoreg", tid=str(t3))
ok("W3 ... with no count it goes back, and he is told the fix was undone", "ok=" in loc and any(x.endswith(":undone") for x in rp.owner_lines(chk(c))), (unquote(loc), list(rp.owner_lines(chk(c)))))
c, p = base_nf(OLD); ko = card(chk(c, OLD), "notfound")
ok("W3 no register fix on a day older than 7 (review S2)", ko is not None and "value='regfix'" not in page(OLD))
c, p = fresh(); line(c, "consult", "WKA", 600, "UPI"); line(c, "consult", "WKB", 0); reg(c, cons_upi=1200); slip(c, "opd", "WKA")
c.execute("INSERT INTO clinic_drawer_day (business_date, counted_p, status) VALUES (?, 0, 'counted')", (D,)); c.commit()
k = card(chk(c), "notfound"); h = page()
ok("W3 a UPI cell is offered whatever the drawer says", k and k.get("cell") == ("consult", "upi") and "value='regfix'" in h and "consultation UPI Rs 1,200 → " in h, k and k.get("cell"))

# W4 -- the less: card: register one-tap, Refund tha (cash), Pata nahi
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=600); slip(c, "opd", "WKA"); slip(c, "opd", "WKB")
k = card(chk(c), "less"); h = page()
ok("W4 less card with its cell", k is not None and k.get("cell") == ("consult", "cash"), k and (k["key"], k.get("cell")))
ok("W4 the page offers the fix, Paise nahi diye, Refund tha, Pata nahi",
   all(x in h for x in ("value='regfix'", "value='lessnp'", "value='lessref'", "Refund tha (cash)", "value='dunno'")))
st, loc = post(key=k["key"], act="lessref", pick="WKB")
a = c.execute("SELECT * FROM slip_adjust WHERE kind='cancel'").fetchone()
ok("W4 Refund tha: the radd, money returned, in cash, pending his approval", "ok=" in loc and a is not None and a["cancel_how"] == "returned"
   and a["refund_t"] == "cash" and a["state"] == "pending" and a["made_by"] == "shavez", (unquote(loc), a and dict(a)))
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=600); slip(c, "opd", "WKA"); slip(c, "opd", "WKB")
k = card(chk(c), "less"); st, loc = post(key=k["key"], act="regfix", field="cons_cash_p", was="60000", now="120000")
ch = chk(c); ok("W4 the register one-tap on less:", "ok=" in loc and CR.register_row(c, D)["cons_cash_p"] == 120000 and card(ch, "less") is None, unquote(loc))

# W5 -- Pata nahi: off the staff list, onto his push, once
OWN = []
dc.PUSHER = lambda who, title, body, url, tag: (OWN.append((tuple(who), title, body)) or (1, ""))
rp._send = lambda who, title, body, tag: ((1, 0, 0), "")
c, p = base_nf(); k = card(chk(c), "notfound"); rp.LIVE_DB = p
AT = dt.datetime.combine(dt.date.fromisoformat(D) + dt.timedelta(days=1), dt.time(9, 0))
rp.judge(c, D, push=True, at=AT, from_save=True); OWN.clear()
st, loc = post(key=k["key"], act="dunno")
k2 = card(chk(c), "notfound")
ok("W5 the dunno tick", "ok=" in loc and k2 is not None and (k2.get("tick") or {}).get("act") == "dunno", unquote(loc))
ok("W5 his line 'pn:'", "pn:nf:consult" in rp.owner_lines(chk(c)) and "Staff don't know" in rp.owner_lines(chk(c))["pn:nf:consult"][0], rp.owner_lines(chk(c)))
rp.judge(c, D, push=True, at=AT + dt.timedelta(minutes=5))
ok("W5 his push", len(OWN) == 1 and OWN[0][0] == ("manoj",) and "Staff don't know" in OWN[0][2], OWN)
rp.judge(c, D, push=True, at=AT + dt.timedelta(minutes=10))
ok("W5 never twice", len(OWN) == 1, OWN)
ok("W5 off the staff's own list", not any(x.startswith("nf:") for x in rp.open_lines(chk(c))), rp.open_lines(chk(c)))
h = page(); ok("W5 the card says it went to him", "Pata nahi — Dr sahab ko bheja" in h and "Dr sahab dekhenge" in h)
st, loc = post(key=k["key"], act="undo")
ok("W5 Undo takes it back", "pn:nf:consult" not in rp.owner_lines(chk(c)))
ok("W5 CONTROL: an un-ticked nf: line is no line of his", not any(x.startswith("pn:") for x in rp.owner_lines(chk(c))))

c, p = base_nf(); k = card(chk(c), "notfound"); rp.LIVE_DB = p
rp.judge(c, D, push=True, at=AT, from_save=True); OWN.clear()
post(key=k["key"], act="regfix", field="cons_cash_p", was="120000", now="60000")
rp.judge(c, D, push=True, at=AT + dt.timedelta(minutes=5))
ok("W5 a register fix reaches him once, named as a fix (review S6)", len(OWN) == 1 and "corrected from the day check" in OWN[0][1] and "Shavez" in OWN[0][2], OWN)
rp.judge(c, D, push=True, at=AT + dt.timedelta(minutes=10)); ok("W5 ... never twice", len(OWN) == 1, OWN)

# W6 -- Sab ho gaya (the S970 morning, DAYCHK_REVENUE=0): the per-card ticks in one tap
os.environ["DAYCHK_REVENUE"] = "0"
c, p = fresh(); line(c, "consult", "WKA", 600, "Cash"); reg(c, cons_upi=600); slip(c, "opd", "WKA")
ch = chk(c); h = page()
ok("W6 a mode card and the one-tap button", card(ch, "mode") is not None and "Sab ho gaya (1)" in h, [x["kind"] for x in ch["cards"]])
st, loc = post(key="", act="saball", keys="none:shown")
ok("W6 a line the page did not show is not ticked (review S4)", card(chk(c), "mode") is not None and not card(chk(c), "mode").get("tick"))
st, loc = post(key="", act="saball", keys=card(chk(c), "mode")["key"])
km = card(chk(c), "mode")
ok("W6 the existing tick written (changed)", "ok=" in loc and km is not None and (km.get("tick") or {}).get("act") == "changed", (unquote(loc), km and km.get("tick")))
ok("W6 the button goes once nothing is left", "Sab ho gaya" not in page())
os.environ["DAYCHK_REVENUE"] = "1"

# W7 -- DAYCHK_TAPS=0: the K2a cards exactly as they were
os.environ["DAYCHK_TAPS"] = "0"
c, p = base_nf(); k = card(chk(c), "notfound"); h = page()
ok("W7 taps off: none of the new buttons", all(x not in h for x in ("value='lateslip'", "value='dunno'", "value='regfix'")) and "value='found'" in h)
st, loc = post(key=k["key"], act="lateslip", pick="WKB", svc="opd", no="102")
ok("W7 taps off: a posted late parchi is refused", "err=" in loc and c.execute("SELECT COUNT(*) FROM slip WHERE clinic_id='WKB'").fetchone()[0] == 0)
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=600); slip(c, "opd", "WKA"); slip(c, "opd", "WKB")
h = page(); ok("W7 taps off: less as K2a left it", "value='lessref'" not in h and "value='lessnp'" in h and "Register galat tha" in h)
os.environ["DAYCHK_TAPS"] = "1"

# W8 -- who may tap
c, p = base_nf(); k = card(chk(c), "notfound")
as_user("bhati"); st, loc = post(key=k["key"], act="lateslip", pick="WKB", svc="opd", no="102")
ok("W8 a parchi-only login cannot make it from the money card", "err=" in loc and c.execute("SELECT COUNT(*) FROM slip WHERE clinic_id='WKB'").fetchone()[0] == 0)
as_user("manoj", ("checker",)); h = page()
ok("W8 his page in English", "Whose was it?" in h and "Make the slip" in h and "Don't know" in h)
as_user("shavez")

# W9 -- the register opens on the last working day until it is saved
c, p = fresh(); CR._s978_hour = lambda: 9
r = cl.get("/finance/clinic/register")
ok("W9 unsaved yesterday: the register opens on it", r.status_code in (301, 302) and r.headers["Location"].endswith("/finance/clinic/register/" + D), r.headers.get("Location"))
reg(c, cons_cash=0); c.commit()
r = cl.get("/finance/clinic/register"); T = dt.date.today().isoformat()
ok("W9 saved: today, as before", r.status_code in (301, 302) and r.headers["Location"].endswith("/finance/clinic/register/" + T), r.headers.get("Location"))
c, p = fresh(); CR._s978_hour = lambda: 15
r = cl.get("/finance/clinic/register")
ok("W9 after 13:00 the register opens on today even with yesterday unsaved (review S5)", r.status_code in (301, 302) and r.headers["Location"].endswith("/finance/clinic/register/" + T), r.headers.get("Location"))

# W10 -- the versions and the tile
ok("W10 register_push says S978", rp.VERSION == "S978 1")
if len(sys.argv) > 3:
    import json
    g = json.load(open(os.path.join(sys.argv[3], "tile_grants.json"), encoding="utf-8"))
    ok("W10 the Day check tile for the three Docterz logins", g.get("version") == 50 and all("Day check" in g["users"][w]["extra"] for w in ("shavez", "shivani", "alisha"))
       and not any("Day check" in (g["users"][w].get("extra") or []) for w in g["users"] if w not in ("shavez", "shivani", "alisha")))
print("WALK S978: %d PASS, %d FAIL" % (PASS, FAIL))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAIL else 0)
