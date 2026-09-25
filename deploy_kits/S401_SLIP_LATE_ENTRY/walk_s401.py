#!/usr/bin/env python3
"""walk_s401.py -- kit S401_SLIP_LATE_ENTRY. The kit's slip_log.py over a SCRATCH COPY of the live finance.db, on the
walk's own slip books (OPD from 90001 to 90100, X-ray/Proc from 90501 to 90600, set in the scratch copy only), clock pinned.
Plays the owner's case of 25-Sep-2026: Bhati and reception write the parchis Shavez would, including the ones
missed on their day, afterwards; the room ticks by Bhati; the Report door for Bhati. The live S398 file is the
negative control (it cannot put a late parchi on its day). Prints counts and slip numbers of the walk only.
Usage: python3 walk_s401.py <kit slip_log.py> <live slip_log.py> <scratch db A> <scratch db B>"""
import datetime as dt, importlib.util, os, sqlite3, sys
new_p, live_p, dba, dbb = [os.path.abspath(x) for x in sys.argv[1:5]]
for d in (dba, dbb):
    assert "walk" in d or "scratch" in d or d.startswith("/tmp"), "refusing a non-scratch database"
NOW = dt.datetime.now().replace(microsecond=0, hour=11, minute=0, second=0)
os.environ["SLIP_NOW"] = NOW.isoformat()
os.environ.setdefault("FINANCE_CRON_TOKEN", "walk-s401-token")
T = NOW.date()
D = lambda n: (T - dt.timedelta(days=n)).isoformat()
N = [0]


def ok(c, label, got=None):
    N[0] += 1
    if not c:
        print("WALK RED %d: %s %s" % (N[0], label, "" if got is None else got)); sys.exit(1)


from flask import Flask
USER = {"u": None}


def build(path, tag, dbp):
    s = importlib.util.spec_from_file_location("slip_log_" + tag, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    a = Flask("w" + tag)

    def dbg():
        c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row; return c

    def req(*roles, **kw):
        u = USER["u"]
        if not set(u["roles"]) & set(roles):
            from flask import jsonify
            return None, (jsonify(ok=False, error="not_permitted"), 403)
        return u, None
    m.init(a, dbg, req, None, unit="slips")
    return a, m


def as_(user, role="maker"):
    USER["u"] = {"user": user, "roles": [role]}


def prep(dbp, mod):
    c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row
    mod.ensure(c)
    c.execute("DELETE FROM slip WHERE slip_no BETWEEN 90001 AND 90600")
    c.execute("UPDATE slip_book SET first_no=90001, last_no=90100, start_no=90020 WHERE series='opd'")
    c.execute("UPDATE slip_book SET first_no=90501, last_no=90600, start_no=90501 WHERE series='xp'")
    c.commit()
    return c


A, S = build(new_p, "new", dba)
B, L = build(live_p, "live", dbb)
ca, cb = A.test_client(), B.test_client()
con = prep(dba, S)
conb = prep(dbb, L)
row = lambda c, series, no: c.execute("SELECT * FROM slip WHERE series=? AND slip_no=? AND state<>'void'", (series, no)).fetchone()
# a known clinic ID from the master (never printed)
cid = con.execute("SELECT clinic_id FROM patient_ref WHERE clinic_id GLOB '[0-9]*' ORDER BY id DESC LIMIT 1").fetchone()[0]
xr, pr = S.services(con)
ok(bool(xr), "the rate page has X-rays")
xid = xr[0]["id"]

# --- the routes: the same doors as S398
ok({r.rule for r in A.url_map.iter_rules()} == {r.rule for r in B.url_map.iter_rules()}, "the same doors as S398")

# --- the menu: Chhooti parchi for every maker; Report for Bhati and Shavez, not reception or the room
for who, want_rep in (("bhati", True), ("shavez", True), ("alisha", False), ("shivani", False), ("awdhesh", False)):
    as_(who)
    h = ca.get("/finance/slips").get_data(as_text=True)
    ok("Chhooti parchi" in h, "menu has Chhooti parchi for " + who)
    ok(("/finance/slips/report" in h) == want_rep, "Report link for %s is %s" % (who, want_rep))
as_("bhati")
ok(ca.get("/finance/slips/report").status_code == 200, "Bhati opens the Report")

# --- the same day: Bhati writes 90020 and 90023 -> 90021, 90022 chhoota today
r = ca.post("/finance/slips/save", data={"series": "opd", "slip_no": "90020", "clinic_id": cid})
ok(r.status_code == 303 and "ok=" in r.headers["Location"], "Bhati saves an OPD parchi", r.headers.get("Location"))
ok(row(con, "opd", 90020)["day"] == D(0) and row(con, "opd", 90020)["logged_by"] == "bhati", "on today, by bhati")
ca.post("/finance/slips/save", data={"series": "opd", "slip_no": "90023", "clinic_id": cid})
ok(row(con, "opd", 90021)["state"] == "missing" and row(con, "opd", 90022)["state"] == "missing", "the two skipped numbers wait as chhoota")

# --- make 90021 yesterday's (as if chhoota yesterday) and see the late screen list it
con.execute("UPDATE slip SET day=? WHERE series='opd' AND slip_no=90021", (D(1),)); con.commit()
as_("alisha")
h = ca.get("/finance/slips?s=late").get_data(as_text=True)
ok("90021" in h and "90022" in h and "s=opd&amp;no=90021&amp;day=%s" % D(1) in h, "late screen lists both, with the right door")
h = ca.get("/finance/slips?s=opd&no=90021&day=%s" % D(1)).get_data(as_text=True)
ok('value="90021"' in h and 'value="%s" selected' % D(1) in h and "Purani parchi" in h, "the form opens pre-filled with number and day")
r = ca.post("/finance/slips/save", data={"series": "opd", "slip_no": "90021", "clinic_id": cid, "day": D(1), "back": "late"})
ok("s=late" in r.headers["Location"] and "ok=" in r.headers["Location"], "reception fills it; back to the late screen", r.headers["Location"])
x = row(con, "opd", 90021)
ok(x["state"] == "ok" and x["day"] == D(1) and x["logged_by"] == "alisha", "saved ON ITS OWN DAY, by alisha")
ok("90021" not in ca.get("/finance/slips?s=late").get_data(as_text=True), "and it leaves the late screen")

# --- a parchi never entered at all, three days back (an older number): written with Din = 3 days back
r = ca.post("/finance/slips/save", data={"series": "opd", "slip_no": "90010", "clinic_id": cid, "day": D(3)})
x = row(con, "opd", 90010)
ok(x is not None and x["day"] == D(3), "a never-entered parchi lands on its own day", r.headers.get("Location"))
# a late number far ahead still asks 'Haan, yahi number'; confirmed, it marks nothing chhoota
r = ca.post("/finance/slips/save", data={"series": "opd", "slip_no": "90070", "clinic_id": cid, "day": D(2)})
ok("err=" in r.headers["Location"] and row(con, "opd", 90070) is None, "a far-ahead late number asks first")
ca.post("/finance/slips/save", data={"series": "opd", "slip_no": "90070", "clinic_id": cid, "day": D(2), "gap_ok": "1"})
ok(row(con, "opd", 90070)["day"] == D(2), "confirmed, it is saved on its day")
ok(con.execute("SELECT COUNT(*) FROM slip WHERE series='opd' AND slip_no BETWEEN 90024 AND 90069").fetchone()[0] == 0,
   "a late parchi marks no numbers chhoota")
x = row(con, "opd", 90010)
as_("alisha")
r = ca.post("/finance/slips/state/%d" % x["id"], data={"act": "void"})
ok("ok=" in r.headers["Location"], "alisha takes off her own late entry the same day without a reason", r.headers["Location"])

# --- the window: 8 days back, tomorrow, rubbish -- refused; nothing written
for bad in (D(LATE := S.LATE_DAYS + 1), (T + dt.timedelta(days=1)).isoformat(), "kal"):
    r = ca.post("/finance/slips/save", data={"series": "opd", "slip_no": "90011", "clinic_id": cid, "day": bad})
    ok("err=" in r.headers["Location"] and row(con, "opd", 90011) is None, "day %s refused" % bad)
ok(ca.post("/finance/slips/save", data={"series": "opd", "slip_no": "90012", "clinic_id": cid, "day": D(S.LATE_DAYS)}).status_code == 303
   and row(con, "opd", 90012)["day"] == D(S.LATE_DAYS), "the last day of the window is taken")

# --- a late mistake keeps its day and number on the way back
r = ca.post("/finance/slips/save", data={"series": "opd", "slip_no": "90021", "clinic_id": cid, "day": D(1)})
ok("err=" in r.headers["Location"] and "day=%s" % D(1) in r.headers["Location"] and "no=90021" in r.headers["Location"],
   "a duplicate late parchi is refused and the form keeps its day")

# --- X-ray/Proc: Bhati writes yesterday's, then ticks it in the room
as_("bhati")
r = ca.post("/finance/slips/save", data={"series": "xp", "slip_no": "90501", "clinic_id": cid, "xray0": str(xid), "day": D(1)})
x = row(con, "xp", 90501)
ok(x is not None and x["day"] == D(1), "Bhati writes yesterday's X-ray parchi on its day", r.headers.get("Location"))
h = ca.get("/finance/slips?s=room").get_data(as_text=True)
ok("/finance/slips/room/%d" % x["id"] in h, "it waits in the room list")
ca.post("/finance/slips/room/%d" % x["id"], data={"act": "upi"})
ca.post("/finance/slips/room/%d" % x["id"], data={"act": "done"})
x = row(con, "xp", 90501)
ok(x["paid_mode"] == "upi" and x["paid_by"] == "bhati" and x["done_by"] == "bhati", "Bhati ticks UPI and Done")
ca.post("/finance/slips/room/%d" % x["id"], data={"act": "unpaid"}); ca.post("/finance/slips/room/%d" % x["id"], data={"act": "cash"})
ok(row(con, "xp", 90501)["paid_mode"] == "cash", "and can change it to Cash")

# --- every screen, every role: no error page
for who, rl in (("bhati", "maker"), ("alisha", "maker"), ("awdhesh", "maker"), ("shavez", "maker"), ("manoj", "checker"), ("sukhveer", "viewer")):
    as_(who, rl)
    for p in ("/finance/slips", "/finance/slips?tile=1", "/finance/slips?s=late", "/finance/slips?s=opd", "/finance/slips?s=xp",
              "/finance/slips?s=room", "/finance/slips?s=list", "/finance/slips?s=book", "/finance/slips?s=all",
              "/finance/slips?s=xp&day=%s" % D(2), "/finance/slips/pending", "/finance/slips/report"):
        ok(ca.get(p).status_code in (200, 302, 303, 403), "GET %s as %s" % (p.split("?")[0], who))

# --- negative control: the live S398 file puts a 'late' parchi on today
as_("alisha")
cb.post("/finance/slips/save", data={"series": "opd", "slip_no": "90010", "clinic_id": cid, "day": D(3)})
ok(row(conb, "opd", 90010)["day"] == D(0), "control: S398 cannot put it on its day")

for c in (con, conb):
    c.execute("DELETE FROM slip WHERE slip_no BETWEEN 90001 AND 90600"); c.commit()
print("WALK OK %d/%d checks" % (N[0], N[0]))
