#!/usr/bin/python3
# walk_s798.py -- kit S798_WA_MESSAGES_SHOWONLY. Usage: walk_s798.py <dir holding portal/> [--control]
# Everything is MADE UP here: a scratch finance.db and a scratch Inbox store are built at run time (made-up patients, mobiles built
# from a counter -- F-185), in a temp folder removed at the end. No live store is opened. Prints ok/BAD only.
# The last line is "WALK OK n/n" or "WALK RED k of n"; with --control, "CONTROL: red ..." when it is red as it must be.
import datetime as dt, hashlib, importlib, os, shutil, sqlite3, sys, tempfile
K = os.path.abspath(sys.argv[1])
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s798w.")
FDB, IDB, SDB, OLD = [os.path.join(T, n) for n in ("f.db", "inbox.db", "wl.db", "old_optouts.csv")]
os.environ.update({"FINANCE_DB": FDB, "WA_LADDER_DB": SDB, "WA_LADDER_INBOX_DB": IDB, "WA_LADDER_OLD_OPTOUT": OLD, "WA_LADDER_INGEST": "0"})
sys.path.insert(0, os.path.join(K, "portal"))
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why and not ok) else ""))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
D = dt.datetime.now(IST).date()
day = lambda n: (D + dt.timedelta(days=n)).strftime("%Y-%m-%d")       # noqa: E731
M = lambda n: "9" + "%09d" % (79800 + n)                              # noqa: E731 -- made-up mobiles

# ---- the made-up records
c = sqlite3.connect(FDB)
c.executescript("""
CREATE TABLE dx_visit (patient_uid TEXT NOT NULL, visit_date TEXT NOT NULL, clinic_id TEXT NOT NULL DEFAULT '', diagnosis_raw TEXT NOT NULL DEFAULT '',
  std_dx TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT '', priority TEXT NOT NULL DEFAULT '', dx_status TEXT NOT NULL DEFAULT '',
  follow_up_date TEXT NOT NULL DEFAULT '', export_id INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL, PRIMARY KEY (patient_uid, visit_date));
CREATE TABLE patient_visit (visit_id TEXT PRIMARY KEY, visit_date TEXT NOT NULL, clinic_id TEXT, patient_uid TEXT, mobile_fp TEXT, had_procedure TEXT);
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT NOT NULL UNIQUE, name TEXT, phone_last4 TEXT, first_seen TEXT, merged_into INTEGER,
  note TEXT, mobile_fp TEXT, patient_uid TEXT, last_seen TEXT, mobile TEXT);
CREATE TABLE online_booking (id INTEGER PRIMARY KEY, payment_id TEXT NOT NULL UNIQUE, name TEXT, mobile TEXT, appt_at TEXT);
""")
def pat(n, name, mob):
    c.execute("INSERT INTO patient_ref (clinic_id, name, phone_last4, mobile, patient_uid) VALUES (?,?,?,?,?)", ("W%d" % n, name, mob[-4:], mob, "u%d" % n))
def visit(n, d, fu=None):
    c.execute("INSERT INTO patient_visit VALUES (?,?,?,?,?,?)", ("v%d_%s" % (n, d), d, "W%d" % n, "u%d" % n, "", ""))
    if fu is not None:
        c.execute("INSERT INTO dx_visit (patient_uid, visit_date, clinic_id, follow_up_date, updated_at) VALUES (?,?,?,?,?)", ("u%d" % n, d, "W%d" % n, fu, "x"))
pat(1, "Walk Asha", M(1));    visit(1, day(-7), day(1))                    # follow-up tomorrow -> goes
pat(2, "Walk Bala", M(2));    visit(2, day(-10), day(1)); visit(2, day(-2))  # came since -> on no list
pat(3, "Walk Chand", M(3));   visit(3, day(-8), day(-1))                   # date passed yesterday -> goes
pat(4, "Walk Deep", "");      visit(4, day(-12), day(-5))                  # 5 days, no mobile -> held
pat(5, "Walk Esha", M(5));    visit(5, day(-30), day(-14))                 # long overdue -> goes, then STOP -> held
pat(6, "Walk Firoz", M(1));   visit(6, day(0), day(15))                    # seen today, shares Asha's number -> held (one a day)
pat(7, "Walk Gita", M(7));    visit(7, day(0), day(7))                     # seen today -> goes; then on the older opt-out file -> held
pat(8, "Walk Hari", M(8));    visit(8, day(-9), day(-1))                   # date passed, but an online booking ahead -> held
pat(9, "Walk Indu", M(9));    visit(9, day(-20), day(1)); visit(9, day(-3), day(10))   # the LATEST visit counts -> on no list
pat(10, "Walk Jai", M(10));   visit(10, day(-6), day(-1)); visit(10, day(-1))          # came on the date itself -> on no list
pat(11, "Walk Kiran", M(13) + "/11"); visit(11, day(-7), day(1))            # a number with a tail -> not a plain mobile -> held
pat(12, "Walk Lata", M(14));  visit(12, day(-9), day(-1))                   # came since under the SAME clinic ID but a blank uid -> on no list
c.execute("INSERT INTO patient_visit VALUES (?,?,?,?,?,?)", ("v12b", day(-2), "W12", "", "", ""))
c.execute("INSERT INTO patient_visit VALUES (?,?,?,?,?,?)", ("vnull", day(0), None, None, "", ""))          # a visit row with no ID at all
c.execute("INSERT INTO online_booking (payment_id, name, mobile, appt_at) VALUES (?,?,?,?)", ("pay_S798walk", "Walk Hari", M(8), day(1) + " 11:30"))
c.commit(); c.close()
i = sqlite3.connect(IDB)
i.execute("CREATE TABLE msgs(rid INTEGER PRIMARY KEY AUTOINCREMENT, mid TEXT UNIQUE, phone TEXT NOT NULL, dir TEXT NOT NULL, ts TEXT NOT NULL, "
          "mtype TEXT, body TEXT, media_url TEXT, mime TEXT, fname TEXT, local_path TEXT, status TEXT, sent_by TEXT, src TEXT)")
def msg(n, phone, d, body):
    i.execute("INSERT INTO msgs (mid, phone, dir, ts, mtype, body) VALUES (?,?,?,?,?,?)", ("m%d" % n, phone, d, day(0) + " 09:0%d:00" % n, "text", body))
msg(1, "91" + M(3), "in", "kab aana hai")           # a question -> not a STOP
msg(2, "91" + M(11), "out", "stop")                 # our own outgoing text -> ignored
i.commit()
def fmd5():
    return hashlib.md5(open(FDB, "rb").read()).hexdigest()
F0 = fmd5()

def rows(p, key):
    return {r["cid"] or r["name"]: r for x in p["lists"] if x["key"] == key for r in x["rows"]}
def cnt(p, key):
    x = [x for x in p["lists"] if x["key"] == key][0]
    return (x["go"], x["held"])

# ---- A. the module: from the kit, the STOP rule, and NO send code
try:
    wl = importlib.import_module("wa_ladder")
    src = open(os.path.join(K, "portal", "wa_ladder.py"), encoding="utf-8").read()
    ck("A1 wa_ladder imports from the kit", os.path.dirname(os.path.abspath(wl.__file__)) == os.path.join(K, "portal"))
    ck("A2 the STOP rule's selftest", wl.selftest())
    body = src.split('"""', 2)[2]                                      # the code after the opening description
    banned = [w for w in ("urllib", "urlopen", "requests", "socket", "http.client", "subprocess", "portal_wa", "publicapi", "smtplib", ".send(")
              if w in body]
    ck("A3 no send code in the file (no network, no sender)", not banned, banned)
except Exception as e:  # noqa: BLE001
    wl = None; ck("A wa_ladder present", False, repr(e)[:140])

if wl:
    # ---- B. the day's lists on the made-up records
    try:
        p = wl.plan()
        ck("B1 a plan for today, marked as not sending", p and p["day"] == day(0) and p["sends"] is False)
        ck("B2 follow-up tomorrow: Asha goes; Bala (came since) and Indu (a later visit) are not listed; Kiran's odd number is held",
           cnt(p, "tomorrow") == (1, 1) and "W1" in rows(p, "tomorrow") and rows(p, "tomorrow")["W11"]["hold"] == "no mobile number on record", cnt(p, "tomorrow"))
        ck("B3 date passed yesterday: Chand goes, Hari held for his booking; Jai (came on the date) and Lata (came, blank uid) not listed",
           cnt(p, "due1") == (1, 1) and rows(p, "due1")["W8"]["hold"] == "has an online booking ahead" and "W10" not in rows(p, "due1")
           and "W12" not in rows(p, "due1"), cnt(p, "due1"))
        ck("B4 day 5: Deep held -- no mobile number", cnt(p, "due5") == (0, 1) and rows(p, "due5")["W4"]["hold"] == "no mobile number on record", cnt(p, "due5"))
        od = [x for x in p["lists"] if x["key"] == "overdue"][0]
        ck("B5 long overdue: Esha waits for his tick -- never 'would go' by itself", (od["go"], od["tick"], od["held"]) == (0, 1, 0) and od["rows"][0]["tick"] is True,
           (od["go"], od["tick"], od["held"]))
        ck("B6 after today's visit: Gita goes; Firoz held -- Asha's number already gets one today; the visit with no ID is held, no crash",
           cnt(p, "post_visit") == (1, 2) and rows(p, "post_visit")["W6"]["hold"] == "this number already gets a message today", cnt(p, "post_visit"))
        ck("B6b the lists come in the order he approved", [x["key"] for x in p["lists"]] == ["tomorrow", "post_visit", "appt", "due1", "due5", "overdue"])
        ck("B7 appointment reminder: the online booking of tomorrow goes", cnt(p, "appt") == (1, 0), cnt(p, "appt"))
        ck("B8 the full mobile is given to the page", rows(p, "tomorrow")["W1"]["mobile"] == M(1))
        ck("B9 another day can be asked: for yesterday, nobody's follow-up was 'tomorrow'", cnt(wl.plan(day(-1)), "tomorrow") == (0, 0))
        ck("B10 the counts line carries no name and no number", "Walk" not in wl.counts() and M(1) not in wl.counts() and "tomorrow 1 go" in wl.counts())
    except Exception as e:  # noqa: BLE001
        ck("B the lists", False, repr(e)[:140])

    # ---- C. the STOP listener
    try:
        s1 = wl.stop_scan(ingest=False)
        ck("C1 first pass: one incoming message read (our own outgoing 'stop' is ignored), none a STOP", s1 == (1, 0), s1)
        msg(3, "91" + M(5), "in", "STOP"); msg(4, M(12), "in", "Message mat bhejo"); msg(5, M(3), "in", "report bhej do"); i.commit()
        s2 = wl.stop_scan(ingest=False)
        ck("C2 a STOP and a 'mat bhejo' go on the list; 'report bhej do' does not", s2 == (3, 2), s2)
        ck("C3 a second pass reads nothing again", wl.stop_scan(ingest=False) == (0, 0))
        p = wl.plan()
        ck("C4 Esha is now held: replied STOP", cnt(p, "overdue") == (0, 1) and rows(p, "overdue")["W5"]["hold"] == "replied STOP", cnt(p, "overdue"))
        ck("C4b the page is told the listener is hearing (no error, not stale)", p["fresh"]["stop_error"] == "" and p["fresh"]["stop_stale"] is False)
        ck("C5 the stop list shows two numbers and their words", len(p["stops"]) == 2 and any(r["said"] == "STOP" for r in p["stops"]))
        with open(OLD, "w", encoding="utf-8") as fh:
            fh.write(M(7) + "\n")
        p = wl.plan()
        ck("C6 a number on the older opt-out file is held too", rows(p, "post_visit")["W7"]["hold"] == "replied STOP" and len(p["stops"]) == 3)
        os.rename(IDB, IDB + ".x")
        try:
            wl.stop_scan(ingest=False); deaf = "no error raised"
        except wl.ListenerError as e:
            deaf = str(e)
        ck("C7 with no Inbox store the listener SAYS so (never silently deaf)", "is not at" in deaf and "ERROR" in wl.stop_status(), deaf)
        ck("C8 ... and the page is told", "is not at" in wl.plan()["fresh"]["stop_error"])
        os.rename(IDB + ".x", IDB)
        ck("C9 the store back: the listener hears again and the error clears", wl.stop_scan(ingest=False) == (0, 0) and wl.stop_status().startswith("ok"))
        msg(6, M(15), "in", "report nahi bheji"); msg(7, M(16), "in", "Stop promotions"); i.commit()
        ck("C10 'report nahi bheji' is not a STOP; 'Stop promotions' is", wl.stop_scan(ingest=False) == (2, 1))
        ck("C11 a re-read of every stored message adds nothing twice", wl.stop_scan(ingest=False, rescan=True)[1] == 0 and len(wl.plan()["stops"]) == 4)
        ck("C12 the Inbox check gives a count, not a message", wl.inbox_check()[0] and "incoming messages" in wl.inbox_check()[1])
        with open(SDB, "rb") as fh:
            keep = fh.read()
        with open(SDB, "wb") as fh:
            fh.write(b"this is not a database")
        pb = wl.plan()
        ck("C13 a stop list that cannot be read holds EVERY row (fails closed)",
           pb is not None and sum(x["go"] + x["tick"] for x in pb["lists"]) == 0 and all(r["hold"] for x in pb["lists"] for r in x["rows"]))
        with open(SDB, "wb") as fh:
            fh.write(keep)
    except Exception as e:  # noqa: BLE001
        ck("C the STOP listener", False, repr(e)[:140])

    # ---- D. the page behind a login
    try:
        import flask
        app = flask.Flask("s798walk")
        WHO = {"v": None}
        def login_required(view):
            from functools import wraps
            @wraps(view)
            def w(*a, **k):
                if WHO["v"] is None:
                    return flask.redirect("/portal/login")
                return view(*a, **k)
            return w
        wl.install(app, login_required, lambda req: WHO["v"])
        cl = app.test_client()
        ck("D1 no login: the page's door is closed (a redirect)", cl.get("/portal/messages").status_code == 302 and cl.get("/portal/messages/api/plan").status_code == 302)
        WHO["v"] = {"user": "alisha", "role": "staff"}
        ck("D2 a staff login: 403 on the page and on its data", cl.get("/portal/messages").status_code == 403 and cl.get("/portal/messages/api/plan").status_code == 403)
        WHO["v"] = {"user": "manoj", "role": "doctor"}
        r = cl.get("/portal/messages"); t = r.get_data(as_text=True)
        ck("D3 the doctor: the page, in English, saying SHOW ONLY", r.status_code == 200 and "SHOW ONLY" in t and 'lang="en"' in t)
        j = cl.get("/portal/messages/api/plan").get_json()
        ck("D4 its data: six lists, sends false", j and j["ok"] and len(j["lists"]) == 6 and j["sends"] is False)
        ck("D5 a day far away is refused quietly (today's lists come)", cl.get("/portal/messages/api/plan?day=2031-01-01").get_json()["day"] == day(0))
        ck("D6 only GET: a POST to the page's data is not allowed", cl.post("/portal/messages/api/plan").status_code == 405)
    except Exception as e:  # noqa: BLE001
        ck("D the page", False, repr(e)[:140])

    ck("F1 finance.db was only read (byte-identical after the walk)", fmd5() == F0)
    ck("F2 the kit wrote only its own store", sorted(os.listdir(T)) == ["f.db", "inbox.db", "old_optouts.csv", "wl.db"], sorted(os.listdir(T)))
i.close()

# ---- E. portal.py
try:
    P = open(os.path.join(K, "portal", "portal.py"), encoding="utf-8").read()
    ck("E1 portal.py: the tile once", P.count('"name": "WhatsApp messages"') == 1 and P.count('"url": "/portal/messages"') == 1)
    ck("E2 portal.py: grouped under Patients", '"WhatsApp messages": "Patients"' in P)
    ck("E3 portal.py: the page mounted once, after the booking page", P.count("wa_ladder.install(app, login_required, _sso_user)") == 1
       and P.find("wa_ladder.install(") > P.find("online_booking_portal.install(") > 0)
    import py_compile
    py_compile.compile(os.path.join(K, "portal", "portal.py"), cfile=os.path.join(T, "p.pyc"), doraise=True)
    ck("E4 portal.py compiles", True)
    ck("E5 the older WhatsApp tiles stand as they were", all(P.count('"name": "%s"' % n) == 1 for n in ("WhatsApp Inbox", "Send WhatsApp", "Follow-up WhatsApps", "Online booking")))
except Exception as e:  # noqa: BLE001
    ck("E portal.py", False, repr(e)[:140])

shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
