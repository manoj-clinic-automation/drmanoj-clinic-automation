#!/usr/bin/env python3
"""walk_s687.py -- kit S687_DARPAN_MONTH_JOBS (31-Oct-2026, the parent, S372). Runs the REAL finance app on COPIES only.

    --new  <fin> --db <copy> --scratch <dir> --kit <kitdir> [--root <root>] [--old <fin>] [--only M1,M2]
          every check on the files to test: the S687 checks through the real app (inner), the builder checks (when --root
          is given: make_s687.py re-run on <root> must give <fin>'s four files byte for byte), every other person's Aaj list
          unchanged against --old, and the mutants. Last line: "N of N green".
    --control <fin> --db <copy> --scratch <dir> --kit <kitdir>
          the CONTROL: the S687 checks only, on the LIVE files. Last line: "X S687 check(s) red . Y green".
    --inner <fin> --db <copy> --scratch <dir> --kit <kitdir>       (one process: the app is loaded once)
    --dump  <fin> --db <copy> --scratch <dir> --out <json> [--kit <kitdir>]   every person's list, as the owner sees it

<fin> is a folder holding a whole copy of /root/finance's code (never the database). --db is a COPY of finance.db; the walk
writes to it (made-up rows only: W687 names) and to nothing else but --scratch. DUTY_MAP_JSON (env) names the duty map when
it is not at /root/deploy/repo/claude_code_briefs/DUTY_MAP.json. Header sign-in is switched on for this process only.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys

NOW = "date('now','localtime')"
IDS = ("darpan.home_meds", "darpan.vehicle_check", "darpan.expiry_clear", "darpan.paper_renewal")
DOORS = {"darpan.home_meds": "/finance/monthjobs/home", "darpan.vehicle_check": "/finance/monthjobs/gaadi",
         "darpan.expiry_clear": "/finance/monthjobs/expiry", "darpan.paper_renewal": "/finance/monthjobs/kaagaz"}
WHENS = {"darpan.home_meds": "month", "darpan.vehicle_check": "month", "darpan.expiry_clear": "month", "darpan.paper_renewal": "comeup"}
PAGES = ("/finance/monthjobs", "/finance/monthjobs/home", "/finance/monthjobs/gaadi", "/finance/monthjobs/kaagaz",
         "/finance/monthjobs/expiry", "/finance/monthjobs/owner")
VEHICLES = [("Scooty", 0), ("Bike", 0), ("Kia", 0), ("Wagon R", 1), ("Vento", 1)]
TEN = re.compile(r"(?<!\d)\d{10,}(?!\d)")
SAVED_HI = "सेव हो गया"
CHECK_RE = re.compile(r"^  (ok |RED)  ")
results = []


def check(name, cond, note=""):
    results.append((name, bool(cond), note))
    print("  %s  %s%s" % ("ok " if cond else "RED", name, ("  -- " + str(note)[:220]) if note and not cond else ""))
    sys.stdout.flush()


def md5f(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def copydb(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def safe(fn, default=None):
    try:
        return fn()
    except Exception as e:                                             # noqa: BLE001
        return default if default is not None else ("ERR", "%s: %s" % (type(e).__name__, str(e)[:160]))


# ================================================================================================ the inner walk
def inner(a):
    fin, dbp, scr, kit = os.path.abspath(a.inner), os.path.abspath(a.db), os.path.abspath(a.scratch), os.path.abspath(a.kit)
    os.makedirs(scr, exist_ok=True)
    print("-- S687 inner walk: %s . db %s" % (fin, os.path.basename(dbp)))
    raw = sqlite3.connect(dbp, timeout=30, isolation_level=None)
    raw.row_factory = sqlite3.Row
    # ---- 0 the copy prepared: mj_* gone (first-request state), two made-up expired lines, the lists on, no saved Darpan panel
    for (t,) in list(raw.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mj\\_%' ESCAPE '\\'")):
        raw.execute("DROP TABLE %s" % t)
    have = {r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    run_id = None
    if {"stock_expiry_run", "stock_expiry_line"} <= have:
        r = raw.execute("SELECT MAX(id) FROM stock_expiry_run WHERE ok=1").fetchone()
        run_id = r[0]
        if run_id is None:
            run_id = raw.execute("INSERT INTO stock_expiry_run (at, today, ok, kit, note) VALUES ('2026-10-30T23:57:01','2026-10-30',1,'W687','walk')").lastrowid
        # A and B expired in September; C expires in November (listed by the watch from 1-Nov: next month-end's job);
        # Z has no units left on the shelf (never a job, as expiry_watch counts)
        for b, e, un, s in (("W687A", "2026-09", 3, 900001), ("W687B", "2026-09", 3, 900002), ("W687C", "2026-11", 2, 900003),
                            ("W687Z", "2026-09", 0, 900004)):
            raw.execute("INSERT INTO stock_expiry_line (run_id, section, part, k20, item, batch, expiry, units, pack, packing, seq) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (run_id, "expired", "", "W687 TEST ITEM", "W687 TEST ITEM", b, e, un, 1, "1*1", s))
    on = raw.execute("SELECT value FROM setting WHERE key='aaj.staff_on'").fetchone()
    if not (on and "|" in str(on[0] or "")):
        raw.execute("DELETE FROM setting WHERE key='aaj.staff_on'")
        raw.execute("INSERT INTO setting (key, value, note) VALUES ('aaj.staff_on','2026-10-07T11:27:09|manoj','S687 walk')")
    if "aaj_cfg" in have:
        raw.execute("DELETE FROM aaj_cfg WHERE person='darpan'")
    schema0 = {r[0]: r[1] for r in raw.execute("SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'mj\\_%' ESCAPE '\\' AND sql IS NOT NULL")}

    def exp_sum():
        return raw.execute("SELECT COUNT(*), COALESCE(SUM(id * 7 + units),0) FROM stock_expiry_line").fetchone()[:] if "stock_expiry_line" in have else (0, 0)
    exp0 = tuple(exp_sum())

    # ---- the files under test
    duties_path = os.path.join(fin, "aaj_duties.json")
    duties = safe(lambda: json.load(open(duties_path, encoding="utf-8")), {})
    extra = {x.get("id"): x for x in (duties.get("extra") or [])} if isinstance(duties, dict) else {}
    mine = [extra.get(i) for i in IDS]
    check("S687 F1 the duties file holds the four duties (person darpan, kind sql, each door its own job)",
          all(d and d.get("person") == "darpan" and d.get("kind") == "sql" and d.get("door") == DOORS[d["id"]] for d in mine),
          [d and d.get("door") for d in mine])
    check("S687 F2 each duty SQL is one read-only SELECT (WITH), no ';', its clock written exactly once",
          all(d and re.match(r"(?is)^(select|with)\b", d.get("sql") or "") and ";" not in d["sql"] and d["sql"].count(NOW) == 1 for d in mine))
    wpath = os.path.join(scr, "w687_duties.json")

    def write_duties(day=None):
        w = json.loads(json.dumps(duties)) if isinstance(duties, dict) else {}
        for x in w.get("extra") or []:
            if day and x.get("id") in IDS and isinstance(x.get("sql"), str):
                x["sql"] = x["sql"].replace(NOW, "'%s'" % day)
        with open(wpath, "w", encoding="utf-8") as fh:
            json.dump(w, fh, ensure_ascii=False)
    write_duties()
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", AAJ_DUTIES_JSON=wpath,
                      MONTHJOBS_NOW="2026-10-31T10:00:00")
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                           # noqa: E402
    import aaj_kaam                                                    # noqa: E402
    import aaj_seed                                                    # noqa: E402
    sys.path.insert(1, kit)
    import cfg_s687                                                    # noqa: E402
    mf = [n for n, _w in getattr(fa, "_MOUNT_FAILED", [])]
    check("S687 A1 the real finance app mounts with _MOUNT_FAILED empty, month_jobs loaded", mf == [] and "month_jobs" in sys.modules, mf)
    mj = sys.modules.get("month_jobs")
    seedd = next((p for p in aaj_seed.PEOPLE if p["key"] == "darpan"), {"lines": []})
    sl = {ln["id"]: ln for ln in seedd["lines"]}
    check("S687 F3 Darpan's panel: the four lines, on, three in the month group, the reminder under 'Jab aaye'",
          all(i in sl and sl[i]["on"] and sl[i]["when"] == WHENS[i] for i in IDS), [sl.get(i, {}).get("when") for i in IDS])
    check("S687 F4 the data step's lines are the seed's (id, words, group, on)",
          all(i in sl and any(x["id"] == i and x["hi"] == sl[i]["hi"] and x["en"] == sl[i]["en"] and x["when"] == sl[i]["when"] and x["on"]
                              for x in cfg_s687.LINES) for i in IDS))
    check("S687 F5 darpan.paper_renewal is in NO_HOLD (a reminder day before the floor is not held back)", "darpan.paper_renewal" in aaj_seed.NO_HOLD)

    c = fa.app.test_client(use_cookies=False)
    urls = []

    def req(method, path, user, data=None, now=None):
        if now:
            os.environ["MONTHJOBS_NOW"] = now
        h = {"X-Clinic-User": user} if user else {}
        r = c.get(path, headers=h) if method == "GET" else c.post(path, data=data or {}, headers=h)
        loc = (r.headers.get("Location") or "").replace("http://localhost", "")
        urls.append(path)
        if loc:
            urls.append(loc)
        return r.status_code, r.get_data(as_text=True), loc

    def G(path, user, now=None):
        return req("GET", path, user, now=now)

    def P(path, user, data, now=None):
        return req("POST", path, user, data, now)

    def follow(loc, user):
        return G(loc.replace("http://localhost", ""), user)

    pages = []

    def sq(sql, args=()):
        try:
            return raw.execute(sql, args).fetchall()
        except sqlite3.Error as e:
            return [("ERR", str(e))]

    def n_of(t):
        r = sq("SELECT COUNT(*) FROM %s" % t)
        return r[0][0] if r and r[0][0] != "ERR" else -1

    def due(did, day):
        d = extra.get(did)
        if not d:
            return ("no duty",)
        try:
            r = raw.execute(d["sql"].replace(NOW, "'%s'" % day)).fetchone()
            return (r[0], r[1]) if r[0] else (0,)
        except sqlite3.Error as e:
            return ("ERR", str(e)[:80])

    # ---- 1 the first request makes the tables and the five vehicles
    s, body, _l = G("/finance/monthjobs", "darpan")
    pages.append(body)
    tabs = {r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mj\\_%' ESCAPE '\\'")}
    check("S687 T1 Darpan's first request: 200 and the nine mj_* tables made", s == 200 and len(tabs) == 9, (s, sorted(tabs)))
    vs = sq("SELECT name, has_spare FROM mj_vehicle ORDER BY pos, id")
    check("S687 T2 five vehicles seeded; stepney / jack aur paana only on Wagon R and Vento", [tuple(r) for r in vs] == VEHICLES, [tuple(r) for r in vs])
    out1 = safe(lambda: cfg_s687.tables(dbp, fin), "ERR")
    out2 = safe(lambda: cfg_s687.panel(dbp), "ERR")
    check("S687 T3 the data step after it: 0 tables made, no saved Darpan panel, 0 changed (idempotent)",
          str(out1).startswith("tables: 0 made") and "0 changed" in str(out2), (out1, out2))

    # ---- 2 who reaches what
    want = {"manoj": {p: 200 for p in PAGES}, "darpan": {p: 200 for p in PAGES}}
    want["manoj"]["/finance/monthjobs"] = 302
    want["darpan"]["/finance/monthjobs/owner"] = 403
    got, bad = {}, []
    for u in ("manoj", "darpan", "shavez", "bhawna", "amir", "alisha", "shivani", "w687nobody", ""):
        for p in PAGES:
            st, b, loc = G(p, u)
            got[(u, p)] = st
            if u in ("manoj", "darpan"):
                pages.append(b)
            w = want.get(u, {}).get(p)
            if u in ("shavez", "bhawna", "amir", "alisha", "shivani"):          # the medical viewers
                w = 403
            elif u in ("w687nobody", ""):
                w = 302
            if st != w:
                bad.append((u or "anon", p, st, w))
    check("S687 R1 every page: manoj and darpan 200 (owner page manoj only); the medical viewers (shavez, bhawna, amir, alisha, shivani) 403; "
          "no medical role or no login 302",
          not bad, bad[:6])
    st, b, loc = G("/finance/monthjobs", "manoj")
    check("S687 R2 the owner's /finance/monthjobs goes to his English page", st == 302 and loc.endswith("/finance/monthjobs/owner"), (st, loc))
    n0 = n_of("mj_home_item")
    rr = [P("/finance/monthjobs/owner/item", "darpan", {"op": "add", "name": "W687 X", "unit": "strips", "need": "3"})[0],
          P("/finance/monthjobs/owner/settings", "darpan", {"home_floor": "2027-01"})[0],
          P("/finance/monthjobs/owner/vehicle", "darpan", {"op": "add", "name": "W687 V"})[0],
          P("/finance/monthjobs/owner/paper", "darpan", {"vehicle_id": "1", "paper": "rc", "expiry": "2027-01-01"})[0],
          P("/finance/monthjobs/home", "shavez", {})[0], P("/finance/monthjobs/gaadi", "bhawna", {})[0],
          P("/finance/monthjobs/expiry", "shavez", {})[0]]
    check("S687 R3 darpan cannot change a setting (item, floor, vehicle, paper date: 403); shavez / bhawna cannot save (403); nothing written",
          rr == [403] * 7 and n_of("mj_home_item") == n0 and n_of("mj_setting") == 0 and n_of("mj_paper") == 0 and n_of("mj_vehicle") == 5, rr)

    # ---- 3 the owner's home-medicine list
    locs = []
    for nm, unit, need in (("W687 Dawai A", "strips", "3"), ("W687 Dawai B", "bottle", "1"), ("W687 Dawai C", "strips", "2")):
        st, b, loc = P("/finance/monthjobs/owner/item", "manoj", {"op": "add", "name": nm, "unit": unit, "need": need})
        locs.append((st, loc))
    ids = {r[0]: r[1] for r in sq("SELECT name, id FROM mj_home_item")}
    st, b, loc = P("/finance/monthjobs/owner/item", "manoj", {"op": "edit", "id": str(ids.get("W687 Dawai B", 0)), "name": "W687 Dawai B",
                                                             "unit": "bottle", "need": "2"})
    st2, b2, loc2 = P("/finance/monthjobs/owner/item", "manoj", {"op": "retire", "id": str(ids.get("W687 Dawai C", 0))})
    stb, _b, locb = P("/finance/monthjobs/owner/item", "manoj", {"op": "add", "name": "W687 Bad", "unit": "x", "need": "abc"})
    g = follow(loc2, "manoj") if loc2 else (0, "", "")
    pages.append(g[1])
    rows = [tuple(r) for r in sq("SELECT name, unit, need, active FROM mj_home_item ORDER BY id")]
    aud = sq("SELECT COUNT(*) FROM audit_log WHERE table_name='mj_home_item'")
    check("S687 H1 the owner adds three, edits one, retires one -- each opens on the 'Saved' card, each audited; a bad number refused",
          all(s_ == 302 and "msg=saved" in l_ for s_, l_ in locs + [(st, loc), (st2, loc2)]) and "✓ Saved" in g[1]
          and rows == [("W687 Dawai A", "strips", 3.0, 1), ("W687 Dawai B", "bottle", 2.0, 1), ("W687 Dawai C", "strips", 2.0, 0)]
          and aud and aud[0][0] == 5 and "msg=bad" in locb, (rows, aud, locb))

    # ---- 4 the home-medicines line across the dates (no count saved yet)
    exp = {"2026-10-24": (0,), "2026-10-25": (1, "2026-10-25"), "2026-11-01": (1, "2026-10-25"), "2026-11-23": (1, "2026-10-25"),
           "2026-11-24": (1, "2026-11-24")}
    gotd = {d: due("darpan.home_meds", d) for d in exp}
    check("S687 D1 home medicines: 24-Oct not due; 25-Oct due for November; 1-Nov and 23-Nov still due; 24-Nov December's", gotd == exp, gotd)
    pyok = mj is not None and all(mj.home_month(__import__("datetime").date.fromisoformat(d)) == m for d, m in
                                  (("2026-10-24", "2026-10"), ("2026-10-25", "2026-11"), ("2026-11-23", "2026-11"), ("2026-11-24", "2026-12"),
                                   ("2027-02-21", "2027-02"), ("2027-02-22", "2027-03"), ("2026-12-25", "2027-01")))
    check("S687 D2 the page's month is the line's month (the month of today + 7 days; February's last 7 days too)", pyok)
    raw.execute("BEGIN")
    try:
        raw.execute("UPDATE mj_home_item SET active=0")
        noitem = due("darpan.home_meds", "2026-10-25")
    except sqlite3.Error as e:
        noitem = ("ERR", str(e)[:60])
    raw.execute("ROLLBACK")
    st, b, loc = P("/finance/monthjobs/owner/settings", "manoj", {"lead_pollution_n": "7", "lead_pollution_u": "days", "lead_insurance_n": "1",
                                                                 "lead_insurance_u": "months", "lead_rc_n": "45", "lead_rc_u": "days",
                                                                 "home_floor": "2026-12", "vehicle_floor": "2026-10", "expiry_floor": "2026-10"})
    fl = (due("darpan.home_meds", "2026-10-25"), due("darpan.home_meds", "2026-11-24"))
    P("/finance/monthjobs/owner/settings", "manoj", {"lead_pollution_n": "7", "lead_pollution_u": "days", "lead_insurance_n": "1",
                                                    "lead_insurance_u": "months", "lead_rc_n": "45", "lead_rc_u": "days",
                                                    "home_floor": "2026-11", "vehicle_floor": "2026-10", "expiry_floor": "2026-10"})
    check("S687 D3 no active medicine -> not due; the floor is a setting (December first -> 25-Oct not due, 24-Nov due), kept as rows",
          noitem == (0,) and st == 302 and fl == ((0,), (1, "2026-11-24")) and n_of("mj_setting") == 2, (noitem, fl, n_of("mj_setting")))

    # ---- 5 the vehicle line and the expiry line across the dates (nothing saved yet)
    expv = {"2026-10-30": (0,), "2026-10-31": (1, "2026-10-31"), "2026-11-15": (1, "2026-10-31"), "2026-11-29": (1, "2026-10-31"),
            "2026-11-30": (1, "2026-11-30")}
    gotv = {d: due("darpan.vehicle_check", d) for d in expv}
    check("S687 D4 vehicle check: 30-Oct not due; 31-Oct due; 15-Nov still due for October; 30-Nov November's", gotv == expv, gotv)
    pyv = mj is not None and all(mj.check_month(__import__("datetime").date.fromisoformat(d)) == m for d, m in
                                 (("2026-10-30", "2026-09"), ("2026-10-31", "2026-10"), ("2026-11-15", "2026-10"), ("2026-11-30", "2026-11"),
                                  ("2027-02-28", "2027-02"), ("2026-12-31", "2026-12")))
    check("S687 D5 the check page's month is the line's month (the latest month whose last day has come)", pyv)
    nexp = sq("SELECT COUNT(*) FROM stock_expiry_line WHERE run_id=? AND section='expired' AND units > 0 AND substr(expiry,1,7) <= '2026-10'",
              (run_id,))[0][0] if run_id else -1
    expe = {"2026-10-30": (0,), "2026-10-31": (nexp, "2026-10-31"), "2026-11-15": (nexp, "2026-10-31")}
    gote = {d: due("darpan.expiry_clear", d) for d in expe}
    check("S687 D6 expiry clear-out: 30-Oct not due; from 31-Oct every expired line of the newest run with units on the shelf and "
          "an expiry up to October (%s; the zero-units line not counted)" % nexp, nexp >= 2 and gote == expe, gote)
    expn = {"2026-11-02": (nexp, "2026-10-31"), "2026-11-29": (nexp, "2026-10-31"), "2026-11-30": (nexp + 1, "2026-11-30")}
    gotn = {d: due("darpan.expiry_clear", d) for d in expn}
    check("S687 D12 a batch expiring in November (listed from 1-Nov) is not counted on 2-Nov or 29-Nov, and is on 30-Nov", gotn == expn, gotn)
    st, b, _l = G("/finance/monthjobs/expiry", "darpan", now="2026-10-31T09:00:00")
    st2, b2, _l = G("/finance/monthjobs/expiry", "darpan", now="2026-11-30T09:00:00")
    pages.extend([b, b2])
    check("S687 P4 Darpan's expiry page on 31-Oct lists A and B, not the November batch, not the zero-units line; on 30-Nov the November batch too",
          "Batch W687A" in b and "Batch W687B" in b and "Batch W687C" not in b and "Batch W687Z" not in b
          and "Batch W687C" in b2 and "Batch W687Z" not in b2, st)

    # ---- 6 the pages before any save
    st, b, _l = G("/finance/monthjobs/home", "darpan", now="2026-10-24T09:00:00")
    pages.append(b)
    st2, b2, _l = G("/finance/monthjobs/home", "darpan", now="2026-10-25T09:00:00")
    pages.append(b2)
    st3, b3, _l = G("/finance/monthjobs/home", "darpan", now="2026-11-24T09:00:00")
    check("S687 P1 Darpan's count page: 24-Oct 'first count for November from 25-Oct'; 25-Oct 'Home medicines — November ke liye' with "
          "BACHI HAI / MANGWANA and the two active medicines; 24-Nov December's",
          "Pehli ginti November ke liye — 25-Oct se." in b and "name='left_" not in b
          and "Home medicines — November ke liye" in b2 and "BACHI HAI" in b2 and "MANGWANA" in b2 and "W687 Dawai A" in b2
          and "W687 Dawai B" in b2 and "W687 Dawai C" not in b2 and "Home medicines — December ke liye" in b3, (st, st2, st3))
    st, b, _l = G("/finance/monthjobs/gaadi", "darpan", now="2026-10-30T09:00:00")
    st2, b2, _l = G("/finance/monthjobs/gaadi", "darpan", now="2026-10-31T09:00:00")
    pages.append(b2)
    check("S687 P2 the vehicle page: 30-Oct 'first check on 31-Oct'; 31-Oct 'Gaadi ki jaanch — October', five vehicles, the spare items twice",
          "Pehli jaanch 31-Oct ko." in b and "Gaadi ki jaanch — October" in b2 and b2.count("class='card veh'") == 5
          and b2.count(">Stepney<") == 2 and b2.count(">Jack aur paana<") == 2 and b2.count(">Hai<") == 19, (b2.count(">Hai<"),))

    # ---- 7 papers (the owner enters; darpan cannot), the reminder line at its lead times
    vid = {r[0]: r[1] for r in sq("SELECT name, id FROM mj_vehicle")}
    pl = []
    for v, p, e in (("Kia", "pollution", "2026-11-20"), ("Kia", "insurance", "2026-12-15"), ("Kia", "rc", "2027-01-14")):
        pl.append(P("/finance/monthjobs/owner/paper", "manoj", {"vehicle_id": str(vid.get(v, 0)), "paper": p, "expiry": e}))
    expp = {"2026-11-12": (0,), "2026-11-13": (1, "2026-11-13"), "2026-11-14": (1, "2026-11-13"), "2026-11-15": (2, "2026-11-13"),
            "2026-11-29": (2, "2026-11-13"), "2026-11-30": (3, "2026-11-13")}
    gotp = {d: due("darpan.paper_renewal", d) for d in expp}
    check("S687 D7 paper reminders: pollution 7 days before (13-Nov), insurance one month before (15-Nov), RC 45 days before (30-Nov)",
          all(s_ == 302 and "msg=saved" in l_ for s_, _b, l_ in pl) and gotp == expp, gotp)
    P("/finance/monthjobs/owner/paper", "manoj", {"vehicle_id": str(vid.get("Kia", 0)), "paper": "pollution", "expiry": "2027-11-20"})
    rep = due("darpan.paper_renewal", "2026-11-15")
    hist = sq("SELECT COUNT(*) FROM mj_paper WHERE vehicle_id=? AND paper='pollution'", (vid.get("Kia", 0),))[0][0]
    check("S687 D8 a new pollution date replaces the old one (15-Nov: insurance only), the old one kept", rep == (1, "2026-11-15") and hist == 2, (rep, hist))
    P("/finance/monthjobs/owner/settings", "manoj", {"lead_pollution_n": "10", "lead_pollution_u": "days", "lead_insurance_n": "1",
                                                    "lead_insurance_u": "months", "lead_rc_n": "45", "lead_rc_u": "days",
                                                    "home_floor": "2026-11", "vehicle_floor": "2026-10", "expiry_floor": "2026-10"})
    P("/finance/monthjobs/owner/paper", "manoj", {"vehicle_id": str(vid.get("Kia", 0)), "paper": "pollution", "expiry": "2026-11-25"})
    lt = (due("darpan.paper_renewal", "2026-11-14"), due("darpan.paper_renewal", "2026-11-15"))
    P("/finance/monthjobs/owner/settings", "manoj", {"lead_pollution_n": "7", "lead_pollution_u": "days", "lead_insurance_n": "1",
                                                    "lead_insurance_u": "months", "lead_rc_n": "45", "lead_rc_u": "days",
                                                    "home_floor": "2026-11", "vehicle_floor": "2026-10", "expiry_floor": "2026-10"})
    P("/finance/monthjobs/owner/vehicle", "manoj", {"op": "retire", "id": str(vid.get("Kia", 0))})
    ret = due("darpan.paper_renewal", "2026-11-30")
    P("/finance/monthjobs/owner/vehicle", "manoj", {"op": "restore", "id": str(vid.get("Kia", 0)), "name": "Kia"})
    check("S687 D9 the lead time is a setting (pollution 10 days: due from 15-Nov, not 14-Nov); a retired vehicle reminds nothing",
          lt == ((0,), (2, "2026-11-15")) and ret == (0,), (lt, ret))
    P("/finance/monthjobs/owner/paper", "manoj", {"vehicle_id": str(vid.get("Scooty", 0)), "paper": "insurance", "expiry": "2027-03-31"})
    cl = [due("darpan.paper_renewal", d) for d in ("2027-02-27", "2027-02-28")]
    rem = safe(lambda: mj.remind_day(raw, "2027-03-31", "-1 month"), "ERR") if mj is not None else "no module"
    check("S687 D13 insurance ending 31-Mar is reminded from 28-Feb, never later than one calendar month before (not SQLite's 03-Mar); "
          "the page's day is the line's", len(cl) == 2 and len(cl[0]) == 2 and len(cl[1]) == 2 and cl[1][0] - cl[0][0] == 1 and rem == "2027-02-28",
          (cl, rem))
    st, b, _l = G("/finance/monthjobs/kaagaz", "darpan", now="2026-11-15T09:00:00")
    pages.append(b)
    st2, b2, _l = G("/finance/monthjobs/owner", "manoj", now="2026-11-15T09:00:00")
    pages.append(b2)
    check("S687 P3 Darpan's reminder page names vehicle, paper and date ('Kia — insurance 15-Dec-2026 ko khatm'), no date box; "
          "the owner's grid marks it due in amber",
          st == 200 and "Kia — insurance 15-Dec-2026 ko khatm" in b and "Naya kaagaz banwa kar" in b and "type='date'" not in b
          and "<td class='amb'><div>15-Dec-2026 <span class='due'>due</span>" in b2, st)
    # a paper whose reminder day fell before the staff floor (01-Oct): Bike's RC ending 20-Oct -> reminded from 05-Sep
    P("/finance/monthjobs/owner/paper", "manoj", {"vehicle_id": str(vid.get("Bike", 0)), "paper": "rc", "expiry": "2026-10-20"})

    # ---- 8 the Aaj lists: Darpan's four lines at a fixed day, every line read (unread = 0)
    def rows_of(user, as_=None):
        st_, b_, _l_ = G("/finance/aaj/api/list" + ("?as=%s" % as_ if as_ else ""), user)
        try:
            j = json.loads(b_)
        except ValueError:
            return st_, {}, []
        return st_, j, [dict(r, section=s_["key"]) for s_ in (j.get("sections") or []) for r in s_["rows"]]

    def unread(key):
        rd = aaj_kaam.Reader(dbp)
        try:
            return aaj_kaam.person_list(rd, rd.people[key])["unread"]
        finally:
            rd.close()
    write_duties("2026-10-31")
    st, j, rs = rows_of("darpan")
    new = {r["id"]: r for r in rs if r["id"] in IDS}
    check("S687 L1 Darpan's own list on 31-Oct: the four lines, each opening exactly its job, three under 'Is mahine', the reminder "
          "under 'Jab aaye', his words as on the panel",
          st == 200 and set(new) == set(IDS) and all(new[i]["door"] == DOORS[i] and new[i]["section"] == WHENS[i] and new[i]["kind"] == "job"
                                                     and new[i]["text"] == sl[i]["hi"] for i in IDS), (st, sorted(new), j.get("error")))
    check("S687 L2 Darpan's list is whole: unread = 0 (F-1024), not partial", safe(lambda: unread("darpan"), -1) == 0 and j.get("partial") is False,
          (safe(lambda: unread("darpan"), -1), j.get("partial")))
    st, j2, rs2 = rows_of("manoj", "darpan")
    others = []
    for u in ("shavez", "bhati", "alisha", "amir", "sukhveer"):
        _s, _j, r_ = rows_of("manoj", u)
        others += [(u, r["id"]) for r in r_ if r["id"] in IDS]
    check("S687 L3 the owner's view of darpan shows them; nobody else's list does", st == 200 and len([r for r in rs2 if r["id"] in IDS]) == 4 and not others, others)
    items = safe(lambda: aaj_kaam.build_all(dbp)["items"], [])
    bi = {i.get("id"): i for i in items if isinstance(i, dict) and i.get("id") in IDS}
    check("S687 L4 the owner's console reading (build_all): the four duties read, none in error, n > 0 on 31-Oct",
          set(bi) == set(IDS) and all(bi[i]["err"] is None and bi[i]["n"] > 0 for i in IDS), {k: (v["n"], v["err"]) for k, v in bi.items()})
    write_duties()
    check("S687 L5 on today's real clock the four lines read without an error too (unread = 0)", safe(lambda: unread("darpan"), -1) == 0)

    # ---- 9 the saves: count, check, outcomes -- each opens on the Saved card; the lines leave
    a_id, b_id = ids.get("W687 Dawai A", 0), ids.get("W687 Dawai B", 0)
    sb, _b, lb = P("/finance/monthjobs/home", "darpan", {"m": "2026-11", "left_%d" % a_id: "1"}, now="2026-10-27T10:00:00")
    nb = n_of("mj_home_count")
    st, b, loc = P("/finance/monthjobs/home", "darpan", {"m": "2026-11", "left_%d" % a_id: "1", "left_%d" % b_id: "5"}, now="2026-10-27T10:00:00")
    g = follow(loc, "darpan") if loc else (0, "", "")
    pages.append(g[1])
    ln = [tuple(r) for r in sq("SELECT l.name, l.need, l.left_qty, l.order_qty FROM mj_home_line l JOIN mj_home_count c ON c.id=l.count_id "
                               "WHERE c.saved_by='darpan' ORDER BY l.id")]
    check("S687 S1 Darpan saves November's count: MANGWANA = max(0, needed - left) (A 3-1 = 2, B 2-5 -> 0); the Saved card "
          "'सेव हो गया' with '1 dawai · 2 strips'; a count with a blank line refused, nothing written",
          "msg=blank" in lb and nb == 0 and st == 302 and "msg=saved" in loc and SAVED_HI in g[1] and "1 dawai · 2 strips" in g[1]
          and ln == [("W687 Dawai A", 3.0, 1.0, 2.0), ("W687 Dawai B", 2.0, 5.0, 0.0)], (lb, ln))
    st, b, loc = P("/finance/monthjobs/home", "manoj", {"m": "2026-11", "left_%d" % a_id: "3", "left_%d" % b_id: "0"}, now="2026-10-28T10:00:00")
    g = follow(loc, "manoj") if loc else (0, "", "")
    cnt = sq("SELECT saved_by FROM mj_home_count WHERE month='2026-11' ORDER BY id")
    st2, b2, _l = G("/finance/monthjobs/owner", "manoj", now="2026-10-28T11:00:00")
    pages.append(b2)
    check("S687 S2 the owner saves it again: his supersedes, Darpan's is kept; his page says who and when",
          st == 302 and "✓ Saved" in g[1] and [r[0] for r in cnt] == ["darpan", "manoj"]
          and "<span class='okc'>Saved</span> 28-Oct 10:00 by Dr Manoj" in b2 and "(1 earlier save(s) kept)" in b2, [r[0] for r in cnt])
    hd = (due("darpan.home_meds", "2026-11-01"), due("darpan.home_meds", "2026-11-24"))
    check("S687 D10 with November counted: 1-Nov not due; 24-Nov December's is", hd == ((0,), (1, "2026-11-24")), hd)

    form = {}
    for v, spare in VEHICLES:
        for k in ("pollution", "insurance", "rc") + (("stepney", "jack") if spare else ()):
            form["v%d_%s" % (vid.get(v, 0), k)] = "0" if (v, k) == ("Vento", "stepney") else "1"
    half = dict(form)
    half.pop("v%d_rc" % vid.get("Kia", 0), None)
    sh, _b, lh = P("/finance/monthjobs/gaadi", "darpan", dict(half, m="2026-10"), now="2026-10-31T18:00:00")
    st, b, loc = P("/finance/monthjobs/gaadi", "darpan", dict(form, m="2026-10"), now="2026-10-31T18:00:00")
    g = follow(loc, "darpan") if loc else (0, "", "")
    pages.append(g[1])
    st2, b2, _l = G("/finance/monthjobs/owner", "manoj", now="2026-10-31T19:00:00")
    pages.append(b2)
    check("S687 S3 Darpan saves October's check (one Save; a half-filled form refused); 'Nahi' on Vento's stepney is on the owner's page",
          "msg=blank" in lh and st == 302 and SAVED_HI in g[1] and n_of("mj_vehicle_check") == 1 and n_of("mj_vehicle_check_line") == 19
          and "<span class='nahi'>Vento: no stepney</span>" in b2, (lh, n_of("mj_vehicle_check_line")))
    vd = (due("darpan.vehicle_check", "2026-11-15"), due("darpan.vehicle_check", "2026-11-30"))
    check("S687 D11 with October checked: 15-Nov not due; 30-Nov November's is", vd == ((0,), (1, "2026-11-30")), vd)

    def okey(r):
        return "o_" + hashlib.md5("\x1f".join(str(r[c] or "") for c in ("k20", "batch", "expiry")).encode("utf-8")).hexdigest()[:16]

    def oct_lines(rid):
        return sq("SELECT id, k20, batch, expiry FROM stock_expiry_line WHERE run_id=? AND section='expired' AND units > 0 "
                  "AND substr(expiry,1,7) <= '2026-10' ORDER BY id", (rid,)) if rid else []
    lines = oct_lines(run_id)
    la = next((r for r in lines if r["batch"] == "W687A"), None) if lines and lines[0][0] != "ERR" else None
    ka = okey(la) if la is not None else "o_none"
    # THE SAVE RACE: Darpan's page was drawn from this run; a NEW expiry run lands (same lines, new row ids) before he saves
    new_run = None
    if run_id:
        new_run = raw.execute("INSERT INTO stock_expiry_run (at, today, ok, kit, export_as_on, note) "
                              "VALUES ('2026-10-31T18:01:00','2026-10-31',1,'W687','2026-10-30','walk: a run landing between load and save')").lastrowid
        raw.execute("INSERT INTO stock_expiry_line (run_id, section, part, k20, item, batch, expiry, units, pack, packing, seq) "
                    "SELECT ?, section, part, k20, item, batch, expiry, units, pack, packing, seq FROM stock_expiry_line WHERE run_id=? AND section='expired'",
                    (new_run, run_id))
        run_id = new_run
        exp0 = tuple(exp_sum())                                        # the walk's own run; the pages must not touch it either
    sbad, _b, lbad = P("/finance/monthjobs/expiry", "darpan", {ka: "kuch"}, now="2026-10-31T18:00:00")
    sst, _b, lst_ = P("/finance/monthjobs/expiry", "darpan", {"o_" + "0" * 16: "nasht"}, now="2026-10-31T18:00:00")
    st, b, loc = P("/finance/monthjobs/expiry", "darpan", {ka: "wapas"}, now="2026-10-31T18:00:00")
    g = follow(loc, "darpan") if loc else (0, "", "")
    pages.append(g[1])
    sdup, _b, ldup = P("/finance/monthjobs/expiry", "darpan", {ka: "wapas"}, now="2026-10-31T18:05:00")
    o = [tuple(r) for r in sq("SELECT k20, batch, expiry, outcome, saved_by, run_id FROM mj_expiry_outcome")]
    ed = due("darpan.expiry_clear", "2026-10-31")
    check("S687 S4 Darpan marks batch W687A 'supplier ko wapas' on a page drawn before a NEW expiry run landed: kept by item, batch and "
          "expiry against the new run; the other batch still waits (n %s -> %s); an unknown answer refused; an answer for a line no longer "
          "on the list said, not dropped silently; the same answer twice not kept twice" % (nexp, nexp - 1),
          "msg=bad" in lbad and "msg=stale" in lst_ and st == 302 and SAVED_HI in g[1]
          and o == [("W687 TEST ITEM", "W687A", "2026-09", "wapas", "darpan", new_run)]
          and ed == (nexp - 1, "2026-10-31") and "msg=none" in ldup, (o, ed, lst_, ldup))
    lines = oct_lines(run_id)
    form = {okey(r): "nasht" for r in lines if r["batch"] != "W687A"} if lines and lines[0][0] != "ERR" else {}
    P("/finance/monthjobs/expiry", "darpan", form, now="2026-10-31T18:10:00")
    st2, b2, _l = G("/finance/monthjobs/owner", "manoj", now="2026-10-31T19:00:00")
    pages.append(b2)
    check("S687 S5 every line answered: the line is done (0); the owner's page shows the outcomes",
          due("darpan.expiry_clear", "2026-10-31") == (0,) and "Returned to the supplier <span class='sm'>by Darpan" in b2
          and "Destroyed <span class='sm'>by Darpan" in b2 and "<span class='okc'>Done</span>" in b2)
    write_duties("2026-10-31")
    st, j, rs = rows_of("darpan")
    left = sorted(r["id"] for r in rs if r["id"] in IDS)
    check("S687 L6 after the saves Darpan's 31-Oct list keeps only the paper reminder (Bike's RC, its reminder day before the floor, not held)",
          left == ["darpan.paper_renewal"] and safe(lambda: unread("darpan"), -1) == 0, left)
    write_duties()

    # ---- 10 the pages' words, the URLs, the tables
    jp = "".join(p for p in pages if isinstance(p, str))
    check("S687 W1 no rupee amount on any of these pages", "₹" not in jp and not re.search(r"\bRs\.? ?\d", jp) and "rupee" not in jp.lower())
    st, own, _l = G("/finance/monthjobs/owner", "manoj")
    check("S687 W2 the owner's page is English (no Devanagari), with its five parts",
          st == 200 and not re.search(r"[ऀ-ॿ]", own) and all(x in own for x in ("THIS MONTH", "SETTINGS · HOME MEDICINES",
                                                                                         "VEHICLE PAPERS · REMINDERS", "LEAD TIMES", "EXPIRY OUTCOMES")))
    bad_urls = [u for u in urls if TEN.search(u) or not re.match(r"^/portal$|^/finance/(monthjobs|aaj)[A-Za-z0-9/_\-]*(\?((m|msg|id|n|s|what|as)=[A-Za-z0-9_.\-]*&?)*)?$", u)]
    hrefs = re.findall(r"(?:href|action)='([^']*)'", jp)
    bad_h = [h for h in hrefs if TEN.search(h)]
    check("S687 W3 no patient data and no ten-digit number in any URL or link (only m, msg, id, n, what in a query)", not bad_urls and not bad_h,
          (bad_urls[:4], bad_h[:4]))
    schema1 = {r[0]: r[1] for r in raw.execute("SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'mj\\_%' ESCAPE '\\' AND sql IS NOT NULL")}
    newt = sorted(r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table'") if r[0] not in schema0 and not r[0].startswith("mj_"))
    check("S687 W4 additive only: no existing table changed, every new table mj_*; Sanjeevni's expiry lines untouched by the pages",
          schema1 == schema0 and not newt and tuple(exp_sum()) == exp0, (newt, tuple(exp_sum()), exp0))
    big = re.findall(r"min-height:(\d+)px", jp)
    check("S687 W5 touch targets: every button and choice of the pages at least 44 px", big and min(int(x) for x in big) >= 44, sorted(set(big)))

    # ---- 11 the data step on a saved Darpan panel (its own copy)
    cdb = os.path.join(scr, "cfg.db")
    copydb(dbp, cdb)
    cc = sqlite3.connect(cdb)
    cc.execute("CREATE TABLE IF NOT EXISTS aaj_cfg (person TEXT PRIMARY KEY, doc TEXT NOT NULL, edited_at TEXT NOT NULL, edited_by TEXT NOT NULL)")
    old_lines = [dict(id=x["id"], hi=x["hi"], en=x.get("en", ""), when=x["when"], on=x["on"]) for x in seedd["lines"] if x["id"] not in IDS]
    doc = dict(on=True, note="", first_on=None, lines=old_lines, removed=[dict(id="darpan.paper_renewal", hi="Kaagaz ki yaad", en="", when="comeup", on=False)])
    cc.execute("INSERT OR REPLACE INTO aaj_cfg VALUES ('darpan', ?, '2026-10-30T10:00:00', 'manoj')", (json.dumps(doc),))
    cc.commit()
    cc.close()

    def merged():
        con_ = sqlite3.connect("file:%s?mode=ro" % cdb, uri=True)
        try:
            p = aaj_kaam.cfg_load(con_)[0]["darpan"]
            return {ln["id"]: bool(ln["on"]) for ln in p["lines"] if ln["id"] in IDS}
        finally:
            con_.close()
    m0 = safe(merged, {})
    r1 = safe(lambda: cfg_s687.panel(cdb), "ERR")
    m1 = safe(merged, {})
    r2 = safe(lambda: cfg_s687.panel(cdb), "ERR")
    check("S687 C1 a saved Darpan panel: before the data step the three month lines would show OFF (new); the step puts them ON, "
          "the line the owner took off stays off; a second run changes nothing",
          m0 == {i: False for i in IDS[:3]} and "3 changed" in str(r1) and m1 == {i: True for i in IDS[:3]} and "0 changed" in str(r2), (m0, r1, m1, r2))
    os.remove(cdb)
    red = sum(1 for r in results if not r[1])
    print("INNER %d red . %d green" % (red, len(results) - red))
    return 0


# ================================================================================================ every person's list (for old = new)
def dump(a):
    fin, dbp = os.path.abspath(a.dump), os.path.abspath(a.db)
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="", FINANCE_DEV_ROLE="")
    os.environ.pop("AAJ_DUTIES_JSON", None)
    if a.kit and os.path.isfile(os.path.join(fin, "month_jobs.py")):
        sys.path.insert(0, fin)
        sys.path.insert(1, os.path.abspath(a.kit))
        import cfg_s687                                                # noqa: E402
        cfg_s687.tables(dbp, fin)                                      # as the installer's data step does before the restart
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                           # noqa: E402
    import aaj_kaam                                                    # noqa: E402
    import aaj_seed                                                    # noqa: E402
    c = fa.app.test_client(use_cookies=False)
    out = {"mount_failed": [n for n, _w in fa._MOUNT_FAILED], "lists": {}, "unread": {}, "own": {}}
    for p in aaj_seed.PEOPLE:
        r = c.get("/finance/aaj/api/list?as=%s" % p["key"], headers={"X-Clinic-User": "manoj"})
        j = r.get_json(silent=True) or {}
        out["lists"][p["key"]] = [(s["key"], x["id"], x["kind"], x["text"], x.get("door")) for s in (j.get("sections") or []) for x in s["rows"]]
    for login in ("alisha", "shivani", "shavez", "bhati", "darpan", "amir", "sukhveer"):
        r = c.get("/finance/aaj/api/list", headers={"X-Clinic-User": login})
        j = r.get_json(silent=True) or {}
        out["own"][login] = (r.status_code, j.get("partial"), [(s["key"], x["id"]) for s in (j.get("sections") or []) for x in s["rows"]])
    rd = aaj_kaam.Reader(dbp)
    try:
        for k, doc in rd.people.items():
            out["unread"][k] = aaj_kaam.person_list(rd, doc)["unread"]
    finally:
        rd.close()
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    return 0


# ================================================================================================ the outer walk
def run_inner(fin, db, scr, kit, tag):
    shutil.rmtree(scr, ignore_errors=True)
    os.makedirs(scr)
    wdb = os.path.join(scr, "inner.db")
    copydb(db, wdb)
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", fin, "--db", wdb, "--scratch", scr, "--kit", kit],
                       cwd="/tmp", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    outp = p.stdout.decode("utf-8", "replace")
    for f in (wdb, wdb + "-journal", wdb + "-wal", wdb + "-shm"):
        if os.path.exists(f):
            os.remove(f)
    m = re.search(r"^INNER (\d+) red \. (\d+) green$", outp, re.M)
    return (int(m.group(1)), int(m.group(2))) if m else None, outp


def mkfin(src, dst, over=None):
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("*.db", "*.db-*", "*.bak*", "__pycache__", "*uploads*", "*.gz", "*.tar"))
    for f, b in (over or {}).items():
        with open(os.path.join(dst, f), "wb") as fh:
            fh.write(b)


MUTANTS = [
    ("X1", "the home line due one day early (today + 8 days)", "aaj_duties.json", "darpan.home_meds", "'+7 days'", "'+8 days'"),
    ("X2", "the home line's 7-day window removed (today + 0 days)", "aaj_duties.json", "darpan.home_meds", "'+7 days'", "'+0 days'"),
    ("X3", "the vehicle check due on the 30th", "aaj_duties.json", "darpan.vehicle_check", "'+1 day', 'start of month'", "'+2 day', 'start of month'"),
    ("X4", "a 'Nahi' not shown on the owner's page", "month_jobs.py", None,
     'return [(ln["vehicle"], ln["item"]) for ln in lines.values() if not ln["present"]]', "return []"),
    ("X5", "Darpan allowed to edit the settings", "month_jobs.py", None, 'u, _lang = _user("checker")', 'u, _lang = _user("maker", "checker")'),
    ("X6", "the expiry outcome not keyed by batch", "aaj_duties.json", "darpan.expiry_clear", " AND o.batch = COALESCE(l.batch, '')", ""),
    ("X7", "MANGWANA without the max(0, ...)", "month_jobs.py", None, "return max(0.0, round(float(need) - float(left), 2))",
     "return round(float(need) - float(left), 2)"),
    ("X8", "a new paper date ignored (the oldest date read)", "aaj_duties.json", "darpan.paper_renewal", "SELECT MAX(q.id)", "SELECT MIN(q.id)"),
    ("X9", "the reminder held back from staff (not in NO_HOLD)", "aaj_seed.py", None, ',\n           "darpan.paper_renewal")', ")"),
    ("X10", "no Saved card after a save", "month_jobs.py", None, 'head = "✓ Saved — सेव हो गया" if lang == "hi" else "✓ Saved"', 'head = "OK"'),
    ("X11", "the expiry line's month gate removed (a batch turning expired on the 1st due from the 2nd)", "aaj_duties.json", "darpan.expiry_clear",
     " AND substr(COALESCE(l.expiry, ''), 1, 7) <= (SELECT m FROM x)", ""),
    ("X12", "expired lines with no units counted", "aaj_duties.json", "darpan.expiry_clear", " AND COALESCE(l.units, 0) > 0", ""),
    ("X13", "the insurance month not clamped (31-Mar reminded on 03-Mar)", "aaj_duties.json", "darpan.paper_renewal",
     "MIN(date(p.expiry, ld.md), date(p.expiry, 'start of month', ld.md, '+1 month', '-1 day'))", "date(p.expiry, ld.md)"),
    ("X14", "the expiry form keyed by row id (a new run drops the answers)", "month_jobs.py", None,
     'return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]', 'return str(ln["id"])'),
    ("X15", "the expiry page's month gate removed", "month_jobs.py", None,
     '"AND substr(COALESCE(expiry, \'\'), 1, 7) <= ? ORDER BY seq, id", (r["id"], ym)))', '"ORDER BY seq, id", (r["id"],)))'),
]


def mutate(fin, mid):
    for x in MUTANTS:
        if x[0] != mid:
            continue
        _i, _w, f, did, old, new = x
        p = os.path.join(fin, f)
        s = open(p, encoding="utf-8").read()
        if did is None:
            if s.count(old) != 1:
                return None
            s = s.replace(old, new)
        else:
            j = json.loads(s)
            hit = [d for d in j["extra"] if d.get("id") == did]
            if len(hit) != 1 or hit[0]["sql"].count(old) != 1:
                return None
            hit[0]["sql"] = hit[0]["sql"].replace(old, new)
            s = json.dumps(j, ensure_ascii=False, indent=1)
        return {f: s.encode("utf-8")}
    return None


def builder_checks(a, fin, scr):
    kit, root = os.path.abspath(a.kit), os.path.abspath(a.root)
    files = ("finance/finance_app.py", "finance/aaj_duties.json", "finance/aaj_seed.py", "finance/month_jobs.py")
    b1 = os.path.join(scr, "b1")
    shutil.rmtree(b1, ignore_errors=True)
    p = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s687.py"), root, b1], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    o = p.stdout.decode("utf-8", "replace")
    same = p.returncode == 0 and all(md5f(os.path.join(b1, f)) == md5f(os.path.join(fin, f[len("finance/"):])) for f in files)
    check("M1 make_s687.py re-run on the FROM files gives the four TO files byte for byte", same, o[-300:])
    check("M2 its edits are counted: 4, each anchor found exactly once", "4 counted edits, each anchor found exactly once" in o and o.count("edit ok:") == 4)
    r2 = os.path.join(scr, "r2")
    shutil.rmtree(r2, ignore_errors=True)
    os.makedirs(os.path.join(r2, "finance"))
    for f in files[:3]:
        shutil.copyfile(os.path.join(root, f), os.path.join(r2, f))
    with open(os.path.join(r2, "finance/aaj_seed.py"), "ab") as fh:
        fh.write(b"\n")
    b2 = os.path.join(scr, "b2")
    p2 = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s687.py"), r2, b2], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    check("M3 a changed FROM file is refused, nothing written", p2.returncode != 0 and not os.path.exists(b2), p2.stdout[-160:])
    shutil.copyfile(os.path.join(root, "finance/aaj_seed.py"), os.path.join(r2, "finance/aaj_seed.py"))
    with open(os.path.join(r2, "finance/month_jobs.py"), "w") as fh:
        fh.write("# someone else's\n")
    p3 = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s687.py"), r2, b2], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    check("M4 a month_jobs.py already on the box is refused, nothing written", p3.returncode != 0 and not os.path.exists(b2), p3.stdout[-160:])
    sys.path.insert(0, kit)
    import make_s687 as mk                                             # noqa: E402
    olda = open(os.path.join(root, files[0]), encoding="utf-8").read()
    newa = open(os.path.join(fin, "finance_app.py"), encoding="utf-8").read()
    check("M5 finance_app.py: exactly ONE inserted mount block, nothing else changed", newa.replace(mk.MOUNT, mk.MOUNT_ANCHOR, 1) == olda
          and newa.count("import month_jobs") == 1 and len(newa.splitlines()) - len(olda.splitlines()) == mk.MOUNT.count("\n") - 1)
    olds = open(os.path.join(root, files[2]), encoding="utf-8").read()
    news = open(os.path.join(fin, "aaj_seed.py"), encoding="utf-8").read()
    back = news.replace(mk.NOHOLD_NEW, mk.NOHOLD_OLD).replace("},\n" + mk.seed_lines_text() + "]}]\n\nSEPT", "}]}]\n\nSEPT")
    check("M6 aaj_seed.py: NO_HOLD and Darpan's four lines only", back == olds)
    oj = json.load(open(os.path.join(root, files[1]), encoding="utf-8"))
    nj = json.load(open(os.path.join(fin, "aaj_duties.json"), encoding="utf-8"))
    check("M7 aaj_duties.json: the four duties added at the end, every other key and duty as it was",
          {k: v for k, v in nj.items() if k != "extra"} == {k: v for k, v in oj.items() if k != "extra"}
          and nj["extra"][:len(oj["extra"])] == oj["extra"] and [d["id"] for d in nj["extra"][len(oj["extra"]):]] == list(IDS))
    kf = [os.path.join(kit, f) for f in sorted(os.listdir(kit)) if os.path.isfile(os.path.join(kit, f))]
    ten = [os.path.basename(f) for f in kf if TEN.search(open(f, "rb").read().decode("utf-8", "replace"))]
    crlf = [os.path.basename(f) for f in kf if b"\r" in open(f, "rb").read()]
    check("M8 no ten-digit number in any kit file; every kit file LF only", not ten and not crlf, (ten, crlf))
    bad = []
    for f in [x for x in kf if x.endswith(".py")] + [os.path.join(fin, "month_jobs.py"), os.path.join(fin, "finance_app.py"), os.path.join(fin, "aaj_seed.py")]:
        q = subprocess.run([sys.executable, "-c", "import sys,py_compile; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)", f,
                            os.path.join(scr, "pc.pyc")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if q.returncode:
            bad.append(os.path.basename(f))
    check("M9 every kit and built python file compiles", not bad, bad)
    for d in (b1, r2):
        shutil.rmtree(d, ignore_errors=True)


def outer(a):
    scr = os.path.abspath(a.scratch)
    os.makedirs(scr, exist_ok=True)
    kit = os.path.abspath(a.kit)
    if a.control:
        fin = os.path.abspath(a.control)
        print("CONTROL -- the S687 checks on the LIVE files")
        sc, outp = run_inner(fin, a.db, os.path.join(scr, "c0"), kit, "live")
        print("\n".join(l for l in outp.splitlines() if CHECK_RE.match(l)))
        if sc is None:
            print(outp[-600:])
            print("CONTROL did not finish")
            return 1
        print("%d S687 check(s) red . %d green" % sc)
        return 0
    fin = os.path.abspath(a.new)
    only = set((a.only or "").split(",")) - {""}
    if not only or "inner" in only:
        print("THE FILES -- the S687 checks through the real app")
        sc, outp = run_inner(fin, a.db, os.path.join(scr, "n0"), kit, "new")
        for l in outp.splitlines():
            if CHECK_RE.match(l):
                print(l)
                results.append((l[7:], l.startswith("  ok "), ""))
        if sc is None:
            print(outp[-800:])
            check("the inner walk finished", False)
    if a.root and (not only or "builder" in only):
        print("THE BUILDER")
        builder_checks(a, fin, scr)
    if a.old and (not only or "lists" in only):
        print("EVERY PERSON'S AAJ LIST -- the live files against these, on two identical copies, today's clock")
        outs = {}
        for tag, f in (("old", os.path.abspath(a.old)), ("new", fin)):
            d = os.path.join(scr, "d_%s.db" % tag)
            copydb(a.db, d)
            o = os.path.join(scr, "d_%s.json" % tag)
            p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--dump", f, "--db", d, "--scratch", scr, "--out", o, "--kit", kit],
                               cwd="/tmp", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
            outs[tag] = json.load(open(o)) if p.returncode == 0 and os.path.exists(o) else None
            for x in (d, o):
                if os.path.exists(x):
                    os.remove(x)
            if outs[tag] is None:
                print(p.stdout.decode("utf-8", "replace")[-600:])
        o_, n_ = outs.get("old"), outs.get("new")
        ok = o_ is not None and n_ is not None
        diff = []
        if ok:
            for k in sorted(set(o_["lists"]) | set(n_["lists"])):
                a1 = o_["lists"].get(k)
                b1 = [x for x in (n_["lists"].get(k) or []) if x[1] not in IDS]
                if a1 != b1:
                    diff.append(k)
        check("B1 every person's list as the owner sees it (?as=) is unchanged apart from Darpan's new lines", ok and not diff, diff)
        check("B2 every login's own list unchanged apart from Darpan's new lines (status, partial, lines)",
              ok and all((o_["own"][k][0], o_["own"][k][1], o_["own"][k][2]) ==
                         (n_["own"][k][0], n_["own"][k][1], [x for x in n_["own"][k][2] if x[1] not in IDS]) for k in o_["own"]),
              ok and {k: (o_["own"][k][:2], n_["own"][k][:2]) for k in o_["own"]})
        check("B3 unread per person unchanged (darpan's new lines all read: F-1024)", ok and o_["unread"] == n_["unread"],
              ok and (o_["unread"], n_["unread"]))
        check("B4 the app mounts on both, _MOUNT_FAILED empty", ok and o_["mount_failed"] == [] and n_["mount_failed"] == [])
    if not only or [x for x in only if x.startswith("X")]:
        print("THE MUTANTS -- each must turn at least one S687 check red")
        for x in MUTANTS:
            if only and "mutants" not in only and x[0] not in only:
                continue
            over = mutate(fin, x[0])
            if over is None:
                check("%s %s: the mutation applies" % (x[0], x[1]), False)
                continue
            mf = os.path.join(scr, "mut_fin")
            mkfin(fin, mf, over)
            sc, outp = run_inner(mf, a.db, os.path.join(scr, "m_" + x[0]), kit, x[0])
            reds = [l[7:60] for l in outp.splitlines() if l.startswith("  RED  ")]
            check("%s caught: %s (%s)" % (x[0], x[1], (reds[0].strip() if reds else "no red")), sc is not None and sc[0] >= 1, outp[-300:] if sc is None else "")
            shutil.rmtree(mf, ignore_errors=True)
    green = sum(1 for r in results if r[1])
    print("%d of %d green" % (green, len(results)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--new")
    g.add_argument("--control")
    g.add_argument("--inner")
    g.add_argument("--dump")
    ap.add_argument("--db", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--kit")
    ap.add_argument("--root")
    ap.add_argument("--old")
    ap.add_argument("--out")
    ap.add_argument("--only")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder by accident
    if a.inner:
        return inner(a)
    if a.dump:
        return dump(a)
    if not a.kit:
        raise SystemExit("--kit is needed")
    return outer(a)


if __name__ == "__main__":
    sys.exit(main())
