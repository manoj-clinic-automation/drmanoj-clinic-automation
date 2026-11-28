#!/usr/bin/env python3
"""walk_s980.py -- kit S980_FILM_COUNT_RISE. Made-up counts only, through the real Flask routes of xray_film.py.
Usage: walk_s980.py FINANCE_DIR REAL_SCHEMA_DB.  Last line 'WALK S980: n PASS, m FAIL'."""
import sys, os, sqlite3, shutil, tempfile, datetime as dt
FIN, SCHEMA_DB = sys.argv[1], sys.argv[2]
sys.path.insert(0, FIN)
os.environ.update({"EVCHK_LIVE_DB": "/nonexistent/live.db", "RING_PORTAL_DIR": "/nonexistent/portal"})
from flask import Flask
import xray_film as xf, day_check as dc
TMP = tempfile.mkdtemp(prefix="w980_")
P = F = 0
def ok(n, c, info=""):
    global P, F
    if c: P += 1; print("PASS", n)
    else: F += 1; print("FAIL", n, str(info)[:200])
DDL = [r[0] for r in sqlite3.connect(SCHEMA_DB).execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index') AND sql IS NOT NULL AND name LIKE 'xf_%'")]
CON = [None]; USER = [{"user": "alisha", "roles": ["maker"]}]
app = Flask("w980"); app.config["TESTING"] = True
xf.init(app, lambda: CON[0], lambda *r, **k: (USER[0], None), None)
cl = app.test_client()
OWN = []
dc.PUSHER = lambda who, title, body, url, tag: (OWN.append((tuple(who), title, body)) or (1, ""))
T = dt.date.today()
n = [0]
def fresh(p8, p11, days_ago=2):
    n[0] += 1
    c = sqlite3.connect(os.path.join(TMP, "w%d.db" % n[0])); c.row_factory = sqlite3.Row
    for s in DDL:
        try: c.execute(s)
        except sqlite3.Error: pass
    c.commit(); CON[0] = c
    for a in ("_done", "_schema_done"):
        if hasattr(xf, a): setattr(xf, a, False)
    cl.get("/finance/slips/film/subah")                      # the page makes its own tables
    d = (T - dt.timedelta(days=days_ago)).isoformat()
    sid = c.execute("INSERT INTO xf_save (day, saved_at, saved_by, kind, note) VALUES (?,?,?,'count','')", (d, d + " 09:00:00", "shivani")).lastrowid
    for k, v in (("8x10", p8), ("11x14", p11)):
        c.execute("INSERT INTO xf_count (save_id, day, size, remaining, saved_at, saved_by) VALUES (?,?,?,?,?,?)", (sid, d, k, v, d + " 09:00:00", "shivani"))
    c.commit()
    OWN.clear()
    return c
def today_rows(c):
    return {r[0]: r[1] for r in c.execute("SELECT size, remaining FROM xf_count WHERE day=? AND void=0", (T.isoformat(),))}
def post(**f):
    r = cl.post("/finance/slips/film/subah", data=f)
    return r.headers.get("Location", "")

c = fresh(21, 137)
h = cl.get("/finance/slips/film/subah").get_data(as_text=True)
ok("E the new-box tick is offered to staff after a last count of 21", "name='newbox_8x10'" in h)
loc = post(c_8x10="140", c_11x14="135")
ok("B a rise with no tick is refused (asks for the tick)", "msg=tick" in loc and not today_rows(c), loc)
loc = post(c_8x10="140", c_11x14="135", newbox_8x10="1")
ok("A the box load from 21 is saved (the stuck case)", "msg=saved" in loc and today_rows(c) == {"8x10": 140, "11x14": 135}, (loc, today_rows(c)))
ok("A ... and told to him once", len(OWN) == 1 and OWN[0][0] == ("manoj",) and "21 -> 140" in OWN[0][2] and "Alisha" in OWN[0][1], OWN)
st = xf.stock(c, "8x10", T) if hasattr(xf, "stock") else None
rs = xf.readings(c, "8x10", T)
ok("A the readings record the box load on the day", rs[-1]["load"] is True and rs[-1]["left"] == 140, rs[-1])
c = fresh(21, 137)
loc = post(c_8x10="30", c_11x14="135", newbox_8x10="1")
ok("C a small rise from above 20 is still refused (a typo, never a box)", "msg=risen" in loc and not today_rows(c), loc)
c = fresh(15, 137)
loc = post(c_8x10="140", c_11x14="135", newbox_8x10="1")
ok("D a box load from 15 (the old rule) is saved, not told", "msg=saved" in loc and OWN == [], (loc, OWN))
c = fresh(21, 137)
loc = post(c_8x10="18", c_11x14="135")
ok("F a fall needs no tick, tells nobody", "msg=saved" in loc and today_rows(c)["8x10"] == 18 and OWN == [], (loc, OWN))
c = fresh(21, 137, days_ago=19)
loc = post(c_8x10="35", c_11x14="100", newbox_8x10="1", sure_11x14="1")
ok("H after a 19-day gap a small rise with the tick is a box load (review M1)", "msg=saved" in loc and today_rows(c)["8x10"] == 35, loc)
c = fresh(21, 137)
loc = post(c_8x10="15", c_11x14="135", newbox_8x10="1")
ok("I a ticked new box whose figure fell is refused, not dropped (review M2)", "msg=boxlow" in loc and not today_rows(c), loc)
ok("I ... the typed figures come back, the tick does not", "v_8x10=15" in loc and "nb_8x10" not in loc, loc)
h = cl.get(loc.split("localhost", 1)[-1] if loc.startswith("http") else loc).get_data(as_text=True)
ok("I ... the page says both ways out and keeps the figure", "tick hata kar Save kijiye" in h and "value='15'" in h, h[-300:])
c = fresh(60, 137)
loc = post(c_8x10="55", c_11x14="135", newbox_8x10="1")
ok("J a stray tick on a normal fall: refused once, figures kept", "msg=boxlow" in loc and "v_8x10=55" in loc, loc)
loc = post(c_8x10="55", c_11x14="135")
ok("J ... unticked, it saves", "msg=saved" in loc and today_rows(c)["8x10"] == 55, loc)
USER[0] = {"user": "manoj", "roles": ["checker"]}
c = fresh(21, 137)
loc = post(c_8x10="140", c_11x14="135", newbox_8x10="1")
ok("G his own save of a box load is saved and not pushed to himself", "msg=saved" in loc and OWN == [], (loc, OWN))
print("WALK S980: %d PASS, %d FAIL" % (P, F))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if F else 0)
