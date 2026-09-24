#!/usr/bin/env python3
"""walk_s382.py -- kit S382_REPORT_BAAKI. The real slip_log.py over a SCRATCH COPY of the real finance.db, on the walk's
own days (2001-02-01/02, SLIP_NOW moved through the day) and IDs (9092xx): the blood list's states (baaki, der, mail
bheja, mail nahi aaya, baad mein), a report clearing its own line, a report with no order, a missing name, reception's
walk-in, Sukhveer's taps and limits, the X-ray tab, the answers reaching Check karein, the doctors' counts. The live
slip_log.py (S379) is the negative control. Prints IDs and counts only.
Usage: FINANCE_DB=<scratch copy> python3 walk_s382.py <dir with the kit slip_log.py> <live slip_log.py>"""
import importlib.util, os, sqlite3, sys
new_dir, live = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
dbp = os.environ["FINANCE_DB"]
assert "walk" in dbp or "scratch" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
os.environ["PEND_XRAY_FROM"] = "2001-01-01"
N = [0]
def ok(c, label, got=None):
    N[0] += 1
    if not c:
        print("WALK RED %d: %s %s" % (N[0], label, "" if got is None else got)); sys.exit(1)
def at(ts):
    os.environ["SLIP_NOW"] = ts
def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
from flask import Flask
USER = {"u": {"user": "alisha", "roles": ["maker"]}}
def build(path, tag):
    m = load(path, "slip_log_" + tag)
    a = Flask("w" + tag)
    def dbg():
        c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row; return c
    def req(*roles, **kw):
        u = USER["u"]
        if not set(u["roles"]) & set(roles):
            from flask import jsonify
            return None, (jsonify(ok=False, error="not_permitted"), 403)
        return u, None
    m.init(a, dbg, req)
    return a, m
A, S = build(os.path.join(new_dir, "slip_log.py"), "new")
c = A.test_client()
con = sqlite3.connect(dbp); con.row_factory = sqlite3.Row
D, D2 = "2001-02-01", "2001-02-02"
at(D + "T09:00:00")
S.pend_ensure(con)
con.execute("DELETE FROM blood_order WHERE clinic_id LIKE '9092%'"); con.execute("DELETE FROM lab_report WHERE clinic_id LIKE '9092%'")
con.execute("DELETE FROM patient_ref WHERE clinic_id LIKE '9092%'")
for cid in ("909201", "909202", "909203", "909204", "909205", "909208", "909209"):
    con.execute("INSERT INTO patient_ref(clinic_id, name) VALUES (?,?)", (cid, "WALK " + cid))
con.executemany("INSERT INTO blood_order(day, clinic_id, name_seen, logged_by, logged_at) VALUES (?,?,?,?,?)", [
    (D, "909201", "", "shavez", D + " 10:00:00"), (D, "909202", "", "shavez", D + " 18:00:00"),
    (D, "909203", "", "shavez", D + " 11:00:00"), (D, "909204", "", "shavez", D + " 11:30:00"),
    (D, "909206", "", "shavez", D + " 12:00:00")])
con.executemany("INSERT INTO lab_report(msg_id, clinic_id, received_at, pushed_at) VALUES (?,?,?,?)", [
    ("walkmsg1", "909204", D + " 19:00:00", ""), ("walkmsg2", "909205", D + " 19:10:00", "")])
con.commit()
def blood():
    b, g, o = S.blood_pending(con)
    return {x["clinic_id"]: x for x in b if x["clinic_id"].startswith("9092")}, {x["clinic_id"] for x in g}, {x["clinic_id"]: x for x in o}
at(D + "T12:00:00")
b, g, o = blood()
ok(set(b) == {"909201", "909202", "909203", "909206"} and "909204" in g, "a report that arrived clears its own line", (sorted(b), g))
ok(all(b[k]["st"] == "wait" for k in b), "at noon every open line is simply baaki", {k: b[k]["st"] for k in b})
ok(b["909201"]["name"] == "WALK 909201" and b["909206"]["name"] == "", "the name comes from the patient list; an unknown ID has none")
ok("909205" in o, "a report with no test written is listed", sorted(o))
USER["u"] = {"user": "sukhveer", "roles": ["viewer"]}
at(D + "T14:00:00")
pg = c.get("/finance/slips/pending").get_data(as_text=True)
ok("Blood report baaki" in pg and "t=xray" not in pg and "+ Naya" not in pg and "Test hua tha" not in pg,
   "Sukhveer: the blood list only -- no X-ray tab, no walk-in, no report-without-order buttons")
ok("naam nahi" in pg and 'name="name"' in pg, "a line with no name shows it and asks for it")
id3 = con.execute("SELECT id FROM blood_order WHERE clinic_id='909203'").fetchone()[0]
r = c.post("/finance/slips/pending/act", data={"key": "b:%d" % id3, "act": "mailed"})
ok(r.status_code == 303 and "ok=" in r.headers["Location"], "Sukhveer taps Mail kar diya")
ok(con.execute("SELECT answer FROM record_check WHERE key=?", ("bo:%s:909203" % D,)).fetchone()[0] == "asked",
   "the same item in Check karein is answered 'asked' -- reception is not asked twice")
id6 = con.execute("SELECT id FROM blood_order WHERE clinic_id='909206'").fetchone()[0]
c.post("/finance/slips/pending/act", data={"key": "b:%d" % id6, "act": "name", "name": "WALK SIXNAME"})
ok(con.execute("SELECT name_seen FROM blood_order WHERE id=?", (id6,)).fetchone()[0] == "WALK SIXNAME", "the missing name is written once")
ok(c.post("/finance/slips/pending/new", data={"clinic_id": "909207", "name": "X"}).status_code == 403, "Sukhveer cannot add a walk-in")
ok(c.post("/finance/slips/pending/act", data={"key": "xm:%s:909208" % D, "act": "put"}).headers.get("Location", "").find("err=") > 0,
   "Sukhveer cannot tap the X-ray tab")
at(D + "T16:00:00")
b, g, o = blood()
ok(b["909203"]["st"] == "mailed", "two hours after the tap: waiting for the mail", b["909203"]["st"])
at(D + "T18:30:00")
b, g, o = blood()
ok(b["909203"]["st"] == "nomail" and "dobara" in b["909203"]["word"], "three hours and no mail: flagged, send again", b["909203"]["word"])
at(D2 + "T09:00:00")
b, g, o = blood()
ok(b["909201"]["st"] == "late" and b["909202"]["st"] == "wait", "next morning: the 10 am test is late, the 6 pm test is not yet",
   (b["909201"]["st"], b["909202"]["st"]))
at(D2 + "T12:00:00")
b, g, o = blood()
ok(b["909202"]["st"] == "late", "after 11 am the evening test is late too")
ok(list(b)[:2] in (["909203", "909201"], ["909203", "909202"]) or [x for x in b][0] == "909203", "mail-not-arrived sits at the top", list(b))
USER["u"] = {"user": "alisha", "roles": ["maker"]}
id1 = con.execute("SELECT id FROM blood_order WHERE clinic_id='909201'").fetchone()[0]
id2 = con.execute("SELECT id FROM blood_order WHERE clinic_id='909202'").fetchone()[0]
c.post("/finance/slips/pending/act", data={"key": "b:%d" % id1, "act": "not_tested"})
c.post("/finance/slips/pending/act", data={"key": "b:%d" % id2, "act": "later"})
b, g, o = blood()
ok("909201" not in b and con.execute("SELECT outcome FROM blood_order WHERE id=?", (id1,)).fetchone()[0] == "not_tested",
   "Test nahi hua closes the line (and Check karein, which skips an answered order)")
ok(b["909202"]["st"] == "later", "Baad mein: quiet for three days")
r = c.post("/finance/slips/pending/new", data={"clinic_id": "909207", "name": ""})
ok("naam" in r.headers["Location"], "a walk-in with an unknown ID needs its name")
r = c.post("/finance/slips/pending/new", data={"clinic_id": "909209", "name": ""})
ok("ok=" in r.headers["Location"] and con.execute("SELECT name_seen FROM blood_order WHERE clinic_id='909209'").fetchone()[0] == "WALK 909209",
   "reception's walk-in with a known ID: the name fills itself")
ok("err=" in c.post("/finance/slips/pending/new", data={"clinic_id": "909209"}).headers["Location"], "the same walk-in twice is refused")
c.post("/finance/slips/pending/act", data={"key": "orph:%s:909205" % D, "act": "orph_ok"})
b, g, o = blood()
ok("909205" not in o and "909205" in g, "Test hua tha: the report-without-order becomes a test with its report")
# ---- X-ray
con.execute("DELETE FROM slip_item WHERE slip_id IN (SELECT id FROM slip WHERE day=?)", (D,)); con.execute("DELETE FROM slip WHERE day=?", (D,))
con.execute("DELETE FROM record_file WHERE clinic_id LIKE '9092%'")
for n, cid in ((1, "909208"), (2, "909209")):
    sid = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_at) VALUES ('xp',?,?,?,'ok',?)",
                      (990000 + n, D, cid, D + " 11:00:00")).lastrowid
    con.execute("INSERT INTO slip_item(slip_id, kind, name, side, price_p, sort) VALUES (?,'xray','Knee AP & Lateral view','R',50000,0)", (sid,))
con.commit()
at(D + "T13:00:00")
x = {i["clinic_id"]: i for i in S.xray_pending(con) if i["clinic_id"].startswith("9092")}
ok(set(x) == {"909208", "909209"} and all(i["st"] == "wait" for i in x.values()), "X-ray: both slips wait for a photo")
pg = c.get("/finance/slips/pending?t=xray").get_data(as_text=True)
ok("X-ray photo baaki" in pg and "Photo daal di" in pg, "reception/Shavez see the X-ray tab with its buttons")
c.post("/finance/slips/pending/act", data={"key": "xm:%s:909208" % D, "act": "put"})
c.post("/finance/slips/pending/act", data={"key": "xm:%s:909209" % D, "act": "not_done"})
x = {i["clinic_id"]: i for i in S.xray_pending(con) if i["clinic_id"].startswith("9092")}
ok(set(x) == {"909208"} and x["909208"]["st"] == "mailed", "Photo daal di waits; X-ray nahi hua closes", {k: v["st"] for k, v in x.items()})
ok(con.execute("SELECT answer FROM record_check WHERE key=?", ("xm:%s:909209" % D,)).fetchone()[0] == "not_done",
   "the X-ray answer reaches Check karein too")
at(D + "T14:30:00")
x = {i["clinic_id"]: i for i in S.xray_pending(con) if i["clinic_id"].startswith("9092")}
ok(x["909208"]["st"] == "nomail", "an hour and more after the tap, no photo filed: flagged")
con.execute("INSERT INTO record_file(clinic_id, kind, day, drive_id, file_name, mime, bytes, source, source_ref, note, added_by, added_at) "
            "VALUES ('909208','xray',?,'walkDRIVE000001','w.jpg','image/jpeg',0,'xray_inbox','walkSRC','','walk','')", (D,))
con.commit()
ok(not [i for i in S.xray_pending(con) if i["clinic_id"] == "909208"], "the photo filed clears its own line")
USER["u"] = {"user": "manoj", "roles": ["checker"]}
j = c.get("/finance/slips/api/pending-counts").get_json()
ok(j["ok"] and {"blood", "blood_red", "xray", "xray_red", "orphans"} <= set(j), "the doctors' counts answer", j)
menu_live = None
USER["u"] = {"user": "shavez", "roles": ["maker"]}
menu = c.get("/finance/slips").get_data(as_text=True)
ok("/finance/slips/pending" in menu, "the Parchi menu carries Report baaki")
A0, S0 = build(live, "old")
ok(A0.test_client().get("/finance/slips/pending").status_code == 404, "negative control: the live slip_log has no Report baaki")
ok({r.rule for r in A.url_map.iter_rules()} - {r.rule for r in A0.url_map.iter_rules()} ==
   {"/finance/slips/pending", "/finance/slips/pending/act", "/finance/slips/pending/new", "/finance/slips/api/pending-counts"}
   and not ({r.rule for r in A0.url_map.iter_rules()} - {r.rule for r in A.url_map.iter_rules()}), "routes: +4, none lost")
print("WALK OK %d/%d checks" % (N[0], N[0]))
