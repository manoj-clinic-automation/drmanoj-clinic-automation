#!/usr/bin/python3
# walk_s805.py -- kit S805_WA_STOP_LIST_REMOVE. Usage: walk_s805.py <dir holding portal/wa_ladder.py> [--control]
# Everything is MADE UP: a scratch finance.db, Inbox store, Call Console list, older opt-out file and the kit's own store are built
# at run time (made-up patients, mobiles built from a counter -- F-185) in a temp folder removed at the end. No live store is opened.
# The last line is "WALK OK n/n" or "WALK RED k of n"; with --control, "CONTROL: red ..." when it is red as it must be.
import datetime as dt, hashlib, importlib, os, shutil, sqlite3, sys, tempfile, time
K = os.path.abspath(sys.argv[1])
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s805w.")
FDB, IDB, SDB, OLD, CDB = [os.path.join(T, n) for n in ("f.db", "inbox.db", "wl.db", "old_optouts.csv", "console.db")]
os.environ.update({"FINANCE_DB": FDB, "WA_LADDER_DB": SDB, "WA_LADDER_INBOX_DB": IDB, "WA_LADDER_OLD_OPTOUT": OLD, "WA_LADDER_INGEST": "0", "WA_LADDER_CONSOLE_DB": CDB})
sys.path.insert(0, os.path.join(K, "portal"))
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why and not ok) else ""))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
D = dt.datetime.now(IST).date()
day = lambda n: (D + dt.timedelta(days=n)).strftime("%Y-%m-%d")       # noqa: E731
M = lambda n: "9" + "%09d" % (80500 + n)                              # noqa: E731 -- made-up mobiles

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
CON = sqlite3.connect(CDB)
CON.execute("CREATE TABLE patients (phone10 TEXT, name TEXT, diagnosis TEXT, age TEXT, gender TEXT, last_visit TEXT, patient_uid TEXT, clinic_id TEXT)")
# one made-up patient whose follow-up is tomorrow, on the number M(3)
c.execute("INSERT INTO patient_ref (clinic_id, name, phone_last4, mobile, patient_uid) VALUES (?,?,?,?,?)", ("W3", "Walk Chand", M(3)[-4:], None, "u3"))
CON.execute("INSERT INTO patients (phone10, name, patient_uid, clinic_id) VALUES (?,?,?,?)", (M(3), "Walk Chand", "u3", "W3"))
c.execute("INSERT INTO patient_visit VALUES (?,?,?,?,?,?)", ("v3", day(-7), "W3", "u3", "", ""))
c.execute("INSERT INTO dx_visit (patient_uid, visit_date, clinic_id, follow_up_date, updated_at) VALUES (?,?,?,?,?)", ("u3", day(-7), "W3", day(1), "x"))
c.commit(); c.close(); CON.commit(); CON.close()
i = sqlite3.connect(IDB)
i.execute("CREATE TABLE msgs (rid INTEGER PRIMARY KEY, phone TEXT, ts TEXT, body TEXT, dir TEXT)")
def said(rid, mob, body):
    i.execute("INSERT INTO msgs (rid, phone, ts, body, dir) VALUES (?,?,?,?,'in')", (rid, "91" + mob, day(0) + " 10:00:%02d" % rid, body)); i.commit()
said(1, M(1), "STOP"); said(2, M(2), "report bhej do"); said(3, M(3), "stop please")
open(OLD, "w", encoding="utf-8").write("mobile\n%s\n" % M(4))
def tomorrow_row(wl):
    p = wl.plan()
    return [r for x in p["lists"] if x["key"] == "tomorrow" for r in x["rows"]][0], p
def rows_removed():
    q = sqlite3.connect(SDB); n = q.execute("SELECT mobile, removed_by, was_said, was_source, upto_rid FROM optout_removed ORDER BY id").fetchall(); q.close(); return n

try:
    wl = importlib.import_module("wa_ladder")
    ck("A1 wa_ladder imports from the given folder, version S805", os.path.dirname(os.path.abspath(wl.__file__)) == os.path.join(K, "portal") and wl.VERSION.startswith("S805"), wl.VERSION)
    src = open(os.path.join(K, "portal", "wa_ladder.py"), encoding="utf-8").read()
    ck("A2 still NO send code in the file (no urllib, http.client, requests, smtplib, subprocess)", not any(w in src for w in ("urllib", "http.client", "import requests", "smtplib", "subprocess")))
    ck("A3 the STOP rule's selftest is green", wl.selftest())
    seen, new = wl.stop_scan()
    st, err = wl.stops()
    ck("B1 the listener: two STOP replies and the older file's number are on the stop list", new == 2 and not err and sorted(st) == sorted([M(1), M(3), M(4)]), (new, err, len(st)))
    r, p = tomorrow_row(wl)
    ck("B2 the patient whose number said STOP is held: 'replied STOP'", r["hold"] == "replied STOP", r["hold"])
    ok, text = wl.unstop(M(3), "manoj")
    st, err = wl.stops()
    ck("B3 the doctor takes that number off: it is off the list", ok and M(3) not in st and M(1) in st and M(4) in st, (ok, text))
    rr = rows_removed()
    ck("B4 the removal is RECORDED, not erased: the number, who, what it had said, the listener's place", len(rr) == 1 and rr[0][0] == M(3) and rr[0][1] == "manoj" and rr[0][2] == "stop please" and rr[0][3] == "WhatsApp reply" and rr[0][4] >= 3, rr)
    r, p = tomorrow_row(wl)
    ck("B5 that patient now WOULD GO (no hold), and the page's data lists the taking-off", r["hold"] == "" and p["taken_off"] and p["taken_off"][0]["mobile"] == M(3) and p["taken_off"][0]["by"] == "manoj" and p["sends"] is False, (r["hold"], p.get("taken_off")))
    seen, new = wl.stop_scan(rescan=True)
    st, err = wl.stops()
    ck("B6 reading every stored message again (--rescan) does NOT put the number back", new == 0 and M(3) not in st and M(1) in st, (new, sorted(st)))
    said(4, M(2), "hello"); said(5, M(3), "STOP")
    seen, new = wl.stop_scan()
    st, err = wl.stops()
    r, p = tomorrow_row(wl)
    ck("B7 a NEW STOP reply from that number puts it back on the list, and the patient is held again", new == 1 and M(3) in st and r["hold"] == "replied STOP", (new, r["hold"]))
    ok, text = wl.unstop(M(3), "manoj")
    ck("B8 taken off a second time: two records kept; the page lists the number once, its newest record", ok and len(rows_removed()) == 2 and [(x["mobile"], x["said"]) for x in wl.taken_off()] == [(M(3), "STOP")], len(rows_removed()))
    ok, text = wl.unstop(M(4), "manoj")
    st, err = wl.stops()
    ck("B9 a number that came from the OLDER opt-out file is taken off the same way (the file itself untouched)", ok and M(4) not in st and M(4) in open(OLD, encoding="utf-8").read(), (ok, text))
    wl.stop_scan(); wl.stop_scan(rescan=True)
    st, err = wl.stops()
    ck("B10 ... and stays off through the listener's passes", M(4) not in st and M(3) not in st and M(1) in st, sorted(st))
    said(6, M(4), "Stop")
    wl.stop_scan(); st, err = wl.stops()
    ck("B11 ... until it sends a NEW STOP", M(4) in st)
    n0 = len(rows_removed())
    a = wl.unstop(M(9), "manoj"); b = wl.unstop("abc", "manoj"); b2 = wl.unstop(M(1)[:9], "manoj")
    ck("B12 a number not on the list, or not a mobile: refused in words, nothing recorded", (not a[0]) and "not on the stop list" in a[1] and (not b[0]) and (not b2[0]) and len(rows_removed()) == n0, (a, b, b2))
    keep = wl.STORE
    wl.STORE = os.path.join(T, "nowhere", "wl.db")
    a = wl.unstop(M(1), "manoj"); r, p = tomorrow_row(wl)
    wl.STORE = keep
    ck("B13 the store unreadable: nothing is taken off, and every row is held (it still fails closed)", (not a[0]) and r["hold"] == "the stop list could not be read", (a, r["hold"]))
    st, err = wl.stops()
    ck("B14 ... and the list is as it was when the store is back", not err and M(1) in st and M(4) in st, (err, sorted(st)))
    ck("B15 the listener still says ok", wl.stop_status().startswith("ok"), wl.stop_status())
    # -- a STOP that had ARRIVED but was not read yet when the number was taken off
    said(7, M(1), "stop")                                              # M(1) is on the list from message 1; this one is unread
    ok, text = wl.unstop(M(1), "manoj"); off_now = M(1) not in wl.stops()[0]
    wl.stop_scan()
    ck("B16 a STOP that had arrived but was not read yet at the taking-off: the next pass puts the number back", ok and off_now and M(1) in wl.stops()[0], (ok, off_now))
    ck("B17 a number back on the list (it said STOP again) is NOT shown under 'taken off'", M(1) not in [x["mobile"] for x in wl.taken_off()] and M(4) not in [x["mobile"] for x in wl.taken_off()], wl.taken_off())
    # -- the listener cannot write while the taking-off reads its place (the write lock is held from the first read)
    seen_lock = {"v": None}
    real_meta = wl._meta
    def probing_meta(con, k, default=""):
        if k == "last_rid" and seen_lock["v"] is None:
            other = sqlite3.connect(SDB, timeout=0.2)
            try:
                other.execute("INSERT OR REPLACE INTO meta(k, v) VALUES ('probe', '1')"); other.commit(); seen_lock["v"] = "written"
            except sqlite3.OperationalError:
                seen_lock["v"] = "locked"
            finally:
                other.close()
        return real_meta(con, k, default)
    wl._meta = probing_meta
    ok, text = wl.unstop(M(1), "manoj")
    wl._meta = real_meta
    ck("B18 while a number is being taken off, another writer (the listener) is locked out of the store", ok and seen_lock["v"] == "locked", (ok, seen_lock["v"]))
    # -- the store locked by another writer: refused in words, the number still listed (10 s is the store's own patience)
    wl.restop(M(1), "manoj")
    hold = sqlite3.connect(SDB, timeout=1); hold.execute("BEGIN IMMEDIATE")
    t0 = time.time(); a = wl.unstop(M(1), "manoj"); waited = time.time() - t0
    hold.rollback(); hold.close()
    ck("B19 the store busy with another writer: nothing is taken off, said in words", (not a[0]) and "could not be changed" in a[1] and M(1) in wl.stops()[0] and waited < 30, (a, round(waited, 1)))
    # -- the older (hand-kept) file changed AFTER one of its numbers was taken off: that number is back on the list
    n_off = M(4) in wl.stops()[0]                                      # M(4) said STOP again in B11 -> on the list by its own reply
    wl.unstop(M(4), "manoj"); off4 = M(4) not in wl.stops()[0]
    future = time.time() + 120
    os.utime(OLD, (future, future))
    ck("B20 the older file changed after its number was taken off: the number is back on the list (the safe direction)", n_off and off4 and M(4) in wl.stops()[0] and wl.stops()[0][M(4)]["source"] == "older list", (n_off, off4))
    past = time.time() - 86400
    os.utime(OLD, (past, past))
    ck("B21 ... and with the file unchanged since, it stays off", M(4) not in wl.stops()[0])
    # -- the way back: the doctor puts a number he took off back on the list
    a = wl.restop(M(4), "manoj"); st, err = wl.stops()
    ck("B22 put back by the doctor: on the list again, marked so, and no longer under 'taken off'", a[0] and M(4) in st and st[M(4)]["source"] == "put back by manoj" and M(4) not in [x["mobile"] for x in wl.taken_off()], (a, st.get(M(4))))
    wl.stop_scan(); wl.stop_scan(rescan=True)
    ck("B23 ... and it stays on through the listener's passes", M(4) in wl.stops()[0])
    a = wl.restop(M(9), "manoj"); b = wl.restop("abc", "manoj")
    ck("B24 a number that was never taken off cannot be put on the list this way", (not a[0]) and "not taken off" in a[1] and (not b[0]) and M(9) not in wl.stops()[0], (a, b))
    ok, text = wl.unstop(M(4), "manoj")
    ck("B25 a number put back can be taken off again (three records of it kept)", ok and M(4) not in wl.stops()[0] and [x[0] for x in rows_removed()].count(M(4)) == 3, [x[0] for x in rows_removed()].count(M(4)))
    wl.restop(M(4), "manoj")
except Exception as e:  # noqa: BLE001
    ck("A/B the stop list", False, repr(e)[:170])

# ---- D. the door on the page
try:
    import flask
    app = flask.Flask("s805walk")
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
    U = "/portal/messages/api/unstop"; HD = {"X-Messages": "1"}
    onlist = lambda m: m in wl.stops()[0]                               # noqa: E731
    if not onlist(M(1)):
        wl.restop(M(1), "walk")
    ck("D1 no login: the door is closed (a redirect), nothing taken off", cl.post(U, json={"mobile": M(1)}, headers=HD).status_code == 302 and onlist(M(1)))
    WHO["v"] = {"user": "alisha", "role": "staff"}
    ck("D2 a staff login: 403, nothing taken off", cl.post(U, json={"mobile": M(1)}, headers=HD).status_code == 403 and onlist(M(1)))
    WHO["v"] = {"user": "manoj", "role": "doctor"}
    ck("D3 the doctor, but not from the page's own script (no X-Messages): 400, nothing taken off", cl.post(U, json={"mobile": M(1)}).status_code == 400 and onlist(M(1)))
    ck("D4 a GET on that door is not allowed", cl.get(U).status_code == 405 and onlist(M(1)))
    if not onlist(M(1)):
        wl.restop(M(1), "walk")
    r = cl.post(U, json={"mobile": M(1)}, headers=HD); j = r.get_json(); n1 = [x[0] for x in rows_removed()].count(M(1))
    ck("D5 the doctor from the page: taken off, recorded under his login", r.status_code == 200 and j["ok"] and not onlist(M(1)) and rows_removed()[-1][0] == M(1) and rows_removed()[-1][1] == "manoj", (r.status_code, j))
    r = cl.post(U, json={"mobile": M(1)}, headers=HD)
    ck("D6 the same number again: 409 in words, no second record", r.status_code == 409 and "not on the stop list" in r.get_json()["msg"] and [x[0] for x in rows_removed()].count(M(1)) == n1, r.status_code)
    ck("D7 a broken body is refused quietly", cl.post(U, data="not json", headers=HD).status_code == 409 and cl.post(U, json=[1], headers=HD).status_code == 409)
    U2 = "/portal/messages/api/restop"
    WHO["v"] = None
    a1 = cl.post(U2, json={"mobile": M(1)}, headers=HD).status_code
    WHO["v"] = {"user": "alisha", "role": "staff"}
    a2 = cl.post(U2, json={"mobile": M(1)}, headers=HD).status_code
    WHO["v"] = {"user": "manoj", "role": "doctor"}
    a3 = cl.post(U2, json={"mobile": M(1)}).status_code; a4 = cl.get(U2).status_code
    ck("D7b the put-back door: closed without a login (302), 403 for staff, 400 without the page's header, no GET -- nothing changed", (a1, a2, a3, a4) == (302, 403, 400, 405) and not onlist(M(1)), (a1, a2, a3, a4))
    r = cl.post(U2, json={"mobile": M(1)}, headers=HD)
    ck("D7c the doctor puts it back from the page: on the list, under his login", r.status_code == 200 and r.get_json()["ok"] and onlist(M(1)) and wl.stops()[0][M(1)]["source"] == "put back by manoj", r.status_code)
    cl.post(U, json={"mobile": M(1)}, headers=HD)                      # off again, for D9
    r = cl.get("/portal/messages"); t = r.get_data(as_text=True)
    ck("D8 the page: English, still SHOW ONLY, carries both buttons and both doors", r.status_code == 200 and "SHOW ONLY" in t and "Take off the stop list" in t and "Put back on the stop list" in t and "'/portal/messages/api/'" in t and "'unstop':'restop'" in t and "X-Messages" in t and 'lang="en"' in t)
    j = cl.get("/portal/messages/api/plan").get_json()
    ck("D9 the page's data: six lists, sends false, the stop list and the taken-off list", j["ok"] and len(j["lists"]) == 6 and j["sends"] is False and isinstance(j["taken_off"], list) and j["taken_off"][0]["mobile"] == M(1) and j["version"].startswith("S805"))
except Exception as e:  # noqa: BLE001
    ck("D the door", False, repr(e)[:170])

i.close()
ck("F1 the kit wrote only its own store", sorted(os.listdir(T)) == ["console.db", "f.db", "inbox.db", "old_optouts.csv", "wl.db"], sorted(os.listdir(T)))
shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
