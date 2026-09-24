#!/usr/bin/env python3
"""walk_s391.py -- kit S391_LAB_NO_ID. The real S391 slip_log.py over a SCRATCH COPY of the live finance.db, on the
walk's own days (2001-03-xx) and IDs (9093xx). Replays 24-Sep-2026's shape (invented names): nine blood orders, Sukhveer taps
"Mail kar diya", the lab mails back with the ID left out of eight subjects (and three re-sends) -- each report must
find its line and clear it. Then the unsure cases: two open orders of the same name (none mailed / one mailed), a name
with no usable word, a report before its order, reception's pick, "Hamara nahi", the token, the counts, the page.
The live slip_log.py (S384) is the negative control. Prints IDs and counts only.
Usage: FINANCE_DB=<scratch copy> python3 walk_s391.py <dir with the kit slip_log.py> <live slip_log.py>"""
import importlib.util, os, sqlite3, sys
new_dir, live = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
dbp = os.environ["FINANCE_DB"]
assert "walk" in dbp or "scratch" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
os.environ["PEND_XRAY_FROM"] = "2001-01-01"
os.environ["FINANCE_CRON_TOKEN"] = "walk-s391-token"
TOK = {"X-Finance-Cron": "walk-s391-token"}
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
USER = {"u": {"user": "sukhveer", "roles": ["viewer"]}}


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
D1, D2, D4 = "2001-03-01", "2001-03-02", "2001-03-04"
at(D4 + "T09:00:00")
S.noid_ensure(con)
for t in ("blood_order", "lab_report", "patient_ref"):
    con.execute("DELETE FROM %s WHERE clinic_id LIKE '9093%%'" % t)
con.execute("DELETE FROM lab_noid WHERE msg_id LIKE 'walk391%'")
people = [("909301", "Chanda", D1), ("909302", "Bhupendra Kumar", D1), ("909303", "Savita Mishra", D1),
          ("909304", "Pramod Kumar", D1), ("909305", "Shabana Begum", D1), ("909306", "Rajveer Pratap", D2),
          ("909307", "Anuj", D2), ("909308", "Kamlesh Devi", D1), ("909309", "Tahseena", D2),
          ("909311", "Sunita Sharma", D2), ("909312", "Sunita Verma", D2),        # same first name, neither mailed
          ("909313", "Sunil Yadav", D2), ("909314", "Sunil Gupta", D2),           # same first name, one mailed
          ("909315", "Ram Kumar", D2)]                                             # no usable word
for cid, nm, d in people:
    con.execute("INSERT INTO patient_ref(clinic_id, name) VALUES (?,?)", (cid, nm))
    con.execute("INSERT INTO blood_order(day, clinic_id, name_seen, logged_by, logged_at) VALUES (?,?,?,?,?)",
                (d, cid, "", "shavez", d + " 11:00:00"))
con.commit()


def oid(cid):
    return con.execute("SELECT id FROM blood_order WHERE clinic_id=? AND state='ok'", (cid,)).fetchone()[0]


def blood():
    b, g, o = S.blood_pending(con)
    return ({x["clinic_id"]: x for x in b if x["clinic_id"].startswith("9093")},
            {x["clinic_id"] for x in g if x["clinic_id"].startswith("9093")}, o)


# Sukhveer mails at 16:33..17:30 and taps each line
USER["u"] = {"user": "sukhveer", "roles": ["viewer"]}
for i, cid in enumerate(("909301", "909302", "909303", "909304", "909305", "909306", "909307", "909308", "909309", "909313")):
    at(D4 + "T16:%02d:00" % (33 + i))
    r = c.post("/finance/slips/pending/act", data={"key": "b:%d" % oid(cid), "act": "mailed"})
    ok(r.status_code == 303 and "ok=" in r.headers["Location"], "Sukhveer taps Mail kar diya on %s" % cid)
at(D4 + "T19:40:00")
b, g, _o = blood()
ok(b["909301"]["st"] == "nomail" and not g, "before S391's door is used, the mailed lines sit at 'nahi aaya' -- the owner's 7 pm",
   {k: b[k]["st"] for k in b})

# the door: no token / wrong token
mail = [("walk391a", "MRS. CHANDA", "16:33:57"), ("walk391b", "MR. BHUPENDRA KUMAR", "16:34:57"),
        ("walk391c", "MRS. SAVITA", "16:35:31"), ("walk391d", "MR. PRAMOD KUMAR", "16:36:10"),
        ("walk391e", "MR. RAJVEER PRATAP", "16:38:24"), ("walk391f", "MR. RAJVEER PRATAP", "16:45:47"),
        ("walk391g", "MR. ANUJ", "16:46:22"), ("walk391h", "MRS. TAHSEENA", "16:46:53"),
        ("walk391i", "MRS. TAHSEENA", "17:25:21"), ("walk391j", "MRS. TAHSEENA", "17:33:18"),
        ("walk391k", "Mr. .KAMLESH DEVI", "16:33:19"), ("walk391l", "Mr. .KAMLESH DEVI", "17:30:54")]
body = {"reports": [{"msg_id": m, "name": n, "received_at": D4 + " " + t} for m, n, t in mail]}
ok(c.post("/finance/slips/api/lab-noid", json=body).status_code == 401, "no token: refused 401")
ok(c.post("/finance/slips/api/lab-noid", json=body, headers={"X-Finance-Cron": "guess"}).status_code == 401, "wrong token: refused 401")
ok(con.execute("SELECT COUNT(*) FROM lab_noid WHERE msg_id LIKE 'walk391%'").fetchone()[0] == 0, "a refused call stores nothing")
r = c.post("/finance/slips/api/lab-noid", json=body, headers=TOK)
j = r.get_json()
got = {x["msg_id"]: x["clinic_id"] for x in j["reports"]}
want = {"walk391a": "909301", "walk391b": "909302", "walk391c": "909303", "walk391d": "909304", "walk391e": "909306",
        "walk391f": "909306", "walk391g": "909307", "walk391h": "909309", "walk391i": "909309", "walk391j": "909309",
        "walk391k": "909308", "walk391l": "909308"}
ok(r.status_code == 200 and got == want, "24-Sep replayed: all 12 ID-less e-mails (8 patients, 4 re-sends) find their patient", got)
b, g, _o = blood()
ok({"909301", "909302", "909303", "909304", "909306", "909307", "909308", "909309"} <= g and "909305" in b,
   "their lines clear the same minute; Shabana (whose report never came without an ID) still waits", (sorted(b), sorted(g)))
ok(con.execute("SELECT COUNT(*) FROM lab_report WHERE clinic_id LIKE '9093%'").fetchone()[0] == 12, "one lab_report row per e-mail")
r2 = c.post("/finance/slips/api/lab-noid", json=body, headers=TOK).get_json()
ok({x["msg_id"]: x["clinic_id"] for x in r2["reports"]} == want and
   con.execute("SELECT COUNT(*) FROM lab_report WHERE clinic_id LIKE '9093%'").fetchone()[0] == 12,
   "the mailbox asking again gets the same answers, nothing doubled")

# the unsure cases
more = {"reports": [{"msg_id": "walk391m", "name": "MRS. SUNITA", "received_at": D4 + " 19:50:00"},
                    {"msg_id": "walk391n", "name": "MR. SUNIL", "received_at": D4 + " 19:51:00"},
                    {"msg_id": "walk391o", "name": "MR. RAM", "received_at": D4 + " 19:52:00"},
                    {"msg_id": "walk391p", "name": "MRS. PRIYANKA WALKNEW", "received_at": D4 + " 19:53:00"},
                    {"msg_id": "walk391q", "name": "MRS. NOBODY ZZQX", "received_at": D4 + " 19:54:00"}]}
g2 = {x["msg_id"]: x["clinic_id"] for x in c.post("/finance/slips/api/lab-noid", json=more, headers=TOK).get_json()["reports"]}
ok(g2["walk391m"] == "", "two open Sunitas, neither mailed: not guessed", g2)
ok(g2["walk391n"] == "909313", "two open Sunils, one mailed: the mailed one", g2)
ok(g2["walk391o"] == "", "'MR. RAM' has no usable word: not guessed", g2)
ok(g2["walk391p"] == "" and g2["walk391q"] == "", "no order of that name yet: waits", g2)
ids = {r["msg_id"] for r in S.noid_pending(con)}
ok({"walk391m", "walk391o", "walk391p", "walk391q"} <= ids and "walk391n" not in ids, "the four unsure ones are listed", sorted(ids))

# the page (Sukhveer)
at(D4 + "T20:00:00")
pg = c.get("/finance/slips/pending").get_data(as_text=True)
ok("Report aayi, ID nahi likha" in pg and "MRS. SUNITA" in pg and "Yahi hai" in pg and "Hamara nahi" in pg,
   "Sukhveer sees 'Report aayi, ID nahi likha' with the pick and 'Hamara nahi'")
ok("SITA ( 1234 )" in pg, "the blood tab tells the desk to write the ID in the subject")
ok(pg.find('value="909311"') > 0 and pg.find('value="909311"') < pg.find('value="909301"') if 'value="909301"' in pg else pg.find('value="909311"') > 0,
   "the same-name orders are offered first")
ok("naam se juda" in pg, "what arrived by name says so under Aa gayi")

# a pick, a free ID, "not ours"
r = c.post("/finance/slips/pending/act", data={"key": "nx:walk391m", "act": "noid_pick", "cid": "909312"})
ok(r.status_code == 303 and "ok=" in r.headers["Location"], "Sukhveer picks Sunita Verma")
b, g, _o = blood()
ok("909312" in g and "909311" in b, "Sunita Verma's line clears; Sunita Sharma's stays")
r = c.post("/finance/slips/pending/act", data={"key": "nx:walk391o", "act": "noid_pick", "cid": "", "cid2": "909315"})
ok("ok=" in r.headers["Location"] and "909315" in blood()[1], "a typed ID works too (Ram Kumar)")
r = c.post("/finance/slips/pending/act", data={"key": "nx:walk391q", "act": "noid_gone"})
ok("ok=" in r.headers["Location"] and "walk391q" not in {x["msg_id"] for x in S.noid_pending(con)}, "'Hamara nahi' takes it off")
gq = c.post("/finance/slips/api/lab-noid", json={"reports": [more["reports"][4]]}, headers=TOK).get_json()["reports"][0]
ok(gq["clinic_id"] == "" and gq["gone"], "the mailbox is told it is not ours -- nothing filed")
r = c.post("/finance/slips/pending/act", data={"key": "nx:walk391m", "act": "noid_pick", "cid": "909311"})
ok("ok=" in r.headers["Location"] and "909311" in blood()[0], "a second tap on a placed report changes nothing")
r = c.post("/finance/slips/pending/act", data={"key": "nx:walk391p", "act": "noid_pick", "cid": ""})
ok("err=" in r.headers["Location"], "a pick with no patient is refused")

# the order is written after the report: the page's sweep joins it
USER["u"] = {"user": "alisha", "roles": ["maker"]}
con.execute("INSERT INTO patient_ref(clinic_id, name) VALUES (?,?)", ("909316", "Priyanka Walknew"))
con.execute("INSERT INTO blood_order(day, clinic_id, name_seen, logged_by, logged_at) VALUES (?,?,?,?,?)",
            (D4, "909316", "", "alisha", D4 + " 20:10:00"))
con.commit()
at(D4 + "T20:15:00")
c.get("/finance/slips/pending")
ok("909316" in blood()[1] and "walk391p" not in {x["msg_id"] for x in S.noid_pending(con)},
   "an order written after its report is joined on the next look")

# the doctors' counts
USER["u"] = {"user": "manoj", "roles": ["checker"]}
j = c.get("/finance/slips/api/pending-counts").get_json()
ok(j["ok"] and "no_id" in j and {"blood", "blood_red", "xray", "xray_red", "orphans", "name_mismatch"} <= set(j),
   "the doctors' counts carry the ID-less reports and keep every old field", j)

# negative control
A0, S0 = build(live, "old")
c0 = A0.test_client()
ok(c0.post("/finance/slips/api/lab-noid", json=body, headers=TOK).status_code in (404, 405) and not hasattr(S0, "noid_match"),
   "negative control: the live slip_log (S384) has no door for an ID-less report")
extra = {r.rule for r in A.url_map.iter_rules()} - {r.rule for r in A0.url_map.iter_rules()}
ok(extra == {"/finance/slips/api/lab-noid"} and not ({r.rule for r in A0.url_map.iter_rules()} - {r.rule for r in A.url_map.iter_rules()}),
   "exactly one new route, none lost", extra)
for t in ("blood_order", "lab_report", "patient_ref"):
    con.execute("DELETE FROM %s WHERE clinic_id LIKE '9093%%'" % t)
con.execute("DELETE FROM lab_noid WHERE msg_id LIKE 'walk391%'")
con.commit()
print("WALK OK %d/%d checks" % (N[0], N[0]))
