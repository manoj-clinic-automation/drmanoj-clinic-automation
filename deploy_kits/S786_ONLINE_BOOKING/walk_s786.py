#!/usr/bin/python3
# walk_s786.py -- kit S786_ONLINE_BOOKING. Usage: walk_s786.py <dir holding finance/ and portal/> <a finance.db copy> [--control]
# Everything runs on a SCRATCH copy of the database (made here, removed at the end); made-up patients only (an ID checked absent
# from the copy first, F-1251); the mailbox and the push are stand-ins. Prints counts and ok/BAD only -- never a name or a number
# from the copy. The last line is "WALK OK n/n" or "WALK RED k of n"; with --control, "CONTROL: red ..." when it is red as it must be.
import datetime as dt, hashlib, importlib, json, os, shutil, sqlite3, sys, tempfile
K, SRC = os.path.abspath(sys.argv[1]), sys.argv[2]
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s786w.")
DB = os.path.join(T, "f.db"); shutil.copyfile(SRC, DB)
os.environ.update({"FINANCE_DB": DB, "OB_STATE": os.path.join(T, "state.json"), "PATIENT_FP_SALT": "s786-walk-salt",
                   "FINANCE_DIR": os.path.join(K, "finance"), "RING_PORTAL_DIR": os.path.join(K, "portal"),
                   "TILE_GRANTS_FILE": os.path.join(T, "tile_grants.json"), "RING_OUTCOME_DB": os.path.join(T, "none.db")})
for p in [x for x in os.environ.get("S786_LIBS", "").split(os.pathsep) if x] + [os.path.join(K, "portal"), os.path.join(K, "finance")]:
    if p not in sys.path:
        sys.path.insert(0, p)                                          # the kit's own dirs end up first
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + why) if (why and not ok) else ""))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
M = lambda n: "9" + "%09d" % (78600 + n)   # made-up mobiles, built at run time (F-185)
today = dt.datetime.now(IST).date()
def dmy(d, hm):  # 'DD Mon YYYY HH:MM AM'
    return "%02d %s %d %s" % (d.day, d.strftime("%b"), d.year, hm)
def mail(name, mob, pay, d, hm):
    s = "%s appointment at %s payment completed." % (name, dmy(d, hm))
    b = ("Hi,\n\nInvoice No. :\n\nOrder Id : order_%s\n\nPatient Name : %s\n\nPatient Mobile : %s\n\nDoctor Name : Manoj Agarwal\n\n"
         "Payment Amount : 600\n\nPayment ID : %s\n" % (pay, name, mob, pay))
    return (s, b, dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M"))
nxt = today + dt.timedelta(days=1)
while nxt.weekday() == 6:
    nxt += dt.timedelta(days=1)
MAILS = [mail("Walk Anita", M(1), "pay_S786walkA", today, "08:15 AM"),         # today, before 11 -> call
         mail("Walk Bina", M(2), "pay_S786walkB", nxt, "11:30 AM"),           # next clinic day, inside the timings
         mail("Walk Chand", M(3), "pay_S786walkC", today - dt.timedelta(days=2), "07:30 PM"),   # past -> no push
         ("Docterz update", "Hello doctor, nothing paid here.", "")]                 # not a booking -> unreadable

# ---- A. the module's own selftest
try:
    ob = importlib.import_module("online_booking")
    ck("A1 online_booking imports from the kit", os.path.dirname(os.path.abspath(ob.__file__)) == os.path.join(K, "finance"))
    ck("A2 the parser selftest", ob.selftest())
except Exception as e:  # noqa: BLE001
    ob = None; ck("A online_booking present", False, repr(e)[:120])

# ---- B. one pass on the scratch copy, a made-up patient on Bina's number
con = sqlite3.connect(DB)
cid = "S786W%d" % (int(hashlib.md5(T.encode()).hexdigest()[:6], 16) % 100000)
absent = con.execute("SELECT COUNT(*) FROM patient_ref WHERE clinic_id=?", (cid,)).fetchone()[0] == 0
ck("B0 the made-up clinic ID is not on the copy", absent)
try:
    import finance_patient_match as fpm  # noqa: E402
    fp = fpm.fingerprint(M(2), "s786-walk-salt")
except Exception:  # noqa: BLE001
    fpm, fp = None, ""
if absent and fp:
    con.execute("INSERT INTO patient_ref (clinic_id, name, mobile_fp, last_seen) VALUES (?,?,?,?)", (cid, "Walk Bina", fp, str(today)))
    con.commit()
con.close()
pushed = []
if ob:
    st = ob.run(mails=MAILS, pusher=lambda b: (pushed.append(b["payment_id"]) or 1, "sent 1, failed 0"))
    ck("B1 the pass ends without an error", not st.get("error"), st.get("error"))
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    rs = {r["payment_id"]: r for r in c.execute("SELECT * FROM online_booking")}
    ck("B2 three bookings kept, the newsletter not", len(rs) == 3 and st.get("unreadable") == 1, "%d rows" % len(rs))
    a, b = rs.get("pay_S786walkA"), rs.get("pay_S786walkB")
    ck("B3 today 08:15 is outside the timings", a is not None and a["out_of_hours"] == 1 and a["appt_at"] == "%s 08:15" % today)
    ck("B4 the next clinic day 11:30 is inside", b is not None and b["out_of_hours"] == 0)
    ck("B5 the full mobile and Rs 600 kept", a is not None and a["mobile"] == M(1) and a["amount_p"] == 60000)
    ids = json.loads(b["clinic_ids"] or "[]") if b is not None else []
    ck("B6 the clinic ID found on the patient's mobile", bool(ids) and ids[0]["id"] == cid, str(len(ids)))
    ck("B7 pushed for today and later only", sorted(pushed) == ["pay_S786walkA", "pay_S786walkB"], str(sorted(pushed)))
    st2 = ob.run(mails=MAILS, pusher=lambda b: (pushed.append(b["payment_id"]) or 1, "x"))
    n2 = c.execute("SELECT COUNT(*) FROM online_booking").fetchone()[0]
    ck("B8 a second pass keeps each once and pushes nothing", n2 == 3 and st2.get("new") == 0 and len(pushed) == 2)
    ck("B9 the state says when it last ran well", bool(json.load(open(os.environ["OB_STATE"])).get("last_ok")))
    c.close()

# ---- C. the owner's console line
try:
    oc = importlib.import_module("owner_console")
    f = getattr(oc, "_s786_booking_line", None)
    ck("C1 owner_console has the booking line", callable(f))
    if callable(f):
        c = sqlite3.connect(DB)
        ln = f(c) or {}
        ck("C2 red while the outside-timings booking is not called", ln.get("dot") == "b" and "/portal/booking" == ln.get("href")
           and "not called" in ln.get("text", "") and "2 online bookings" in ln.get("text", ""), str(ln.get("text"))[:90])
        c.execute("UPDATE online_booking SET called_by='walk', called_at='x' WHERE payment_id='pay_S786walkA'"); c.commit()
        ln2 = f(c) or {}
        ck("C3 amber once staff called", ln2.get("dot") == "w" and "not called" not in ln2.get("text", ""))
        c.execute("UPDATE online_booking SET called_by=NULL, called_at=NULL WHERE payment_id='pay_S786walkA'"); c.commit(); c.close()
        e = sqlite3.connect(os.path.join(T, "empty.db"))
        ck("C4 no table -> no line, no error", f(e) is None); e.close()
except Exception as e:  # noqa: BLE001
    ck("C owner_console imports", False, repr(e)[:120])

# ---- D. the page module (Flask test client, stand-in login)
try:
    shutil.copyfile(os.path.join(K, "portal", "tile_grants.json.s786") if os.path.exists(os.path.join(K, "portal", "tile_grants.json.s786"))
                    else os.path.join(K, "portal", "tile_grants.json"), os.environ["TILE_GRANTS_FILE"])
    from flask import Flask  # noqa: E402
    obp = importlib.import_module("online_booking_portal")
    app = Flask("w"); WHO = {}
    obp.install(app, lambda v: v, lambda req: dict(WHO) or None)
    cl = app.test_client()
    def as_(u, r): WHO.clear(); WHO.update({"user": u, "role": r})
    as_("manoj", "doctor"); r = cl.get("/portal/booking")
    ck("D1 the doctor gets the page in English", r.status_code == 200 and b'lang="en"' in r.data)
    as_("shivani", "staff"); r = cl.get("/portal/booking")
    ck("D2 a granted staff login gets it in Hindi", r.status_code == 200 and b'lang="hi"' in r.data)
    for u in ("reception", "alisha", "shavez"):
        as_(u, "staff"); ck("D3 granted: " + u, cl.get("/portal/booking/api/list").status_code == 200)
    as_("darpan", "staff")
    ck("D4 a login without the tile is refused", cl.get("/portal/booking").status_code == 403 and cl.get("/portal/booking/api/list").status_code == 403)
    as_("shivani", "staff"); j = cl.get("/portal/booking/api/list").get_json()
    rows = [x for x in j.get("rows", []) if x["mobile"].startswith(M(0)[:8])]
    ck("D5 the list carries name, full mobile, ID, Rs 600, the time", len(rows) == 3 and all(x["rupees"] == 600 for x in rows)
       and any(x["ids"] and x["ids"][0]["id"] == cid for x in rows) and rows[0]["today"], str(len(rows)))
    ck("D6 today's first, the past one last", rows and rows[0]["mobile"] == M(1) and rows[-1]["past"])
    rid = rows[0]["id"] if rows else 0
    r1 = cl.post("/portal/booking/api/called", json={"id": rid}).get_json(); r2 = cl.post("/portal/booking/api/called", json={"id": rid}).get_json()
    ck("D7 'Phone kar diya' is kept once, by who tapped", r1.get("saved") is True and r2.get("saved") is False)
    c = sqlite3.connect(DB); by = c.execute("SELECT called_by FROM online_booking WHERE id=?", (rid,)).fetchone(); c.close()
    ck("D8 the tap names the login", by and by[0] == "shivani")
    ck("D9 a bad id is refused", cl.post("/portal/booking/api/called", json={"id": "x"}).status_code == 400)
    ck("D10 the state line is on the list", "last_ok" in (j.get("state") or {}))
except Exception as e:  # noqa: BLE001
    ck("D the page module", False, repr(e)[:160])

# ---- E. portal.py and the grants file
try:
    P = open(os.path.join(K, "portal", "portal.py"), encoding="utf-8").read()
    ck("E1 portal.py: the tile once", P.count('"name": "Online booking"') == 1 and P.count('"url": "/portal/booking"') == 1)
    ck("E2 portal.py: grouped under Patients", '"Online booking": "Patients"' in P)
    ck("E3 portal.py: the page mounted once", P.count("online_booking_portal.install(app, login_required, _sso_user)") == 1)
    import py_compile  # noqa: E402
    py_compile.compile(os.path.join(K, "portal", "portal.py"), cfile=os.path.join(T, "p.pyc"), doraise=True)
    ck("E4 portal.py compiles", True)
    gk = os.path.join(K, "portal", "tile_grants.json.s786")
    G = json.load(open(gk, encoding="utf-8")) if os.path.exists(gk) else {}
    ck("E5 grants v46: the tile to reception, shivani, alisha, shavez",
       G.get("version") == 46 and all("Online booking" in G["users"][u]["extra"] for u in ("reception", "shivani", "alisha", "shavez")))
    others = [u for u, v in (G.get("users") or {}).items() if "Online booking" in (v.get("extra") or []) and u not in ("reception", "shivani", "alisha", "shavez")]
    ck("E6 nobody else granted", G and not others, str(others))
except Exception as e:  # noqa: BLE001
    ck("E portal files", False, repr(e)[:120])

shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
