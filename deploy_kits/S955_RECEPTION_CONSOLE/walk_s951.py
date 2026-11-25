#!/usr/bin/env python3
"""walk_s951.py -- S951_YESTERDAY_CARRY: the walk on a MADE-UP console.db + inbox.db (every number 500000xxxx), built on
S948's own fixture (walk_s948.py beside this file) with the evening before added.

  python walk_s951.py walk <code dir>        every check; exit 0 only when all pass
  python walk_s951.py lists <code dir> <out> the staff lists (shivani, 11:30) as JSON, for the FROM/TO compare

Nothing here reads a real store: every path is a temp file. 'today' is 24-Nov (S948's fixture), 'yesterday' 23-Nov.
"""
import datetime as _dt
import json
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import walk_s948 as W  # noqa: E402

YDAY = (_dt.date.fromisoformat(W.TODAY) - _dt.timedelta(days=1)).isoformat()
DAY2 = (_dt.date.fromisoformat(W.TODAY) - _dt.timedelta(days=2)).isoformat()
FAILS = []


def ok(cond, what):
    print(("  PASS  " if cond else "  FAIL  ") + what)
    if not cond:
        FAILS.append(what)


def add_call(c, n, dr, a, day, hm, ring=8, dur=8, agent=""):
    jk = "%s_%d" % (W.ph(n), W.unix(hm, day))
    end = (_dt.datetime.strptime(day + " " + hm, "%Y-%m-%d %H:%M") + _dt.timedelta(seconds=dur)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO calls (status,direction,answered,total_duration,customer_talk_duration,customer_ring_duration,"
              "recording_filename,ended_at_ist,phone10,join_key,client_ref_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
              ("bridged" if a else "missed", dr, a, str(dur), str(max(0, dur - ring)) if a else "0", str(ring), "", end,
               W.ph(n), jk, ""))
    if agent:
        c.execute("INSERT INTO call_agent VALUES (?,?)", (jk, agent))


def add_msg(i, mid, n, dr, day, hm, body="Namaste"):
    i.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES (?,?,?,?,?,?,?,?,?)",
              (mid, W.ph(n), dr, day + " " + hm + ":00", "text", body, "delivered" if dr == "out" else "", "", ""))


def fixture(root, extra=True):
    con_p, inbox_p = W.make_fixture(root)
    if not extra:
        return con_p, inbox_p
    c = sqlite3.connect(con_p)
    for n, name, dx, cid in ((3020, "Carry Known", "Knee pain", "120"), (3021, "Came Yesterday", "Hip", "121"),
                             (3023, "Came Before", "Back", "123"), (3030, "Tried Thrice", "Hip", "130")):
        c.execute("INSERT INTO patients (phone10,name,diagnosis,age,gender,last_visit,patient_uid,clinic_id) VALUES (?,?,?,?,?,?,?,?)",
                  (W.ph(n), name, dx, "50", "F", "", "", cid))
    c.execute("INSERT INTO fu_all VALUES (?,?,?,?,?,?,?,?)", ("k3030", "Due Today", "", W.ph(3030), "", W.TODAY, "", ""))
    S, A_ = "Shivani Test", "Alisha Test"
    add_call(c, 3001, "In", 0, YDAY, "21:40")                       # A after hours, no try -> Incoming missed
    add_call(c, 3002, "In", 0, YDAY, "14:10")                       # B daytime, not reached -> Incoming missed
    add_call(c, 3003, "In", 0, YDAY, "20:00")                       # C answered after, same day -> not
    add_call(c, 3003, "In", 1, YDAY, "20:05", 5, 60, S)
    add_call(c, 3004, "In", 0, YDAY, "19:30")                       # D wrote after it -> WhatsApp tab
    add_call(c, 3005, "In", 0, YDAY, "21:00")                       # E one try today -> Call again
    add_call(c, 3005, "Out", 0, W.TODAY, "10:00", 12, 14, S)
    add_call(c, 3006, "In", 0, YDAY, "22:00")                       # F two tries today -> Evening calls
    add_call(c, 3006, "Out", 0, W.TODAY, "09:00", 12, 14, S)
    add_call(c, 3006, "Out", 0, W.TODAY, "10:00", 0, 2, S)
    add_call(c, 3007, "In", 0, YDAY, "22:00")                       # G three tries today -> ended
    for hm in ("09:00", "10:00", "11:00"):
        add_call(c, 3007, "Out", 0, W.TODAY, hm, 12, 14, S)
    add_call(c, 3008, "In", 0, YDAY, "22:00")                       # H reached today -> off
    add_call(c, 3008, "Out", 1, W.TODAY, "09:30", 5, 90, S)
    add_call(c, 3009, "In", 0, YDAY, "22:00")                       # I missed again today -> today's row only
    add_call(c, 3009, "In", 0, W.TODAY, "10:50")
    add_call(c, 3010, "In", 0, YDAY, "23:00")                       # J wrote today -> WhatsApp tab
    add_call(c, 3011, "In", 0, DAY2, "19:00")                       # L two days ago -> not
    add_call(c, 1, "In", 0, YDAY, "19:00")                          # K a follow-up patient -> once, missed path
    add_call(c, 3012, "In", 0, YDAY, "15:00")                       # N tried 3 times yesterday -> fresh day today
    for hm in ("16:00", "17:00", "18:00"):
        add_call(c, 3012, "Out", 0, YDAY, hm, 12, 14, A_)
    add_call(c, 3013, "In", 0, YDAY, "18:40")                       # O two misses, one in hours -> "not reached 2"
    add_call(c, 3013, "In", 0, YDAY, "21:15")
    add_call(c, 3018, "In", 0, YDAY, "21:10")                       # O2 two misses, both after 21:00 -> "after hours 2"
    add_call(c, 3018, "In", 0, YDAY, "22:30")
    add_call(c, 3020, "In", 0, YDAY, "20:20")                       # P an existing patient -> name + dx
    add_call(c, 3021, "In", 0, YDAY, "12:00")                       # V came yesterday (Docterz, by clinic ID) -> not
    add_call(c, 3022, "In", 0, YDAY, "12:30")                       # V2 a new number that came today (by its mobile) -> not
    add_call(c, 3023, "In", 0, YDAY, "13:00")                       # V3 a visit BEFORE yesterday -> still carried
    add_call(c, 3014, "In", 0, YDAY, "19:45")                       # Q answered BEFORE the miss -> still carried
    add_call(c, 3014, "In", 1, YDAY, "19:00", 5, 60, S)
    add_call(c, 3030, "In", 0, YDAY, "19:00")                       # R a follow-up patient tried 3 times yesterday
    for hm in ("19:30", "20:30", "21:30"):
        add_call(c, 3030, "Out", 0, YDAY, hm, 12, 14, A_)
    add_call(c, 3016, "In", 0, YDAY, "19:00")                       # T a number he marked spam -> not
    add_call(c, 3019, "Out", 0, YDAY, "10:00", 12, 14, S)           # W a try BEFORE the miss is not "tried yesterday"
    add_call(c, 3019, "In", 0, YDAY, "14:00")
    add_call(c, 3017, "In", 0, YDAY, "23:59", 120, 120)             # U rang 23:59, ended after midnight -> one row
    c.commit()
    c.close()
    i = sqlite3.connect(inbox_p)
    add_msg(i, "y3004", 3004, "in", YDAY, "19:40", "Kal aana hai")
    add_msg(i, "t3010", 3010, "in", W.TODAY, "09:00", "Missed call kiya tha")
    i.commit()
    i.close()
    f = sqlite3.connect(os.path.join(root, "no_finance.db"))      # the walk's made-up finance.db (S948's config names it)
    f.execute("CREATE TABLE patient_visit (visit_date TEXT, clinic_id TEXT, mobile_fp TEXT)")
    f.executemany("INSERT INTO patient_visit VALUES (?,?,?)", [(YDAY, "121.0", ""), (W.TODAY, "", "fp3022"), (DAY2, "123", "")])
    f.commit()
    f.close()
    return con_p, inbox_p


def lists(cl, user="shivani"):
    r = cl.get("/portal/console/staff/api/lists", headers=W.H(user))
    return r.status_code, (r.get_json() or {})


def rows_by(d):
    out = {}
    for k, v in (d.get("tabs") or {}).items():
        for r in v:
            out.setdefault(r["phone"], []).append((k, r))
    return out


def missed_tab(t):
    """The Incoming missed tab's own block of the page."""
    i = t.find('id="p-missed"')
    return t[i:t.find("</section>", i)] if i >= 0 else ""


def setup(root, con_p, inbox_p, now):
    app, cc, pm, _ = W.build_app(root, con_p, inbox_p, now)
    cc._H["spam_phones"] = lambda: [W.ph(3016)]
    cc._ro()._mobile_fp = lambda m: "fp" + str(m)[-4:]          # the walk's own fingerprint (the real one is salted)
    return app, cc


def do_walk(code):
    root = tempfile.mkdtemp(prefix="s951w_")
    con_p, inbox_p = fixture(root)
    app, cc = setup(root, con_p, inbox_p, W.NOW)
    cl = app.test_client()
    called = []
    cc.ivr_call = lambda p, login, **k: (called.append((p, login)) or (True, "Your phone is ringing", 200))
    st, d = lists(cl)
    ok(st == 200 and d.get("carry_ok") is True and str(d.get("kit", "")).startswith("S951") and d.get("carry_visits_ok") is True,
       "the lists: 200, carry_ok, the visits read, kit S951")
    R = rows_by(d)

    def tabs_of(n):
        return [k for k, _ in R.get(W.ph(n), [])]

    def calltabs(n):
        return [k for k in tabs_of(n) if k in ("due", "again", "eve", "missed")]

    def sub_of(n):
        x = [r for k, r in R.get(W.ph(n), []) if k in ("due", "again", "eve", "missed")]
        return x[0]["sub"] if x else ""

    def hi_of(n):
        x = [r for k, r in R.get(W.ph(n), []) if k in ("due", "again", "eve", "missed")]
        return x[0]["hi"] if x else None
    print("[1] who carries, and where")
    ok(calltabs(3001) == ["missed"] and sub_of(3001).startswith("Missed after hours (21:40)") and hi_of(3001) is True,
       "A 21:40 -> Incoming missed, 'Missed after hours (21:40)', lit")
    ok("new number - may be a patient on another mobile" in sub_of(3001), "A a new number says it may be a patient on another mobile")
    ok(__import__("re").search(r"\(21:40\) · \d+ (h|min|days) · new number", sub_of(3001)) is not None, "A says how long he has waited")
    ok(calltabs(3019) == ["missed"] and "tried" not in sub_of(3019), "W a try before the miss is not counted as 'tried yesterday'")
    ok(calltabs(3012) and "tried 3 times" in sub_of(3012), "N's three tries after the miss are")
    ok(calltabs(3002) == ["missed"] and sub_of(3002).startswith("Missed yesterday, not reached (14:10)"),
       "B 14:10 -> 'Missed yesterday, not reached (14:10)'")
    ok(calltabs(3003) == [], "C answered at 20:05 the same day -> not carried")
    ok(calltabs(3004) == [] and "wa" in tabs_of(3004), "D wrote after the miss -> the WhatsApp tab only")
    ok(calltabs(3005) == ["again"] and "call back 10:00 No answer" in sub_of(3005) and hi_of(3005) is False,
       "E one try today -> Call again, not lit before 12:00")
    ok(calltabs(3006) == ["eve"] and "2 attempts (09:00, 10:00) · last attempt today" in sub_of(3006), "F two tries today -> Evening calls")
    ok(calltabs(3007) == [], "G three tries today -> off the lists")
    ok(calltabs(3008) == [] and "mine" in tabs_of(3008), "H reached today -> off the call lists (in Handled today)")
    ok(calltabs(3009) == ["missed"] and "yesterday" not in sub_of(3009) and "after hours" not in sub_of(3009)
       and "(10:50)" in sub_of(3009) and len(R[W.ph(3009)]) == 1, "I missed again today -> today's row only, once")
    ok(calltabs(3010) == [], "J wrote today -> not on a call list")
    ok(calltabs(3011) == [], "L two days ago -> not carried")
    ok(calltabs(1) == ["missed"] and sub_of(1).startswith("Missed yesterday, not reached (19:00)"),
       "K a Due Today follow-up who rang yesterday -> once, on the missed path")
    ok(calltabs(3012) == ["missed"] and "tried 3 times yesterday" in sub_of(3012),
       "N tried 3 times yesterday -> a fresh day: Incoming missed, 'tried 3 times yesterday'")
    ok(calltabs(3013) == ["missed"] and "Missed yesterday, not reached 2 (18:40, 21:15)" in sub_of(3013),
       "O two misses, one in hours -> 'Missed yesterday, not reached 2'")
    ok(calltabs(3018) == ["missed"] and "Missed after hours 2 (21:10, 22:30)" in sub_of(3018), "O2 two after 21:00 -> 'Missed after hours 2'")
    p = [r for k, r in R.get(W.ph(3020), []) if k == "missed"]
    ok(len(p) == 1 and p[0]["name"] == "Carry Known" and "Knee pain" in p[0]["sub"] and "new number" not in p[0]["sub"],
       "P an existing patient: name + diagnosis")
    ok(calltabs(3021) == [], "V came yesterday (Docterz, clinic ID '121.0' = '121') -> not carried")
    ok(calltabs(3022) == [], "V2 a new number that came today (Docterz, by its mobile) -> not carried")
    ok(calltabs(3023) == ["missed"], "V3 a visit two days ago -> still carried")
    ok(calltabs(3014) == ["missed"], "Q answered BEFORE the miss -> still carried")
    ok(calltabs(3030) == ["missed"] and "tried 3 times yesterday" in sub_of(3030),
       "R a follow-up patient tried 3 times yesterday -> once, Incoming missed (not also on Follow-ups due)")
    ok(calltabs(3016) == [], "T a spam number -> not carried")
    ok(calltabs(3017) == ["missed"] and len(R.get(W.ph(3017), [])) == 1, "U rang 23:59, ended after midnight -> one row")
    ms = [r["phone"] for r in d["tabs"]["missed"]]
    try:
        order_ok = ms.index(W.ph(3002)) < ms.index(W.ph(3001)) < ms.index(W.ph(3009))
    except ValueError:
        order_ok = False
    ok(order_ok, "Incoming missed: yesterday's first (oldest first), then today's")
    ok(d["counts"]["missed"] == len(d["tabs"]["missed"]), "the count is the rows")
    print("[2] Call on a carried number")
    r = cl.post("/portal/console/staff/api/call", headers=W.H("shivani", post=True), json={"phone10": W.ph(3001)})
    ok(r.status_code == 200 and called and called[-1][0] == W.ph(3001), "Call on A dials it")
    print("[3] the page")
    t = cl.get("/portal/console/staff", headers=W.H("shivani")).get_data(as_text=True)
    blk = t.split("Missed after hours (21:40)")
    ok(len(blk) == 2 and ('data-ph="%s"' % W.ph(3001)) in blk[1][:1500], "the line on the page, with its Call button")
    print("[4] the setting")
    orig = cc._CFG
    cc._CFG = lambda k, dft="": "22:00" if k == "PORTAL_STAFF_AFTER_HOURS_FROM" else orig(k, dft)
    _, d2 = lists(cl)
    s2 = [r["sub"] for r in d2["tabs"]["missed"] if r["phone"] == W.ph(3001)]
    ok(s2 and s2[0].startswith("Missed yesterday, not reached (21:40)"), "PORTAL_STAFF_AFTER_HOURS_FROM=22:00 -> 21:40 reads 'not reached'")
    cc._CFG = lambda k, dft="": "bad" if k == "PORTAL_STAFF_AFTER_HOURS_FROM" else orig(k, dft)
    _, d3 = lists(cl)
    s3 = [r["sub"] for r in d3["tabs"]["missed"] if r["phone"] == W.ph(3001)]
    ok(s3 and s3[0].startswith("Missed after hours (21:40)"), "a bad setting falls back to 21:00")
    cc._CFG = orig
    print("[5] the Docterz visits unreadable")
    Rm = cc._ro()
    real_vs = Rm.visits_since
    Rm.visits_since = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("locked"))
    _, d6 = lists(cl)
    Rm.visits_since = real_vs
    R6 = rows_by(d6)
    ok(d6.get("carry_ok") is True and d6.get("carry_visits_ok") is False and W.ph(3021) in R6,
       "finance.db unreadable -> still carried (nothing confirms a visit), carry_visits_ok False")
    Rm.visits_since = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("locked"))
    t6 = cl.get("/portal/console/staff", headers=W.H("shivani")).get_data(as_text=True)
    ok("Docterz visits are not up to date" in missed_tab(t6) and "not up to date" not in t6.replace(missed_tab(t6), ""),
       "... and the Incoming missed tab says so (that tab only)")
    Rm.visits_since = lambda day, today, db=None: dict(real_vs(day, today, db), through=_dt.date.fromisoformat(DAY2))
    _, d7 = lists(cl)
    ok(d7.get("carry_visits_ok") is False, "yesterday's Docterz export not in yet -> carry_visits_ok False")
    Rm.visits_since = lambda day, today, db=None: dict(real_vs(day, today, db), through=_dt.date.fromisoformat(YDAY))
    _, d8 = lists(cl)
    ok(d8.get("carry_visits_ok") is True, "the newest visit is yesterday's -> the export is in (carry_visits_ok True)")
    Rm.visits_since = real_vs
    t0 = cl.get("/portal/console/staff", headers=W.H("shivani")).get_data(as_text=True)
    ok("not up to date" not in t0 and "could not be read just now - try again" not in t0, "all read -> no warning line")
    print("[6] a fault costs the carry only")
    real_bp = cc.build_people

    def bad_bp(conn, d_from, d_to, now, **k):
        if d_from == YDAY:
            raise RuntimeError("boom")
        return real_bp(conn, d_from, d_to, now, **k)
    cc.build_people = bad_bp
    st4, d4 = lists(cl)
    cc.build_people = real_bp
    ok(st4 == 200 and d4.get("carry_ok") is False, "yesterday unreadable -> 200, carry_ok False")
    cc.build_people = bad_bp
    t4 = cl.get("/portal/console/staff", headers=W.H("shivani")).get_data(as_text=True)
    cc.build_people = real_bp
    ok("missed calls could not be read just now" in missed_tab(t4) and "could not be read just now - try again in a few" not in t4.replace(missed_tab(t4), ""),
       "... and the Incoming missed tab says so (that tab only)")
    same = {k: [x["phone"] for x in v] for k, v in d4["tabs"].items()}
    ycar = ("Missed after hours", "Missed yesterday, not reached")
    base = {k: [x["phone"] for x in v if not x["sub"].startswith(ycar)] for k, v in d["tabs"].items()}
    ok(all(same[k] == base[k] for k in same if k != "due"), "every other tab's rows as before")
    ok([p for p in same["due"] if p not in (W.ph(1), W.ph(3030))] == base["due"] and W.ph(1) in same["due"] and W.ph(3030) in same["due"],
       "Follow-ups due as before, plus K and R (without the carry they are back there)")
    print("[7] the evening (16:30)")
    app2, _ = setup(root, con_p, inbox_p, W.NOW.replace(hour=16, minute=30))
    _, d5 = lists(app2.test_client())
    R5 = rows_by(d5)
    ok([k for k, _ in R5.get(W.ph(3006), [])] == ["eve"] and R5[W.ph(3006)][0][1]["hi"] is True, "F lit in the evening")
    ok([k for k, _ in R5.get(W.ph(3005), [])] == ["again"] and R5[W.ph(3005)][0][1]["hi"] is True, "E lit after 12:00")
    print("\n%d FAIL" % len(FAILS) if FAILS else "\nALL PASS")
    return 1 if FAILS else 0


def do_lists(code, out):
    root = tempfile.mkdtemp(prefix="s951l_")
    con_p, inbox_p = fixture(root, extra=False)
    res = {}
    for hh in (11, 16):
        app, cc, _, _ = W.build_app(root, con_p, inbox_p, W.NOW.replace(hour=hh, minute=30))
        cl = app.test_client()
        for u in ("shivani", "alisha", "shavez"):
            st, d = lists(cl, u)
            d.pop("kit", None)
            d.pop("carry_ok", None)
            d.pop("carry_visits_ok", None)
            res["%s_%d" % (u, hh)] = [st, d]
        res["page_%d" % hh] = cl.get("/portal/console/staff?as=shivani", headers=W.H("manoj", "doctor")).status_code
    open(out, "w").write(json.dumps(res, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    CODE = os.path.abspath(sys.argv[2])
    W.CODE = CODE
    sys.path.insert(0, CODE)
    if sys.argv[1] == "lists":
        do_lists(CODE, sys.argv[3])
        sys.exit(0)
    sys.exit(do_walk(CODE))
